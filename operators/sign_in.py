# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# Signing in from Blender: press the button, sign in in the browser, and the
# token arrives here on its own.
#
# Blender has no browser and cannot read a page's URL, so this is OAuth 2.1
# on the loopback (properties/sign_in_flow.py, bpy-free): this add-on mints a
# PKCE verifier + challenge and a state, listens on 127.0.0.1:<port>/callback,
# and opens the provider's authorize address carrying its client id, the
# challenge, the state and that loopback address. The person signs in there
# by any method the provider offers; the provider sends the browser back to
# the loopback with a single-use code; a timer here picks the code up, redeems
# it outbound with the verifier, and writes the token into the Publish Token
# preference. A code, never a token, crosses the loopback - a code is
# worthless without the verifier, which never leaves this process.
#
# This add-on names no identity service and hardcodes no host. The authorize
# and token addresses, the client id and the loopback ports are preferences,
# empty by default in a source checkout, so the same button works against any
# OAuth 2.1 provider - or against none.

import os
import threading
import time
import webbrowser

import bpy

from ..properties import deploy_command, sign_in_flow
from ..properties.addon_preferences import ADDON_PACKAGE

#: How long a browser sign-in may take before the listener is closed.
SIGN_IN_TIMEOUT_S = 300.0

#: The flow in progress, or None. One at a time: a new press replaces it.
_pending = None


def _preferences(context):
    entry = context.preferences.addons.get(ADDON_PACKAGE)
    return None if entry is None else entry.preferences


def _pref(prefs, name):
    return "" if prefs is None else getattr(prefs, name, "")


def _refusal(prefs):
    """Why a sign-in may not start now, in a sentence, or None."""
    return sign_in_flow.validate_sign_in_flow(
        _pref(prefs, "authorize_url"),
        _pref(prefs, "oauth_token_url"),
        _pref(prefs, "oauth_client_id"),
        _pref(prefs, "loopback_ports"),
        os.environ.get(deploy_command.PUBLISH_TOKEN_VAR, ""),
    )


def _cancel_pending():
    global _pending
    _unwatch_scene()
    if _pending is not None:
        try:
            _pending["listener"].close()
        except Exception:
            pass
        _pending = None


def pending():
    """The flow in progress (for the panel and the checks), or None."""
    return _pending


def complete_pending(prefs, code=None, exchange=sign_in_flow.exchange_code):
    """Redeem the code the listener caught and write the token. Returns an error sentence, or None.

    `code` may be passed by a caller that already took it off the listener;
    otherwise it is taken now without waiting. This is what the timer calls,
    and what the real-Blender check calls directly — the same path.
    """
    global _pending
    flow = _pending
    if flow is None:
        return "No sign-in is in progress."
    if code is None:
        came = flow["listener"].wait(0)
        if came is not None and came[0] == "error":
            _cancel_pending()
            return "The sign-in was cancelled in the browser (%s)." % came[1]
        code = came[1] if came is not None else None
    if code is None:
        return "The browser has not come back with a code yet."
    _cancel_pending()
    try:
        token, refresh, expires_at = exchange(
            flow["token_url"], flow["client_id"], code, flow["verifier"], flow["redirect_uri"]
        )
    except sign_in_flow.SignInError as err:
        return str(err)
    store_tokens(prefs, token, refresh, expires_at)
    # Ask at the moment of need: a sign-in the publish button started
    # finishes the publish it was asked for, without a second press.
    then = flow.get("then")
    if then == "publish":
        changed = bool(flow.get("scene_changed")) or (
            flow.get("scene") is not None and flow.get("scene") != _scene_fingerprint()
        )
        run = flow.get("run_publish")
        if changed:
            global _notice
            _notice = "Signed in. The scene changed meanwhile, so press Save as My World again."
            print("[veml] sign in: " + _notice)
        elif run is not None:
            try:
                run()
            except Exception as err:  # the publish's own reporting already spoke
                print("[veml] sign in: the publish after sign-in failed: %s" % err)
    return None


def store_tokens(prefs, access, refresh, expires_at):
    """Both tokens and the expiry, in one place. Sign Out clears them the same way."""
    prefs.publish_token = access or ""
    prefs.refresh_token = refresh or ""
    # A Blender IntProperty is 32-bit; a server saying "expires in a century"
    # must not throw on store. Clamped, never negative.
    prefs.token_expires_at = max(0, min(int(expires_at), 2**31 - 1)) if expires_at else 0


def clear_tokens(prefs):
    store_tokens(prefs, "", "", 0)


#: The one-line notice the scene panel shows after a sign-in that could not
#: finish its publish, until the next press clears it.
_notice = None

#: The background renewal in flight, or None. draw() never waits on it.
_renewal = None
#: After a failed renewal, no new attempt before this monotonic time, so a
#: dead network does not start a thread per redraw.
_renew_not_before = 0.0
RENEW_RETRY_S = 60.0


def notice():
    """What the panel says under the publish button, or None."""
    return _notice


def clear_notice():
    global _notice
    _notice = None


def _scene_fingerprint():
    """A cheap summary of what is open, compared when a sign-in completes."""
    try:
        return (bpy.data.filepath, len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.materials))
    except Exception:
        return None


def _on_depsgraph_update(scene, depsgraph=None):
    flow = _pending
    if flow is not None and flow.get("then") == "publish":
        flow["scene_changed"] = True


def _watch_scene():
    try:
        handlers = bpy.app.handlers.depsgraph_update_post
        if _on_depsgraph_update not in handlers:
            handlers.append(_on_depsgraph_update)
    except Exception:
        pass


def _unwatch_scene():
    try:
        handlers = bpy.app.handlers.depsgraph_update_post
        if _on_depsgraph_update in handlers:
            handlers.remove(_on_depsgraph_update)
    except Exception:
        pass


def renew_in_background(prefs):
    """Start renewing the stored token on a thread; returns whether one started.

    Nothing here blocks: draw() calls this, so the request runs
    on its own thread and the outcome is applied by finish_renewal - from the
    timer, or from a check that drives it by hand. One at a time, and none
    for RENEW_RETRY_S after a failure.
    """
    global _renewal
    if _renewal is not None or time.monotonic() < _renew_not_before:
        return False
    token_url = _pref(prefs, "oauth_token_url")
    client_id = _pref(prefs, "oauth_client_id")
    refresh_token = _pref(prefs, "refresh_token")
    if not refresh_token or not token_url:
        return False
    slot = {"prefs": prefs, "result": None, "error": None, "done": threading.Event()}

    def work():
        try:
            slot["result"] = sign_in_flow.refresh_access(token_url, client_id, refresh_token)
        except Exception as err:  # reported by finish_renewal, never raised on a thread
            slot["error"] = err
        finally:
            slot["done"].set()

    slot["thread"] = threading.Thread(target=work, name="veml-renew", daemon=True)
    _renewal = slot
    slot["thread"].start()
    try:
        if not bpy.app.timers.is_registered(_poll_renewal):
            bpy.app.timers.register(_poll_renewal, first_interval=0.5)
    except Exception:  # timers unavailable (some background runs); a check calls finish_renewal itself
        pass
    return True


def _poll_renewal():
    """bpy.app.timers callback: apply the renewal once the thread is done."""
    if _renewal is None:
        return None
    if not _renewal["done"].is_set():
        return 0.5
    error = finish_renewal(_renewal["prefs"])
    if error:
        print("[veml] " + error)
    return None


def finish_renewal(prefs, wait=True):
    """Apply the background renewal's outcome, on the main thread.

    Returns an error sentence, or None - including when nothing was in flight.
    A refusal signs out (both tokens cleared); an endpoint that could not be
    reached keeps both tokens and backs off, because a network blip is not a
    revoked session.
    """
    global _renewal, _renew_not_before
    slot = _renewal
    if slot is None:
        return None
    if wait:
        slot["done"].wait()
    elif not slot["done"].is_set():
        return None
    _renewal = None
    err = slot["error"]
    if err is None:
        access, refresh, expires_at = slot["result"]
        store_tokens(prefs, access, refresh or _pref(prefs, "refresh_token"), expires_at)
        print("[veml] publish token renewed")
        return None
    if isinstance(err, sign_in_flow.SignInUnreachable):
        _renew_not_before = time.monotonic() + RENEW_RETRY_S
        return "could not renew the publish token (%s); the sign-in is kept, trying again later" % err
    if isinstance(err, sign_in_flow.SignInError):
        clear_tokens(prefs)
        return "signed out: the token endpoint refused the renewal (%s)" % err
    _renew_not_before = time.monotonic() + RENEW_RETRY_S
    return "could not renew the publish token: %s" % err


def start_sign_in(prefs, then=None, run_publish=None, open_browser=None):
    """Begin the loopback flow. Returns an error sentence, or None once the browser is off.

    Shared by the Sign In button and the publish button: the latter
    passes then="publish" and the callable that finishes its publish.
    """
    global _pending
    error = _refusal(prefs)
    if error:
        return error
    _cancel_pending()
    verifier, challenge = sign_in_flow.make_pkce()
    state = sign_in_flow.make_state()
    try:
        listener = sign_in_flow.start_listener(state, sign_in_flow.parse_ports(prefs.loopback_ports))
    except OSError as err:
        return "could not listen on the loopback: %s" % err
    redirect_uri = sign_in_flow.loopback_redirect(listener.port)
    url = sign_in_flow.build_authorize_url(prefs.authorize_url, prefs.oauth_client_id, challenge, redirect_uri, state)
    _pending = {
        "listener": listener,
        "verifier": verifier,
        "state": state,
        "redirect_uri": redirect_uri,
        "token_url": prefs.oauth_token_url.strip(),
        "client_id": prefs.oauth_client_id.strip(),
        "prefs": prefs,
        "started": time.monotonic(),
        "then": then,
        "run_publish": run_publish,
        # What was open when the button was pressed, so a scene
        # edited while the browser was open is not published unasked.
        "scene": _scene_fingerprint() if then == "publish" else None,
        "scene_changed": False,
    }
    if then == "publish":
        _watch_scene()
    opener = open_browser or webbrowser.open
    try:
        opened = opener(url)
    except Exception as err:  # a headless or locked-down machine
        _cancel_pending()
        return "could not open a browser: %s" % err
    if not opened:
        _cancel_pending()
        return "could not open a browser. Open this address yourself: " + url
    try:
        if not bpy.app.timers.is_registered(_poll):
            bpy.app.timers.register(_poll, first_interval=0.5)
    except Exception:  # timers unavailable (some background runs); the check calls complete_pending itself
        pass
    return None


def _poll():
    """bpy.app.timers callback: finish the flow when the code arrives, give up after the timeout."""
    flow = _pending
    if flow is None:
        return None
    came = flow["listener"].wait(0)
    if came is not None and came[0] == "error":
        _cancel_pending()
        print("[veml] sign in: cancelled in the browser (%s)" % came[1])
        return None
    if came is not None:
        error = complete_pending(flow["prefs"], code=came[1])
        if error:
            print("[veml] sign in: " + error)
        else:
            print("[veml] sign in: token stored in the add-on preferences")
        return None
    if time.monotonic() - flow["started"] > SIGN_IN_TIMEOUT_S:
        _cancel_pending()
        print("[veml] sign in: timed out waiting for the browser")
        return None
    return 0.5


class VEML_OT_sign_in(bpy.types.Operator):
    """Sign in in your browser; the token arrives here on its own"""
    bl_idname = "veml.sign_in"
    bl_label = "Sign In"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        prefs = _preferences(context)
        error = _refusal(prefs)
        if error:
            cls.poll_message_set(error)
            return False
        return True

    def execute(self, context):
        global _pending
        prefs = _preferences(context)
        # Checked again rather than trusted from poll(): an environment
        # variable can be set by something else between a redraw and a click.
        error = _refusal(prefs)
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        error = start_sign_in(prefs, open_browser=webbrowser.open)
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}
        self.report({'INFO'}, "Finish signing in in your browser. Blender picks the token up on its own.")
        return {'FINISHED'}


class VEML_OT_sign_out(bpy.types.Operator):
    """Forget the publish token and the refresh token"""
    bl_idname = "veml.sign_out"
    bl_label = "Sign Out"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = _preferences(context)
        if prefs is None:
            return {'CANCELLED'}
        _cancel_pending()
        clear_tokens(prefs)
        self.report({'INFO'}, "Signed out. The tokens are cleared.")
        return {'FINISHED'}
