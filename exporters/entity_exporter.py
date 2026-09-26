# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Entity COLLECTOR (#21): gathers Blender object data into the plain
# structures `veml40_writer` serializes. This module owns bpy access and
# 4.0-surface policy; it emits NO XML.
#
# 4.0 core surface: mesh objects export as `asset` (glb) or `primitive`
# (recognized primitive meshes / explicit primitive entity types); empties
# group as `container`. 3.0-era types with no 4.0 core equivalent (light,
# audio, character, text, canvas UI, terrain, water, voxel, vehicles) are
# SKIPPED with a report warning — they are profile / §11 surfaces, and
# emitting 3.0 grammar for them would produce invalid 4.0 documents.

import uuid

from ..utils.color_utils import get_object_color
from ..utils.transform_utils import get_transform_elements


class EntityExporter:
    """Collects Blender objects into 4.0 entity data for veml40_writer."""

    # Blender primitive mesh names -> 4.0 §4.5 shapes.
    PRIMITIVE_MAP = {
        'Cube': 'cube',
        'Sphere': 'sphere',
        'Cylinder': 'cylinder',
        'Cone': 'cone',
        'Plane': 'plane',
        'Torus': 'torus',
        'Circle': 'plane',   # Circles become planes
        'Grid': 'plane',     # Grids become planes
        'Icosphere': 'sphere',
        'UV Sphere': 'sphere',
    }

    # Property-enum overrides -> 4.0 disposition. Primitive enum values map
    # to shapes; MESH/CONTAINER map to kinds; everything else is a skip.
    ENTITY_TYPE_SHAPES = {
        'CUBEMESH': 'cube',
        'SPHEREMESH': 'sphere',
        'CYLINDERMESH': 'cylinder',
        'CONEMESH': 'cone',
        'PLANEMESH': 'plane',
        'TORUSMESH': 'torus',
        'CAPSULEMESH': 'capsule',
        'PRISMMESH': 'prism',
        'ARCHMESH': 'arch',
        'TETRAHEDRONMESH': 'tetrahedron',
        'RECTANGULARPYRAMIDMESH': 'rectangular-pyramid',
    }

    UNSUPPORTED_IN_40_CORE = {
        'LIGHT', 'AUDIO', 'CHARACTER', 'CANVAS', 'TEXT', 'BUTTON', 'INPUT',
        'IMAGE', 'HTML', 'TERRAIN', 'WATER', 'WATERBLOCKER', 'VOXEL',
        'AUTOMOBILE', 'AIRPLANE',
    }

    def __init__(self, mesh_exporter, export_meshes=True):
        self.mesh_exporter = mesh_exporter
        self.export_meshes = export_meshes
        # Report of skipped objects: (object name, reason) — surfaced by the
        # operator so an author knows what the 4.0 core export left out.
        self.skipped = []

    # -- public --------------------------------------------------------------

    def collect_object(self, obj):
        """Collect one object (and its children) as 4.0 entity data.
        Returns a dict for veml40_writer, or None (skipped)."""
        kind, shape = self._classify(obj)
        if kind is None:
            return None

        entity = {
            'kind': kind,
            'tag': self._tag_of(obj),
            'id': self._id_of(obj),
            'transform': self._collect_transform(obj),
            'sockets': self._collect_sockets(obj),
            'children': [],
        }

        if kind == 'primitive':
            entity['shape'] = shape
            color = get_object_color(obj)
            if color:
                entity['color'] = color
        elif kind == 'asset':
            src = None
            if self.export_meshes:
                src = self.mesh_exporter.export_mesh(obj)
            if not src:
                self.skipped.append((obj.name, 'mesh export failed or disabled'))
                return None
            entity['src'] = src

        for child in sorted(obj.children, key=lambda o: o.name):
            child_entity = self.collect_object(child)
            if child_entity is not None:
                entity['children'].append(child_entity)

        return entity

    # -- classification ------------------------------------------------------

    def _classify(self, obj):
        """Returns (kind, shape) — kind in {'asset','primitive','container'}
        or (None, None) when the object has no 4.0 core disposition."""
        veml_props = obj.veml_properties

        if veml_props.entity_type != 'AUTO':
            enum = veml_props.entity_type
            if enum in self.ENTITY_TYPE_SHAPES:
                return 'primitive', self.ENTITY_TYPE_SHAPES[enum]
            if enum == 'MESH':
                return 'asset', None
            if enum == 'CONTAINER':
                return 'container', None
            if enum in self.UNSUPPORTED_IN_40_CORE:
                self.skipped.append(
                    (obj.name, f'{enum.lower()}: no VEML 4.0 core equivalent (profile/§11 surface)'))
                return None, None
            return 'container', None

        if obj.type == 'EMPTY':
            return 'container', None

        if obj.type == 'MESH':
            mesh_name = obj.data.name
            if mesh_name in self.PRIMITIVE_MAP:
                return 'primitive', self.PRIMITIVE_MAP[mesh_name]
            for primitive_name, shape in self.PRIMITIVE_MAP.items():
                if mesh_name.startswith(primitive_name):
                    return 'primitive', shape
            return 'asset', None

        if obj.type == 'CAMERA':
            return None, None  # never exported; the shell owns cameras

        self.skipped.append(
            (obj.name, f'{obj.type.lower()}: no VEML 4.0 core equivalent (profile/§11 surface)'))
        return None, None

    # -- fields --------------------------------------------------------------

    def _tag_of(self, obj):
        veml_props = obj.veml_properties
        return veml_props.tag if veml_props.tag else obj.name

    def _id_of(self, obj):
        veml_props = obj.veml_properties
        return veml_props.entity_id if veml_props.entity_id else str(uuid.uuid4())

    def _collect_transform(self, obj):
        """4.0 §4.2 transform data: position/rotation/SCALE — never size
        (§11 same-name trap: 3.0 per-axis size must not become 4.0
        uniform-fit size by rename). A 3.0-era SIZE/canvas preference
        collapses to the object's real scale, with a report note."""
        veml_props = obj.veml_properties
        pos, rot, scale = get_transform_elements(obj)

        if getattr(veml_props, 'use_canvas_transform', False):
            self.skipped.append(
                (obj.name, 'canvas transform: no 4.0 core equivalent — exported as plain transform'))
        elif getattr(veml_props, 'transform_type', 'SCALE') == 'SIZE':
            self.skipped.append(
                (obj.name, '3.0 size transform collapsed to scale (§11: 4.0 size means uniform-fit)'))

        r6 = lambda v: round(v, 6)  # noqa: E731
        return {
            'position': (r6(pos[0]), r6(pos[1]), r6(pos[2])),
            'rotation': (r6(rot[0]), r6(rot[1]), r6(rot[2]), r6(rot[3])),
            'scale': (r6(scale[0]), r6(scale[1]), r6(scale[2])),
        }

    def _collect_sockets(self, obj):
        veml_props = obj.veml_properties
        sockets = []
        for socket in getattr(veml_props, 'placement_sockets', []):
            sockets.append({
                'name': (socket.name or '').strip(),  # writer synthesizes blanks (§4.7)
                'position': (round(socket.position_x, 6), round(socket.position_y, 6), round(socket.position_z, 6)),
                'rotation': (round(socket.rotation_x, 6), round(socket.rotation_y, 6), round(socket.rotation_z, 6), round(socket.rotation_w, 6)),
                'connecting_offset': (round(socket.connecting_offset_x, 6), round(socket.connecting_offset_y, 6), round(socket.connecting_offset_z, 6)),
            })
        return sockets
