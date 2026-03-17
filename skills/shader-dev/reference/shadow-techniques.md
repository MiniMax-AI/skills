# SDF Soft Shadow Techniques - Detailed Reference

This document is a complete supplement to [SKILL.md](SKILL.md), covering prerequisite knowledge, step-by-step detailed explanations, mathematical derivations, variant descriptions, and full code examples for combinations.

## Use Cases

- **Shadow computation in SDF raymarching scenes**: When using signed distance fields (SDF) for ray marching rendering and you need to add soft shadow effects to the scene
- **Real-time soft shadow / penumbra effects**: Simulating the penumbra gradient produced by real light source area, rather than simple hard shadow binary results
- **Terrain / heightfield shadows**: Shadow computation for procedural terrain and height maps
- **Multi-layer shadow compositing**: Combining ground shadows, vegetation shadows, cloud shadows, and other shadow sources into a final result
- **Volumetric light / God Ray effects**: Reusing the shadow function to sample along the view ray to generate volumetric light scattering effects
- **Analytical shadows**: Using O(1) analytical shadows for simple geometry like spheres instead of ray marching

## Prerequisites

- **GLSL fundamentals**: uniforms, varyings, built-in functions (`clamp`, `mix`, `smoothstep`, `normalize`, `dot`, `reflect`)
- **Raymarching**: Understanding SDF scene representation and the basic sphere tracing workflow
- **SDF basics**: Understanding signed distance fields — `map(p)` returns the distance from point p to the nearest surface
- **Basic lighting models**: Diffuse (N·L), specular (Blinn-Phong), ambient light
- **Vector math**: Dot product, cross product, vector normalization, ray parametric equation `ro + rd * t`

## Core Principles in Detail

The core idea of SDF soft shadows is: **march from a surface point toward the light source, using the ratio of "nearest distance to march distance" to estimate penumbra width**.

### Classic Formula (2013)

```
shadow = min(shadow, k * h / t)
```

Where:
- `h` = SDF value at the current march position (distance to nearest surface)
- `t` = distance already traveled along the shadow ray
- `k` = constant controlling penumbra softness (larger = harder, smaller = softer)

**Geometric intuition**: The ratio `h/t` approximates "the angular width of the nearest occluder as seen from the current point on the shadow ray." When the ray grazes an object's surface, `h` is small while `t` is large, making `h/t` small and producing a penumbra region; when the ray is far from all objects, `h/t` is large and the area is fully lit.

Taking the minimum `min(res, k*h/t)` across all sample points along the ray yields "the darkest point," which is the final shadow factor.

### Improved Formula (2018)

The classic formula produces overly dark artifacts near sharp edges. The improved version uses SDF values from adjacent steps to perform geometric triangulation, estimating a more accurate nearest point:

```
y = h² / (2 * ph)           // ph = SDF value from previous step
d = sqrt(h² - y²)           // true nearest distance perpendicular to ray direction
shadow = min(shadow, d / (w * max(0, t - y)))
```

**Mathematical derivation**: Assume the previous step at ray position `t-h_step` had SDF value `ph`, and the current step at position `t` has SDF value `h`. The intersection region of these two SDF spheres (with radii `ph` and `h` respectively) provides a more accurate estimate of the nearest surface point. Through simple triangle geometry:
- `y` is the distance to step back along the ray from the current sample point to the nearest point projection
- `d` is the perpendicular distance from the nearest surface point to the ray
- The corrected effective distance is `t - y` rather than `t`

### Negative Extension (2020)

Allows `res` to drop to negative values (minimum -1), then remaps to [0,1] with a custom smooth mapping:

```
res = max(res, -1.0)
shadow = 0.25 * (1 + res)² * (2 - res)
```

This eliminates the hard crease produced by the classic `clamp(0,1)`, achieving a smoother penumbra transition.

**Why it works**: The classic method produces a C0 continuous (non-smooth) crease at `res=0` due to clamping. By allowing `res` to enter the negative domain [-1, 0], then remapping with the C1 continuous function `0.25*(1+res)²*(2-res)`, a completely smooth penumbra gradient is obtained. This function evaluates to 0 at `res=-1` and 1 at `res=1`, with smooth derivative transitions at both ends.

## Implementation Steps in Detail

### Step 1: Scene SDF Definition

**What**: Define the scene's signed distance function, returning the distance from any point in space to the nearest surface.

**Why**: Shadow ray marching needs `map(p)` queries to determine step size and penumbra estimation.

```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdPlane(vec3 p) {
    return p.y;
}

float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

float map(vec3 p) {
    float d = sdPlane(p);
    d = min(d, sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5));
    d = min(d, sdRoundBox(p - vec3(-1.2, 0.3, 0.5), vec3(0.3), 0.05));
    return d;
}
```

### Step 2: Classic Soft Shadow Function

**What**: March from a surface point toward the light source, progressively accumulating the minimum `k*h/t` ratio as the shadow factor.

**Why**: This is the foundational framework for all SDF soft shadows. At each step, `h/t` approximates the angular width of occlusion at that point; the minimum across the entire ray serves as the final penumbra estimate. The k value controls penumbra softness.

```glsl
// Classic SDF soft shadow
// ro: shadow ray origin (surface position)
// rd: light direction (normalized)
// mint: starting offset (to avoid self-shadowing)
// tmax: maximum march distance
float calcSoftShadow(vec3 ro, vec3 rd, float mint, float tmax) {
    float res = 1.0;
    float t = mint;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float s = clamp(SHADOW_K * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, MIN_STEP, MAX_STEP);    // Step size clamping
        if (res < 0.004 || t > tmax) break;    // Early exit
    }

    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);      // Smoothstep smoothing
}
```

### Step 3: Improved Soft Shadow (Geometric Triangulation)

**What**: Use SDF values from the current and previous steps to estimate a more accurate nearest point position via geometric triangulation, eliminating penumbra artifacts near sharp edges.

**Why**: The classic `h/t` formula assumes the nearest surface point is directly below the current sample position, but the actual nearest point may lie between two steps. Using the intersection relationship of SDF spheres from two adjacent steps provides a more accurate estimate of perpendicular distance `d` and corrected depth `t-y` along the ray.

```glsl
// Improved SDF soft shadow
float calcSoftShadowImproved(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;
    float ph = 1e10;  // Previous step SDF value, initialized large so first step y≈0

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);

        // Geometric triangulation: estimate corrected nearest distance
        float y = h * h / (2.0 * ph);         // Step-back distance along ray
        float d = sqrt(h * h - y * y);         // True nearest distance perpendicular to ray
        res = min(res, d / (w * max(0.0, t - y)));

        ph = h;                                // Save current h for next step
        t += h;

        if (res < 0.0001 || t > tmax) break;
    }

    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}
```

### Step 4: Negative Extension Version (Smoothest Penumbra)

**What**: Allow the shadow factor to drop into the negative range [-1, 0], then remap to [0, 1] with a custom quadratic smooth function, eliminating hard creases.

**Why**: The classic method produces a C0 continuous (non-smooth) crease at `clamp(0,1)`. By allowing `res` to enter the negative domain and remapping with the C1 continuous function `0.25*(1+res)²*(2-res)`, a completely smooth penumbra gradient is achieved.

```glsl
// Negative extension soft shadow
float calcSoftShadowSmooth(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        res = min(res, h / (w * t));
        t += clamp(h, MIN_STEP, MAX_STEP);
        if (res < -1.0 || t > tmax) break;    // Allow res to drop to -1
    }

    res = max(res, -1.0);                      // Clamp to [-1, 1]
    return 0.25 * (1.0 + res) * (1.0 + res) * (2.0 - res);  // Smooth remapping
}
```

### Step 5: Bounding Volume Optimization

**What**: Before starting the march, use simple geometric tests (plane clipping or AABB ray intersection) to narrow the shadow ray's effective range.

**Why**: If the shadow ray cannot possibly hit any object outside a bounded region (e.g., above the scene is empty), `tmax` can be shortened early or 1.0 returned immediately, saving many march iterations.

```glsl
// Method A: Plane clipping — clip ray to scene upper bound plane
float tp = (SCENE_Y_MAX - ro.y) / rd.y;
if (tp > 0.0) tmax = min(tmax, tp);

// Method B: AABB bounding box clipping
vec2 iBox(vec3 ro, vec3 rd, vec3 rad) {
    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF < 0.0) return vec2(-1.0);
    return vec2(tN, tF);
}

// Usage in shadow function
vec2 dis = iBox(ro, rd, BOUND_SIZE);
if (dis.y < 0.0) return 1.0;       // Ray completely misses bounding box
tmin = max(tmin, dis.x);
tmax = min(tmax, dis.y);
```

### Step 6: Shadow Color Rendering (Color Bleeding)

**What**: Instead of using a uniform scalar shadow value, apply different shadow attenuation curves to the RGB channels.

**Why**: In the real world, penumbra regions exhibit a warm color shift due to subsurface scattering and atmospheric effects — red light penetrates the most while blue light is blocked first. By applying per-channel power operations on the shadow value, this physical phenomenon can be approximated at low cost.

```glsl
// Method A: Classic color shadow
// sha is a [0,1] shadow factor
vec3 shadowColor = vec3(sha, sha * sha * 0.5 + 0.5 * sha, sha * sha);
// R = sha (linear), G = softer quadratic blend, B = sha² (darkest)

// Method B: Per-channel power operation (Woods style)
vec3 shadowColor = pow(vec3(sha), vec3(1.0, 1.2, 1.5));
// R = sha^1.0, G = sha^1.2, B = sha^1.5 → penumbra region shifts warm
```

### Step 7: Integration into the Lighting Model

**What**: Multiply the shadow value into the diffuse and specular lighting contributions.

**Why**: Shadows are essentially an estimate of "light source visibility" and should act as a multiplicative factor on all lighting terms that depend on that light source. Shadows are typically only computed when N·L > 0 (surface faces the light) to avoid wasting GPU cycles on backlit faces.

```glsl
// Lighting integration
vec3 sunDir = normalize(vec3(-0.5, 0.4, -0.6));
vec3 hal = normalize(sunDir - rd);

// Diffuse × shadow
float dif = clamp(dot(nor, sunDir), 0.0, 1.0);
if (dif > 0.0001)
    dif *= calcSoftShadow(pos + nor * 0.01, sunDir, 0.02, 8.0);

// Specular is also modulated by shadow
float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0);
spe *= dif;  // dif already includes shadow

// Final color compositing
vec3 col = vec3(0.0);
col += albedo * 2.0 * dif * vec3(1.0, 0.9, 0.8);       // Sun diffuse
col += 5.0 * spe * vec3(1.0, 0.9, 0.8);                 // Sun specular
col += albedo * 0.5 * clamp(0.5 + 0.5 * nor.y, 0.0, 1.0)
     * vec3(0.4, 0.6, 1.0);                              // Sky ambient (no shadow)
```

## Variant Details

### Variant 1: Analytical Sphere Shadow

**Difference from base version**: Does not use ray marching; instead performs an O(1) analytical closest-distance computation for spheres. Suitable for scenes containing only spheres or objects that can be approximated by spheres.

**Principle**: For a ray and a sphere, the closest distance from the ray to the sphere surface and the parameter `t` at that closest point along the ray can be computed analytically. These two values directly form the `d/t` ratio without iterative marching.

```glsl
// Sphere analytical soft shadow
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    return vec2(d, -b - sqrt(max(h, 0.0)));
}

float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph, float k) {
    vec2 r = sphDistances(ro, rd, sph);
    if (r.y > 0.0)
        return clamp(k * max(r.x, 0.0) / r.y, 0.0, 1.0);
    return 1.0;
}
// Multi-sphere aggregation: res = min(res, sphSoftShadow(ro, rd, sphere[i], k))
```

### Variant 2: Terrain Heightfield Shadow

**Difference from base version**: `h` is not obtained from a generic SDF `map()`, but computed as `p.y - terrain(p.xz)`, the height difference between the ray and the terrain. Step size adapts to camera distance.

**Use cases**: Procedural terrain rendering (using FBM noise-generated height maps). Terrain SDF is difficult to define precisely, but height difference serves as an approximate distance estimate.

```glsl
float terrainShadow(vec3 ro, vec3 rd, float dis) {
    float minStep = clamp(dis * 0.01, 0.5, 50.0);  // Distance-adaptive minimum step
    float res = 1.0;
    float t = 0.01;
    for (int i = 0; i < 80; i++) {                  // Terrain needs more iterations
        vec3 p = ro + t * rd;
        float h = p.y - terrainMap(p.xz);           // Height difference replaces SDF
        res = min(res, 16.0 * h / t);               // k=16
        t += max(minStep, h);
        if (res < 0.001 || p.y > MAX_TERRAIN_HEIGHT) break;
    }
    return clamp(res, 0.0, 1.0);
}
```

### Variant 3: Per-Material Hard/Soft Blend

**Difference from base version**: Uses a global variable or extra parameter to control each object's shadow hardness, blending via `mix(1.0, k*h/t, hardness)`. When `hardness=0`, it produces hard shadows; when `hardness=1`, fully soft shadows.

**Use cases**: Characters need sharp hard shadows (to enhance silhouette), while environment objects use softer shadows.

```glsl
float hsha = 1.0;  // Global variable, set per material in map()

float mapWithShadowHardness(vec3 p) {
    float d = sdPlane(p);
    hsha = 1.0;  // Ground: fully soft shadow
    float dChar = sdCharacter(p);
    if (dChar < d) { d = dChar; hsha = 0.0; }  // Character: hard shadow
    return d;
}

// Inside shadow loop:
res = min(res, mix(1.0, SHADOW_K * h / t, hsha));
```

### Variant 4: Multi-Layer Shadow Composition

**Difference from base version**: Different types of occlusion sources are computed separately, then composed multiplicatively. Typical scenario: ground shadow × vegetation shadow × cloud shadow.

**Design rationale**: Different shadow sources have very different characteristics — terrain shadows need high-precision marching, vegetation shadows can use probability/density field approximation, cloud shadows are large-scale planar projections. Layered computation allows using the optimal algorithm for each type.

```glsl
// Layered computation
float sha_terrain = terrainShadow(pos, sunDir, 0.02);
float sha_trees   = treesShadow(pos, sunDir);
float sha_clouds  = cloudShadow(pos, sunDir);  // Single planar projection + FBM sample

// Multiplicative composition
float sha = sha_terrain * sha_trees;
sha *= smoothstep(-0.3, -0.1, sha_clouds);  // Cloud shadow softened with smoothstep

// Apply to lighting
dif *= sha;
```

### Variant 5: Volumetric Light / God Ray Reusing Shadow Function

**Difference from base version**: Marches uniformly along the view ray direction, calling the shadow function toward the light at each step, accumulating light energy. Essentially a secondary sampling of the shadow function to produce volumetric scattering effects.

**Principle**: Volumetric light effects come from the scattering of light by airborne particles. At each point along the view ray, if that point is illuminated by the sun (high shadow value), it contributes some scattered light to the final color. Summing the lighting contributions from all sample points along the view ray produces the volumetric light effect.

```glsl
// Volumetric light (God Rays)
float godRays(vec3 ro, vec3 rd, float tmax, vec3 sunDir) {
    float v = 0.0;
    float dt = 0.15;                                 // View ray step size
    float t = dt * fract(texelFetch(iChannel0, ivec2(fragCoord) & 255, 0).x); // Jittering
    for (int i = 0; i < 32; i++) {                   // Number of samples
        if (t > tmax) break;
        vec3 p = ro + rd * t;
        float sha = calcSoftShadow(p, sunDir, 0.02, 8.0); // Reuse shadow function
        v += sha * exp(-0.2 * t);                    // Exponential distance falloff
        t += dt;
    }
    v /= 32.0;
    return v * v;                                    // Square to enhance contrast
}
// Usage: col += godRayIntensity * godRays(...) * vec3(1.0, 0.75, 0.4);
```

## Performance Optimization Details

### Bottleneck Analysis

The main cost of SDF soft shadows is the **shadow ray marching per pixel**, which involves multiple `map()` calls. For complex scenes, a single `map()` call may contain dozens of SDF combination operations.

### Optimization Techniques

#### 1. Bounding Volume Culling (Most Significant)

- Plane clipping: `tmax = min(tmax, (yMax - ro.y) / rd.y)` restricts the ray within the scene height range
- AABB clipping: Use `iBox()` to restrict `tmin`/`tmax` within the bounding box; return 1.0 immediately when the ray completely misses
- Can reduce 30-70% of wasted iterations

#### 2. Step Size Clamping

- `t += clamp(h, minStep, maxStep)` prevents extremely small steps (getting stuck near surface) and extremely large steps (skipping thin objects)
- Typical `minStep` values: 0.005~0.05, `maxStep`: 0.2~0.5
- Distance-adaptive: `minStep = clamp(dis * 0.01, 0.5, 50.0)` uses larger steps for distant shadows

#### 3. Early Exit

- Classic version: `res < 0.004` is already dark enough, no need to continue
- Negative extension: `res < -1.0` is saturated
- Height upper bound: `pos.y > yMax` means the ray has left the scene

#### 4. Reduced Shadow SDF Precision

- Use a simplified `map2()` that omits material computation and only returns distance
- For terrain scenes, use a low-resolution `terrainM()` (fewer FBM octaves) instead of full-precision `terrainH()`

#### 5. Conditional Computation

- `if (dif > 0.0001) dif *= shadow(...)` only computes shadow when facing the light
- Backlit faces are directly 0, no shadow needed

#### 6. Iteration Count Adjustment

- Simple scenes (a few primitives): 16~32 iterations suffice
- Complex FBM surfaces: Need 64~128 iterations
- Terrain scenes: With distance-adaptive step sizes, around 80 iterations

#### 7. Loop Unrolling Control

- `#define ZERO (min(iFrame,0))` prevents the compiler from unrolling loops at compile time, reducing instruction cache pressure

## Combination Suggestions with Full Code

### With Ambient Occlusion (AO)

Shadows handle direct light occlusion; AO handles indirect light occlusion. They complement each other:

```glsl
float sha = calcSoftShadow(pos, sunDir, 0.02, 8.0);
float occ = calcAO(pos, nor);
col += albedo * dif * sha * sunColor;       // Direct light × shadow
col += albedo * sky * occ * skyColor;       // Ambient light × AO
```

### With Subsurface Scattering (SSS)

Shadow values can modulate SSS intensity, simulating the translucent light-through effect at shadow edges:

```glsl
float sss = pow(clamp(dot(rd, sunDir), 0.0, 1.0), 4.0);
sss *= 0.25 + 0.75 * sha;  // SSS reduced but not eliminated in shadow
col += albedo * sss * vec3(1.0, 0.4, 0.2);
```

### With Fog / Atmospheric Scattering

Shadows should be "washed out" by fog at distance. The common approach is to complete shadow lighting before applying fog, which naturally blends:

```glsl
// First complete lighting with shadows
vec3 col = albedo * lighting_with_shadow;
// Then apply fog (distance fog naturally weakens shadow contrast)
col = mix(col, fogColor, 1.0 - exp(-0.001 * t * t));
```

### With Normal Maps / Bump Mapping

Shadows use the geometric normal (not the perturbed normal) to compute N·L for determining light-facing, but shadow rays are still cast from the actual surface point. Normal maps only affect lighting calculations, not shadows:

```glsl
vec3 geoNor = calcNormal(pos);              // Geometric normal
vec3 nor = perturbNormal(geoNor, ...);      // Perturbed normal
float dif = clamp(dot(nor, sunDir), 0.0, 1.0);  // Use perturbed normal for diffuse
if (dot(geoNor, sunDir) > 0.0)                    // Use geometric normal to decide shadow
    dif *= calcSoftShadow(pos + geoNor * 0.01, sunDir, 0.02, 8.0);
```

### With Reflections

The shadow function can be reused for the reflection direction, occluding specular highlights that should not be visible:

```glsl
vec3 ref = reflect(rd, nor);
float refSha = calcSoftShadow(pos + nor * 0.01, ref, 0.02, 8.0);
col += specular * envColor * refSha * occ;
```
