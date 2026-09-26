# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# VEML 4.0 document writer (#21) — DELIBERATELY bpy-free: the Blender-side
# exporters COLLECT plain data (dicts/tuples) and delegate every byte of XML
# to this module, so the monorepo test suite can exercise real exporter
# output without a Blender install (tools/emit_samples.py).
#
# Grammar target: specs/veml/veml-4.0.xsd (the package carries a verified
# copy under schema/). Binding rules honored here:
#   - §1.4: the root carries version="4.0"; the namespace declaration is
#     optional (namespace-omitted mode) — a namespace-less root WITH version
#     is a VEML 4.0 document.
#   - §11 same-name trap: sizing is ALWAYS emitted as <scale> (per-axis,
#     from Blender object scale); <size> (4.0 uniform-fit) is never emitted.
#   - §4.7: placement-socket requires a name — blank names are synthesized.

from xml.etree import ElementTree as ET

VEML_40_NAMESPACE = "http://www.fivesqd.com/schemas/veml/4.0"

_PRIMITIVE_SHAPES = {
    "cube", "sphere", "capsule", "cylinder", "plane", "torus", "cone",
    "rectangular-pyramid", "tetrahedron", "prism", "arch",
}


def _num(value):
    """Compact numeric formatting: integral floats print without .0."""
    f = float(value)
    return str(int(f)) if f == int(f) else repr(f)


def _vec_element(parent, name, xyz):
    el = ET.SubElement(parent, name)
    el.set("x", _num(xyz[0]))
    el.set("y", _num(xyz[1]))
    el.set("z", _num(xyz[2]))
    return el


def _quat_element(parent, name, xyzw):
    el = ET.SubElement(parent, name)
    el.set("x", _num(xyzw[0]))
    el.set("y", _num(xyzw[1]))
    el.set("z", _num(xyzw[2]))
    el.set("w", _num(xyzw[3]))
    return el


def _build_transform(parent, transform):
    """§4.2 transform: position/rotation/scale children — NEVER size."""
    if transform is None:
        return
    el = ET.SubElement(parent, "transform")
    if transform.get("position") is not None:
        _vec_element(el, "position", transform["position"])
    if transform.get("rotation") is not None:
        _quat_element(el, "rotation", transform["rotation"])
    if transform.get("scale") is not None:
        _vec_element(el, "scale", transform["scale"])


def _list_value(values):
    return " ".join(_num(v) for v in values)


def _build_sockets(parent, sockets, tag):
    """§4.7 placement sockets; name is REQUIRED — synthesize when blank.
    4.0 sockets carry ATTRIBUTE-form vectors (vem:vec3/vem:quat list
    values, §1.6), not child elements."""
    for index, socket in enumerate(sockets or []):
        el = ET.SubElement(parent, "placement-socket")
        name = (socket.get("name") or "").strip()
        if not name:
            name = f"{tag or 'entity'}-socket-{index + 1}"
        el.set("name", name)
        el.set("position", _list_value(socket.get("position", (0, 0, 0))))
        el.set("rotation", _list_value(socket.get("rotation", (0, 0, 0, 1))))
        el.set("connecting-offset", _list_value(socket.get("connecting_offset", (0, 0, 0))))


def _build_entity(parent, entity):
    kind = entity["kind"]
    if kind == "asset":
        el = ET.SubElement(parent, "asset")
        if entity.get("src"):
            el.set("src", entity["src"])
    elif kind == "primitive":
        el = ET.SubElement(parent, "primitive")
        shape = entity.get("shape")
        if shape in _PRIMITIVE_SHAPES:
            el.set("shape", shape)
        if entity.get("color"):
            el.set("color", entity["color"])
    elif kind == "container":
        el = ET.SubElement(parent, "container")
    else:
        raise ValueError(f"veml40_writer: unknown entity kind {kind!r}")

    if entity.get("tag"):
        el.set("tag", entity["tag"])
    if entity.get("id"):
        el.set("id", entity["id"])

    # Schema child order (§4.1): transform, then sockets, then children.
    _build_transform(el, entity.get("transform"))
    _build_sockets(el, entity.get("sockets"), entity.get("tag"))
    for child in entity.get("children") or []:
        _build_entity(el, child)
    return el


def build_world_root(world, include_namespace=True):
    """Build the ElementTree root for a 4.0 world document."""
    root = ET.Element("veml")
    root.set("version", "4.0")
    if include_namespace:
        root.set("xmlns", VEML_40_NAMESPACE)

    metadata = ET.SubElement(root, "metadata")
    title = ET.SubElement(metadata, "title")
    title.text = world.get("title") or "Untitled World"

    sync = world.get("sync")
    if sync:
        service = ET.SubElement(metadata, "synchronization-service")
        for attr in ("type", "address", "id", "session"):
            if sync.get(attr):
                service.set(attr, sync[attr])

    environment = ET.SubElement(root, "environment")

    background = world.get("background")
    if background:
        bg = ET.SubElement(environment, "background")
        if background.get("color"):
            bg.set("color", background["color"])
        elif background.get("panorama"):
            bg.set("panorama", background["panorama"])

    entry = world.get("entry_point")
    if entry:
        ep = ET.SubElement(environment, "entry-point")
        ep.set("id", entry.get("id") or "default")
        _vec_element(ep, "position", entry.get("position", (0, 0, 0)))
        _quat_element(ep, "rotation", entry.get("rotation", (0, 0, 0, 1)))

    for entity in world.get("entities") or []:
        _build_entity(environment, entity)

    return root


def build_world_document(world, include_namespace=True):
    """Build the full serialized document (declaration + pretty print)."""
    root = build_world_root(world, include_namespace=include_namespace)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
