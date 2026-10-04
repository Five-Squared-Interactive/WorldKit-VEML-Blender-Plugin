# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#
#
# How a .blend stops updating the world it has been updating and starts a
# new one.
#
# The scene remembers `publish_world_id` so a second press updates the same
# world at the same address. The field is shown read-only, because it is the
# service's id and a typed-in one produces "that world is not on this
# service" at the worst possible moment. Read-only leaves no way to clear
# it, and the property's own description tells people to clear it. This
# operator is that way.
#
# It asks first. Clearing is not undoable in the sense that matters: the
# previously published world stays live at its URL, but THIS .blend can no
# longer update it. The old id is reported so it can be pasted back by
# someone who meant to keep it.

import bpy


class VEML_OT_publish_as_new_world(bpy.types.Operator):
    """Forget the published world, so the next publish creates a new one"""
    bl_idname = "veml.publish_as_new_world"
    bl_label = "Publish as New World"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        veml = getattr(context.scene, "veml_scene_properties", None)
        if veml is None or not veml.publish_world_id:
            cls.poll_message_set("This scene has not published a world yet.")
            return False
        return True

    def invoke(self, context, event):
        # The confirm carries the consequence, not just the question: the old
        # world does not disappear, it becomes something this file no longer
        # updates.
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        veml = context.scene.veml_scene_properties
        previous = veml.publish_world_id
        veml.publish_world_id = ""
        # A new world is a new room: an id the add-on made for the old world
        # goes with it. One a person typed is theirs, and stays.
        if veml.sync_id.startswith("room-"):
            veml.sync_id = ""
        self.report(
            {'INFO'},
            f"Next publish creates a new world. The previous one ({previous}) stays online; "
            f"paste that id back to update it again.",
        )
        return {'FINISHED'}
