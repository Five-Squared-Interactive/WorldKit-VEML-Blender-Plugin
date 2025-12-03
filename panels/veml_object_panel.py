# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy


class VEML_PT_object_panel(bpy.types.Panel):
    """VEML properties panel for objects"""
    bl_label = "VEML Entity"
    bl_idname = "VEML_PT_object_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        obj = context.object
        veml = obj.veml_properties

        layout.use_property_split = True
        layout.use_property_decorate = False

        # Basic properties
        layout.prop(veml, "tag")
        layout.prop(veml, "entity_id")
        layout.prop(veml, "entity_type")
        layout.prop(veml, "on_load_event")

        # Color override (for primitive meshes)
        if obj.type == 'MESH':
            layout.separator()
            layout.prop(veml, "use_custom_color")
            if veml.use_custom_color:
                layout.prop(veml, "color")

        # Mesh entity specific
        if veml.entity_type == 'MESH' or (veml.entity_type == 'AUTO' and obj.type == 'MESH'):
            layout.separator()
            box = layout.box()
            box.label(text="Mesh Settings", icon='MESH_DATA')
            box.prop(veml, "mesh_name")

        # Audio entity specific
        if veml.entity_type == 'AUDIO' or (veml.entity_type == 'AUTO' and obj.type == 'SPEAKER'):
            layout.separator()
            box = layout.box()
            box.label(text="Audio Settings", icon='SPEAKER')
            box.prop(veml, "audio_file")
            box.prop(veml, "audio_autoplay")
            box.prop(veml, "audio_loop")
            box.prop(veml, "audio_volume")

        # Light entity specific
        if veml.entity_type == 'LIGHT' or (veml.entity_type == 'AUTO' and obj.type == 'LIGHT'):
            layout.separator()
            box = layout.box()
            box.label(text="Light Settings", icon='LIGHT')
            box.prop(veml, "light_use_blender_settings")
            if not veml.light_use_blender_settings:
                box.prop(veml, "light_color")
                box.prop(veml, "light_intensity")
                box.prop(veml, "light_range")
                if obj.type == 'LIGHT' and obj.data.type == 'SPOT':
                    box.prop(veml, "light_spot_angle")
            box.prop(veml, "light_cast_shadows")

        # Transform type settings
        layout.separator()
        box = layout.box()
        box.label(text="Transform Settings", icon='ORIENTATION_GLOBAL')
        box.prop(veml, "transform_type")
        if veml.transform_type == 'SIZE':
            row = box.row(align=True)
            row.prop(veml, "size_x")
            row.prop(veml, "size_y")
            row.prop(veml, "size_z")

        # Character entity specific
        if veml.entity_type == 'CHARACTER' or (veml.entity_type == 'AUTO' and obj.type == 'ARMATURE'):
            layout.separator()
            box = layout.box()
            box.label(text="Character Settings", icon='ARMATURE_DATA')
            box.prop(veml, "character_mesh_name")
            box.prop(veml, "character_mesh_resource")
            
            # Mesh offset
            box.label(text="Mesh Offset:")
            row = box.row(align=True)
            row.prop(veml, "character_mesh_offset_x")
            row.prop(veml, "character_mesh_offset_y")
            row.prop(veml, "character_mesh_offset_z")
            
            # Mesh rotation
            box.label(text="Mesh Rotation (Quaternion):")
            row = box.row(align=True)
            row.prop(veml, "character_mesh_rotation_x")
            row.prop(veml, "character_mesh_rotation_y")
            row.prop(veml, "character_mesh_rotation_z")
            row.prop(veml, "character_mesh_rotation_w")
            
            # Label offset
            box.label(text="Label Offset:")
            row = box.row(align=True)
            row.prop(veml, "character_label_offset_x")
            row.prop(veml, "character_label_offset_y")
            row.prop(veml, "character_label_offset_z")

        # Synchronizer (available for all entities)
        layout.separator()
        box = layout.box()
        box.label(text="Synchronization", icon='LINKED')
        box.prop(veml, "synchronizer")

        # Placement Sockets
        layout.separator()
        box = layout.box()
        box.label(text="Placement Sockets", icon='EMPTY_ARROWS')
        
        row = box.row()
        row.template_list(
            "VEML_UL_placement_sockets", "",
            veml, "placement_sockets",
            veml, "placement_sockets_index",
            rows=3
        )
        
        col = row.column(align=True)
        col.operator("veml.add_placement_socket", icon='ADD', text="")
        col.operator("veml.remove_placement_socket", icon='REMOVE', text="")
        col.separator()
        col.operator("veml.move_placement_socket", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("veml.move_placement_socket", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # Show selected socket properties
        if veml.placement_sockets and veml.placement_sockets_index < len(veml.placement_sockets):
            socket = veml.placement_sockets[veml.placement_sockets_index]
            
            sub_box = box.box()
            sub_box.label(text="Position:")
            row = sub_box.row(align=True)
            row.prop(socket, "position_x")
            row.prop(socket, "position_y")
            row.prop(socket, "position_z")
            
            sub_box.label(text="Rotation (Quaternion):")
            row = sub_box.row(align=True)
            row.prop(socket, "rotation_x")
            row.prop(socket, "rotation_y")
            row.prop(socket, "rotation_z")
            row.prop(socket, "rotation_w")
            
            sub_box.label(text="Connecting Offset:")
            row = sub_box.row(align=True)
            row.prop(socket, "connecting_offset_x")
            row.prop(socket, "connecting_offset_y")
            row.prop(socket, "connecting_offset_z")

        # Canvas transform settings (for UI elements)
        is_canvas_entity = veml.entity_type in ('CANVAS', 'BUTTON', 'INPUT', 'IMAGE', 'TEXT', 'HTML')
        if is_canvas_entity or veml.use_canvas_transform:
            layout.separator()
            box = layout.box()
            box.label(text="Canvas Transform", icon='UV')
            box.prop(veml, "use_canvas_transform")
            if veml.use_canvas_transform:
                box.label(text="Position (0-1):")
                row = box.row(align=True)
                row.prop(veml, "canvas_position_x")
                row.prop(veml, "canvas_position_y")
                
                box.label(text="Size (0-1):")
                row = box.row(align=True)
                row.prop(veml, "canvas_size_x")
                row.prop(veml, "canvas_size_y")
                
                box.prop(veml, "canvas_align_horizontal")
                box.prop(veml, "canvas_align_vertical")
                box.prop(veml, "canvas_stretch_to_parent")

        # Button entity specific
        if veml.entity_type == 'BUTTON':
            layout.separator()
            box = layout.box()
            box.label(text="Button Settings", icon='MOUSE_LMB')
            box.prop(veml, "button_on_click")
            box.prop(veml, "button_color")

        # Image entity specific
        if veml.entity_type == 'IMAGE':
            layout.separator()
            box = layout.box()
            box.label(text="Image Settings", icon='IMAGE_DATA')
            box.prop(veml, "image_file")

        # HTML entity specific
        if veml.entity_type == 'HTML':
            layout.separator()
            box = layout.box()
            box.label(text="HTML Settings", icon='URL')
            box.prop(veml, "html_url")
            box.prop(veml, "html_on_message")

        # Text entity specific (manual TEXT type, not Blender FONT)
        if veml.entity_type == 'TEXT':
            layout.separator()
            box = layout.box()
            box.label(text="Text Settings", icon='FONT_DATA')
            box.prop(veml, "text_content")
            box.prop(veml, "text_font_size")
            box.prop(veml, "text_font")
            box.prop(veml, "text_color")
            
            row = box.row(align=True)
            row.prop(veml, "text_bold", toggle=True)
            row.prop(veml, "text_italic", toggle=True)
            row.prop(veml, "text_underline", toggle=True)
            row.prop(veml, "text_strikethrough", toggle=True)
            
            box.prop(veml, "text_align_horizontal")
            box.prop(veml, "text_align_vertical")
            box.prop(veml, "text_wrap")

        # Terrain entity specific
        if veml.entity_type == 'TERRAIN':
            layout.separator()
            box = layout.box()
            box.label(text="Terrain Settings", icon='RNDCURVE')
            box.prop(veml, "terrain_type")
            row = box.row(align=True)
            row.prop(veml, "terrain_length")
            row.prop(veml, "terrain_width")
            row.prop(veml, "terrain_height")
            box.prop(veml, "terrain_heights")
            box.prop(veml, "terrain_layer_masks")

        # Water entity specific
        if veml.entity_type == 'WATER':
            layout.separator()
            box = layout.box()
            box.label(text="Water Settings", icon='MOD_FLUIDSIM')
            
            col = box.column(align=True)
            col.label(text="Colors:")
            col.prop(veml, "water_shallow_color")
            col.prop(veml, "water_deep_color")
            col.prop(veml, "water_specular_color")
            col.prop(veml, "water_scattering_color")
            
            col = box.column(align=True)
            col.label(text="Depth:")
            row = col.row(align=True)
            row.prop(veml, "water_deep_start")
            row.prop(veml, "water_deep_end")
            
            col = box.column(align=True)
            col.label(text="Surface:")
            col.prop(veml, "water_distortion")
            col.prop(veml, "water_smoothness")
            
            col = box.column(align=True)
            col.label(text="Waves:")
            col.prop(veml, "water_num_waves")
            col.prop(veml, "water_wave_amplitude")
            col.prop(veml, "water_wave_steepness")
            col.prop(veml, "water_wave_speed")
            col.prop(veml, "water_wave_length")
            col.prop(veml, "water_wave_scale")
            col.prop(veml, "water_wave_intensity")

        # Automobile entity specific
        if veml.entity_type == 'AUTOMOBILE':
            layout.separator()
            box = layout.box()
            box.label(text="Automobile Settings", icon='AUTO')
            box.prop(veml, "automobile_mesh_name")
            box.prop(veml, "automobile_mesh_resource")
            box.prop(veml, "automobile_type")
            box.prop(veml, "automobile_mass")
            box.prop(veml, "automobile_wheels")
            box.label(text="Wheels format: submesh1:radius1,submesh2:radius2")

        # Airplane entity specific
        if veml.entity_type == 'AIRPLANE':
            layout.separator()
            box = layout.box()
            box.label(text="Airplane Settings", icon='GHOST_ENABLED')
            box.prop(veml, "airplane_mesh_name")
            box.prop(veml, "airplane_mesh_resource")
            box.prop(veml, "airplane_mass")
