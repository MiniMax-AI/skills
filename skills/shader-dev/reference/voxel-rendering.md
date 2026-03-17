# Voxel Rendering — Detailed Reference

> This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

### GLSL Fundamentals
- GLSL basic syntax (uniforms, varyings, built-in functions)
- Vector math: dot product, cross product, normalize, reflect
- Understanding of step functions like `floor()`, `sign()`, `step()`

### Ray-AABB Intersection (Ray-Box Intersection)
The foundation of voxel rendering is ray tracing. You need to understand how a ray `P(t) = O + t * D` intersects with an axis-aligned bounding box (AABB). The DDA algorithm is essentially an extension of this test to the entire grid space.

### Basic Lighting Models
- Lambert diffuse: `diffuse = max(dot(normal, lightDir), 0.0)`
- Phong specular: `specular = pow(max(dot(reflect(-lightDir, normal), viewDir), 0.0), shininess)`

### SDF (Signed Distance Field) Basics
An SDF function returns the signed distance from a point to the nearest surface (negative inside, positive outside). In voxel rendering, SDF is commonly used to define voxel occupancy: `d < 0.0` means occupied.

Common SDF primitives:
```glsl
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}
```

SDF boolean operations:
- Union: `min(d1, d2)`
- Intersection: `max(d1, d2)`
- Subtraction: `max(d1, -d2)`

## Implementation Steps

### Step 1: Camera Ray Construction

**What**: Convert each pixel coordinate into a world-space ray origin and direction.

**Why**: Voxel rendering follows the ray tracing paradigm, with each pixel independently casting a ray. Screen coordinates must first be normalized to the [-1, 1] range, then transformed through camera parameters (focal length, plane vectors) to construct world-space ray directions.

**Mathematical derivation**:
1. `screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0` normalizes pixel coordinates to [-1, 1]
2. The z component of `cameraDir` controls focal length: larger values = smaller FOV (more "telephoto")
3. `cameraPlaneV` is multiplied by aspect ratio correction to ensure square voxels aren't stretched
4. Final ray direction = camera forward + screen offset, no normalization needed (the DDA algorithm handles it naturally)

**Code**:
```glsl
vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
vec3 cameraDir = vec3(0.0, 0.0, 0.8);  // Tunable: focal length, larger = smaller FOV
vec3 cameraPlaneU = vec3(1.0, 0.0, 0.0);
vec3 cameraPlaneV = vec3(0.0, 1.0, 0.0) * iResolution.y / iResolution.x;
vec3 rayDir = cameraDir + screenPos.x * cameraPlaneU + screenPos.y * cameraPlaneV;
vec3 rayPos = vec3(0.0, 2.0, -12.0);  // Tunable: camera position
```

### Step 2: DDA Initialization

**What**: Compute the initial parameters needed for grid traversal by the ray.

**Why**: The DDA algorithm requires precomputing the step direction, step cost, and distance to the first boundary for each axis. These values are incrementally updated throughout traversal, avoiding per-step division.

**Key variable details**:

- **`mapPos = floor(rayPos)`**: grid coordinate of the cell containing the ray origin. `floor()` discretizes continuous coordinates to the integer grid.

- **`rayStep = sign(rayDir)`**: step direction for each axis. `sign()` returns +1 or -1, determining whether the ray advances in the positive or negative direction on that axis.

- **`deltaDist = abs(1.0 / rayDir)`**: the t cost for the ray to traverse one full grid cell on each axis. If the ray is normalized (length=1), use `1.0/rayDir` directly; when unnormalized, it's equivalent to `abs(vec3(length(rayDir)) / rayDir)`.

- **`sideDist`**: the t distance from the ray origin to the next grid boundary on each axis. The formula `(sign(rayDir) * (mapPos - rayPos) + sign(rayDir) * 0.5 + 0.5) * deltaDist` computes the distance ratio from the ray origin to the next boundary on that axis, then multiplies by deltaDist to get the actual t value.

**Code**:
```glsl
ivec3 mapPos = ivec3(floor(rayPos));        // Current grid coordinate
vec3 rayStep = sign(rayDir);                 // Step direction per axis (+1/-1)
vec3 deltaDist = abs(1.0 / rayDir); // t cost to traverse one cell (ray already normalized)
// Initial t distance to next boundary
vec3 sideDist = (sign(rayDir) * (vec3(mapPos) - rayPos) + (sign(rayDir) * 0.5) + 0.5) * deltaDist;
```

### Step 3: DDA Traversal Loop (Branchless Version)

**What**: Traverse the grid cell by cell, checking for hits.

**Why**: The branchless version uses `lessThanEqual` + `min` vector comparisons to determine the minimum axis in one pass, avoiding nested if-else statements and improving GPU efficiency (reduces warp divergence).

**Algorithm logic**:
1. Each iteration first checks if the current cell is occupied
2. If no hit, find the axis corresponding to the smallest component in `sideDist`
3. `lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy))` generates a bvec3 where the minimum axis is true
4. Add `deltaDist` to that axis's `sideDist`, and add `rayStep` to `mapPos`
5. `mask` records the axis of the last step, used later for normal calculation

**Code**:
```glsl
#define MAX_RAY_STEPS 64  // Tunable: maximum traversal steps, affects maximum view distance

bvec3 mask;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    if (getVoxel(mapPos)) break;  // Hit detection

    // Branchless axis selection: choose the axis with smallest sideDist
    mask = lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy));

    sideDist += vec3(mask) * deltaDist;
    mapPos += ivec3(vec3(mask)) * ivec3(rayStep);
}
```

**Alternative form (step version, common in compact demos)**:
```glsl
vec3 mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
sideDist += mask * deltaDist;
mapPos += mask * rayStep;
```

`step(a, b)` returns `a <= b ? 1.0 : 0.0`; multiplying two steps is equivalent to "this axis is simultaneously <= both other axes," i.e., it is the minimum axis.

### Step 4: Voxel Occupancy Function

**What**: Determine whether a given grid coordinate is occupied.

**Why**: This is the sole "scene definition" interface. By replacing this function, you can generate voxel worlds from any data source — procedural SDF, heightmaps, noise, etc. This design completely decouples scene content from the rendering algorithm.

**Design points**:
- Input is integer grid coordinates; add 0.5 to get the voxel center point
- Returns a boolean (simple version) or material ID (advanced version)
- Can use any combination of SDFs, noise functions, or texture sampling internally
- Performance-critical: this function is called once per DDA step, so keep it concise

**Code**:
```glsl
// Basic version: solid cube (use this when user requests a "voxel cube")
// NOTE: getVoxel receives ivec3, but internal calculations must all use float!
bool getVoxel(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);  // ivec3 → vec3 conversion (required!)
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 block
    return d < 0.0;
}

// SDF boolean version: sphere carving out a block (keeping only edges)
bool getVoxelCarved(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    float d = max(-sdSphere(p, 7.5), sdBox(p, vec3(6.0)));  // box ∩ ¬sphere
    return d < 0.0;
}

// Advanced version: heightmap terrain with material IDs
// NOTE: Two correct approaches:
// Approach 1: Use vec3 parameter (recommended)
int getVoxelMaterial(vec3 c) {
    float height = getTerrainHeight(c.xz);
    if (c.y < height) return 1;       // Ground (c.y is float)
    if (c.y < height + 4.0) return 7;  // Tree trunk
    return 0;                          // Air
}

// Approach 2: Use ivec3 parameter (requires explicit conversion)
int getVoxelMaterial(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion (required!)
    float height = getTerrainHeight(p.xz);
    if (float(c.y) < height) return 1;       // int → float comparison
    if (float(c.y) < height + 4.0) return 7; // int → float comparison
    return 0;
}
```

### Step 5: Face Shading (Normal + Base Color)

**What**: Assign different brightness levels to different faces based on the hit face's normal direction.

**Why**: This is the simplest voxel shading approach — three distinct face brightnesses produce the classic "Minecraft-style" visual effect. No additional lighting calculations needed; face orientation alone provides differentiation.

**Principle**:
- `mask` records the axis of the last DDA step
- Normal = reverse direction of the step axis: `-mask * rayStep`
- X-axis faces (sides) are darkest, Y-axis faces (top/bottom) brightest, Z-axis faces (front/back) medium brightness
- This fixed three-value shading simulates basic lighting under overhead illumination

**Code**:
```glsl
// Face normal derived directly from mask
vec3 normal = -vec3(mask) * rayStep;

// Three faces with different brightness
vec3 color;
if (mask.x) color = vec3(0.5);   // Side face (X axis) darkest
if (mask.y) color = vec3(1.0);   // Top face (Y axis) brightest
if (mask.z) color = vec3(0.75);  // Front/back face (Z axis) medium

fragColor = vec4(color, 1.0);
```

### Step 6: Precise Hit Position and Face UV

**What**: Compute the precise intersection point of the ray with the voxel surface, and the UV coordinates within that face.

**Why**: The precise intersection point is used for texture mapping and AO interpolation, rather than just grid coordinates. Face UV provides continuous coordinates (0 to 1) within a single voxel face — the basis for texture mapping and smooth AO.

**Mathematical derivation**:
1. `sideDist - deltaDist` steps back to get the t value of the hit face
2. `dot(sideDist - deltaDist, mask)` selects the hit axis's t
3. `hitPos = rayPos + rayDir * t` gives the precise intersection point
4. `uvw = hitPos - mapPos` gives voxel-local coordinates [0,1]^3
5. UV is obtained by projecting uvw onto the two tangent axes of the hit face:
   - If X face is hit, UV = (uvw.y, uvw.z)
   - If Y face is hit, UV = (uvw.z, uvw.x)
   - If Z face is hit, UV = (uvw.x, uvw.y)
   - `dot(mask * uvw.yzx, vec3(1.0))` cleverly uses mask to select the correct components

**Code**:
```glsl
// Precise t value: step back one step using sideDist
float t = dot(sideDist - deltaDist, vec3(mask));
vec3 hitPos = rayPos + rayDir * t;

// Face UV (for texturing, AO interpolation)
vec3 uvw = hitPos - vec3(mapPos);  // Voxel-local coordinates [0,1]^3
vec2 uv = vec2(dot(vec3(mask) * uvw.yzx, vec3(1.0)),
               dot(vec3(mask) * uvw.zxy, vec3(1.0)));
```

### Step 7: Neighbor Voxel Ambient Occlusion (AO)

**What**: Sample the 8 neighboring voxels around the hit face (4 edges + 4 corners), compute an occlusion value for each vertex, then bilinearly interpolate.

**Why**: This is the core technique for Minecraft-style smooth lighting. When neighboring voxels are present at edges or corners, those vertex areas should appear darker. This AO requires no additional ray tracing — it's entirely based on neighbor queries, with low computational cost and good results.

**Algorithm details**:
1. For each vertex of the hit face, check the adjacent 2 edges and 1 corner
2. `vertexAo(side, corner)` formula: `(side.x + side.y + max(corner, side.x * side.y)) / 3.0`
   - `side.x * side.y`: when both edges are occupied, even if the corner is empty, there should be full occlusion (prevents light leaking)
   - `max(corner, side.x * side.y)`: takes the larger of the corner and edge product
3. Store the 4 vertex AO values in a vec4
4. Bilinearly interpolate using the face UV for a continuous AO value
5. `pow(ao, gamma)` controls AO contrast

**Code**:
```glsl
// Per-vertex AO: two edges + one corner
float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

// Sample AO for 4 vertices of a face
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

// Bilinear interpolation using face UV
vec4 ambient = voxelAo(mapPos - rayStep * mask, mask.zxy, mask.yzx);
float ao = mix(mix(ambient.z, ambient.w, uv.x), mix(ambient.y, ambient.x, uv.x), uv.y);
ao = pow(ao, 1.0 / 3.0);  // Tunable: gamma correction controls AO intensity
```

### Step 8: DDA Shadow Ray

**What**: Cast a second DDA ray from the hit point toward the light source to detect occlusion.

**Why**: Reusing the same DDA algorithm achieves hard shadows without requiring additional ray tracing infrastructure. Shadow rays typically use fewer steps (e.g., 16-32) to save performance.

**Implementation details**:
- The origin must be offset by `normal * 0.01` to avoid self-intersection
- Shadow rays only need to determine 0/1 occlusion (hard shadows), no precise intersection needed
- Returns 0.0 (occluded) or 1.0 (unoccluded)
- Step count can be lower than the primary ray since only occlusion detection is needed

**Code**:
```glsl
#define MAX_SHADOW_STEPS 32  // Tunable: shadow ray steps

float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        if (getVoxel(ivec3(pos))) return 0.0;  // Occluded
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;  // Unoccluded
}

// Usage during shading
vec3 sundir = normalize(vec3(-0.5, 0.6, 0.7));
float shadow = castShadow(hitPos + normal * 0.01, sundir);
float diffuse = max(dot(normal, sundir), 0.0) * shadow;
```

## Variant Details

### Variant 1: Glowing Voxels (Glow Accumulation)

**Difference from the base version**: During DDA traversal, accumulates a distance-based glow value at each step, producing a semi-transparent glow effect even without a hit.

**Use cases**: Neon light effects, energy fields, particle clouds, sci-fi style

**Principle**: Using the SDF distance field, glow contribution is large near the voxel surface (small distance → large 1/d²) and small far away. Accumulating contributions from all steps produces a continuous glow field.

**Key parameters**:
- `0.015`: glow intensity coefficient — larger = brighter
- `0.01`: minimum distance threshold — prevents division by zero and controls glow "sharpness"
- Glow color `vec3(0.4, 0.6, 1.0)`: can vary based on distance or material

**Code**:
```glsl
float glow = 0.0;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    float d = sdSomeShape(vec3(mapPos));  // Distance to nearest surface
    glow += 0.015 / (0.01 + d * d);      // Tunable: glow falloff
    if (d < 0.0) break;
    // ... normal DDA stepping ...
}
vec3 col = baseColor + glow * vec3(0.4, 0.6, 1.0); // Overlay glow color
```

### Variant 2: Rounded Voxels (Intra-Voxel SDF Refinement)

**Difference from the base version**: After DDA hit, performs a few SDF ray march steps inside the voxel, rendering rounded blocks instead of perfect cubes.

**Use cases**: Organic-style voxels, building block/LEGO effects, chibi characters

**Principle**: After DDA hit, we know which voxel the ray entered, but the precise shape inside is defined by the SDF. Starting SDF ray marching from the voxel entry point, using `sdRoundedBox` to define a rounded cube, marching to the surface yields the precise rounded intersection and normal.

**Key parameters**:
- `w` (corner radius): 0.0 = perfect cube, 0.5 = sphere
- 6 internal march steps are typically sufficient for convergence
- `hash31(mapPos)` randomizes the corner radius per voxel, adding variety

**Code**:
```glsl
// Refine inside the voxel after DDA hit
float id = hash31(mapPos);
float w = 0.05 + 0.35 * id;  // Tunable: corner radius

float sdRoundedBox(vec3 p, float w) {
    return length(max(abs(p) - 0.5 + w, 0.0)) - w;
}

// Start 6-step SDF march from voxel entry
vec3 localP = hitPos - mapPos - 0.5;
for (int j = 0; j < 6; j++) {
    float h = sdRoundedBox(localP, w);
    if (h < 0.025) break;  // Hit rounded surface
    localP += rd * max(0.0, h);
}
```

### Variant 3: Hybrid SDF-Voxel Traversal

**Difference from the base version**: Uses SDF sphere-tracing (large steps) when far from surfaces, switching to precise DDA voxel traversal when close. Greatly improves traversal efficiency in open areas.

**Use cases**: Large open worlds, long-distance voxel terrain, scenes requiring high view distance

**Principle**:
1. In open areas far from any voxel surface, SDF values are large, allowing sphere-tracing to skip large distances in one step
2. When the SDF value approaches `sqrt(3) * voxelSize` (voxel diagonal length), we may be about to enter a voxel region
3. Switch to DDA to ensure no voxels are skipped
4. If DDA finds the ray has left the dense region (SDF value increases again), switch back to sphere-tracing

**Key parameters**:
- `VOXEL_SIZE`: voxel dimensions
- `SWITCH_DIST = VOXEL_SIZE * 1.732`: switching threshold, sqrt(3) is the voxel diagonal safety factor

**Code**:
```glsl
#define VOXEL_SIZE 0.0625       // Tunable: voxel size
#define SWITCH_DIST (VOXEL_SIZE * 1.732)  // sqrt(3) * voxelSize

bool useVoxel = false;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 pos = ro + rd * t;
    float d = mapSDF(useVoxel ? voxelCenter : pos);

    if (!useVoxel) {
        t += d;
        if (d < SWITCH_DIST) {
            useVoxel = true;              // Switch to DDA
            voxelPos = getVoxelPos(pos);
        }
    } else {
        if (d < 0.0) { /* hit */ break; }
        if (d > SWITCH_DIST) {
            useVoxel = false;             // Switch back to SDF
            t += d;
            continue;
        }
        // DDA step one cell
        vec3 exitT = (voxelPos - ro * ird + ird * VOXEL_SIZE * 0.5);
        // ... select minimum axis and advance ...
    }
}
```

### Variant 4: Voxel Cone Tracing

**Difference from the base version**: Builds a multi-level mipmap hierarchy of voxels (e.g., 64→32→16→8→4→2), casts cone-shaped rays from hit points, samples coarser LOD levels as distance increases, achieving diffuse/specular global illumination.

**Use cases**: High-quality global illumination, colored indirect lighting, real-time GI for dynamic scenes

**Principle**:
1. Precompute mipmap levels of voxel data (resolution halved per level)
2. Cast multiple cone-shaped rays from the hit point across the normal hemisphere (typically 5-7 cones)
3. Each cone's diameter increases linearly with distance during traversal
4. Diameter maps to mipmap level: `lod = log2(diameter)`
5. Sample the corresponding mipmap level
6. Front-to-back compositing accumulates lighting and occlusion

**Key parameters**:
- `coneRatio`: cone angle — diffuse uses wide cones (~1.0), specular uses narrow cones (~0.1)
- 58 steps is a common balance value
- `voxelFetch(sp, lod)` requires a custom mipmap query function

**Code**:
```glsl
// Cone tracing: cast a cone-shaped ray along direction d
vec4 traceCone(vec3 origin, vec3 dir, float coneRatio) {
    vec4 light = vec4(0.0);
    float t = 1.0;
    for (int i = 0; i < 58; i++) {
        vec3 sp = origin + dir * t;
        float diameter = max(1.0, t * coneRatio);  // Cone diameter
        float lod = log2(diameter);                  // Corresponding mipmap level
        vec4 sample = voxelFetch(sp, lod);           // LOD sample
        light += sample * (1.0 - light.w);           // Front-to-back compositing
        t += diameter;
    }
    return light;
}
```

### Variant 5: PBR Lighting + Multi-Bounce Reflections

**Difference from the base version**: Uses GGX BRDF instead of Lambert, supports metallic/roughness material parameters, and casts a second DDA ray for reflections.

**Use cases**: Realistic voxel rendering, metallic/glass materials, architectural visualization

**Principle**:
1. GGX (Trowbridge-Reitz) microfacet model provides physically correct light distribution
2. Roughness parameter controls specular sharpness: 0.0 = perfect mirror, 1.0 = fully diffuse
3. Schlick Fresnel approximation: `F = F0 + (1 - F0) * (1 - cos(theta))^5`
4. Reflection ray reuses the `castRay` function with reduced step count (64 steps typically sufficient)
5. Multi-bounce reflections can call recursively, but 1-2 bounces usually suffice

**Key parameters**:
- `roughness`: roughness [0, 1]
- `F0 = 0.04`: base reflectance for non-metals
- 64 steps for reflection ray (fewer than primary ray to save performance)

**Code**:
```glsl
// GGX diffuse term
float ggxDiffuse(float NoL, float NoV, float LoH, float roughness) {
    float FD90 = 0.5 + 2.0 * roughness * LoH * LoH;
    float a = 1.0 + (FD90 - 1.0) * pow(1.0 - NoL, 5.0);
    float b = 1.0 + (FD90 - 1.0) * pow(1.0 - NoV, 5.0);
    return a * b / 3.14159;
}

// Reflection ray - needs a separate shading function to handle HitInfo
vec3 shadeHit(HitInfo h, vec3 rd, vec3 sunDir, vec3 skyColor) {
    if (!h.hit) return skyColor;
    vec3 matCol = getMaterialColor(h.mat, h.uv);
    float diff = max(dot(h.normal, sunDir), 0.0);
    return matCol * diff;
}

vec3 rd2 = reflect(rd, normal);
HitInfo reflHit = castRay(hitPos + normal * 0.001, rd2, 64);
vec3 reflColor = shadeHit(reflHit, rd2, sunDir, skyColor);

// Schlick Fresnel blending
float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(normal, -rd), 0.0), 5.0);
col += fresnel * reflColor;
```

## In-Depth Performance Optimization

### Main Bottlenecks

1. **DDA Loop Step Count**: Each pixel needs to traverse tens to hundreds of cells — the largest performance cost. Step count is proportional to scene size and openness.

2. **Voxel Query Function**: `getVoxel()` is called once per step; if using noise/textures, texture fetch overhead is significant. The complexity of procedural SDF functions directly impacts frame rate.

3. **AO Neighbor Sampling**: Each hit point requires 8 additional `getVoxel()` queries. Manageable for simple scenes, but with a complex `getVoxel`, these 8 queries may exceed the main traversal cost.

4. **Shadow Rays**: Equivalent to a second full DDA traversal. Dual traversal doubles the pixel shader burden.

### Optimization Techniques

#### Early Exit
Break immediately when `mapPos` exceeds scene boundaries, avoiding continued traversal in meaningless space:
```glsl
if (any(lessThan(mapPos, vec3(-GRID_SIZE))) || any(greaterThan(mapPos, vec3(GRID_SIZE)))) break;
```

#### Reduce Shadow Steps
Shadow rays only need to determine occlusion — 16-32 steps usually suffice. No need for the same step count as the primary ray:
```glsl
#define MAX_SHADOW_STEPS 32  // Instead of MAX_RAY_STEPS of 128
```

#### Distance-Based Quality Scaling
Use high step counts for precise traversal up close, low step counts or LOD at distance. Dynamically adjust the step limit based on screen pixel size.

#### Hybrid Traversal
Use SDF sphere-tracing for large steps in open areas, switching to DDA near surfaces (see Variant 3). Can reduce traversal steps by 80%+ in large scenes.

#### Avoid Complex Computation Inside the Loop
Material queries, AO, normals, etc. are all done only after a hit. The traversal loop should only perform the simplest occupancy detection.

#### Leverage GPU Texture Hardware
Replace procedural voxel queries with texture sampling (`texelFetch`). 3D textures can store precomputed voxel data and are cache-friendly on hardware.

#### Temporal Accumulation
Multi-frame accumulation — each frame only needs a small number of samples, combined with reprojection for low-noise results. Suitable for scenarios requiring many rays (GI, soft shadows).

## Complete Combination Code Examples

### Procedural Noise Terrain
Use FBM/Perlin noise inside `getVoxel()` to generate heightmaps, producing Minecraft-style infinite terrain:
```glsl
// Recommended approach: use vec3 parameter (simple, no type conversion issues)
int getVoxel(vec3 c) {
    // FBM noise heightmap
    float height = 0.0;
    float amp = 8.0;
    float freq = 0.05;
    vec2 xz = c.xz;
    for (int i = 0; i < 4; i++) {
        height += amp * noise(xz * freq);
        amp *= 0.5;
        freq *= 2.0;
    }

    if (c.y > height) return 0;           // Air
    if (c.y > height - 1.0) return 1;     // Grass
    if (c.y > height - 4.0) return 2;     // Dirt
    return 3;                              // Stone
}

// ivec3 parameter version (requires type conversion)
int getVoxel(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion
    float height = 0.0;
    float amp = 8.0;
    float freq = 0.05;
    // NOTE: p.xz returns vec2, must pass vec2 version of noise!
    // If noise only has vec3 version, use noise(vec3(p.xz * freq, 0.0))
    vec2 xz = p.xz;
    for (int i = 0; i < 4; i++) {
        height += amp * noise(xz * freq);
        amp *= 0.5;
        freq *= 2.0;
    }

    if (float(c.y) > height) return 0;           // int → float comparison
    if (float(c.y) > height - 1.0) return 1;    // int → float comparison
    if (float(c.y) > height - 4.0) return 2;    // int → float comparison
    return 3;
}
```

### Texture Mapping
Sample textures using face UV after hit, achieving a retro pixel art style:
```glsl
// During the shading stage
vec2 texUV = hit.uv;
// 16x16 pixel texture atlas
int tileX = mat % 4;
int tileY = mat / 4;
vec2 atlasUV = (vec2(tileX, tileY) + texUV) / 4.0;
vec3 texCol = texture(iChannel0, atlasUV).rgb;
col *= texCol;
```

### Atmospheric Scattering / Volumetric Fog
Accumulate medium density during DDA traversal, achieving volumetric lighting and fog effects:
```glsl
float fogAccum = 0.0;
vec3 fogColor = vec3(0.0);
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    // ... DDA stepping ...
    float density = getDensity(mapPos);  // Atmospheric density
    if (density > 0.0) {
        float dt = length(vec3(mask) * deltaDist);  // Current step size
        fogAccum += density * dt;
        // Volumetric light: compute lighting within fog
        float shadowInFog = castShadow(vec3(mapPos) + 0.5, sunDir);
        fogColor += density * dt * shadowInFog * sunColor * exp(-fogAccum);
    }
    if (getVoxel(mapPos) > 0) break;
}
// Apply fog effect
col = col * exp(-fogAccum) + fogColor;
```

### Water Surface Rendering (Voxel Water Scene)
A complete voxel water scene with surface wave reflections, underwater refraction, sand, and seaweed:
```glsl
float waterY = 0.0;

// Underwater voxel scene (sand + seaweed)
// IMPORTANT: c.xz returns vec2, which only has .x/.y components — never use .z!
int getVoxel(vec3 c) {
    float sandHeight = -3.0 + 0.5 * sin(c.x * 0.3) * cos(c.z * 0.4);
    if (c.y < sandHeight) return 1;      // Sand interior
    if (c.y < sandHeight + 1.0) return 2; // Sand surface
    // Seaweed
    float grassHash = fract(sin(dot(floor(c.xz), vec2(12.9898, 78.233))) * 43758.5453);
    if (grassHash > 0.85 && c.y >= sandHeight + 1.0 && c.y < sandHeight + 1.0 + 3.0 * grassHash) {
        return 3;
    }
    return 0;
}

// Check if ray intersects water surface
float tWater = (waterY - ro.y) / rd.y;
bool hitWater = tWater > 0.0 && (tWater < hit.t || !hit.hit);

if (hitWater) {
    vec3 waterPos = ro + rd * tWater;
    vec3 waterNormal = vec3(0.0, 1.0, 0.0);
    // NOTE: waterPos.xz is vec2, access with .x/.y (not .x/.z)
    vec2 waveXZ = waterPos.xz;  // vec2: waveXZ.x = worldX, waveXZ.y = worldZ
    waterNormal.x += 0.05 * sin(waveXZ.x * 3.0 + iTime);
    waterNormal.z += 0.05 * cos(waveXZ.y * 2.0 + iTime * 0.7);
    waterNormal = normalize(waterNormal);

    // Fresnel
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
        // Underwater color attenuation (bluer with distance)
        float underwaterDist = length(refrHit.pos - waterPos);
        refrCol = mix(matCol, vec3(0.0, 0.15, 0.3), 1.0 - exp(-0.1 * underwaterDist));
    } else {
        refrCol = vec3(0.0, 0.1, 0.3);  // Deep water color
    }

    col = mix(refrCol, reflCol, fresnel);
    col = mix(col, vec3(0.0, 0.3, 0.5), 0.2);
}
```

### Global Illumination (Monte Carlo Hemisphere Sampling)
Use random hemisphere direction sampling for diffuse indirect lighting:
```glsl
vec3 indirectLight = vec3(0.0);
int numSamples = 4;  // Few samples per frame, accumulate across frames
for (int s = 0; s < numSamples; s++) {
    // Cosine-weighted hemisphere sampling
    vec2 xi = hash22(vec2(fragCoord) + float(iFrame) * 0.618 + float(s));
    float cosTheta = sqrt(xi.x);
    float sinTheta = sqrt(1.0 - xi.x);
    float phi = 6.28318 * xi.y;

    vec3 sampleDir = cosTheta * normal
                   + sinTheta * cos(phi) * tangent
                   + sinTheta * sin(phi) * bitangent;

    HitInfo giHit = castRay(hitPos + normal * 0.01, sampleDir, 32);
    if (giHit.hit) {
        vec3 giColor = getMaterialColor(giHit.mat, giHit.uv);
        float giDiff = max(dot(giHit.normal, sunDir), 0.0);
        indirectLight += giColor * giDiff;
    } else {
        indirectLight += skyColor;
    }
}
indirectLight /= float(numSamples);
col += matCol * indirectLight * 0.5;  // Indirect light contribution
```
