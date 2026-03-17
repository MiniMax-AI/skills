---
name: shader-dev
description: Comprehensive GLSL shader techniques for creating stunning visual effects — ray marching, SDF modeling, fluid simulation, particle systems, procedural generation, lighting, post-processing, and more.
license: MIT
metadata:
  version: "1.0"
  category: graphics
---

# Shader Craft

A unified skill covering 36 GLSL shader techniques (ShaderToy-compatible) for real-time visual effects.

## Invocation

```
/shader-dev <request>
```

`$ARGUMENTS` contains the user's request (e.g. "create a raymarched SDF scene with soft shadows").

## Skill Structure

```
shader-dev/
├── SKILL.md                      # Core skill (this file)
├── techniques/                   # Implementation guides (read per routing table)
│   ├── ray-marching.md           # Sphere tracing with SDF
│   ├── sdf-3d.md                 # 3D signed distance functions
│   ├── lighting-model.md         # PBR, Phong, toon shading
│   ├── procedural-noise.md       # Perlin, Simplex, FBM
│   └── ...                       # 34 more technique files
└── reference/                    # Detailed guides (read as needed)
    ├── ray-marching.md           # Math derivations & advanced patterns
    ├── sdf-3d.md                 # Extended SDF theory
    ├── lighting-model.md         # Lighting math deep-dive
    ├── procedural-noise.md       # Noise function theory
    └── ...                       # 34 more reference files
```

## How to Use

1. Read the **Technique Routing Table** below to identify which technique(s) match the user's request
2. Read the relevant file(s) from `techniques/` — each file contains core principles, implementation steps, and complete code templates
3. If you need deeper understanding (math derivations, advanced patterns), follow the reference link at the bottom of each technique file to `reference/`
4. Apply the **WebGL2 Adaptation Rules** below when generating standalone HTML pages

## Technique Routing Table

| User wants to create... | Primary technique | Combine with |
|---|---|---|
| 3D objects / scenes from math | [ray-marching](techniques/ray-marching.md) + [sdf-3d](techniques/sdf-3d.md) | lighting-model, shadow-techniques |
| Complex 3D shapes (booleans, blends) | [csg-boolean-operations](techniques/csg-boolean-operations.md) | sdf-3d, ray-marching |
| Infinite repeating patterns in 3D | [domain-repetition](techniques/domain-repetition.md) | sdf-3d, ray-marching |
| Organic / warped shapes | [domain-warping](techniques/domain-warping.md) | procedural-noise |
| Fluid / smoke / ink effects | [fluid-simulation](techniques/fluid-simulation.md) | multipass-buffer |
| Particle effects (fire, sparks, snow) | [particle-system](techniques/particle-system.md) | procedural-noise, color-palette |
| Physically-based simulations | [simulation-physics](techniques/simulation-physics.md) | multipass-buffer |
| Game of Life / reaction-diffusion | [cellular-automata](techniques/cellular-automata.md) | multipass-buffer, color-palette |
| Ocean / water surface | [water-ocean](techniques/water-ocean.md) | atmospheric-scattering, lighting-model |
| Terrain / landscape | [terrain-rendering](techniques/terrain-rendering.md) | atmospheric-scattering, procedural-noise |
| Clouds / fog / volumetric fire | [volumetric-rendering](techniques/volumetric-rendering.md) | procedural-noise, atmospheric-scattering |
| Sky / sunset / atmosphere | [atmospheric-scattering](techniques/atmospheric-scattering.md) | volumetric-rendering |
| Realistic lighting (PBR, Phong) | [lighting-model](techniques/lighting-model.md) | shadow-techniques, ambient-occlusion |
| Shadows (soft / hard) | [shadow-techniques](techniques/shadow-techniques.md) | lighting-model |
| Ambient occlusion | [ambient-occlusion](techniques/ambient-occlusion.md) | lighting-model, normal-estimation |
| Path tracing / global illumination | [path-tracing-gi](techniques/path-tracing-gi.md) | analytic-ray-tracing, multipass-buffer |
| Precise ray-geometry intersections | [analytic-ray-tracing](techniques/analytic-ray-tracing.md) | lighting-model |
| Voxel worlds (Minecraft-style) | [voxel-rendering](techniques/voxel-rendering.md) | lighting-model, shadow-techniques |
| Noise / FBM textures | [procedural-noise](techniques/procedural-noise.md) | domain-warping |
| Tiled 2D patterns | [procedural-2d-pattern](techniques/procedural-2d-pattern.md) | polar-uv-manipulation |
| Voronoi / cell patterns | [voronoi-cellular-noise](techniques/voronoi-cellular-noise.md) | color-palette |
| Fractals (Mandelbrot, Julia, 3D) | [fractal-rendering](techniques/fractal-rendering.md) | color-palette, polar-uv-manipulation |
| Color grading / palettes | [color-palette](techniques/color-palette.md) | — |
| Bloom / tone mapping / glitch | [post-processing](techniques/post-processing.md) | multipass-buffer |
| Multi-pass ping-pong buffers | [multipass-buffer](techniques/multipass-buffer.md) | — |
| Texture / sampling techniques | [texture-sampling](techniques/texture-sampling.md) | — |
| Camera / matrix transforms | [matrix-transform](techniques/matrix-transform.md) | — |
| Surface normals | [normal-estimation](techniques/normal-estimation.md) | — |
| Polar coords / kaleidoscope | [polar-uv-manipulation](techniques/polar-uv-manipulation.md) | procedural-2d-pattern |
| 2D shapes / UI from SDF | [sdf-2d](techniques/sdf-2d.md) | color-palette |
| Procedural audio / music | [sound-synthesis](techniques/sound-synthesis.md) | — |
| SDF tricks / optimization | [sdf-tricks](techniques/sdf-tricks.md) | sdf-3d, ray-marching |
| Anti-aliased rendering | [anti-aliasing](techniques/anti-aliasing.md) | sdf-2d, post-processing |
| Depth of field / motion blur / lens effects | [camera-effects](techniques/camera-effects.md) | post-processing, multipass-buffer |
| Advanced texture mapping / no-tile textures | [texture-mapping-advanced](techniques/texture-mapping-advanced.md) | terrain-rendering, texture-sampling |
| WebGL2 shader errors / debugging | [webgl-pitfalls](techniques/webgl-pitfalls.md) | — |

## Technique Index

### Geometry & SDF
- **sdf-2d** — 2D signed distance functions for shapes, UI, anti-aliased rendering
- **sdf-3d** — 3D signed distance functions for real-time implicit surface modeling
- **csg-boolean-operations** — Constructive solid geometry: union, subtraction, intersection with smooth blending
- **domain-repetition** — Infinite space repetition, folding, and limited tiling
- **domain-warping** — Distort domains with noise for organic, flowing shapes
- **sdf-tricks** — SDF optimization, bounding volumes, binary search refinement, hollowing, layered edges, debug visualization

### Ray Casting & Lighting
- **ray-marching** — Sphere tracing with SDF for 3D scene rendering
- **analytic-ray-tracing** — Closed-form ray-primitive intersections (sphere, plane, box, torus)
- **path-tracing-gi** — Monte Carlo path tracing for photorealistic global illumination
- **lighting-model** — Phong, Blinn-Phong, PBR (Cook-Torrance), and toon shading
- **shadow-techniques** — Hard shadows, soft shadows (penumbra estimation), cascade shadows
- **ambient-occlusion** — SDF-based AO, screen-space AO approximation
- **normal-estimation** — Finite-difference normals, tetrahedron technique

### Simulation & Physics
- **fluid-simulation** — Navier-Stokes fluid solver with advection, diffusion, pressure projection
- **simulation-physics** — GPU-based physics: springs, cloth, N-body gravity, collision
- **particle-system** — Stateless and stateful particle systems (fire, rain, sparks, galaxies)
- **cellular-automata** — Game of Life, reaction-diffusion (Turing patterns), sand simulation

### Natural Phenomena
- **water-ocean** — Gerstner waves, FFT ocean, caustics, underwater fog
- **terrain-rendering** — Heightfield ray marching, FBM terrain, erosion
- **atmospheric-scattering** — Rayleigh/Mie scattering, god rays, SSS approximation
- **volumetric-rendering** — Volume ray marching for clouds, fog, fire, explosions

### Procedural Generation
- **procedural-noise** — Value noise, Perlin, Simplex, Worley, FBM, ridged noise
- **procedural-2d-pattern** — Brick, hexagon, truchet, Islamic geometric patterns
- **voronoi-cellular-noise** — Voronoi diagrams, Worley noise, cracked earth, crystal
- **fractal-rendering** — Mandelbrot, Julia sets, 3D fractals (Mandelbox, Mandelbulb)
- **color-palette** — Cosine palettes, HSL/HSV/Oklab, dynamic color mapping

### Post-Processing & Infrastructure
- **post-processing** — Bloom, tone mapping (ACES, Reinhard), vignette, chromatic aberration, glitch
- **multipass-buffer** — Ping-pong FBO setup, state persistence across frames
- **texture-sampling** — Bilinear, bicubic, mipmap, procedural texture lookup
- **matrix-transform** — Camera look-at, projection, rotation, orbit controls
- **polar-uv-manipulation** — Polar/log-polar coordinates, kaleidoscope, spiral mapping
- **anti-aliasing** — SSAA, SDF analytical AA, temporal anti-aliasing (TAA), FXAA post-process
- **camera-effects** — Depth of field (thin lens), motion blur, lens distortion, film grain, vignette
- **texture-mapping-advanced** — Biplanar mapping, texture repetition avoidance, ray differential filtering

### Audio
- **sound-synthesis** — Procedural audio in GLSL: oscillators, envelopes, filters, FM synthesis

### Debugging & Validation
- **webgl-pitfalls** — Common WebGL2/GLSL errors: `fragCoord`, `main()` wrapper, function order, macro limitations, uniform null

## WebGL2 Adaptation Rules

All technique files use ShaderToy GLSL style. When generating standalone HTML pages, apply these adaptations:

### Shader Version & Output
- Use `canvas.getContext("webgl2")`
- Shader first line: `#version 300 es`, fragment shader adds `precision highp float;`
- Fragment shader must declare: `out vec4 fragColor;`
- Vertex shader: `attribute` → `in`, `varying` → `out`
- Fragment shader: `varying` → `in`, `gl_FragColor` → `fragColor`, `texture2D()` → `texture()`

### Fragment Coordinate
- **Use `gl_FragCoord.xy`** instead of `fragCoord` (WebGL2 does not have `fragCoord` built-in)
```glsl
// WRONG
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
// CORRECT
vec2 uv = (2.0 * gl_FragCoord.xy - iResolution.xy) / iResolution.y;
```

### main() Wrapper for ShaderToy Templates
- ShaderToy uses `void mainImage(out vec4 fragColor, in vec2 fragCoord)`
- WebGL2 requires standard `void main()` entry point — always wrap mainImage:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}
```

### Function Declaration Order
- GLSL requires functions to be declared before use — either declare before use or reorder:
```glsl
// WRONG — getAtmosphere() calls getSunDirection() before it's defined
vec3 getAtmosphere(vec3 dir) { return getSunDirection(); } // Error!
vec3 getSunDirection() { return normalize(vec3(1.0)); }

// CORRECT — define callee first
vec3 getSunDirection() { return normalize(vec3(1.0)); }
vec3 getAtmosphere(vec3 dir) { return getSunDirection(); } // Works
```

### Macro Limitations
- `#define` cannot use function calls — use `const` instead:
```glsl
// WRONG
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6))

// CORRECT
const vec3 SUN_DIR = vec3(0.756, 0.378, -0.567); // Pre-computed normalized value
```

### Script Tag Extraction
- When extracting shader source from `<script>` tags, ensure `#version` is the **first character** — use `.trim()`:
```javascript
const fs = document.getElementById('fs').text.trim();
```

### Common Pitfalls
- **Unused uniforms**: Compiler may optimize away unused uniforms, causing `gl.getUniformLocation()` to return `null` — always use uniforms in a way the compiler cannot optimize out
- **Loop indices**: Use runtime constants in loops, not `#define` macros in some ES versions
- **Terrain functions**: Functions like `terrainM(vec2)` need XZ components — use `terrainM(pos.xz + offset)` not `terrainM(pos + offset)`

## HTML Page Setup

When generating a standalone HTML page:

- Canvas fills the entire viewport, auto-resizes on window resize
- Page background black, no scrollbars: `body { margin: 0; overflow: hidden; background: #000; }`
- Implement ShaderToy-compatible uniforms: `iTime`, `iResolution`, `iMouse`, `iFrame`
- For multi-pass effects (Buffer A/B), use WebGL2 framebuffer + ping-pong (see multipass-buffer technique)

## Common Pitfalls

### JS Variable Declaration Order (TDZ — causes white screen crash)

`let`/`const` variables must be declared at the **top** of the `<script>` block, before any function that references them:

```javascript
// 1. State variables FIRST
let frameCount = 0;
let startTime = Date.now();

// 2. Canvas/GL init, shader compile, FBO creation
const canvas = document.getElementById('canvas');
const gl = canvas.getContext('webgl2');
// ...

// 3. Functions and event bindings LAST
function resize() { /* can now safely reference frameCount */ }
function render() { /* ... */ }
window.addEventListener('resize', resize);
```

Reason: `let`/`const` have a Temporal Dead Zone — referencing them before declaration throws `ReferenceError`, causing a white screen.

### GLSL Compilation Errors (self-check after writing shaders)

- **Function signature mismatch**: Call must exactly match definition in parameter count and types. If defined as `float fbm(vec3 p)`, cannot call `fbm(uv)` with a `vec2`
- **Reserved words as variable names**: Do not use: `patch`, `cast`, `sample`, `filter`, `input`, `output`, `common`, `partition`, `active`
- **Strict type matching**: `vec3 x = 1.0` is illegal — use `vec3 x = vec3(1.0)`; cannot use `.z` to access a `vec2`
- **No ternary on structs**: ESSL does not allow ternary operator on struct types — use `if`/`else` instead

### Performance Budget

Deployment environments may use headless software rendering with limited GPU power. Stay within these limits:

- Ray marching main loop: ≤ 128 steps
- Volume sampling / lighting inner loops: ≤ 32 steps
- FBM octaves: ≤ 6 layers
- Total nested loop iterations per pixel: ≤ 1000 (exceeding this freezes the browser)

## Quick Recipes

Common effect combinations — complete rendering pipelines assembled from technique modules.

### Photorealistic SDF Scene
1. **Geometry**: sdf-3d (extended primitives) + csg-boolean-operations (cubic/quartic smin)
2. **Rendering**: ray-marching + normal-estimation (tetrahedron method)
3. **Lighting**: lighting-model (outdoor three-light model) + shadow-techniques (improved soft shadow) + ambient-occlusion
4. **Atmosphere**: atmospheric-scattering (height-based fog with sun tint)
5. **Post**: post-processing (ACES tone mapping) + anti-aliasing (2x SSAA) + camera-effects (vignette)

### Organic / Biological Forms
1. **Geometry**: sdf-3d (extended primitives + deformation operators: twist, bend) + csg-boolean (gradient-aware smin for material blending)
2. **Detail**: procedural-noise (FBM with derivatives) + domain-warping
3. **Surface**: lighting-model (subsurface scattering approximation via half-Lambert)

### Procedural Landscape
1. **Terrain**: terrain-rendering + procedural-noise (erosion FBM with derivatives)
2. **Texturing**: texture-mapping-advanced (biplanar mapping + no-tile)
3. **Sky**: atmospheric-scattering (Rayleigh/Mie + height fog)
4. **Water**: water-ocean (Gerstner waves) + lighting-model (Fresnel reflections)

### Stylized 2D Art
1. **Shapes**: sdf-2d (extended library) + sdf-tricks (layered edges, hollowing)
2. **Color**: color-palette (cosine palettes) + polar-uv-manipulation (kaleidoscope)
3. **Polish**: anti-aliasing (SDF analytical AA) + post-processing (bloom, chromatic aberration)

## Shader Debugging Techniques

Visual debugging methods — temporarily replace your output to diagnose issues.

| What to check | Code | What to look for |
|---|---|---|
| Surface normals | `col = nor * 0.5 + 0.5;` | Smooth gradients = correct normals; banding = epsilon too large |
| Ray march step count | `col = vec3(float(steps) / float(MAX_STEPS));` | Red hotspots = performance bottleneck; uniform = wasted iterations |
| Depth / distance | `col = vec3(t / MAX_DIST);` | Verify correct hit distances |
| UV coordinates | `col = vec3(uv, 0.0);` | Check coordinate mapping |
| SDF distance field | `col = (d > 0.0 ? vec3(0.9,0.6,0.3) : vec3(0.4,0.7,0.85)) * (0.8 + 0.2*cos(150.0*d));` | Visualize SDF bands and zero-crossing |
| Checker pattern (UV) | `col = vec3(mod(floor(uv.x*10.)+floor(uv.y*10.), 2.0));` | Verify UV distortion, seams |
| Lighting only | `col = vec3(shadow);` or `col = vec3(ao);` | Isolate shadow/AO contributions |
| Material ID | `col = palette(matId / maxMatId);` | Verify material assignment |
