# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy

from ..operators.open_my_world import _viewer_url
from ..operators import sign_in as sign_in_op
from ..operators.save_as_my_world import _ingest_command, _resolve_token
from ..properties import deploy_command


class VEML_PT_scene_panel(bpy.types.Panel):
    """VEML properties panel for scene/world settings"""
    bl_label = "VEML World"
    bl_idname = "VEML_PT_scene_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        veml = scene.veml_scene_properties

        layout.use_property_split = True
        layout.use_property_decorate = False

        # Metadata
        layout.prop(veml, "title")

        # Scripts
        layout.separator()
        box = layout.box()
        box.label(text="Scripts", icon='FILE_SCRIPT')
        box.prop(veml, "scripts")

        # Background
        layout.separator()
        box = layout.box()
        box.label(text="Background", icon='WORLD')
        box.prop(veml, "background_type")

        if veml.background_type == 'COLOR':
            box.prop(veml, "background_color")
        elif veml.background_type == 'PANORAMA':
            box.prop(veml, "background_panorama")
        elif veml.background_type == 'PROCEDURAL':
            box.prop(veml, "procedural_day_night_cycle")
            box.prop(veml, "procedural_sun_enabled")
            box.prop(veml, "procedural_moon_enabled")
            box.prop(veml, "procedural_stars_enabled")
            box.prop(veml, "procedural_clouds_enabled")

        # Effects
        layout.separator()
        box = layout.box()
        box.label(text="Effects", icon='SHADERFX')
        box.prop(veml, "fog_enabled")
        if veml.fog_enabled:
            box.prop(veml, "fog_color")
            box.prop(veml, "fog_density")

        # Synchronization Service
        layout.separator()
        box = layout.box()
        box.label(text="Synchronization Service", icon='LINKED')
        box.prop(veml, "sync_enabled")
        if veml.sync_enabled:
            box.prop(veml, "sync_type")
            box.prop(veml, "sync_address")
            box.prop(veml, "sync_id")
            box.prop(veml, "sync_session")

        # Save as My World (#119)
        layout.separator()
        box = layout.box()
        box.label(text="Save as My World", icon='EXPORT')
        box.prop(veml, "deploy_dir")
        # Blank is fine, and the panel says where blank goes rather than
        # leaving the user to find out by pressing the button (#297).
        if not veml.deploy_dir:
            world_dir = deploy_command.default_world_dir(bpy.data.filepath)
            if world_dir:
                box.label(text=f"Writes to {world_dir}", icon='FILE_FOLDER')
        box.prop(veml, "deploy_title")
        # Named for what the person sees, not for the flag it sends: "lookdev"
        # is Blender's word, and someone pressing this button is asking about
        # the forest behind their world, not about a shading mode (#257).
        box.prop(veml, "no_lookdev_sky")
        # Publishing (#257 story 3) — optional. With an address, the same
        # press uploads the world and hands back a link.
        box.prop(veml, "publish_endpoint")
        if veml.publish_endpoint and veml.publish_world_id:
            # The id is the service's, shown but not typed: a hand-edited one
            # fails at publish time with "that world is not on this service".
            # Disabling the row also disables the right-click Clear, though,
            # so the way to stop updating this world is an explicit operator
            # rather than an instruction nobody can follow (#262 review).
            row = box.row(align=True)
            field = row.row()
            field.enabled = False
            field.prop(veml, "publish_world_id")
            row.operator("veml.publish_as_new_world", text="", icon='X')
        token, source, conflict = _resolve_token(context)
        # #366 AC2 - a sign-in that could not finish its publish says so here,
        # until the next press.
        if sign_in_op.notice():
            box.label(text=sign_in_op.notice(), icon='INFO')
        error = deploy_command.validate_deploy_inputs(bpy.data.filepath, veml.deploy_dir)
        if error is None:
            error = deploy_command.validate_publish_inputs(veml.publish_endpoint, token)
        if error:
            box.label(text=error, icon='ERROR')
            # #366 - say it where it happens: the fix for a missing or expired
            # token is one press, here, not a trip to the add-on preferences.
            if veml.publish_endpoint and deploy_command.token_needs_sign_in(token):
                box.operator("veml.sign_in", icon='URL')
        elif veml.publish_endpoint:
            # No error, so say what WILL happen: which credential goes out,
            # and how long it has left. A 24-hour token that died overnight
            # should be visible here, not fifteen seconds into an upload.
            if conflict:
                box.label(
                    text=deploy_command.PUBLISH_TOKEN_VAR + " is set and differs from the preference.",
                    icon='ERROR',
                )
            line = deploy_command.describe_publish_token(token, source)
            if line:
                box.label(text=line, icon='CHECKMARK')
        # #308: an installed add-on with no Node says so here, rather than
        # letting someone press a button that cannot work.
        node_missing = _ingest_command(context) == deploy_command.NODE_MISSING
        if node_missing:
            box.label(text="Node.js not found — install the LTS build from nodejs.org", icon='ERROR')

        # The press ends in the world rather than with a link to carry
        # somewhere (#308). Only offered when there is something to publish -
        # a local deploy has no address to open.
        if veml.publish_endpoint:
            box.prop(veml, "open_after_publish")

        row = box.row()
        row.enabled = error is None and not node_missing
        label = "Save and Publish" if veml.publish_endpoint else "Save as My World"
        row.operator("veml.save_as_my_world", icon='EXPORT', text=label)

        # Open in Browser (#257) — the last step of the one-button story. A
        # publish fills the address in; a local deploy needs it pasted once,
        # because only the person running the server knows what it exposes.
        box.prop(veml, "world_url")
        view_error = deploy_command.validate_view_inputs(_viewer_url(context), veml.world_url)
        if view_error:
            box.label(text=view_error, icon='INFO')
        row = box.row()
        row.enabled = view_error is None
        row.operator("veml.open_my_world", icon='URL')
