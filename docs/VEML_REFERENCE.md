# VEML Format Reference

Quick reference for the VEML (Virtual Environment Markup Language) format as exported by the Blender VEML Exporter.

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<veml xmlns="http://www.fivesqd.com/schemas/veml/3.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <metadata>
    <!-- World metadata -->
  </metadata>
  <environment>
    <!-- Background, effects, and entities -->
  </environment>
</veml>
```

## Metadata Section

```xml
<metadata>
  <title>World Title</title>
  <script>scripts/main.js</script>
  <script>scripts/utils.js</script>
  <capability>vr</capability>
  <inputevent input="move" event="MoveCharacter(?);"/>
  <controlflags>
    <joystick-motion>true</joystick-motion>
  </controlflags>
  <synchronizationservice type="vss" address="ws://server:8080" 
                          id="uuid-here" session="MySession"/>
</metadata>
```

## Environment Section

### Background Types

**Color:**
```xml
<background>
  <color>#87ceebff</color>
</background>
```

**Panorama:**
```xml
<background>
  <panorama>skybox/panorama.hdr</panorama>
</background>
```

**Procedural Sky:**
```xml
<background>
  <lite-procedural-sky 
    day-night-cycle-enabled="true"
    sun-enabled="true"
    moon-enabled="true"
    stars-enabled="true"
    clouds-enabled="true"/>
</background>
```

### Effects

```xml
<effects>
  <lite-fog fog-enabled="true" color="#808080ff" density="0.5"/>
</effects>
```

## Entity Types

### Common Attributes

All entities support:
```xml
<entity xsi:type="vem:TYPE" tag="Name" id="uuid" on-load-event="Script();">
  <transform>...</transform>
  <synchronizer>sync-id</synchronizer>
  <placement-socket>...</placement-socket>
  <!-- Type-specific content -->
  <entity><!-- Children --></entity>
</entity>
```

### Transform Types

**Scale Transform:**
```xml
<transform xsi:type="vem:scaletransform">
  <position x="0" y="0" z="0"/>
  <rotation x="0" y="0" z="0" w="1"/>
  <scale x="1" y="1" z="1"/>
</transform>
```

**Size Transform:**
```xml
<transform xsi:type="vem:sizetransform">
  <position x="0" y="0" z="0"/>
  <rotation x="0" y="0" z="0" w="1"/>
  <size x="2" y="1" z="3"/>
</transform>
```

**Canvas Transform:**
```xml
<transform xsi:type="vem:canvastransform" 
           align-horizontal="center" 
           align-vertical="top"
           stretch-to-parent="false">
  <position-percent x="0.5" y="0.1"/>
  <size-percent x="0.8" y="0.2"/>
</transform>
```

### Placement Socket

```xml
<placement-socket>
  <position x="1" y="0" z="0"/>
  <rotation x="0" y="0" z="0" w="1"/>
  <connecting-offset x="0.1" y="0" z="0"/>
</placement-socket>
```

### Container

```xml
<entity xsi:type="vem:container" tag="Group">
  <transform>...</transform>
</entity>
```

### Primitive Meshes

Types: `cubemesh`, `spheremesh`, `cylindermesh`, `conemesh`, `planemesh`, `torusmesh`, `capsulemesh`, `prismmesh`, `archmesh`, `tetrahedronmesh`, `rectangularpyramidmesh`

```xml
<entity xsi:type="vem:cubemesh" tag="Cube">
  <transform>...</transform>
  <color>#ff0000ff</color>
</entity>
```

### Custom Mesh

```xml
<entity xsi:type="vem:mesh" tag="CustomObject">
  <transform>...</transform>
  <mesh-name>ObjectName</mesh-name>
  <mesh-resource>meshes/object.glb</mesh-resource>
</entity>
```

### Light

```xml
<entity xsi:type="vem:light" tag="MainLight">
  <transform>...</transform>
  <light-type>directional</light-type>  <!-- point, directional, spot, area -->
  <color>#ffffffff</color>
  <intensity>1.0</intensity>
  <range>100</range>
  <spot-angle>45</spot-angle>  <!-- Only for spot lights -->
  <cast-shadows>true</cast-shadows>
</entity>
```

### Audio

```xml
<entity xsi:type="vem:audio" tag="BackgroundMusic">
  <transform>...</transform>
  <audio-file>audio/music.mp3</audio-file>
  <auto-play>true</auto-play>
  <loop>true</loop>
  <priority>0</priority>
  <volume>0.8</volume>
  <pitch>0</pitch>
  <stereo-pan>0</stereo-pan>
</entity>
```

### Character

```xml
<entity xsi:type="vem:character" tag="Player">
  <transform>...</transform>
  <mesh-name>PlayerModel</mesh-name>
  <mesh-resource>meshes/player.glb</mesh-resource>
  <mesh-offset x="0" y="-1" z="0"/>
  <mesh-rotation x="0" y="0" z="0" w="1"/>
  <label-offset x="0" y="2" z="0"/>
</entity>
```

### Canvas

```xml
<entity xsi:type="vem:canvas" tag="UI">
  <transform>...</transform>
  <!-- Child UI elements -->
</entity>
```

### Text

```xml
<entity xsi:type="vem:text" tag="Label" 
        text="Hello World" 
        font-size="24"
        font="Arial"
        color="#ffffffff"
        bold="true"
        italic="false"
        underline="false"
        strikethrough="false"
        text-align-horizontal="center"
        text-align-vertical="center"
        text-wrap="wrap">
  <transform>...</transform>
</entity>
```

### Button

```xml
<entity xsi:type="vem:button" tag="ClickMe" 
        on-click-event="HandleClick();"
        color="#4488ffff">
  <transform>...</transform>
</entity>
```

### Input

```xml
<entity xsi:type="vem:input" tag="TextField">
  <transform>...</transform>
</entity>
```

### Image

```xml
<entity xsi:type="vem:image" tag="Logo">
  <transform>...</transform>
  <image-file>images/logo.png</image-file>
</entity>
```

### HTML

```xml
<entity xsi:type="vem:html" tag="WebView" 
        url="https://example.com"
        on-message="HandleMessage(?);">
  <transform>...</transform>
</entity>
```

### Terrain

```xml
<entity xsi:type="vem:terrain" tag="Ground"
        length="100" width="100" height="50"
        type="heightmap"
        heights="0,1,2;3,2,1;0,1,0">
  <transform>...</transform>
  <layer>
    <diffuse-texture>textures/grass_diffuse.png</diffuse-texture>
    <normal-texture>textures/grass_normal.png</normal-texture>
    <mask-texture>textures/grass_mask.png</mask-texture>
    <specular>#ffffff</specular>
    <metallic>0</metallic>
    <smoothness>0.5</smoothness>
  </layer>
  <layer-masks>1,1,1;1,1,1;1,1,1</layer-masks>
</entity>
```

### Water

```xml
<entity xsi:type="vem:water" tag="Ocean">
  <transform>...</transform>
  <shallow-color>#00cce6cc</shallow-color>
  <deep-color>#003366ff</deep-color>
  <specular-color>#ffffffff</specular-color>
  <scattering-color>#006666ff</scattering-color>
  <deep-start>1</deep-start>
  <deep-end>10</deep-end>
  <distortion>0.5</distortion>
  <smoothness>0.9</smoothness>
  <num-waves>4</num-waves>
  <wave-amplitude>0.5</wave-amplitude>
  <wave-steepness>0.5</wave-steepness>
  <wave-speed>1</wave-speed>
  <wave-length>10</wave-length>
  <wave-scale>1</wave-scale>
  <wave-intensity>1</wave-intensity>
</entity>
```

### Water Blocker

```xml
<entity xsi:type="vem:waterblocker" tag="Dam">
  <transform>...</transform>
</entity>
```

### Voxel

```xml
<entity xsi:type="vem:voxel" tag="VoxelObject">
  <transform>...</transform>
</entity>
```

### Automobile

```xml
<entity xsi:type="vem:automobile" tag="Car">
  <transform>...</transform>
  <mesh-name>SportsCar</mesh-name>
  <mesh-resource>meshes/car.glb</mesh-resource>
  <wheels>
    <wheel-submesh>Wheel_FL</wheel-submesh>
    <wheel-radius>0.3</wheel-radius>
  </wheels>
  <wheels>
    <wheel-submesh>Wheel_FR</wheel-submesh>
    <wheel-radius>0.3</wheel-radius>
  </wheels>
  <mass>1500</mass>
  <automobile-type>car</automobile-type>
</entity>
```

### Airplane

```xml
<entity xsi:type="vem:airplane" tag="Plane">
  <transform>...</transform>
  <mesh-name>Cessna</mesh-name>
  <mesh-resource>meshes/plane.glb</mesh-resource>
  <mass>5000</mass>
</entity>
```

## Color Formats

Supported color formats:
- Hex RGB: `#ff0000`
- Hex RGBA: `#ff0000ff`
- Color function: `color(255 0 0 255)` or `color(255, 0, 0, 255)`
- Named colors: `red`, `green`, `blue`, `white`, `black`, `gray`, etc.

## Coordinate System

VEML uses a Y-up coordinate system:
- **X**: Right
- **Y**: Up
- **Z**: Forward

Rotations are quaternions in (x, y, z, w) format.
