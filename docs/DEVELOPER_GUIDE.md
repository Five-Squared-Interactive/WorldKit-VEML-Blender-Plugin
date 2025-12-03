# VEML Exporter - Developer Documentation

Technical documentation for developers extending or maintaining the VEML Exporter addon.

## Architecture Overview

```
veml_exporter/
├── __init__.py                 # Plugin registration, bl_info
├── operators/
│   ├── __init__.py
│   ├── export_veml.py          # Main export operator
│   └── socket_operators.py     # Placement socket UI operators
├── panels/
│   ├── __init__.py
│   ├── veml_object_panel.py    # Object properties panel
│   └── veml_scene_panel.py     # Scene properties panel
├── properties/
│   ├── __init__.py
│   ├── veml_object_properties.py   # Per-object custom properties
│   └── veml_scene_properties.py    # Scene-level custom properties
├── exporters/
│   ├── __init__.py
│   ├── veml_exporter.py        # Main export orchestration
│   ├── entity_exporter.py      # Object → Entity conversion
│   └── mesh_exporter.py        # GLB/GLTF mesh export
└── utils/
    ├── __init__.py
    ├── color_utils.py          # Color format conversion
    └── transform_utils.py      # Coordinate system conversion
```

## Module Responsibilities

### `__init__.py`
- Defines `bl_info` for Blender addon registration
- Registers/unregisters all submodules
- Adds export menu item to File → Export

### `operators/export_veml.py`
**Class: `EXPORT_OT_veml`**
- Inherits from `bpy.types.Operator` and `ExportHelper`
- Provides export dialog with options
- Instantiates and calls `VEMLExporter`

### `operators/socket_operators.py`
**Classes:**
- `VEML_OT_add_placement_socket` - Add socket to collection
- `VEML_OT_remove_placement_socket` - Remove selected socket
- `VEML_OT_move_placement_socket` - Reorder sockets
- `VEML_UL_placement_sockets` - UIList for socket display

### `exporters/veml_exporter.py`
**Class: `VEMLExporter`**
- Main export orchestration
- Builds XML document structure
- Handles metadata and environment sections
- Coordinates entity and mesh export

**Key Methods:**
```python
def export(self) -> dict                    # Main entry point
def _build_metadata(self, root)             # Build <metadata> section
def _build_environment(self, root)          # Build <environment> section
def _build_background(self, environment, veml_props)
def _build_effects(self, environment, veml_props)
def _build_entities(self, environment)      # Process all objects
def _write_xml(self, root)                  # Format and save XML
```

### `exporters/entity_exporter.py`
**Class: `EntityExporter`**
- Converts Blender objects to VEML entity XML elements
- Handles entity type detection
- Manages type-specific content generation

**Key Methods:**
```python
def export_object(self, obj) -> ET.Element  # Main object export
def _get_entity_type(self, obj) -> str      # Auto-detect entity type
def _set_common_attributes(self, entity, obj)
def _create_transform(self, obj) -> ET.Element
def _add_type_specific_content(self, entity, obj, entity_type)
def _process_children(self, entity, obj)    # Recursive child processing
```

**Entity Type Detection Flow:**
1. Check `veml_properties.entity_type` for manual override
2. Check Blender object type (EMPTY, MESH, LIGHT, etc.)
3. For MESH: check against `PRIMITIVE_MAP` dictionary
4. Fall back to appropriate default

### `exporters/mesh_exporter.py`
**Class: `MeshExporter`**
- Exports meshes to GLB/GLTF format
- Caches exported meshes to avoid duplicates
- Creates `meshes/` subdirectory

**Key Methods:**
```python
def export_mesh(self, obj) -> str           # Export and return relative path
def _sanitize_filename(self, name) -> str   # Clean filename
```

### `utils/transform_utils.py`
Coordinate system conversion between Blender (Z-up) and VEML (Y-up).

**Functions:**
```python
def get_transform_elements(obj) -> tuple    # Returns (pos, rot, scale)
def convert_position_to_yup(pos) -> tuple
def convert_rotation_to_yup(rot) -> tuple
def convert_scale_to_yup(scale) -> tuple
```

**Coordinate Conversion:**
- Blender: X-right, Y-forward, Z-up
- VEML: X-right, Y-up, Z-forward
- Position: `(x, y, z)` → `(x, z, -y)`
- Rotation: -90° rotation around X axis applied to quaternion

### `utils/color_utils.py`
Color format conversion utilities.

**Functions:**
```python
def blender_to_veml_color(color) -> str     # RGBA tuple → "#rrggbbaa"
def veml_to_blender_color(veml_color) -> tuple
def get_object_color(obj) -> str            # Extract color from material
```

**Supported Color Formats:**
- Hex: `#rgb`, `#rrggbb`, `#rrggbbaa`
- Function: `color(r g b a)`, `color(r, g, b, a)`
- Named: `red`, `blue`, `gray`, etc.

## Adding a New Entity Type

### 1. Add to Entity Type Enum
In `properties/veml_object_properties.py`:
```python
entity_type: EnumProperty(
    items=[
        # ... existing items ...
        ('NEWTYPE', "New Type", "Description"),
    ],
)
```

### 2. Add Type-Specific Properties
```python
# In VEMLObjectProperties class
newtype_property: FloatProperty(
    name="Property Name",
    description="Description",
    default=1.0,
)
```

### 3. Add to Entity Type Map
In `exporters/entity_exporter.py`:
```python
ENTITY_TYPE_MAP = {
    # ... existing mappings ...
    'NEWTYPE': 'newtype',
}
```

### 4. Add Export Logic
```python
def _add_type_specific_content(self, entity, obj, entity_type):
    # ... existing code ...
    elif entity_type == 'newtype':
        self._add_newtype_properties(entity, obj, veml_props)

def _add_newtype_properties(self, entity, obj, veml_props):
    """Add newtype-specific properties"""
    prop_elem = ET.SubElement(entity, 'property-name')
    prop_elem.text = str(veml_props.newtype_property)
```

### 5. Add UI Panel
In `panels/veml_object_panel.py`:
```python
if veml.entity_type == 'NEWTYPE':
    layout.separator()
    box = layout.box()
    box.label(text="New Type Settings", icon='ICON_NAME')
    box.prop(veml, "newtype_property")
```

## Adding New Scene Properties

### 1. Add Property
In `properties/veml_scene_properties.py`:
```python
new_scene_prop: StringProperty(
    name="New Property",
    default="",
)
```

### 2. Add UI
In `panels/veml_scene_panel.py`:
```python
box.prop(veml, "new_scene_prop")
```

### 3. Add Export Logic
In `exporters/veml_exporter.py`:
```python
def _build_metadata(self, root):
    # ... existing code ...
    if veml_props.new_scene_prop:
        elem = ET.SubElement(metadata, 'new-element')
        elem.text = veml_props.new_scene_prop
```

## XML Namespaces

The exporter uses these namespaces:
```python
VEML_NAMESPACE = "http://www.fivesqd.com/schemas/veml/3.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
```

Entity types use `xsi:type` attribute:
```python
entity.set(f'{{{self.XSI_NAMESPACE}}}type', f'vem:{entity_type}')
```

## Testing

### Manual Testing
1. Create test scene with various object types
2. Export to VEML
3. Validate XML against `veml.xsd` schema
4. Import into target application

### Common Test Cases
- Empty scene (metadata only)
- Single primitive mesh
- Custom mesh (verify GLB export)
- Hierarchical objects (parent-child)
- All entity types
- All transform types
- UI canvas with children
- Placement sockets

## Performance Considerations

- Mesh export caches by mesh name to avoid duplicate exports
- Objects are sorted by name for deterministic output
- Large scenes may take time due to GLB export

## Error Handling

The main `export()` method wraps everything in try/except:
```python
def export(self) -> dict:
    try:
        # ... export logic ...
        return {'success': True, 'error': None}
    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
```

Mesh export failures are logged but don't stop the overall export.

## Future Improvements

Potential enhancements:
- Terrain layer editor with texture slots
- Visual placement socket preview in 3D viewport
- Import functionality (VEML → Blender)
- Batch export for multiple scenes
- Custom mesh export settings per object
- Animation export support
- LOD (Level of Detail) support
