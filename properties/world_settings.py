# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT
"""World settings: how a published world behaves, stored on the scene.

The World panel reads and writes the raw scene custom property ``veml_world``,
a dict. That property is the contract the ingest step reads when it opens the
.blend, the same way it reads ``veml_spawn`` for the entry point, so the
settings travel with the file even where this add-on is not installed.

Only values that differ from their default are stored: a world that sets
nothing publishes exactly as before. This module has no ``bpy`` import, so its
rules are tested with plain Python.
"""

KEY = "veml_world"

# name -> (kind, default, extra): extra is (lo, hi) for numbers, the allowed
# values for choices, None otherwise.
SCHEMA = {
    # Movement
    "fly": ("bool", True, None),
    "speed": ("float", 1.0, (0.1, 5.0)),
    "gravity": ("float", 9.81, (0.5, 40.0)),
    "jump_height": ("float", 1.1, (0.0, 5.0)),
    # People
    "avatar": ("str", "", None),
    "labels": ("bool", True, None),
    "label_height": ("float", 0.0, (0.0, 10.0)),  # 0: just above the head
    "tint": ("bool", True, None),
    # Chat
    "chat": ("bool", True, None),
    "chat_panel": ("bool", True, None),
    # Phone buttons and the menu
    "phone_jump": ("bool", True, None),
    "phone_chat": ("bool", True, None),
    "phone_fly": ("bool", True, None),
    "menu": ("bool", True, None),
    # VR
    "vr_turn": ("choice", "snap", ("snap", "smooth", "none")),
    "vr_stick": ("bool", False, None),
    "vr_left": ("choice", "none", ("none", "ui", "teleport")),
    "vr_right": ("choice", "ui", ("none", "ui", "teleport")),
    # Sky
    "sky": ("bool", False, None),
    "sun_elevation": ("float", 45.0, (-90.0, 90.0)),
    "sun_azimuth": ("float", 180.0, (0.0, 360.0)),
    # Scripts: comma-separated paths, relative to the .blend
    "scripts": ("str", "", None),
}


def _stored(store):
    raw = store.get(KEY) if hasattr(store, "get") else None
    if raw is None:
        return {}
    # A Blender IDPropertyGroup converts with to_dict(); a plain dict is itself.
    return dict(raw.to_dict()) if hasattr(raw, "to_dict") else dict(raw)


def get(store, name):
    """The value in force: the stored one, or the default. Never writes."""
    kind, default, _ = SCHEMA[name]
    value = _stored(store).get(name, default)
    return value


def _normalize(name, value):
    kind, default, extra = SCHEMA[name]
    if kind == "bool":
        return bool(value)
    if kind == "float":
        lo, hi = extra
        return min(hi, max(lo, float(value)))
    if kind == "choice":
        if value not in extra:
            raise ValueError(f"{name}: {value!r} is not one of {extra}")
        return value
    return str(value).strip()


def set(store, name, value):  # noqa: A001 - the module's verb, as entry_point's
    """Store a value; a value equal to the default removes it."""
    if name not in SCHEMA:
        raise KeyError(name)
    try:
        value = _normalize(name, value)
    except ValueError:
        return  # an unknown choice is refused; the old value stays
    current = _stored(store)
    if value == SCHEMA[name][1]:
        current.pop(name, None)
    else:
        current[name] = value
    if current:
        store[KEY] = current
    elif KEY in store:
        del store[KEY]


def settings(store):
    """Exactly what was set (non-defaults)."""
    return _stored(store)
