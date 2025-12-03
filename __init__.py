# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

bl_info = {
    "name": "VEML Import/Export",
    "author": "Five Squared Interactive",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import/Export > VEML (.veml)",
    "description": "Import and export Blender scenes to VEML (Virtual Environment Markup Language) format",
    "warning": "",
    "doc_url": "https://github.com/FiveSquared/WorldKit-VEML-Blender-Plugin/blob/main/docs/USER_GUIDE.md",
    "tracker_url": "https://github.com/FiveSquared/WorldKit-VEML-Blender-Plugin/issues",
    "category": "Import-Export",
}

import bpy

from . import operators
from . import panels
from . import properties


def menu_func_export(self, context):
    self.layout.operator(operators.EXPORT_OT_veml.bl_idname, text="VEML (.veml)")


def menu_func_import(self, context):
    self.layout.operator(operators.IMPORT_OT_veml.bl_idname, text="VEML (.veml)")


def register():
    properties.register()
    operators.register()
    panels.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    panels.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
