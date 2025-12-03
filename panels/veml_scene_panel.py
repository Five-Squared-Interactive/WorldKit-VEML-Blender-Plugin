# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy


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
