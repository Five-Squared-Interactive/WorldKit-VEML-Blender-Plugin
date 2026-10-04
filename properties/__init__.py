# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

import bpy

from .veml_object_properties import VEMLPlacementSocket, VEMLObjectProperties
from .veml_scene_properties import VEMLSceneProperties
from .veml_world_settings import VEMLWorldSettings
from .addon_preferences import VEMLAddonPreferences

classes = (
    VEMLPlacementSocket,
    VEMLObjectProperties,
    VEMLSceneProperties,
    VEMLWorldSettings,
    VEMLAddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register properties on object and scene types
    bpy.types.Object.veml_properties = bpy.props.PointerProperty(type=VEMLObjectProperties)
    bpy.types.Scene.veml_scene_properties = bpy.props.PointerProperty(type=VEMLSceneProperties)
    # Stores nothing itself; its fields read and write scene["veml_world"].
    bpy.types.Scene.veml_world_settings = bpy.props.PointerProperty(type=VEMLWorldSettings)


def unregister():
    del bpy.types.Scene.veml_world_settings
    del bpy.types.Scene.veml_scene_properties
    del bpy.types.Object.veml_properties

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
