# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# "Open in Browser": the last step of pressing one button and getting a
# link someone can walk into. It opens the published (or locally deployed)
# world in the viewer, so the person never copies a link out of the status
# bar.
#
# All the thinking is in the bpy-free properties/deploy_command.py, which is
# tested without a Blender install. What
# lives here is one call to Blender's own URL opener — deliberately, because
# the part that can be wrong is the ADDRESS, and the address is testable
# everywhere while `bpy.ops.wm.url_open` is not.

import bpy

from ..properties import deploy_command
from ..properties.addon_preferences import ADDON_PACKAGE


def _open_url(address):
    """Hand an address to the desktop's browser.

    A named seam around the operator's single impure act, for the same reason
    the engine injects its clock: `bpy.ops` is an accessor rather than an
    ordinary attribute, so it cannot be substituted from a test — and a check
    that cannot substitute it either launches a real browser on a headless
    runner or asserts nothing about the address that reached it. Patching
    this function is how the real-Blender check reads the URL.
    """
    bpy.ops.wm.url_open(url=address)


def _viewer_url(context):
    """The configured viewer, or "" - which means the world's own address."""
    entry = context.preferences.addons.get(ADDON_PACKAGE)
    if entry is None:
        return deploy_command.DEFAULT_VIEWER_URL
    return getattr(entry.preferences, "viewer_url", "") or deploy_command.DEFAULT_VIEWER_URL


class VEML_OT_open_my_world(bpy.types.Operator):
    """Open this world in the viewer"""
    bl_idname = "veml.open_my_world"
    bl_label = "Open in Browser"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        veml = context.scene.veml_scene_properties
        error = deploy_command.validate_view_inputs(_viewer_url(context), veml.world_url)
        if error:
            cls.poll_message_set(error)
            return False
        return True

    def execute(self, context):
        veml = context.scene.veml_scene_properties
        viewer = _viewer_url(context)

        # Re-checked rather than assumed, as defence in depth and not because
        # a path is known to reach it: Blender enforces poll() on every route
        # into an operator, including the search menu and a script call, and
        # RAISES rather than running it. What this guards is the gap between
        # poll and execute — the scene is mutable in between — and it costs one
        # comparison to close.
        error = deploy_command.validate_view_inputs(viewer, veml.world_url)
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        address = deploy_command.viewer_world_url(viewer, veml.world_url)
        if address is None:
            # Unreachable while the validation above holds. Reported rather
            # than asserted, because a silent {'FINISHED'} with no browser is
            # the one outcome a user cannot diagnose.
            self.report({'ERROR'}, "could not build the viewer address")
            return {'CANCELLED'}

        _open_url(address)
        self.report({'INFO'}, f"Opened {veml.world_url}")
        return {'FINISHED'}
