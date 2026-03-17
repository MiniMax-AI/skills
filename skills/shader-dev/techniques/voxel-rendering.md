## WebGL2 Adaptation Requirements

The code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt for WebGL2:

- Use `canvas.getContext("webgl2")` **(required! WebGL1 does not support in/out keywords)**
- Shader first line: `#version 300 es`, add `precision highp float;` to fragment shader
- **IMPORTANT: #version must be the very first line of the shader! No characters before it (including blank lines/comments/Unicode BOM)**
- Vertex shader: `attribute` → `in`, `varying` → `out`
- Fragment shader: `varying` → `in`, `gl_FragColor` → custom `out vec4 fragColor`, `texture2D()` → `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` needs to be adapted to the standard `void main()` entry point

### WebGL2 Full Adaptation Example

```glsl
// === Vertex Shader ===
const vertexShaderSource = `#version 300 es
in vec2 a_position;
void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
}`;

// === Fragment Shader ===
const fragmentShaderSource = `#version 300 es
precision highp float;

uniform float iTime;
uniform vec2 iResolution;

// IMPORTANT: Important: WebGL2 must declare the output variable!
out vec4 fragColor;

// ... other functions ...

void main() {
    // IMPORTANT: Use gl_FragCoord.xy instead of fragCoord
    vec2 fragCoord = gl_FragCoord.xy;

    vec3 col = vec3(0.0);

    // ... rendering logic ...

    // IMPORTANT: Write to fragColor, not gl_FragColor!
    fragColor = vec4(col, 1.0);
}`;
```

**IMPORTANT: Common GLSL compile errors:**
- `in/out storage qualifier supported in GLSL ES 3.00 only` → Check that you are using `getContext("webgl2")` and `#version 300 es`
- `#version directive must occur on the first line` → Check that the shader string starts with #version, with no characters before it
- **IMPORTANT: GLSL reserved words**: `cast`, `class`, `template`, `namespace`, `union`, `enum`, `typedef`, `sizeof`, `input`, `output`, `filter`, `image`, `sampler`, `fixed`, `volatile`, `public`, `static`, `extern`, `external`, `interface`, `long`, `short`, `double`, `half`, `unsigned`, `superp`, `inline`, `noinline`, etc. are all GLSL reserved words and **must never be used as variable or function names**! Common pitfall: naming a function `cast` for ray casting → compile failure. **Use compound names like `castRay`, `castShadow`, `shootRay` instead**.
- **IMPORTANT: GLSL strict typing**: float/int cannot be mixed. `if (x > 0)` for int, `if (y < 0.0)` for float. Comparing ivec3 members to float requires explicit conversion: `float(c.y) < height`. When getVoxel returns int, compare with `> 0` not `> 0.0`. Function parameter types must match exactly.
- **IMPORTANT: Vector dimension mismatch (vec2 vs vec3)**: `p.xz` returns `vec2` and **must never** be added to `vec3` or passed to functions expecting `vec3` parameters (e.g., `fbm(vec3)`, `noise(vec3)`)! Common error: `fbm(p.xz * 0.08 + vec3(...))` — `vec2 + vec3` compile failure. **Fix**: either use a `vec2` version of noise/fbm, or construct a full vec3: `fbm(vec3(p.xz * 0.08, p.y * 0.05))`. Similarly, `vec2` only has `.x`/`.y`, cannot access `.z`/`.w`.
- **IMPORTANT: length() / floating-point precision**: `length(ivec2)` must first convert to `vec2`: `length(vec2(d))`. Exact floating-point equality comparison almost never works; use range comparison: `floor(p.y) == floor(height)`

# Voxel Rendering Skill

## Use Cases
- Rendering discrete volumetric data on regular 3D grids (Minecraft-style worlds, medical volume data, architectural voxel models)
- Pixel-accurate block/cube scenes
- "Block art", "3D pixel art", "low-poly voxel" visual styles
- Real-time voxel scenes in pure fragment shader environments like ShaderToy
- Advanced lighting effects including shadows, AO, and global illumination

## Core Principles

The core of voxel rendering is the **DDA (Digital Differential Analyzer) ray traversal algorithm**: cast a ray from the camera through each pixel, stepping through the 3D grid cell by cell along the ray direction until hitting an occupied voxel.

For ray `P(t) = rayPos + t * rayDir`, DDA maintains:
- **`mapPos`** = `floor(rayPos)`: current grid coordinate (integer)
- **`deltaDist`** = `abs(1.0 / rayDir)`: t cost to cross one cell
- **`sideDist`** = `(sign(rayDir) * (mapPos - rayPos) + sign(rayDir) * 0.5 + 0.5) * deltaDist`: t distance to the next boundary on each axis

Each step advances along the axis with the smallest `sideDist`, updating `sideDist += deltaDist` and `mapPos += rayStep`.

Normal on hit: `normal = -mask * rayStep`

Face UV is obtained by projecting the hit point onto the two tangent axes of the hit face.

## Implementation Steps

### Step 1: Camera Ray Construction
```glsl
vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
vec3 cameraDir = vec3(0.0, 0.0, 0.8);  // Focal length; larger = narrower FOV
vec3 cameraPlaneU = vec3(1.0, 0.0, 0.0);
vec3 cameraPlaneV = vec3(0.0, 1.0, 0.0) * iResolution.y / iResolution.x;
vec3 rayDir = cameraDir + screenPos.x * cameraPlaneU + screenPos.y * cameraPlaneV;
vec3 rayPos = vec3(0.0, 2.0, -12.0);
```

### Step 2: DDA Initialization
```glsl
ivec3 mapPos = ivec3(floor(rayPos));
vec3 rayStep = sign(rayDir);
vec3 deltaDist = abs(1.0 / rayDir);  // When ray is normalized, equivalent to abs(1.0/rd), no length() needed
vec3 sideDist = (sign(rayDir) * (vec3(mapPos) - rayPos) + (sign(rayDir) * 0.5) + 0.5) * deltaDist;
```

### Step 3: DDA Traversal Loop (Branchless Version)
```glsl
#define MAX_RAY_STEPS 64

bvec3 mask;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    if (getVoxel(mapPos)) break;
    // Branchless axis selection
    mask = lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy));
    sideDist += vec3(mask) * deltaDist;
    mapPos += ivec3(vec3(mask)) * ivec3(rayStep);
}
```

Alternative form (step version):
```glsl
vec3 mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
sideDist += mask * deltaDist;
mapPos += mask * rayStep;
```

### Step 4: Voxel Occupancy Function
```glsl
// Basic version: solid block (most common; use this when user asks for "voxel cube")
// IMPORTANT: Important: getVoxel receives ivec3, but all internal calculations must use float!
bool getVoxel(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);  // ivec3 → vec3 conversion (required!)
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 cube
    return d < 0.0;
}

// Advanced version: SDF boolean operations (sphere carved from box = only corners remain)
bool getVoxelCarved(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    float d = max(-sdSphere(p, 7.5), sdBox(p, vec3(6.0)));  // box ∩ ¬sphere
    return d < 0.0;
}

// Advanced version: height map terrain with material IDs
// IMPORTANT: Key: all comparisons must use float! c.y is int and must be converted to float for comparison
// IMPORTANT: Important: must use range comparison, not exact equality (floating-point precision issues)
int getVoxelMaterial(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion (required!)
    float groundHeight = getTerrainHeight(p.xz);  // p.xz is vec2, passes float parameters
    if (float(c.y) < groundHeight) return 1;       // int → float comparison
    if (float(c.y) < groundHeight + 4.0) return 7;  // int → float comparison
    return 0;
}

// Pure float version (simpler, recommended):
int getVoxelMaterial(vec3 c) {
    float groundHeight = getTerrainHeight(c.xz);
    // IMPORTANT: Use range comparison, never exact equality!
    if (c.y >= groundHeight && c.y < groundHeight + 1.0) return 1;  // Grass top layer
    if (c.y >= groundHeight - 3.0 && c.y < groundHeight) return 2; // Dirt layer
    if (c.y < groundHeight - 3.0) return 3;  // Stone layer
    return 0;
}

// Advanced version: mountain terrain (height-based coloring: grass green → rock gray → snow white)
// IMPORTANT: Key 1: color thresholds must be based on heightRatio (normalized height 0~1), not absolute height!
// IMPORTANT: Key 2: maxH must match the actual maximum return value of getMountainHeight!
//           If getMountainHeight returns at most 15.0, maxH must be 15.0, not arbitrarily 20.0
// IMPORTANT: Key 3: threshold spacing must be large enough (at least 0.2), otherwise color bands are too narrow to see
// IMPORTANT: Key 4: grass area typically covers the largest terrain area (low elevation); set grass threshold high (0.4) to ensure green is clearly visible
float maxH = 15.0;  // IMPORTANT: Must equal the actual max value of getMountainHeight!
int getMountainVoxel(vec3 c) {
    float height = getMountainHeight(c.xz);  // Returns 0 ~ maxH
    if (c.y > height) return 0;  // Air
    float heightRatio = c.y / maxH;  // Normalize to 0~1
    // IMPORTANT: Thresholds from low to high: grass < 0.4, rock 0.4~0.7, snow > 0.7
    if (heightRatio < 0.4) return 1;  // Grass (green) — largest area
    if (heightRatio < 0.7) return 2;  // Rock (gray)
    return 3;                          // Snow cap (white)
}
// IMPORTANT: Corresponding material colors must have sufficient saturation and clear contrast:
// mat==1: vec3(0.25, 0.55, 0.15)  Grass green (saturated green, must not be grayish!)
// mat==2: vec3(0.5, 0.45, 0.4)   Rock gray-brown
// mat==3: vec3(0.92, 0.93, 0.96) Snow white
// IMPORTANT: Lighting must not be too bright or it washes out colors! Sun intensity ≤ 2.0, sky light ≤ 1.0
// IMPORTANT: Gamma correction pow(col, vec3(0.4545)) brightens dark colors and reduces saturation;
//    if colors look grayish-white, make grass green more saturated: vec3(0.2, 0.5, 0.1)

// IMPORTANT: Rotating objects: to rotate a voxel object, apply inverse rotation to the sample point in getVoxel!
// Do not rotate the camera to simulate object rotation (that only changes the viewpoint)
bool getVoxelRotating(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    // Rotate around Y axis: apply inverse rotation to sample point
    float angle = -iTime;  // Negative sign = inverse transform
    float s = sin(angle), co = cos(angle);
    p.xz = vec2(p.x * co - p.z * s, p.x * s + p.z * co);
    float d = sdBox(p, vec3(6.0));  // Rotated solid cube
    return d < 0.0;
}
```

### Step 5: Face Shading (Normal + Base Color)
```glsl
vec3 normal = -vec3(mask) * rayStep;
vec3 color;
if (mask.x) color = vec3(0.5);   // Side faces darkest
if (mask.y) color = vec3(1.0);   // Top face brightest
if (mask.z) color = vec3(0.75);  // Front/back faces medium
fragColor = vec4(color, 1.0);
```

### Step 6: Precise Hit Position and Face UV
```glsl
float t = dot(sideDist - deltaDist, vec3(mask));
vec3 hitPos = rayPos + rayDir * t;
vec3 uvw = hitPos - vec3(mapPos);
vec2 uv = vec2(dot(vec3(mask) * uvw.yzx, vec3(1.0)),
               dot(vec3(mask) * uvw.zxy, vec3(1.0)));
```

### Step 7: Neighbor Voxel AO
```glsl
float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

vec4 voxelAo(vec3 pos, vec3 d1, vec3 d2) {
    vec4 side = vec4(
        getVoxel(pos + d1), getVoxel(pos + d2),
        getVoxel(pos - d1), getVoxel(pos - d2));
    vec4 corner = vec4(
        getVoxel(pos + d1 + d2), getVoxel(pos - d1 + d2),
        getVoxel(pos - d1 - d2), getVoxel(pos + d1 - d2));
    vec4 ao;
    ao.x = vertexAo(side.xy, corner.x);
    ao.y = vertexAo(side.yz, corner.y);
    ao.z = vertexAo(side.zw, corner.z);
    ao.w = vertexAo(side.wx, corner.w);
    return 1.0 - ao;
}

// Bilinear interpolation
vec4 ambient = voxelAo(mapPos - rayStep * mask, mask.zxy, mask.yzx);
float ao = mix(mix(ambient.z, ambient.w, uv.x), mix(ambient.y, ambient.x, uv.x), uv.y);
ao = pow(ao, 1.0 / 3.0);  // Gamma correction to control AO intensity
```

### Step 8: DDA Shadow Ray
```glsl
// IMPORTANT: Shadow steps must be capped at 16; total main ray + shadow ray steps should not exceed 80
#define MAX_SHADOW_STEPS 16

float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        if (getVoxel(ivec3(pos))) return 0.0;
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;
}

vec3 sundir = normalize(vec3(-0.5, 0.6, 0.7));
float shadow = castShadow(hitPos + normal * 0.01, sundir);
float diffuse = max(dot(normal, sundir), 0.0) * shadow;
```

## Complete Code Template

```glsl
// === Voxel Rendering - Complete ShaderToy Template ===
// Includes: DDA traversal, face shading, neighbor AO, hard shadows

// IMPORTANT: Performance critical: SwiftShader software renderer (headless browser evaluation environment) cannot handle too many loop iterations
// Default 64+16=80 steps, suitable for most scenes. Simple scenes (single cube) can increase to 96+24
// Multi-building/character/Minecraft scenes must keep 64+16 or lower!
#define MAX_RAY_STEPS 64
#define MAX_SHADOW_STEPS 16
#define GRID_SIZE 16.0

// ---- Math Utilities ----
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}
float hash31(vec3 n) { return fract(sin(dot(n, vec3(1.0, 113.0, 257.0))) * 43758.5453); }

vec2 rotate2d(vec2 v, float a) {
    float s = sin(a), c = cos(a);
    return vec2(v.x * c - v.y * s, v.y * c + v.x * s);
}

// ---- Voxel Scene Definition ----
// IMPORTANT: Default solid cube. Use sdBox for "voxel cube"; add SDF boolean ops for carved/sculpted shapes
int getVoxel(vec3 c) {
    vec3 p = c + 0.5;
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 block
    if (d < 0.0) {
        if (p.y < -3.0) return 2;
        return 1;
    }
    return 0;
}

// ---- Neighbor AO ----
float getOccupancy(vec3 c) { return float(getVoxel(c) > 0); }

float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

vec4 voxelAo(vec3 pos, vec3 d1, vec3 d2) {
    vec4 side = vec4(
        getOccupancy(pos + d1), getOccupancy(pos + d2),
        getOccupancy(pos - d1), getOccupancy(pos - d2));
    vec4 corner = vec4(
        getOccupancy(pos + d1 + d2), getOccupancy(pos - d1 + d2),
        getOccupancy(pos - d1 - d2), getOccupancy(pos + d1 - d2));
    vec4 ao;
    ao.x = vertexAo(side.xy, corner.x);
    ao.y = vertexAo(side.yz, corner.y);
    ao.z = vertexAo(side.zw, corner.z);
    ao.w = vertexAo(side.wx, corner.w);
    return 1.0 - ao;
}

// ---- DDA Traversal Core ----
struct HitInfo {
    bool  hit;
    float t;
    vec3  pos;
    vec3  normal;
    vec3  mapPos;
    vec2  uv;
    int   mat;
};

HitInfo castRay(vec3 ro, vec3 rd, int maxSteps) {
    HitInfo info;
    info.hit = false;
    info.t = 0.0;

    vec3 mapPos = floor(ro);
    vec3 rayStep = sign(rd);
    vec3 deltaDist = abs(1.0 / rd);
    vec3 sideDist = (rayStep * (mapPos - ro) + rayStep * 0.5 + 0.5) * deltaDist;
    vec3 mask = vec3(0.0);

    for (int i = 0; i < maxSteps; i++) {
        int vox = getVoxel(mapPos);
        if (vox > 0) {
            info.hit = true;
            info.mat = vox;
            info.normal = -mask * rayStep;
            info.mapPos = mapPos;
            info.t = dot(sideDist - deltaDist, mask);
            info.pos = ro + rd * info.t;
            vec3 uvw = info.pos - mapPos;
            info.uv = vec2(dot(mask * uvw.yzx, vec3(1.0)),
                           dot(mask * uvw.zxy, vec3(1.0)));
            return info;
        }
        mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
        sideDist += mask * deltaDist;
        mapPos += mask * rayStep;
    }
    return info;
}

// ---- Shadow Ray ----
// IMPORTANT: Shadow steps at 16 (combined with main ray 64 = 80, within SwiftShader safe range)
float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        // IMPORTANT: getVoxel returns int; comparison must use int constant (0), not float (0.0)
        if (getVoxel(pos) > 0) return 0.0;
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;
}

// ---- Material Colors ----
// IMPORTANT: Texture coloring key: "low saturation" does not mean "near white/gray"!
// Low saturation = colorful but not vivid, must retain clear hue differences (e.g., brick red 0.55,0.35,0.3 not gray-white 0.8,0.8,0.8)
// Brick/stone textures: use UV periodic patterns (mortar lines = dark lines), never use solid colors!
vec3 getMaterialColor(int mat, vec2 uv) {
    vec3 col = vec3(0.6);
    if (mat == 1) col = vec3(0.7, 0.7, 0.75);
    if (mat == 2) col = vec3(0.4, 0.55, 0.3);
    float checker = mod(floor(uv.x * 4.0) + floor(uv.y * 4.0), 2.0);
    col *= 0.85 + 0.15 * checker;
    return col;
}

// ---- Brick/Stone Texture Coloring (use this to replace getMaterialColor when user requests "brick texture") ----
// IMPORTANT: Key: brick texture = UV periodic pattern (staggered rows + mortar dark lines), not solid color!
vec3 getBrickColor(vec2 uv, vec3 baseColor, vec3 mortarColor) {
    vec2 brickUV = uv * vec2(4.0, 8.0);
    float row = floor(brickUV.y);
    brickUV.x += mod(row, 2.0) * 0.5;  // Staggered row offset
    vec2 f = fract(brickUV);
    float mortar = step(f.x, 0.06) + step(f.y, 0.08);  // Mortar joints
    mortar = clamp(mortar, 0.0, 1.0);
    float noise = fract(sin(dot(floor(brickUV), vec2(12.9898, 78.233))) * 43758.5453);
    vec3 brickVariation = baseColor * (0.85 + 0.3 * noise);  // Slight color variation per brick
    return mix(brickVariation, mortarColor, mortar);
}
// Usage example (maze walls):
// if (mat == 1) col = getBrickColor(uv, vec3(0.55, 0.35, 0.3), vec3(0.4, 0.38, 0.35)); // Brick red + mortar
// if (mat == 2) col = getBrickColor(uv, vec3(0.5, 0.48, 0.42), vec3(0.35, 0.33, 0.3)); // Gray stone brick

// ---- Main Function ----
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
    screenPos.x *= iResolution.x / iResolution.y;

    vec3 ro = vec3(0.0, 2.0 * sin(iTime * 0.5), -12.0);
    vec3 forward = vec3(0.0, 0.0, 0.8);
    vec3 rd = normalize(forward + vec3(screenPos, 0.0));

    ro.xz = rotate2d(ro.xz, iTime * 0.3);
    rd.xz = rotate2d(rd.xz, iTime * 0.3);

    vec3 sunDir = normalize(vec3(-0.5, 0.6, 0.7));
    vec3 skyColor = vec3(0.6, 0.75, 0.9);

    HitInfo hit = castRay(ro, rd, MAX_RAY_STEPS);

    vec3 col;
    if (hit.hit) {
        vec3 matCol = getMaterialColor(hit.mat, hit.uv);

        vec3 mask = abs(hit.normal);
        vec4 ambient = voxelAo(hit.mapPos, mask.zxy, mask.yzx);
        float ao = mix(
            mix(ambient.z, ambient.w, hit.uv.x),
            mix(ambient.y, ambient.x, hit.uv.x),
            hit.uv.y);
        ao = pow(ao, 0.5);

        float shadow = castShadow(hit.pos + hit.normal * 0.01, sunDir);

        float diff = max(dot(hit.normal, sunDir), 0.0);
        float sky = 0.5 + 0.5 * hit.normal.y;

        vec3 lighting = vec3(0.0);
        // IMPORTANT: Mountain/terrain scenes: sun light ≤ 2.0, sky light ≤ 1.0; too bright washes out material color differences
        lighting += 2.0 * diff * vec3(1.0, 0.95, 0.8) * shadow;
        lighting += 1.0 * sky * skyColor;
        lighting *= ao;

        col = matCol * lighting;

        // IMPORTANT: Fog: coefficient should not be too large, otherwise nearby objects get swallowed into pure sky color
        // 0.0002 suits GRID_SIZE=16 scenes; use smaller coefficients for larger scenes
        float fog = 1.0 - exp(-0.0002 * hit.t * hit.t);
        col = mix(col, skyColor, clamp(fog, 0.0, 0.7));  // Clamp prevents objects from disappearing entirely
    } else {
        col = skyColor - rd.y * 0.2;
    }

    col = pow(clamp(col, 0.0, 1.0), vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Glowing Voxels (Glow Accumulation)
Accumulate distance-based glow values during DDA traversal; produces semi-transparent glow even on miss.
```glsl
float glow = 0.0;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    float d = sdSomeShape(vec3(mapPos));
    glow += 0.015 / (0.01 + d * d);
    if (d < 0.0) break;
    // ... normal DDA stepping ...
}
vec3 col = baseColor + glow * vec3(0.4, 0.6, 1.0);
```

### Variant 2: Rounded Voxels (Intra-voxel SDF Refinement)
After DDA hit, perform SDF ray march inside the voxel to render rounded blocks.
```glsl
float id = hash31(mapPos);
float w = 0.05 + 0.35 * id;

float sdRoundedBox(vec3 p, float w) {
    return length(max(abs(p) - 0.5 + w, 0.0)) - w;
}

vec3 localP = hitPos - mapPos - 0.5;
for (int j = 0; j < 6; j++) {
    float h = sdRoundedBox(localP, w);
    if (h < 0.025) break;
    localP += rd * max(0.0, h);
}
```

### Variant 3: Hybrid SDF-Voxel Traversal
SDF sphere-tracing with large steps at distance, switching to precise DDA near the surface.
```glsl
#define VOXEL_SIZE 0.0625
#define SWITCH_DIST (VOXEL_SIZE * 1.732)

bool useVoxel = false;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 pos = ro + rd * t;
    float d = mapSDF(useVoxel ? voxelCenter : pos);
    if (!useVoxel) {
        t += d;
        if (d < SWITCH_DIST) { useVoxel = true; voxelPos = getVoxelPos(pos); }
    } else {
        if (d < 0.0) break;
        if (d > SWITCH_DIST) { useVoxel = false; t += d; continue; }
        vec3 exitT = (voxelPos - ro * ird + ird * VOXEL_SIZE * 0.5);
        // ... select minimum axis to advance ...
    }
}
```

### Variant 4: Voxel Cone Tracing
Build multi-level mipmaps, cast cone-shaped rays from hit points for global illumination.
```glsl
vec4 traceCone(vec3 origin, vec3 dir, float coneRatio) {
    vec4 light = vec4(0.0);
    float t = 1.0;
    for (int i = 0; i < 58; i++) {
        vec3 sp = origin + dir * t;
        float diameter = max(1.0, t * coneRatio);
        float lod = log2(diameter);
        vec4 sample = voxelFetch(sp, lod);
        light += sample * (1.0 - light.w);
        t += diameter;
    }
    return light;
}
```

### Variant 5: PBR Lighting + Multi-Bounce Reflection
GGX BRDF replacing Lambert, with metallic/roughness parameters; cast a second DDA ray for reflections.
```glsl
float ggxDiffuse(float NoL, float NoV, float LoH, float roughness) {
    float FD90 = 0.5 + 2.0 * roughness * LoH * LoH;
    float a = 1.0 + (FD90 - 1.0) * pow(1.0 - NoL, 5.0);
    float b = 1.0 + (FD90 - 1.0) * pow(1.0 - NoV, 5.0);
    return a * b / 3.14159;
}

vec3 rd2 = reflect(rd, normal);
HitInfo reflHit = castRay(hitPos + normal * 0.001, rd2, 64);
vec3 reflColor = reflHit.hit ? shade(reflHit) : skyColor;

float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(normal, -rd), 0.0), 5.0);
col += fresnel * reflColor;
```

### Variant 6: Voxel Water Scene (Water + Underwater Voxels)
Water surface ripple reflections, underwater refraction, sand and seaweed for a complete water scene.
```glsl
float waterY = 0.0;

// Underwater voxel scene definition (sand + seaweed)
// IMPORTANT: All coordinate operations must use correct vector dimensions!
// c.xz returns vec2, only has .x/.y components, cannot use .z!
int getVoxel(vec3 c) {
    float sandHeight = -3.0 + 0.5 * sin(c.x * 0.3) * cos(c.z * 0.4);
    if (c.y < sandHeight) return 1;      // Sand interior
    if (c.y < sandHeight + 1.0) return 2; // Sand surface
    // Seaweed: only grows underwater, above sand
    float grassHash = fract(sin(dot(floor(c.xz), vec2(12.9898, 78.233))) * 43758.5453);
    // IMPORTANT: floor(c.xz) is vec2; the second argument to dot() must also be vec2
    if (grassHash > 0.85 && c.y >= sandHeight + 1.0 && c.y < sandHeight + 1.0 + 3.0 * grassHash) {
        return 3;  // Seaweed
    }
    return 0;
}

// Handle water surface in main rendering
float tWater = (waterY - ro.y) / rd.y;
bool hitWater = tWater > 0.0 && (tWater < hit.t || !hit.hit);

if (hitWater) {
    vec3 waterPos = ro + rd * tWater;
    vec3 waterNormal = vec3(0.0, 1.0, 0.0);
    // IMPORTANT: waterPos.xz is vec2; access with .x/.y (not .x/.z)
    vec2 waveXZ = waterPos.xz;  // vec2: waveXZ.x = worldX, waveXZ.y = worldZ
    waterNormal.x += 0.05 * sin(waveXZ.x * 3.0 + iTime);
    waterNormal.z += 0.05 * cos(waveXZ.y * 2.0 + iTime * 0.7);
    waterNormal = normalize(waterNormal);

    float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(waterNormal, -rd), 0.0), 5.0);

    // Reflection
    vec3 reflDir = reflect(rd, waterNormal);
    HitInfo reflHit = castRay(waterPos + waterNormal * 0.01, reflDir, 64);
    vec3 reflCol = reflHit.hit ? getMaterialColor(reflHit.mat, reflHit.uv) : skyColor;

    // Refraction (underwater voxels: sand, seaweed)
    vec3 refrDir = refract(rd, waterNormal, 1.0 / 1.33);
    HitInfo refrHit = castRay(waterPos - waterNormal * 0.01, refrDir, 64);
    vec3 refrCol;
    if (refrHit.hit) {
        vec3 matCol = getMaterialColor(refrHit.mat, refrHit.uv);
        float underwaterDist = length(refrHit.pos - waterPos);
        refrCol = mix(matCol, vec3(0.0, 0.15, 0.3), 1.0 - exp(-0.1 * underwaterDist));
    } else {
        refrCol = vec3(0.0, 0.1, 0.3);
    }

    col = mix(refrCol, reflCol, fresnel);
    col = mix(col, vec3(0.0, 0.3, 0.5), 0.2);
}
```

### Variant 7: Rotating Voxel Objects
Rotate voxel objects as a whole. Core: apply inverse rotation to sample points in getVoxel.
```glsl
// IMPORTANT: Correct way to rotate objects: apply inverse rotation to sample coordinates in getVoxel
// Wrong approach: only rotate the camera (that just changes the viewpoint, not the object)
int getVoxel(vec3 c) {
    vec3 p = c + 0.5;
    // Rotate around Y axis
    float angle = -iTime * 0.5;
    float s = sin(angle), co = cos(angle);
    p.xz = vec2(p.x * co - p.z * s, p.x * s + p.z * co);
    // Can also rotate around multiple axes:
    // p.yz = vec2(p.y * co2 - p.z * s2, p.y * s2 + p.z * co2);  // X axis rotation
    float d = sdBox(p, vec3(6.0));
    if (d < 0.0) return 1;
    return 0;
}
```

### Variant 8: Indoor/Cave/Enclosed Scenes (Point Lights + High Ambient Lighting)
Indoor, cave, underground, sci-fi base, and other enclosed or semi-enclosed scenes require point lights and high ambient lighting.
```glsl
// IMPORTANT: Key points for enclosed/semi-enclosed scenes (caves, interiors, sci-fi bases, mazes, etc.):
// 1. Camera must be placed inside the cavity (a position where getVoxel returns 0)
// 2. Must use point lights, not just directional light (directional light blocked by walls/ceiling = total darkness!)
// 3. Ambient light must be high enough (at least 0.2-0.3) to prevent scene from being too dark to see details
// 4. Can use multiple point lights + emissive voxels to simulate torches/fluorescence/holographic displays
// 5. Sci-fi scene metallic walls need bright enough light sources to show reflections
// 6. Emissive elements (holographic screens, indicator lights, magic circles) use emissive materials: add emissive color directly to lighting

// Cave scene: cavity = area where getVoxel returns 0
// IMPORTANT: Cave/terrain noise functions must respect vector dimensions!
// p.xz is vec2; if noise/fbm function takes vec3, construct a full vec3:
//   Correct: fbm(vec3(p.xz, p.y * 0.5))  or use vec2 version of noise
//   Wrong: fbm(p.xz + vec3(...))  ← vec2 + vec3 compile failure!
int getVoxel(vec3 c) {
    float cave = sdSphere(c + 0.5, 12.0);
    // IMPORTANT: For noise-carved detail, use c's components directly (all float)
    cave += 2.0 * sin(c.x * 0.3) * sin(c.y * 0.4) * sin(c.z * 0.35);
    if (cave > 0.0) return 1;  // Rock wall
    return 0;  // Cavity (camera goes here)
}

// Point light attenuation
vec3 pointLightPos = vec3(0.0, 3.0, 0.0);
vec3 toLight = pointLightPos - hit.pos;
float lightDist = length(toLight);
vec3 lightDir = toLight / lightDist;
float attenuation = 1.0 / (1.0 + 0.1 * lightDist + 0.01 * lightDist * lightDist);

float diff = max(dot(hit.normal, lightDir), 0.0);
float shadow = castShadow(hit.pos + hit.normal * 0.01, lightDir);

vec3 lighting = vec3(0.0);
// IMPORTANT: High ambient light to prevent total darkness (required for enclosed scenes! at least 0.2)
lighting += vec3(0.25, 0.22, 0.2);  // Warm ambient light
lighting += 3.0 * diff * attenuation * vec3(1.0, 0.8, 0.5) * shadow;  // Point light

// Multiple torches/emissive objects (use sin for flicker animation)
vec3 torch1 = vec3(5.0, 2.0, 3.0);
vec3 torch2 = vec3(-4.0, 1.0, -5.0);
float flicker1 = 0.8 + 0.2 * sin(iTime * 5.0 + 1.0);
float flicker2 = 0.8 + 0.2 * sin(iTime * 4.3 + 2.7);
lighting += calcPointLight(hit.pos, hit.normal, torch1, vec3(1.0, 0.6, 0.2)) * flicker1;
lighting += calcPointLight(hit.pos, hit.normal, torch2, vec3(0.2, 1.0, 0.5)) * flicker2;

// Emissive materials (holographic displays, fluorescent moss, indicator lights, magic circles, etc.)
// IMPORTANT: Emissive colors are added directly to lighting, unaffected by shadows
if (hit.mat == 2) {
    lighting += vec3(0.1, 0.4, 0.15);  // Fluorescent moss (faint green)
}
if (hit.mat == 3) {
    float pulse = 0.7 + 0.3 * sin(iTime * 2.0);
    lighting += vec3(0.2, 0.6, 1.0) * pulse;  // Blue pulse light
}

col = matCol * lighting;
```

### Variant 9: Voxel Character Animation
Simple voxel character animation using time-driven offsets and rotations.
```glsl
// IMPORTANT: Voxel character animation core approach:
// 1. Split the character into multiple body parts (head, torso, left arm, right arm, left leg, right leg)
// 2. Each part is an sdBox with independent offset/rotation parameters
// 3. iTime drives limb swinging (sin/cos periodic motion)
// 4. Combine all parts using SDF min()
// IMPORTANT: SwiftShader performance critical: character function is called at every DDA step!
//    Must add AABB bounding box check in getVoxel: first check if c is near the character,
//    skip sdBox calculations for that character if not nearby. Otherwise frame timeout → black screen
//    Reduce MAX_RAY_STEPS to 64, MAX_SHADOW_STEPS to 16

int getCharacter(vec3 p, vec3 charPos, float animPhase) {
    vec3 lp = p - charPos;
    float limbSwing = sin(iTime * 4.0 + animPhase) * 0.5;

    // Torso
    float body = sdBox(lp - vec3(0, 3, 0), vec3(1.5, 2.0, 1.0));
    // Head
    float head = sdBox(lp - vec3(0, 6, 0), vec3(1.2, 1.2, 1.2));

    // Arm swing (offset y coordinate around shoulder joint to simulate rotation)
    vec3 armOffset = vec3(0, limbSwing * 2.0, limbSwing);
    float leftArm = sdBox(lp - vec3(-2.5, 3, 0) - armOffset, vec3(0.5, 2.0, 0.5));
    float rightArm = sdBox(lp - vec3(2.5, 3, 0) + armOffset, vec3(0.5, 2.0, 0.5));

    // Alternating leg swing
    vec3 legOffset = vec3(0, 0, limbSwing * 1.5);
    float leftLeg = sdBox(lp - vec3(-0.7, 0, 0) - legOffset, vec3(0.5, 1.5, 0.5));
    float rightLeg = sdBox(lp - vec3(0.7, 0, 0) + legOffset, vec3(0.5, 1.5, 0.5));

    float d = min(body, min(head, min(leftArm, min(rightArm, min(leftLeg, rightLeg)))));
    if (d < 0.0) {
        if (head < 0.0) return 10;  // Head (skin color)
        if (leftArm < 0.0 || rightArm < 0.0) return 11;  // Arms
        return 12;  // Torso/legs
    }
    return 0;
}

// Combine scene + characters in getVoxel
// IMPORTANT: Must add AABB bounding box early exit! Character sdBox calculations are expensive
int getVoxel(vec3 c) {
    // Scene (floor, walls, etc.)
    int scene = getSceneVoxel(c);
    if (scene > 0) return scene;
    // IMPORTANT: AABB check: only call getCharacter near the character
    // Character 1: warrior (at position (5,0,0)), bounding box ±5 cells
    if (abs(c.x - 5.0) < 5.0 && c.y >= 0.0 && c.y < 10.0 && abs(c.z) < 5.0) {
        int char1 = getCharacter(c, vec3(5, 0, 0), 0.0);
        if (char1 > 0) return char1;
    }
    // Character 2: mage (at position (-5,0,3)), bounding box ±5 cells
    if (abs(c.x + 5.0) < 5.0 && c.y >= 0.0 && c.y < 10.0 && abs(c.z - 3.0) < 5.0) {
        int char2 = getCharacter(c, vec3(-5, 0, 3), 3.14);
        if (char2 > 0) return char2;
    }
    return 0;
}
```

### Variant 10: Waterfall / Flowing Water Particle Effects
Dynamic waterfall, splash particles, water mist effects. Core: time-offset noise simulates water flow, hashed particles simulate splashes, exponential decay simulates mist.
```glsl
// IMPORTANT: Key points for waterfall/flowing water/particle effects:
// 1. Waterfall stream: noise + iTime vertical offset simulates water column flowing down
// 2. Splash particles: hash-distributed voxels at the bottom, positions change with iTime to simulate splashing
// 3. Water mist: semi-transparent accumulation (reduced alpha) or density field at the bottom simulates mist diffusion
// 4. Waterfall must have a clear high point (cliff/rock wall) and low point (pool), drop ≥ 10 cells
// 5. Water stream material uses light blue-white + brightness flicker to simulate flowing water feel

float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

int getVoxel(vec3 c) {
    // Cliff rock walls (both sides + back)
    if (c.x < -5.0 || c.x > 5.0) {
        if (c.y < 15.0 && c.z > -3.0 && c.z < 3.0) return 1;  // Rock
    }
    if (c.z > 2.0 && c.y < 15.0 && abs(c.x) < 6.0) return 1;  // Back wall

    // Cliff top platform
    if (c.y >= 13.0 && c.y < 15.0 && c.z > -1.0 && c.z < 3.0 && abs(c.x) < 5.0) return 1;

    // Bottom pool floor
    if (c.y < -2.0 && abs(c.x) < 8.0 && c.z > -6.0 && c.z < 3.0) return 2;  // Pool bottom

    // IMPORTANT: Waterfall stream: narrow band x ∈ [-2, 2], falling from y=13 to y=0
    //    Use iTime offset on y-coordinate noise to simulate downward water flow
    if (abs(c.x) < 2.0 && c.y >= 0.0 && c.y < 13.0 && c.z > -1.0 && c.z < 1.0) {
        float flowNoise = hash21(vec2(floor(c.x), floor(c.y - iTime * 8.0)));
        if (flowNoise > 0.25) return 3;  // Water (gaps simulate translucent water curtain)
    }

    // IMPORTANT: Splash particles: bottom y ∈ [-1, 3], x ∈ [-4, 4]
    //    Use hash + iTime to generate randomly bouncing voxel particles
    if (c.y >= -1.0 && c.y < 3.0 && abs(c.x) < 4.0 && c.z > -3.0 && c.z < 2.0) {
        float t = iTime * 3.0;
        float particleHash = hash21(vec2(floor(c.x * 2.0), floor(c.z * 2.0) + floor(t)));
        float yOffset = fract(t + particleHash) * 3.0;  // Particle upward trajectory
        if (abs(c.y - yOffset) < 0.6 && particleHash > 0.7) return 4;  // Splash particle
    }

    // IMPORTANT: Water mist: bottom y ∈ [-1, 2], wider range than splashes
    //    Density decreases with height and distance from waterfall center
    if (c.y >= -1.0 && c.y < 2.0 && abs(c.x) < 6.0 && c.z > -5.0 && c.z < 3.0) {
        float distFromCenter = length(vec2(c.x, c.z));
        float mistDensity = exp(-0.15 * distFromCenter) * exp(-0.5 * max(c.y, 0.0));
        float mistNoise = hash21(vec2(floor(c.x * 0.5 + iTime * 0.5), floor(c.z * 0.5)));
        if (mistNoise < mistDensity * 0.8) return 5;  // Water mist
    }

    return 0;
}

// Material colors
vec3 getMaterialColor(int mat, vec2 uv) {
    if (mat == 1) return vec3(0.45, 0.4, 0.35);    // Rock
    if (mat == 2) return vec3(0.35, 0.3, 0.25);    // Pool bottom
    if (mat == 3) {                                  // Water stream (shimmering blue-white)
        float shimmer = 0.8 + 0.2 * sin(uv.y * 20.0 + iTime * 10.0);
        return vec3(0.6, 0.8, 1.0) * shimmer;
    }
    if (mat == 4) return vec3(0.85, 0.92, 1.0);    // Splash (bright white)
    if (mat == 5) return vec3(0.7, 0.82, 0.9);     // Water mist (pale blue-white)
    return vec3(0.5);
}

// IMPORTANT: Water mist material needs special lighting: high emissive + translucent feel
// During shading:
if (hit.mat == 5) {
    lighting += vec3(0.4, 0.5, 0.6);  // Water mist emissive (unaffected by shadows)
}

// Camera: side angle slightly elevated, showing the full waterfall (top to bottom + bottom splashes and mist)
// ro = vec3(12.0, 10.0, -10.0), lookAt = vec3(0.0, 6.0, 0.0)
```

### Variant 11: Multi-Building / Town / Minecraft-Style Scenes (Multi-Structure Town Composition)
Towns, villages, Minecraft-style worlds, and other scenes requiring multiple discrete structures (houses, trees, lampposts, etc.) placed on the ground.
**IMPORTANT: "Minecraft-like voxel scene" = multi-building scene; must follow the performance constraints of this template!**
```glsl
// IMPORTANT: Key points for multi-building scenes:
// 1. Define the ground first (height map or flat plane), ensure ground getVoxel returns correct material
// 2. Each building uses an independent helper function, receiving local coordinates, returning material ID
// 3. In getVoxel, check each building sequentially (using offset coordinates), return on first hit
// 4. Camera must be outside the scene facing the center, far enough to see the full view
// 5. IMPORTANT: Building coordinate ranges must be within DDA traversal range (MAX_RAY_STEPS * cell ≈ reachable distance)
// 6. IMPORTANT: Scene range should not be too large! Concentrate all buildings within -20~20 range, camera 30-50 cells away
// 7. IMPORTANT: SwiftShader performance critical: getVoxel must have AABB bounding box early exit!
//    Above ground (c.y > 0), check AABB range first; return 0 immediately if outside building area
//    Otherwise every DDA step checks all buildings → frame timeout → black screen / only sky renders
// 8. IMPORTANT: MAX_RAY_STEPS reduced to 64, MAX_SHADOW_STEPS to 16 (complex getVoxel requires lower step counts)

// Single house: width w, depth d, height h, with triangular roof
int makeHouse(vec3 p, float w, float d, float h, int wallMat, int roofMat) {
    // Walls
    if (p.x >= 0.0 && p.x < w && p.z >= 0.0 && p.z < d && p.y >= 0.0 && p.y < h) {
        return wallMat;
    }
    // Triangular roof: starts from wall top, x range narrows by 1 per level
    float roofY = p.y - h;
    float roofInset = roofY;  // Inset by 1 cell per level
    if (roofY >= 0.0 && roofY < w * 0.5
        && p.x >= roofInset && p.x < w - roofInset
        && p.z >= 0.0 && p.z < d) {
        return roofMat;
    }
    return 0;
}

// Tree: trunk + spherical canopy
int makeTree(vec3 p, float trunkH, float crownR, int trunkMat, int leafMat) {
    // Trunk (1x1 column)
    if (p.x >= -0.5 && p.x < 0.5 && p.z >= -0.5 && p.z < 0.5
        && p.y >= 0.0 && p.y < trunkH) {
        return trunkMat;
    }
    // Spherical canopy
    vec3 crownCenter = vec3(0.0, trunkH + crownR * 0.5, 0.0);
    if (length(p - crownCenter) < crownR) {
        return leafMat;
    }
    return 0;
}

// Lamppost: thin pole + glowing top block
int makeLamp(vec3 p, float h, int poleMat, int lightMat) {
    if (p.x >= -0.3 && p.x < 0.3 && p.z >= -0.3 && p.z < 0.3
        && p.y >= 0.0 && p.y < h) {
        return poleMat;  // Pole
    }
    if (p.x >= -0.5 && p.x < 0.5 && p.z >= -0.5 && p.z < 0.5
        && p.y >= h && p.y < h + 1.0) {
        return lightMat;  // Lamp head (emissive)
    }
    return 0;
}

int getVoxel(vec3 c) {
    // 1. Ground (y < 0 is underground, y == 0 layer is surface)
    if (c.y < -1.0) return 0;
    if (c.y < 0.0) return 1;  // Ground (dirt/grass)

    // 2. Road (along z direction, x range -2~2)
    if (c.y < 1.0 && abs(c.x) < 2.0) return 2;  // Road surface

    // IMPORTANT: AABB bounding box early exit (required for SwiftShader!)
    // All buildings are within x:-15~15, y:0~12, z:-5~15
    // Return 0 immediately outside this range, avoiding per-building checks
    if (c.x < -15.0 || c.x > 15.0 || c.y > 12.0 || c.z < -5.0 || c.z > 15.0) return 0;

    // 3. Place buildings (each with offset coordinates)
    // IMPORTANT: House width/height must be ≥ 5 cells, otherwise they look like dots from far away! Use bright material colors
    int m;

    // House A: position (5, 0, 3), width 6, depth 5, height 5
    m = makeHouse(c - vec3(5.0, 0.0, 3.0), 6.0, 5.0, 5.0, 3, 4);
    if (m > 0) return m;

    // House B: position (-10, 0, 2), width 7, depth 5, height 5
    m = makeHouse(c - vec3(-10.0, 0.0, 2.0), 7.0, 5.0, 5.0, 5, 4);
    if (m > 0) return m;

    // Tree: position (0, 0, 8)
    m = makeTree(c - vec3(0.0, 0.0, 8.0), 4.0, 2.5, 6, 7);
    if (m > 0) return m;

    // Lamppost: position (3, 0, 0)
    m = makeLamp(c - vec3(3.0, 0.0, 0.0), 5.0, 8, 9);
    if (m > 0) return m;

    return 0;
}

// IMPORTANT: Camera setup: must be far enough to overlook the entire town
// Recommended: ro = vec3(0, 15, -35), looking at scene center vec3(0, 3, 5)
vec3 ro = vec3(0.0, 15.0, -35.0);
vec3 lookAt = vec3(0.0, 3.0, 5.0);
vec3 forward = normalize(lookAt - ro);
vec3 right = normalize(cross(forward, vec3(0, 1, 0)));
vec3 up = cross(right, forward);
vec3 rd = normalize(forward * 0.8 + right * screenPos.x + up * screenPos.y);

// IMPORTANT: Sunset/side-lit scene key: when light comes from the side or at low angle, building fronts may be completely backlit turning into black silhouettes!
// Must satisfy all: (1) ambient light ≥ 0.3 (prevent backlit faces from going black); (2) house walls use bright materials (e.g., light yellow 0.85,0.75,0.55)
// (3) house dimensions must not be too small (width/height ≥ 5 cells), otherwise they look like dots from far away
vec3 sunDir = normalize(vec3(-0.8, 0.3, 0.5));  // Sunset low angle
vec3 sunColor = vec3(1.0, 0.6, 0.3);  // Warm orange
vec3 ambientColor = vec3(0.35, 0.3, 0.4);  // IMPORTANT: High ambient light (≥0.3) to prevent silhouettes
// lighting = ambientColor + diff * sunColor * shadow;
```

## Performance & Composition

**Performance Tips:**
- Early exit: break immediately when `mapPos` exceeds scene bounds
- Shadow ray steps of 16-24 are sufficient
- Use SDF sphere-tracing with large steps in open areas, switch to DDA near surfaces
- Material queries, AO, normals, etc. are only computed after hit
- Replace procedural voxel queries with `texelFetch` texture sampling
- Multi-frame accumulation + reprojection for low-noise results
- **IMPORTANT: MAX_RAY_STEPS defaults to 64, MAX_SHADOW_STEPS defaults to 16 (total 80)**. Only simple scenes (single cube/sphere) can increase to 96+24. Multi-building/Minecraft/character scenes with complex getVoxel must keep 64+16 or lower, otherwise SwiftShader frame timeout → only sky background renders

**Composition Tips:**
- **Procedural noise terrain**: use FBM/Perlin noise height maps inside `getVoxel()`
- **SDF procedural modeling**: use SDF boolean operations inside `getVoxel()` to define shapes
- **Texture mapping**: after hit, sample 16x16 pixel textures using face UV * 16
- **Atmospheric scattering / volumetric fog**: accumulate medium density during DDA traversal
- **Water surface rendering**: Fresnel reflection/refraction on a specific Y plane (see Variant 6 above)
- **Global illumination**: cone tracing or Monte Carlo hemisphere sampling
- **Temporal reprojection**: multi-frame accumulation + previous frame reprojection for anti-aliasing and denoising

## Common Errors

1. **GLSL reserved words causing compile failure**: `cast`, `class`, `template`, `namespace`, `input`, `output`, `filter`, `image`, `sampler`, `half`, `fixed`, etc. are GLSL reserved words and **must never be used as variable or function names**. Use compound names: `castRay`, `castShadow`, `shootRay`, `spellEffect` (not `cast`)
2. **Enclosed/semi-enclosed scene total darkness**: caves, interiors, sci-fi bases, mazes, and other enclosed scenes cannot rely solely on directional light (completely blocked by walls/ceiling); must use point lights + high ambient light (≥0.2) + emissive materials (see Variant 8)
3. **Camera inside voxel causing rendering anomalies**: cave/indoor scene camera origin must be inside the cavity (where getVoxel returns 0), otherwise the first DDA step hits immediately = scene invisible
4. **Complex getVoxel causing SwiftShader black screen (most common with Minecraft-style/town/character/multi-building scenes!)**: getVoxel is called once per DDA step; if it contains multiple buildings/characters/terrain+trees without early exit, frame timeout → only sky background renders. **Must do all of**: (1) AABB bounding box early exit (check coordinate range first, return 0 immediately outside building area); (2) MAX_RAY_STEPS ≤ 64, MAX_SHADOW_STEPS ≤ 16; (3) scene range within ±20 cells. **Minecraft-style scene = multi-building scene**; must follow this rule (see Variant 9, 11 template code)
5. **vec2/vec3 dimension mismatch causing compile failure**: `p.xz` returns `vec2` and cannot be passed directly to noise/fbm functions expecting `vec3` parameters or used in operations with `vec3`. Use `vec3(p.xz, val)` to construct a full vec3, or use vec2 versions of functions
6. **Mountain/terrain height-based coloring invisible**: (1) `maxH` must equal the actual max return value of the terrain noise function (don't arbitrarily use 20.0); (2) grass threshold at 0.4 (largest area ensures green is visible), rock 0.4~0.7, snow >0.7; (3) grass green must be saturated enough `vec3(0.25, 0.55, 0.15)` not grayish; (4) sun intensity ≤2.0, sky light ≤1.0, too bright washes out colors; (5) gamma correction reduces saturation, pre-compensate material colors (see Step 4 mountain terrain template)
7. **Waterfall/flowing water effect lacks recognizability**: waterfall must have a clear cliff drop (≥10 cells), visible water column (noise + iTime offset), bottom splash particles (hash random bouncing), and mist (exponential decay density field). Just a gradient color block is not a waterfall! See Variant 10 complete template
8. **"Low saturation coloring" becomes pure white/gray**: low saturation ≠ near white! Low saturation means colors are not vivid but still have clear hue (e.g., brick red `vec3(0.55, 0.35, 0.3)` not gray-white `vec3(0.8, 0.8, 0.8)`). Brick/stone textures must use UV periodic patterns (staggered rows + mortar dark lines), not solid colors. See the `getBrickColor` function in the complete template
9. **Sunset/side-lit scene buildings become black silhouettes**: when low-angle light (sunset/dawn) illuminates from the side, building fronts are completely backlit → pure black silhouettes with no visible detail. Must: (1) ambient light ≥ 0.3; (2) walls use bright materials (light yellow, off-white) not dark colors; (3) buildings large enough (width/height ≥ 5 cells). See Variant 11 sunset scene code

## Further Reading

For full step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/voxel-rendering.md)
