# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy


class VEML_OT_add_placement_socket(bpy.types.Operator):
    """Add a new placement socket to the object"""
    bl_idname = "veml.add_placement_socket"
    bl_label = "Add Placement Socket"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        obj = context.object
        veml = obj.veml_properties
        
        socket = veml.placement_sockets.add()
        socket.name = f"Socket_{len(veml.placement_sockets)}"
        veml.placement_sockets_index = len(veml.placement_sockets) - 1
        
        return {'FINISHED'}


class VEML_OT_remove_placement_socket(bpy.types.Operator):
    """Remove the selected placement socket"""
    bl_idname = "veml.remove_placement_socket"
    bl_label = "Remove Placement Socket"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        veml = context.object.veml_properties
        return len(veml.placement_sockets) > 0

    def execute(self, context):
        obj = context.object
        veml = obj.veml_properties
        
        veml.placement_sockets.remove(veml.placement_sockets_index)
        veml.placement_sockets_index = max(0, veml.placement_sockets_index - 1)
        
        return {'FINISHED'}


class VEML_OT_move_placement_socket(bpy.types.Operator):
    """Move placement socket up or down in the list"""
    bl_idname = "veml.move_placement_socket"
    bl_label = "Move Placement Socket"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "Up", "Move socket up"),
            ('DOWN', "Down", "Move socket down"),
        ]
    )

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        veml = context.object.veml_properties
        return len(veml.placement_sockets) > 1

    def execute(self, context):
        obj = context.object
        veml = obj.veml_properties
        index = veml.placement_sockets_index

        if self.direction == 'UP' and index > 0:
            veml.placement_sockets.move(index, index - 1)
            veml.placement_sockets_index -= 1
        elif self.direction == 'DOWN' and index < len(veml.placement_sockets) - 1:
            veml.placement_sockets.move(index, index + 1)
            veml.placement_sockets_index += 1

        return {'FINISHED'}


class VEML_UL_placement_sockets(bpy.types.UIList):
    """UI List for placement sockets"""
    bl_idname = "VEML_UL_placement_sockets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='EMPTY_ARROWS')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='EMPTY_ARROWS')


classes = (
    VEML_OT_add_placement_socket,
    VEML_OT_remove_placement_socket,
    VEML_OT_move_placement_socket,
    VEML_UL_placement_sockets,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
