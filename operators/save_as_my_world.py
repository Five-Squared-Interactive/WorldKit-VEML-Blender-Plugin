# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Issue #119 — "Save as My World": saves the open .blend, then hands it to
# veml-ingest's own --deploy invocation — the same bare command
# corpus/README.md records. No pipeline knowledge is duplicated here: this
# operator saves the file and shells out; veml-ingest stays the single
# owner of what a world is. Command construction lives in the bpy-free
# properties/deploy_command.py (the entry_point.py precedent, #115) so CI
# pins the argv/validation rules without a Blender install.

import os
import subprocess
import webbrowser

import bpy

#: Written as constants because the report is assembled from them and a
#: literal escape has been mangled by tooling more than once.
NEWLINE = chr(10)
EXITED = "(veml-ingest exited %d)"

from ..properties import deploy_command, sign_in_flow
from . import sign_in as sign_in_op
from ..properties.addon_preferences import ADDON_PACKAGE
from .open_my_world import _viewer_url

def _addon_dir():
    """This add-on's own directory - operators/ is one level inside it."""
    return deploy_command.addon_dir_from(__file__)


def _ingest_command(context):
    entry = context.preferences.addons.get(ADDON_PACKAGE)
    preference = "" if entry is None else entry.preferences.ingest_command
    return deploy_command.resolve_ingest_command(preference, _addon_dir())


def _resolve_token(context):
    """Which credential publishes, where it came from, and whether that is a trap.

    The environment variable still WINS over the stored preference: someone
    who deliberately keeps credentials out of config files should not also
    have to remember to blank the preference field, and a scripted Blender
    depends on it.

    What changed (#257 story 3) is that the losing case is no longer silent.
    With a Sign In button next to the preference, a stale variable turns
    that button into a liar - so when both are set and differ, the panel
    says which one is being used.
    """
    return deploy_command.resolve_publish_token(
        os.environ.get(deploy_command.PUBLISH_TOKEN_VAR, ""),
        _stored_token(context),
    )


def _stored_token(context):
    """The stored access token, as it is. Never the network (#368 review).

    This runs inside the panel's draw(), which fires on every interface
    event and must stay fast. A token near its end with a refresh token
    beside it has its renewal kicked onto a background thread here; the
    renewed tokens land through the add-on's timer, and the next redraw
    sees them. The environment variable is untouched by this: it still wins
    in _resolve_token, as documented.
    """
    entry = context.preferences.addons.get(ADDON_PACKAGE)
    if entry is None:
        return ""
    prefs = entry.preferences
    if getattr(prefs, "refresh_token", "") and sign_in_flow.needs_refresh(getattr(prefs, "token_expires_at", 0) or None):
        sign_in_op.renew_in_background(prefs)
    return getattr(prefs, "publish_token", "")


def _renew_before_publish(context):
    """On the press only: a token near its end is renewed before it goes out (#366 AC3).

    Synchronous, because the person has just pressed a button that starts a
    multi-second export anyway, and one bounded request is the honest cost
    of not starting an upload with a token that dies mid-way. Takes a
    redraw's background renewal first rather than asking twice. Returns an
    error sentence when the endpoint could not be reached - the tokens are
    kept, the publish does not start - or None.
    """
    if os.environ.get(deploy_command.PUBLISH_TOKEN_VAR, ""):
        return None
    prefs = _preferences(context)
    if prefs is None:
        return None
    pending_error = sign_in_op.finish_renewal(prefs)
    if pending_error:
        print("[veml] " + pending_error)
    stored = {
        "access": getattr(prefs, "publish_token", ""),
        "refresh": getattr(prefs, "refresh_token", ""),
        "expires_at": getattr(prefs, "token_expires_at", 0) or None,
    }
    if not stored["refresh"] or not sign_in_flow.needs_refresh(stored["expires_at"]):
        return None
    session = sign_in_flow.resolve_session(
        stored, getattr(prefs, "token_endpoint", ""), getattr(prefs, "identity_api_key", "")
    )
    if session["state"] == "renewed":
        sign_in_op.store_tokens(prefs, session["access"], session["refresh"], session["expires_at"])
        print("[veml] publish token renewed")
    elif session["state"] == "signed_out":
        sign_in_op.clear_tokens(prefs)
        print("[veml] signed out: " + session.get("reason", ""))
    elif session["state"] == "unreachable":
        return "Could not reach the token endpoint (%s). Your sign-in is kept; try again in a moment." % session.get("reason", "")
    return None


def _publish_token(context):
    """Just the credential, for callers that do not need to explain it."""
    return _resolve_token(context)[0]


def _room_args(veml):
    """The panel's Synchronization fields as --sync/--session (#257 story 4).

    Only when synchronization is enabled AND the type is `worldsync`: the
    ingest's --sync declares that type, and the panel's other value (`vss`,
    the legacy server path) belongs to the direct exporter, not to the
    button. The session name is the human-readable one if given, else the
    id; blank lets the ingest default it to the title.
    """
    if not veml.sync_enabled or veml.sync_type.strip() != "worldsync":
        return {}
    address = veml.sync_address.strip()
    if not address:
        return {}
    session = veml.sync_session.strip() or veml.sync_id.strip()
    return {"sync_address": address, "sync_session": session}


def _entry_point_line(stdout):
    """Pull the ingest report's entry-point source line, if present (#99)."""
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("entry point:"):
            return stripped
    return None


def _warning_lines(stderr):
    """Every `warning:`/`warning (blender):` line ingest prints (#99)."""
    return [line.strip() for line in stderr.splitlines() if line.strip().lower().startswith("warning")]


class VEML_OT_save_as_my_world(bpy.types.Operator):
    """Save the scene and deploy it as a world via veml-ingest --deploy"""
    bl_idname = "veml.save_as_my_world"
    bl_label = "Save as My World"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        veml = context.scene.veml_scene_properties
        error = deploy_command.validate_deploy_inputs(bpy.data.filepath, veml.deploy_dir)
        if error:
            cls.poll_message_set(error)
            return False
        return True

    def execute(self, context):
        veml = context.scene.veml_scene_properties
        error = deploy_command.validate_deploy_inputs(bpy.data.filepath, veml.deploy_dir)
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        # Publishing is optional, and every reason it cannot proceed is found
        # BEFORE the file is saved and a process is spawned (#257 story 3).
        # A new press supersedes any notice from the last sign-in (#366 AC2),
        # and a token near its end is renewed now, before it goes out.
        sign_in_op.clear_notice()
        unreachable = _renew_before_publish(context)
        if unreachable:
            self.report({'ERROR'}, unreachable)
            return {'CANCELLED'}
        token, source, conflict = _resolve_token(context)
        error = deploy_command.validate_publish_inputs(veml.publish_endpoint, token)
        if error:
            # #366 - ask at the moment of need: a missing or expired token
            # starts the sign-in here and finishes THIS publish when the token
            # arrives, rather than sending the person to the preferences.
            if veml.publish_endpoint and deploy_command.token_needs_sign_in(token):
                prefs = _preferences(context)
                started = sign_in_op.start_sign_in(
                    prefs, then="publish", run_publish=lambda: _publish_now(context), open_browser=webbrowser.open
                )
                if started:
                    self.report({'ERROR'}, error + " " + started)
                    return {'CANCELLED'}
                self.report({'INFO'}, "Sign in in your browser; the world publishes on its own once you have.")
                return {'FINISHED'}
            self.report({'ERROR'}, error)
            return {'CANCELLED'}
        if conflict and veml.publish_endpoint:
            # Not a refusal - the publish is fine and the variable winning is
            # the documented rule. But someone who just signed in is entitled
            # to know their new token is not the one going out.
            self.report(
                {'WARNING'},
                f"publishing with the token from {source}; the add-on preferences hold a different one",
            )

        # #308: the add-on carries the world builder but not a Node runtime.
        # Say which piece is missing, before saving or spawning anything.
        if _ingest_command(context) == deploy_command.NODE_MISSING:
            self.report({'ERROR'}, deploy_command.NODE_MISSING_MESSAGE)
            return {'CANCELLED'}

        return _publish_now(context, self)


def _preferences(context):
    entry = context.preferences.addons.get(ADDON_PACKAGE)
    return None if entry is None else entry.preferences


#: The check replaces this to prove the continuation runs without spawning.
_run_publish_for_test = None


def _publish_now(context, op=None):
    """Save and run the deploy/publish. op reports when called from the operator; the continuation has none."""
    if _run_publish_for_test is not None:
        return _run_publish_for_test(context)

    def report(kind, text):
        if op is not None:
            op.report({kind}, text)
        else:
            print("[veml] publish: %s: %s" % (kind.lower(), text))

    veml = context.scene.veml_scene_properties
    token = _publish_token(context)
    bpy.ops.wm.save_mainfile()

    argv = deploy_command.build_deploy_argv(
            _ingest_command(context),
            bpy.data.filepath,
            veml.deploy_dir,
            veml.deploy_title,
            publish_endpoint=veml.publish_endpoint,
            world_id=veml.publish_world_id,
            no_lookdev_sky=veml.no_lookdev_sky,
            **_room_args(veml),
        )

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            env=deploy_command.publish_env(os.environ, token),
        )
    except OSError as err:
        report('ERROR', f"could not run '{argv[0]}': {err}")
        return {'CANCELLED'}

    if result.returncode != 0:
            # The REASON, not a tail. Blender truncates a long operator
            # report, and the ingest prints its reason last - so a tail put
            # the successful part of the run in front of a person and cut
            # off the sentence that told them what to do.
            # The exit code rides at the END rather than the front: it is
            # for whoever reports the bug, and it must not be the first
            # thing between a person and the sentence that helps them.
        reason = deploy_command.failure_reason(result.stdout, result.stderr)
        report('ERROR', reason + NEWLINE + EXITED % result.returncode)
        return {'CANCELLED'}

    for warning in _warning_lines(result.stderr):
        report('WARNING', warning)

    entry_line = _entry_point_line(result.stdout)
        # Blank field: the ingest wrote beside the .blend, so name that folder
        # rather than an empty string (#297).
    world_dir = deploy_command.effective_world_dir(veml.deploy_dir, bpy.data.filepath)

    # Remember the world, so the NEXT press updates this one rather than
    # creating another at another address. Only a complete result counts:
    # a half-read id would point the next press at the wrong world.
    url, world_id = deploy_command.parse_publish_result(result.stdout)
    if url and world_id:
        veml.publish_world_id = world_id
        # Fill the viewable address in, so "Open in Browser" lights up
        # without anyone copying a link out of a status bar (#257).
        veml.world_url = url
    elif veml.publish_endpoint:
        # The run was asked to publish and no result came back. It exited
        # zero, so the world IS deployed locally - say both things.
        report('WARNING', "no world address came back; the world was deployed locally only")

    # Address or folder, and the entry point either way (#308) - and, when
    # the export warned about something a person must fix, the LAST line is
    # that warning, because the status bar shows only the last (#396).
    published = url if (url and world_id) else ""
    kind, text = deploy_command.final_report(
        world_dir, entry_line, published, deploy_command.plain_warnings(result.stdout, result.stderr)
    )
    report(kind, text)

    # ...and then be there (#308). The report is already filed, so a
    # viewer that refuses to open cannot cost the person the address.
    if deploy_command.should_open_after_publish(
        veml.open_after_publish, _viewer_url(context), published
    ):
        bpy.ops.veml.open_my_world()
        # Opening reports "Opened <address>", which would now be the last
        # line - covering the warning again. Say the warning once more (#396).
        if kind == "WARNING":
            report(kind, text)
    return {'FINISHED'}
