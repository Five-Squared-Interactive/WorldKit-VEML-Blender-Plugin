# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT
"""The World panel's fields: how a published world behaves.

Every field is get/set-backed and stores nothing of its own: it reads and
writes the raw scene custom property ``veml_world`` through world_settings.py,
the contract veml-ingest reads, the same way the entry-point checkbox writes
``veml_spawn``. Names, defaults and ranges come from world_settings.SCHEMA, so
the panel and the ingest cannot drift apart.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from . import world_settings

# Labels and tooltips for the panel. Behaviour lives in world_settings.SCHEMA.
_TEXT = {
    "fly": ("Allow Flying", "Visitors can fly (F on a keyboard, the Fly button on a phone)"),
    "speed": ("Walking Speed", "Multiplies how fast visitors move"),
    "gravity": ("Gravity", "Downward pull in m/s² (Earth is 9.81)"),
    "jump_height": ("Jump Height", "How high a jump reaches, in metres"),
    "avatar": ("Avatar", "A .glb file beside the .blend that every visitor wears; empty for the default avatar"),
    "labels": ("Name Labels", "Show each visitor's name above their head"),
    "label_height": ("Label Height", "Metres above the avatar's origin; 0 places it just above the head"),
    "tint": ("Colour Tint", "Give each visitor's avatar its own colour"),
    "chat": ("Chat", "Visitors can chat"),
    "chat_panel": ("Chat Starts Shown", "The chat panel is open when a visitor arrives"),
    "phone_jump": ("Jump Button", "Phones show a Jump button"),
    "phone_chat": ("Chat Button", "Phones show a Chat button"),
    "phone_fly": ("Fly Button", "Phones show a Fly button"),
    "menu": ("Menu Button", "Show the menu button"),
    "vr_turn": ("Turning", "How the right stick turns a headset visitor"),
    "vr_stick": ("Stick Movement", "The left stick walks, instead of teleporting only"),
    "vr_left": ("Left Pointer", "What the left controller's ray does"),
    "vr_right": ("Right Pointer", "What the right controller's ray does"),
    "sky": ("Procedural Sky", "Draw a sky with a sun, instead of the World background"),
    "sun_elevation": ("Sun Elevation", "Degrees above the horizon"),
    "sun_azimuth": ("Sun Direction", "Compass degrees the sun sits at"),
    "scripts": ("Scripts", "Comma-separated .js files beside the .blend, run by the world"),
}

_CHOICE_TEXT = {
    "snap": ("Snap", "Turn in steps"),
    "smooth": ("Smooth", "Turn continuously"),
    "none": ("None", "Off"),
    "ui": ("Menus", "Points at menus and buttons"),
    "teleport": ("Teleport", "Points where to teleport"),
}


def _field(name):
    kind, default, extra = world_settings.SCHEMA[name]
    label, tip = _TEXT[name]

    def getter(self):
        return world_settings.get(self.id_data, name)

    def setter(self, value):
        world_settings.set(self.id_data, name, value)

    if kind == "bool":
        return BoolProperty(name=label, description=tip, default=default, get=getter, set=setter)
    if kind == "float":
        lo, hi = extra
        return FloatProperty(name=label, description=tip, default=default, min=lo, max=hi, get=getter, set=setter)
    if kind == "choice":
        items = [(v, *_CHOICE_TEXT[v]) for v in extra]

        # An EnumProperty's get/set speak the item's index.
        def enum_get(self):
            return extra.index(world_settings.get(self.id_data, name))

        def enum_set(self, index):
            world_settings.set(self.id_data, name, extra[index])

        return EnumProperty(name=label, description=tip, items=items, get=enum_get, set=enum_set)
    subtype = "FILE_PATH" if name == "avatar" else "NONE"
    return StringProperty(name=label, description=tip, subtype=subtype, get=getter, set=setter)


VEMLWorldSettings = type(
    "VEMLWorldSettings",
    (bpy.types.PropertyGroup,),
    {
        "__doc__": "How the published world behaves (stored in the scene's veml_world)",
        "__annotations__": {name: _field(name) for name in world_settings.SCHEMA},
    },
)
