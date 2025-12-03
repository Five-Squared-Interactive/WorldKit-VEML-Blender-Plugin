# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy

from .veml_object_properties import VEMLPlacementSocket, VEMLObjectProperties
from .veml_scene_properties import VEMLSceneProperties

classes = (
    VEMLPlacementSocket,
    VEMLObjectProperties,
    VEMLSceneProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register properties on object and scene types
    bpy.types.Object.veml_properties = bpy.props.PointerProperty(type=VEMLObjectProperties)
    bpy.types.Scene.veml_scene_properties = bpy.props.PointerProperty(type=VEMLSceneProperties)


def unregister():
    del bpy.types.Scene.veml_scene_properties
    del bpy.types.Object.veml_properties

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
