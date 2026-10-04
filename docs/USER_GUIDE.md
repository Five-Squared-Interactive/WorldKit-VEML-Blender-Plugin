# VEML Exporter for Blender

A comprehensive Blender addon for exporting scenes to VEML (Virtual Environment Markup Language) format - an XML-based format for specifying entities, scripts, and world attributes.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Export Options](#export-options)
- [Entity Types](#entity-types)
- [Transform Types](#transform-types)
- [Scene Properties](#scene-properties)
- [Object Properties](#object-properties)
- [Placement Sockets](#placement-sockets)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Method 1: Install from ZIP (Recommended)

1. Build the add-on zip:
   ```bash
   pnpm exec turbo build --filter=@fivesqd/blender-ingest
   ```

2. In Blender:
   - Go to **Edit → Preferences → Add-ons**
   - Click **Install...**
   - Select `dist/veml-blender-addon.zip`
   - Enable the addon by checking the box next to **"Import-Export: VEML Exporter"**

### Method 2: Manual Installation

1. Copy the add-on source (`Blender-VEML/`) to your Blender addons
   directory **renamed to `veml_exporter`** — a hyphen is not valid in a
   Python module name, so Blender cannot import the folder under its own
   name. This is what the zip build does for you:
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender/<version>/scripts/addons/`
   - **Linux**: `~/.config/blender/<version>/scripts/addons/`

2. Enable the addon in Blender Preferences → Add-ons.

---

## Quick Start

1. Create your scene in Blender with meshes, lights, and other objects
2. Go to **File → Export → VEML (.veml)**
3. Choose export options and destination
4. Click **Export VEML**

The exporter will create:
- A `.veml` XML file with your scene structure
- A `meshes/` folder with GLB files for custom meshes (if enabled)

---

## Export Options

When exporting, you'll see these options in the file browser sidebar:

| Option | Description | Default |
|--------|-------------|---------|
| **Selected Only** | Export only selected objects | Off |
| **Export Custom Meshes** | Export non-primitive meshes as GLB files | On |
| **Mesh Format** | GLB (binary) or GLTF (separate files) | GLB |
| **Apply Modifiers** | Apply modifiers before exporting meshes | On |

---

## Entity Types

The exporter automatically detects entity types from Blender objects, or you can manually override in the **VEML Entity** panel.

### Automatic Detection

| Blender Object | VEML Entity Type |
|----------------|------------------|
| Empty | `container` |
| Cube mesh | `cubemesh` |
| Sphere/Icosphere/UV Sphere | `spheremesh` |
| Cylinder | `cylindermesh` |
| Cone | `conemesh` |
| Plane/Grid/Circle | `planemesh` |
| Torus | `torusmesh` |
| Custom Mesh | `mesh` (exports GLB) |
| Light | `light` |
| Speaker | `audio` |
| Armature | `character` |
| Text (Font object) | `text` |
| Camera | *Skipped as geometry* — but can mark the world's **entry point** (see Camera Properties) |

### Manual Entity Types

Set **Entity Type** in the VEML Entity panel to override auto-detection:

#### Primitive Meshes
- `cubemesh`, `spheremesh`, `cylindermesh`, `conemesh`, `planemesh`, `torusmesh`
- `capsulemesh`, `prismmesh`, `archmesh`, `tetrahedronmesh`, `rectangularpyramidmesh`

#### Complex Entities
- `container` - Empty grouping entity
- `mesh` - Custom mesh with GLB export
- `light` - Light source
- `audio` - Audio/sound source
- `character` - Rigged character with mesh offset/rotation
- `canvas` - UI container
- `text` - Text display
- `button` - Clickable button
- `input` - Input field
- `image` - Image display
- `html` - Embedded HTML/web content
- `terrain` - Heightmap terrain
- `water` - Water surface with waves
- `waterblocker` - Water blocking volume
- `voxel` - Voxel entity
- `automobile` - Vehicle with wheels
- `airplane` - Aircraft

---

## Transform Types

Each entity can use one of three transform types:

### Scale Transform (Default)
Standard position, rotation, and scale.

```xml
<transform xsi:type="vem:scaletransform">
  <position x="0" y="0" z="0"/>
  <rotation x="0" y="0" z="0" w="1"/>
  <scale x="1" y="1" z="1"/>
</transform>
```

### Size Transform
Position, rotation, and size in meters. Enable by setting **Transform Type** to "Size Transform" in the VEML Entity panel.

```xml
<transform xsi:type="vem:sizetransform">
  <position x="0" y="0" z="0"/>
  <rotation x="0" y="0" z="0" w="1"/>
  <size x="2" y="1" z="3"/>
</transform>
```

### Canvas Transform
For UI elements - position and size as percentages (0-1). Enable by checking **Use Canvas Transform**.

```xml
<transform xsi:type="vem:canvastransform" align-horizontal="center" align-vertical="top">
  <position-percent x="0.5" y="0.1"/>
  <size-percent x="0.8" y="0.2"/>
</transform>
```

**Canvas Transform Options:**
- **Position X/Y**: Position as percentage (0-1) from top-left
- **Size X/Y**: Size as percentage (0-1) of parent
- **Horizontal Align**: none, center, left, right
- **Vertical Align**: none, center, top, bottom
- **Stretch to Parent**: Fill parent bounds

---

## Scene Properties

Access via **Properties Panel → Scene → VEML World**

### Metadata

| Property | Description |
|----------|-------------|
| **Title** | World title (appears in `<title>` element) |

### World settings

How the published world behaves. Save as My World publishes these; a field
left at its default is not stored, so a world that sets nothing publishes as
before. They live in the scene's `veml_world` custom property, so they travel
with the .blend even where the add-on is not installed.

| Group | Settings |
|-------|----------|
| **Movement** | Allow Flying, Walking Speed, Gravity, Jump Height |
| **People** | Avatar (a .glb beside the .blend, copied into the world), Name Labels, Label Height, Colour Tint |
| **Chat** | Chat, Chat Starts Shown |
| **Phone Buttons and Menu** | Jump, Chat and Fly buttons; the Menu button |
| **VR** | Turning (snap, smooth, none), Stick Movement, Left and Right Pointer |
| **Sky** | Procedural Sky, with Sun Elevation and Sun Direction |
| **Scripts** | Comma-separated .js files beside the .blend, copied into the world |

A file that is not found is a warning when you publish, never a failed
publish, and the world does not reference it.

### Background (File > Export only)

The direct VEML exporter writes this background. Save as My World does not
use it: the published world takes its background from the scene's World.

| Type | Properties |
|------|------------|
| **Color** | Solid background color (RGBA) |
| **Panorama** | Path to panoramic image file |

### Synchronization Service

For multiplayer worlds:

| Property | Description |
|----------|-------------|
| **Enable Synchronization** | Enable sync service |
| **Type** | Service type (e.g., "vss") |
| **Address** | Server address |
| **Session ID** | UUID for the session |
| **Session Name** | Human-readable session name |

### Save as My World

One button from the open scene to a deployed world: saves the .blend, then
runs `veml-ingest <blend> --deploy <dir> [--title <t>]` — the same bare
invocation `corpus/README.md` records.

| Property | Description |
|----------|-------------|
| **Deploy Directory** | Serving location `--deploy` updates atomically. Required — the button is disabled without one. |
| **Deploy Title** | Optional `--title`. Left empty, ingest's own default (the file stem) applies. |

The button is disabled, with the reason shown inline, until the file has
been saved at least once and a deploy directory is set. On success it
reports the deployed path and which entry-point source won (`--entry` >
`veml_spawn` camera > active scene camera > bounds framing, #99); every
ingest warning surfaces as a Blender warning, and a failing run reports the
CLI's own error output. The ingest command itself is configured once in
**Preferences → Add-ons → VEML Exporter** (default `veml-ingest` on PATH;
the monorepo's `node packages/ingest/dist/cli.js` works verbatim).

### Animation and sound

Nothing to set: Save as My World carries both.

- **Animation.** The scene's timeline publishes as one animation, looping,
  just as pressing Play in Blender shows it. A scene with no keyframes
  publishes still, as before.
- **Sound.** Each Speaker object that is not muted plays in the world at the
  speaker's place, looping, with its Volume and its Distance settings. Its
  sound is converted to MP3 and published beside the model. Browsers only
  allow sound after the visitor's first click or tap, so it starts then. A
  speaker whose sound file is missing is skipped with a warning.
- **Speaker cones.** A speaker whose Cone angles (Inner or Outer) are below
  360° is directional in the world, facing the way it faces in Blender: full
  volume inside the inner cone, the Outer Cone Volume outside the outer cone,
  and a smooth change between them. A speaker with both angles at 360° spreads
  its sound in all directions.

Not yet carried: a speaker that follows a moving parent, and sounds that play
once or on a trigger.

---

## Object Properties

Access via **Properties Panel → Object → VEML Entity**

### Common Properties

| Property | Description |
|----------|-------------|
| **Tag** | Human-readable identifier (defaults to object name) |
| **ID** | UUID (auto-generated if empty) |
| **Entity Type** | Override auto-detection |
| **On Load Event** | Script to execute when entity loads |
| **Synchronizer** | Sync identifier for multiplayer |

### Camera Properties

| Property | Description |
|----------|-------------|
| **VEML Entry Point** | Marks this camera as the world's entry point. Writes the `veml_spawn` custom property on the camera object — exactly what the ingest pipeline reads, so a scene marked here is identical to one marked by hand. Checking it on another camera moves the mark there; unchecking removes the property entirely. |

The entry-point precedence at ingest is: `--entry` flag > the `veml_spawn`
camera > the active scene camera > automatic bounds framing. The ingest
report names which source won, and warns if the chosen entry lies outside
the model's bounds.

### Portal (mesh objects)

Make any mesh a portal: the object you modelled is what visitors aim at and
activate, where it stands and as big as it is.

| Property | Description |
|----------|-------------|
| **Link** | Where the portal goes: another world's `index.veml`, a `/w/` page, or a relative path. Only `http(s)` addresses and paths are accepted. Clearing it makes the object ordinary scenery again. |
| **Label** | What a visitor sees when they aim at it (optional). |

These write the `veml_link_href` and `veml_link_label` custom properties on
the object, which the publish step reads, so an object marked by hand works
the same. Save as My World publishes each portal as its own asset, carrying
its link. A link with any other scheme (`javascript:`, `file:`) makes no
portal: the object stays scenery and the publish warns.

### Primitive Mesh Properties

| Property | Description |
|----------|-------------|
| **Use Custom Color** | Override material color |
| **Color** | RGBA color for the primitive |

### Light Properties

| Property | Description |
|----------|-------------|
| **Use Blender Settings** | Read from Blender light data |
| **Light Color** | Light color (when not using Blender settings) |
| **Intensity** | Light power/energy |
| **Range** | Maximum light distance |
| **Spot Angle** | Cone angle for spotlights |
| **Cast Shadows** | Enable shadow casting |

### Audio Properties

| Property | Description |
|----------|-------------|
| **Audio File** | Path to audio file |
| **Auto Play** | Play automatically on load |
| **Loop** | Loop playback |
| **Volume** | Playback volume (0-1) |

### Character Properties

| Property | Description |
|----------|-------------|
| **Mesh Name** | Character mesh identifier |
| **Mesh Resource** | Path to mesh file |
| **Mesh Offset** | Position offset for mesh (X, Y, Z) |
| **Mesh Rotation** | Rotation offset for mesh (quaternion) |
| **Label Offset** | Position for character label |

### Text Properties

| Property | Description |
|----------|-------------|
| **Text Content** | Display text |
| **Font Size** | Text size |
| **Font** | Font family name |
| **Color** | Text color |
| **Bold/Italic/Underline/Strikethrough** | Text styles |
| **Horizontal Align** | left, center, right |
| **Vertical Align** | top, center, bottom |
| **Text Wrap** | no-wrap, wrap |

### Button Properties

| Property | Description |
|----------|-------------|
| **On Click Event** | Script to execute on click |
| **Button Color** | Button background color |

### Image Properties

| Property | Description |
|----------|-------------|
| **Image File** | Path to image file |

### HTML Properties

| Property | Description |
|----------|-------------|
| **URL** | Web URL to load |
| **On Message** | Script for message handling |

### Terrain Properties

| Property | Description |
|----------|-------------|
| **Terrain Type** | heightmap, voxel, or hybrid |
| **Length/Width/Height** | Terrain dimensions in meters |
| **Heights** | 2D height array (e.g., "0,1,2;3,2,1") |
| **Layer Masks** | Layer blend masks |

### Water Properties

| Property | Description |
|----------|-------------|
| **Shallow/Deep Color** | Water colors by depth |
| **Specular/Scattering Color** | Light interaction colors |
| **Deep Start/End** | Depth transition range |
| **Distortion** | Surface distortion (0-128) |
| **Smoothness** | Surface smoothness (0-1) |
| **Num Waves** | Wave count (1-32) |
| **Wave Amplitude/Steepness/Speed/Length/Scale/Intensity** | Wave parameters |

### Automobile Properties

| Property | Description |
|----------|-------------|
| **Mesh Name** | Vehicle mesh identifier |
| **Mesh Resource** | Path to mesh file |
| **Automobile Type** | Vehicle type (car, truck, etc.) |
| **Mass** | Vehicle mass in kg |
| **Wheels** | Wheel definitions (format: "submesh:radius,submesh:radius") |

### Airplane Properties

| Property | Description |
|----------|-------------|
| **Mesh Name** | Aircraft mesh identifier |
| **Mesh Resource** | Path to mesh file |
| **Mass** | Aircraft mass in kg |

---

## Placement Sockets

Placement sockets define connection points on entities for modular assembly.

### Adding Sockets

1. Select an object
2. In **VEML Entity → Placement Sockets**, click **+** to add a socket
3. Configure socket properties:
   - **Name**: Socket identifier
   - **Position**: Relative position (X, Y, Z)
   - **Rotation**: Relative rotation (quaternion X, Y, Z, W)
   - **Connecting Offset**: Offset when connecting to another socket

### Socket List Controls

- **+** Add new socket
- **-** Remove selected socket
- **▲/▼** Reorder sockets

### Example Output

```xml
<entity xsi:type="vem:mesh" tag="WallSegment">
  <transform>...</transform>
  <mesh-name>Wall</mesh-name>
  <mesh-resource>meshes/wall.glb</mesh-resource>
  <placement-socket>
    <position x="2" y="0" z="0"/>
    <rotation x="0" y="0" z="0" w="1"/>
    <connecting-offset x="0.1" y="0" z="0"/>
  </placement-socket>
  <placement-socket>
    <position x="-2" y="0" z="0"/>
    <rotation x="0" y="1" z="0" w="0"/>
    <connecting-offset x="0.1" y="0" z="0"/>
  </placement-socket>
</entity>
```

---

## Examples

### Basic Scene

```xml
<?xml version="1.0" encoding="UTF-8"?>
<veml xmlns="http://www.fivesqd.com/schemas/veml/4.0">
  <metadata>
    <title>My Scene</title>
  </metadata>
  <environment>
    <background>
      <color>#87ceebff</color>
    </background>
    <entity xsi:type="vem:cubemesh" tag="Floor" id="...">
      <transform xsi:type="vem:scaletransform">
        <position x="0" y="-0.5" z="0"/>
        <rotation x="0" y="0" z="0" w="1"/>
        <scale x="10" y="0.1" z="10"/>
      </transform>
      <color>#808080ff</color>
    </entity>
    <entity xsi:type="vem:light" tag="Sun" id="...">
      <transform xsi:type="vem:scaletransform">
        <position x="0" y="10" z="0"/>
        <rotation x="-0.5" y="0" z="0" w="0.866"/>
        <scale x="1" y="1" z="1"/>
      </transform>
      <light-type>directional</light-type>
      <color>#ffffffff</color>
      <intensity>1.0</intensity>
      <range>100</range>
      <cast-shadows>true</cast-shadows>
    </entity>
  </environment>
</veml>
```

### UI Canvas Example

```xml
<entity xsi:type="vem:canvas" tag="MainMenu">
  <transform xsi:type="vem:scaletransform">
    <position x="0" y="1.5" z="2"/>
    <rotation x="0" y="0" z="0" w="1"/>
    <scale x="1" y="1" z="1"/>
  </transform>
  <entity xsi:type="vem:text" tag="Title" text="Welcome" font-size="48" 
          text-align-horizontal="center" bold="true" color="#ffffffff">
    <transform xsi:type="vem:canvastransform" align-horizontal="center">
      <position-percent x="0.5" y="0.1"/>
      <size-percent x="0.8" y="0.15"/>
    </transform>
  </entity>
  <entity xsi:type="vem:button" tag="StartBtn" on-click-event="StartGame();" 
          color="#4488ffff">
    <transform xsi:type="vem:canvastransform" align-horizontal="center">
      <position-percent x="0.5" y="0.5"/>
      <size-percent x="0.4" y="0.1"/>
    </transform>
  </entity>
</entity>
```

### Custom Mesh with Synchronization

```xml
<entity xsi:type="vem:mesh" tag="InteractiveObject" id="550e8400-e29b-41d4-a716-446655440000">
  <transform xsi:type="vem:scaletransform">
    <position x="5" y="0" z="3"/>
    <rotation x="0" y="0" z="0" w="1"/>
    <scale x="1" y="1" z="1"/>
  </transform>
  <mesh-name>SpecialObject</mesh-name>
  <mesh-resource>meshes/SpecialObject.glb</mesh-resource>
  <synchronizer>position-rotation-sync</synchronizer>
</entity>
```

---

## Troubleshooting

### "Module not found" errors on install

Make sure you're installing the ZIP the build produces (`dist/veml-blender-addon.zip`), not a ZIP of the raw repository. The addon must be in a folder named `veml_exporter`.

### Meshes not exporting

1. Check that **Export Custom Meshes** is enabled in export options
2. Ensure the object is a MESH type (not a primitive that starts with "Cube", "Sphere", etc.)
3. To force export a primitive as a custom mesh, set **Entity Type** to "Mesh" in VEML Entity panel

### Coordinate system issues

The exporter converts from Blender's Z-up coordinate system to Y-up (common in game engines). If your target system uses a different convention, you may need to adjust transforms.

### Colors not matching

The exporter reads colors from the first material's Principled BSDF node. If using a complex node setup, set **Use Custom Color** and specify the color manually.

### Export fails silently

Check the Blender console (Window → Toggle System Console on Windows) for error messages.

---

## License

MIT License

## Contributing

Contributions welcome! Please submit issues and pull requests to the repository.
