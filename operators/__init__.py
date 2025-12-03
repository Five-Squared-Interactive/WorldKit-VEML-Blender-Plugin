# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

from .export_veml import EXPORT_OT_veml
from .import_veml import IMPORT_OT_veml
from . import socket_operators

classes = (
    EXPORT_OT_veml,
    IMPORT_OT_veml,
)


def register():
    import bpy
    for cls in classes:
        bpy.utils.register_class(cls)
    socket_operators.register()


def unregister():
    import bpy
    socket_operators.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
