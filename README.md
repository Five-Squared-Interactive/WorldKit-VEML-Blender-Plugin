# VEML Exporter for Blender

A Blender addon for exporting scenes to VEML (Virtual Environment Markup Language) format.

![Blender](https://img.shields.io/badge/Blender-3.0%2B-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Full VEML 3.0 Support** - Export all entity types defined in the VEML schema
- **Automatic Entity Detection** - Primitives, meshes, lights, and more auto-detected
- **GLB/GLTF Export** - Custom meshes automatically exported as GLB files
- **UI Integration** - Properties panels for scene and object settings
- **Coordinate Conversion** - Automatic Z-up to Y-up transformation
- **Hierarchical Export** - Parent-child relationships preserved

## Quick Start

### Installation

1. Download or clone this repository
2. Run `.\package_addon.ps1` to create `veml_exporter.zip`
3. In Blender: **Edit → Preferences → Add-ons → Install**
4. Select `veml_exporter.zip` and enable the addon

### Export

1. Create your scene in Blender
2. Go to **File → Export → VEML (.veml)**
3. Configure options and export

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and extension guide
- **[VEML Reference](docs/VEML_REFERENCE.md)** - Format quick reference

## Supported Entity Types

| Category | Types |
|----------|-------|
| **Primitives** | cube, sphere, cylinder, cone, plane, torus, capsule, prism, arch, tetrahedron, pyramid |
| **Complex** | mesh, light, audio, character, terrain, water, automobile, airplane, voxel |
| **UI** | canvas, text, button, input, image, html |
| **Utility** | container, waterblocker |

## Project Structure

```
veml_exporter/
├── operators/      # Export and UI operators
├── panels/         # Blender UI panels
├── properties/     # Custom property definitions
├── exporters/      # XML and mesh export logic
└── utils/          # Color and transform utilities
```

## Requirements

- Blender 3.0 or later
- Python 3.9+ (included with Blender)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the [Developer Guide](docs/DEVELOPER_GUIDE.md) before submitting PRs.
