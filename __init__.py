# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

bl_info = {
    "name": "VEML Import/Export",
    "author": "Five Squared Interactive",
    # 2.0.0 because the format changed: this writes VEML 4.0, where 1.x wrote
    # 3.0, and the add-on now carries a world builder and can publish.
    "version": (2, 0, 0),
    # The floor is what is actually tested — 4.5 LTS, and 5.2. The add-on
    # reads Blender 4-era shader socket names, so 3.x cannot work.
    "blender": (4, 5, 0),
    "location": "File > Import/Export > VEML (.veml), and the VEML panel in Scene properties",
    "description": "Build a world from a Blender scene: VEML 4.0 plus glTF, published to a URL",
    "warning": "",
    "doc_url": "https://github.com/Five-Squared-Interactive/WorldKit-VEML-Blender-Plugin/blob/main/docs/USER_GUIDE.md",
    "tracker_url": "https://github.com/Five-Squared-Interactive/WorldKit-VEML-Blender-Plugin/issues",
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
    # The command builder is kept free of bpy, so it cannot find Blender's
    # user-data directory by itself. Tell it where a runtime this add-on
    # fetched would be, now that there is a Blender to ask.
    from .properties import deploy_command
    from .operators import get_node
    deploy_command.managed_node_lookup = get_node.managed_node
    panels.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    panels.unregister()
    operators.unregister()
    properties.unregister()
    from .properties import deploy_command
    deploy_command.managed_node_lookup = None
    deploy_command.reset_node_cache()


if __name__ == "__main__":
    register()
