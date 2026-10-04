# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

from .export_veml import EXPORT_OT_veml
from .get_node import VEML_OT_get_node
from .import_veml import IMPORT_OT_veml
from .open_my_world import VEML_OT_open_my_world
from .publish_as_new_world import VEML_OT_publish_as_new_world
from .save_as_my_world import VEML_OT_save_as_my_world
from .sign_in import VEML_OT_sign_in, VEML_OT_sign_out
from . import socket_operators

classes = (
    EXPORT_OT_veml,
    IMPORT_OT_veml,
    VEML_OT_save_as_my_world,
    VEML_OT_publish_as_new_world,
    VEML_OT_open_my_world,
    VEML_OT_sign_in,
    VEML_OT_sign_out,
    VEML_OT_get_node,
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
