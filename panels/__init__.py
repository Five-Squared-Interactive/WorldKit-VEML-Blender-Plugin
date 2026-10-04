# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

from .veml_object_panel import VEML_PT_object_panel
from .veml_scene_panel import VEML_PT_scene_panel

classes = (
    VEML_PT_object_panel,
    VEML_PT_scene_panel,
)


def register():
    import bpy
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
