# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# Addon preferences hold the veml-ingest command the "Save as
# My World" operator invokes. `bl_idname` is derived from whatever name the
# addon is actually loaded under (the packaged module name, or a test
# harness's synthetic alias — see tools/save_as_my_world_check.py), never
# hardcoded, so `context.preferences.addons[ADDON_PACKAGE]` resolves in
# both cases.

import bpy

from . import site_defaults

from .deploy_command import (
    DEFAULT_INGEST_COMMAND,
    DEFAULT_VIEWER_URL,
    PUBLISH_TOKEN_VAR,
    describe_publish_token,
    resolve_publish_token,
)

ADDON_PACKAGE = __package__.split(".")[0] if __package__ else __name__


class VEMLAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_PACKAGE

    # Left at the default, the add-on runs the ingest it SHIPPED WITH,
    # then a built CLI in the checkout it was loaded from, then this
    # name on PATH. Setting this overrides all three.
    ingest_command: bpy.props.StringProperty(
        name="Ingest Command",
        description=(
            "Command that runs veml-ingest. Leave this alone unless you have a "
            "reason: an installed add-on already carries its own, and runs it "
            "with the Node on this machine. Set it to override that"
        ),
        default=DEFAULT_INGEST_COMMAND,
    )

    viewer_url: bpy.props.StringProperty(
        name="Viewer Address",
        description=(
            "Optional. A viewer to open worlds in - for someone running a local "
            "shell. Leave it empty and a published world opens at its own "
            "address, which the service serving it answers with the shell"
        ),
        # Empty by default: the world is the address. A packaged build may
        # still point at a viewer.
        default=site_defaults.default_viewer_url() or DEFAULT_VIEWER_URL,
    )

    # Signing in is OAuth 2.1 with this add-on as a public client. The names
    # are new on purpose: Blender keeps a saved preference across upgrades,
    # and a value saved for an older sign-in would otherwise beat these.
    authorize_url: bpy.props.StringProperty(
        name="Authorize Address",
        description=(
            "Your identity provider's OAuth authorize address. The Sign In button opens "
            "it in a browser; when you finish there, the token arrives in Publish Token "
            "below on its own. A packaged build may arrive pointing at the provider it "
            "was built for; built from source it is empty and deliberately not guessed - "
            "this add-on works against any provider, or none"
        ),
        default=site_defaults.default_authorize_url(),
    )

    oauth_token_url: bpy.props.StringProperty(
        name="Token Address",
        description=(
            "Where the sign-in code is redeemed for a token, at your identity provider. "
            "Set alongside the authorize address; empty when built from source"
        ),
        default=site_defaults.default_oauth_token_url(),
    )

    oauth_client_id: bpy.props.StringProperty(
        name="Client ID",
        description=(
            "The client id your identity provider gave this add-on. Public, not secret; "
            "empty when built from source"
        ),
        default=site_defaults.default_oauth_client_id(),
    )

    loopback_ports: bpy.props.StringProperty(
        name="Loopback Ports",
        description=(
            "Comma-separated ports the browser may return to on 127.0.0.1, each "
            "registered with your provider; the first free one is used. Empty uses any "
            "free port, for providers that allow it"
        ),
        default=site_defaults.default_loopback_ports(),
    )

    publish_token: bpy.props.StringProperty(
        name="Publish Token",
        description=(
            "Credential for the publish service. Stored in Blender's user preferences "
            "in PLAIN TEXT, like every add-on preference — leave it empty and set "
            f"{PUBLISH_TOKEN_VAR} in the environment instead if that matters to you"
        ),
        default="",
        subtype='PASSWORD',
    )

    # Kept beside the access token so a person signs in once: when
    # the access token nears its end the add-on renews it through the token
    # endpoint without a browser. Cleared by Sign Out, and by a refused
    # renewal. Plain text like every preference; the panel says so.
    refresh_token: bpy.props.StringProperty(
        name="Refresh Token",
        description="Renews the publish token without signing in again; cleared by Sign Out",
        default="",
        subtype='PASSWORD',
    )
    token_expires_at: bpy.props.IntProperty(
        name="Token Expires At",
        description="When the publish token ends, seconds since the epoch; 0 when unknown",
        default=0,
        min=0,
    )

    def draw(self, context):
        import os

        layout = self.layout
        layout.prop(self, "ingest_command")
        layout.prop(self, "viewer_url")

        layout.separator()
        layout.prop(self, "authorize_url")
        layout.prop(self, "oauth_token_url")
        layout.prop(self, "oauth_client_id")
        layout.prop(self, "loopback_ports")
        row = layout.row(align=True)
        row.operator("veml.sign_in", icon='URL')
        row.operator("veml.sign_out", icon='X')
        row.prop(self, "publish_token")

        # Which credential would actually be used, said where the person is
        # editing it. Without this the field looks authoritative and may not
        # be: the environment variable wins.
        env_token = os.environ.get(PUBLISH_TOKEN_VAR, "")
        token, source, conflict = resolve_publish_token(env_token, self.publish_token)
        if conflict:
            layout.label(
                text=PUBLISH_TOKEN_VAR + " is set and differs from this field - the variable wins.",
                icon='ERROR',
            )
        line = describe_publish_token(token, source)
        if line:
            layout.label(text=line, icon='CHECKMARK' if "expired" not in line.lower() else 'ERROR')

        # Said in the interface, not only in a docstring: a person choosing
        # where to put a credential deserves to know how it is kept.
        layout.label(
            text="Preferences (including the refresh token) are stored unencrypted; "
            + PUBLISH_TOKEN_VAR + " in the environment is an alternative.",
            icon='INFO',
        )
