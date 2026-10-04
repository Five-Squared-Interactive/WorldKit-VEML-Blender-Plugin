# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT
"""The Portal box's rules, deliberately bpy-free.

An object is a portal when it carries the RAW custom property
``veml_link_href`` (and optionally ``veml_link_label``). That is the contract
veml-ingest reads, the same shape as ``veml_spawn`` for the entry point, so an
object marked here is identical to one marked by hand and the marking
survives without the add-on. veml_object_properties.py binds these to
get/set fields; tools/portal_link_check.py pins them without Blender.
"""


HREF_KEY = "veml_link_href"
LABEL_KEY = "veml_link_label"

# --- portal link rule (begin) ---
# Only http(s) URLs and paths may become a portal: a visitor activating one
# must only ever navigate. A browser removes tabs and newlines anywhere in a
# URL, and control characters at its ends, before it reads the scheme, so a
# value holding any control character is refused outright rather than
# guessed at. This block is identical in the Blender add-on
# (Blender-VEML/properties/portal_link.py) and the ingest exporter
# (src/blend/blend_export.py); a test compares the two.
import re as _portal_re

_PORTAL_SCHEME = _portal_re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):")


def valid_href(value):
    value = str(value)
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        return False
    m = _PORTAL_SCHEME.match(value.strip(" "))
    return m is None or m.group(1).lower() in ("http", "https")
# --- portal link rule (end) ---


def get_href(obj):
    """Read-only: never creates the key."""
    return str(obj.get(HREF_KEY, "")) if HREF_KEY in obj else ""


def get_label(obj):
    return str(obj.get(LABEL_KEY, "")) if LABEL_KEY in obj else ""


def set_href(obj, value):
    """Mark or unmark: an empty href removes both keys; an unsafe one is refused."""
    value = str(value).strip()
    if value == "":
        for key in (HREF_KEY, LABEL_KEY):
            if key in obj:
                del obj[key]
        return
    if not valid_href(value):
        return  # refused; the old value stays
    obj[HREF_KEY] = value


def set_label(obj, value):
    value = str(value).strip()
    if value == "":
        if LABEL_KEY in obj:
            del obj[LABEL_KEY]
        return
    obj[LABEL_KEY] = value
