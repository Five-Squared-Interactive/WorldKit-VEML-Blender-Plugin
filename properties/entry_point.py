# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# The "VEML entry point" camera checkbox logic — deliberately bpy-free.
#
# The checkbox binds to the RAW custom property `veml_spawn` on the camera
# OBJECT (never the addon's PropertyGroup storage): that is the format
# contract veml-ingest reads (#99), so a scene marked here is structurally
# identical to one marked by hand, and the property survives without the
# addon installed. This module holds the rules; veml_object_properties.py
# wires them to a get/set BoolProperty; tools/entry_point_logic_check.py
# pins them without a Blender install.

VEML_SPAWN_KEY = "veml_spawn"


def get_entry_point(obj):
    """Truthy `veml_spawn` means enabled — the exporter's own test (#99).

    Read-only: must NEVER create the key (a get that writes would leak
    authored data into every scene the panel merely displays).
    """
    return bool(obj.get(VEML_SPAWN_KEY))


def set_entry_point(all_objects, target, enabled):
    """Enable/disable the entry-point mark on `target`.

    Enabled: writes `veml_spawn = 1` on the target and REMOVES the key from
    every other camera — the checkbox is an exclusive toggle (one entry
    camera is the common case; a hand-authored multi-carrier scene still
    exports per #99's deterministic first-by-name rule, this convenience
    just never CREATES that situation).

    Disabled: removes the key entirely. Never writes 0 — a falsy value
    still shows in Blender's custom-property UI and reads as authored data.
    """
    if enabled:
        for obj in all_objects:
            if obj is not target and getattr(obj, "type", None) == 'CAMERA' and VEML_SPAWN_KEY in obj:
                del obj[VEML_SPAWN_KEY]
        target[VEML_SPAWN_KEY] = 1
    elif VEML_SPAWN_KEY in target:
        del target[VEML_SPAWN_KEY]
