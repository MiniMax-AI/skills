# 3D Signed Distance Fields (3D SDF) — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL Basics**: uniform variables (`iTime`, `iResolution`, `iMouse`), `fragCoord` coordinate system
- **Vector Math**: built-in functions like `dot`, `cross`, `normalize`, `length`, `reflect`
- **Rays and Cameras**: understanding how to generate rays from screen pixels (ray origin + ray direction)
- **Implicit Surface Concept**: f(p) = 0 defines the surface, f(p) > 0 is outside, f(p) < 0 is inside

## Step-by-Step Detailed Explanation

### Step 1: SDF Primitive Library

**What**: Define basic geometric distance functions.

**Why**: All SDF scenes are composed of basic primitives. Each primitive is a pure function that takes a point in space and returns the shortest distance to that primitive's surface. The accuracy of these primitives directly determines the efficiency of sphere tracing — accurate SDFs allow larger step sizes.

**Code**:

```glsl
// Sphere: p=sample point, r=radius
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

// Box: p=sample point, b=half-size (xyz dimensions)
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

// Ellipsoid (approximate): p=sample point, r=three-axis radii
float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

// Torus: p=sample point, t.x=major radius, t.y=tube radius
float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// Capsule (two endpoints + radius): useful for skeleton/limb modeling
float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

// Cylinder (vertical): h.x=radius, h.y=half-height
float sdCylinder(vec3 p, vec2 h) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - h;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// Plane (y=0)
float sdPlane(vec3 p) {
    return p.y;
}
```

### Step 2: Boolean Operations and Smooth Blending

**What**: Define combination operations between primitives — union, subtraction, intersection, and their smooth variants.

**Why**: Union merges multiple primitives into one scene; subtraction carves one object out of another; intersection keeps the overlapping region. Smooth variants (`smin`/`smax`) use a control parameter `k` to produce smooth blend transitions — one of SDF's most powerful capabilities over traditional modeling, achieving organic forms without additional geometry.

**Code**:

```glsl
// === Hard Boolean Operations ===

// Union: take the nearer surface
float opUnion(float d1, float d2) { return min(d1, d2); }

// Subtraction: subtract d2 from d1
float opSubtraction(float d1, float d2) { return max(d1, -d2); }

// Intersection: keep the overlapping region
float opIntersection(float d1, float d2) { return max(d1, d2); }

// Union with material ID (vec2.x stores distance, vec2.y stores material ID)
vec2 opU(vec2 d1, vec2 d2) { return (d1.x < d2.x) ? d1 : d2; }

// === Smooth Boolean Operations ===

// Smooth union: k=blend radius (larger = smoother, typical values 0.1~0.5)
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}
// vec2 version of smin: for smooth blending of vec2(distance, materialID)
vec2 smin(vec2 a, vec2 b, float k) {
    float h = max(k - abs(a.x - b.x), 0.0);
    float d = min(a.x, b.x) - h * h * 0.25 / k;
    float m = (a.x < b.x) ? a.y : b.y;
    return vec2(d, m);
}

// Smooth subtraction / smooth max
float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}
```

### Step 3: Scene Definition (map Function)

**What**: Write the `map()` function that combines the above primitives and operations into a complete 3D scene.

**Why**: `map(p)` is the core of the SDF rendering pipeline — it returns the distance from any point p in space to the nearest scene surface (plus optional material information). Ray marching, normal computation, shadows, and AO all depend on this function. All geometric complexity of the scene is encapsulated here.

**Code**:

```glsl
// Returns vec2(distance, materialID)
vec2 map(vec3 p) {
    // Ground
    vec2 res = vec2(p.y, 0.0); // Material 0: ground

    // Sphere (displaced to y=0.5)
    float d1 = sdSphere(p - vec3(0.0, 0.5, 0.0), 0.4);
    res = opU(res, vec2(d1, 1.0)); // Material 1: sphere

    // Box
    float d2 = sdBox(p - vec3(1.5, 0.4, 0.0), vec3(0.3, 0.4, 0.3));
    res = opU(res, vec2(d2, 2.0)); // Material 2: box

    // Blend two spheres with smin for organic blob effect
    float d3 = sdSphere(p - vec3(-1.2, 0.5, 0.0), 0.3);
    float d4 = sdSphere(p - vec3(-1.5, 0.8, 0.2), 0.25);
    float dBlob = smin(d3, d4, 0.3);
    res = opU(res, vec2(dBlob, 3.0)); // Material 3: blob

    return res;
}
```

### Step 4: Raymarching

**What**: Implement the sphere tracing loop — cast a ray from the camera and step along the ray direction until hitting a surface or exceeding the maximum distance.

**Why**: Sphere tracing exploits the "safe distance" property of SDFs — the current SDF value tells us there is absolutely no surface within that radius, so we can safely advance that far. This is much more efficient than fixed-step volumetric ray marching, typically achieving precise results in 64-128 steps.

**Code**:

```glsl
#define MAX_STEPS 128      // Adjustable: step count, 64=fast/coarse, 256=precise/slow
#define MAX_DIST 40.0       // Adjustable: max trace distance
#define SURF_DIST 0.0001    // Adjustable: surface detection threshold

vec2 raycast(vec3 ro, vec3 rd) {
    vec2 res = vec2(-1.0, -1.0);
    float t = 0.01;

    for (int i = 0; i < MAX_STEPS && t < MAX_DIST; i++) {
        vec2 h = map(ro + rd * t);
        if (abs(h.x) < SURF_DIST * t) {
            res = vec2(t, h.y);
            break;
        }
        t += h.x; // Key: step distance = SDF value
    }
    return res; // .x=hit distance, .y=materialID; -1 means no hit
}
```

### Step 5: Normal Computation

**What**: Compute the surface normal at the hit point by taking the finite-difference gradient of the SDF.

**Why**: The gradient direction of the SDF is the surface normal direction. We use the tetrahedron trick (4 `map` calls) instead of central differences (6 calls), saving performance and avoiding compiler inline bloat from inlining `map()` multiple times.

**Code**:

```glsl
// Tetrahedron normal computation (recommended, only 4 map calls)
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(1.0, -1.0) * 0.5773 * 0.0005; // Adjustable: epsilon
    return normalize(
        e.xyy * map(pos + e.xyy).x +
        e.yyx * map(pos + e.yyx).x +
        e.yxy * map(pos + e.yxy).x +
        e.xxx * map(pos + e.xxx).x
    );
}

// Anti-compiler-inline version (suitable for complex map functions)
// Uses a loop to prevent compiler unrolling, uses a loop to prevent compiler unrolling
#define ZERO (min(iFrame, 0))
vec3 calcNormalLoop(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = ZERO; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.0005 * e).x;
    }
    return normalize(n);
}
```

### Step 6: Soft Shadows

**What**: Cast a secondary ray from the surface point toward the light source, and estimate shadow softness based on the minimum distance encountered along the way.

**Why**: Hard shadows only determine "occluded or not" (0/1), while SDF soft shadows use intermediate distance information to estimate "how close to being occluded." In the formula `k*h/t`, `k` controls shadow softness — larger `k` produces sharper shadows, smaller `k` produces softer shadows. This is one of SDF rendering's killer features.

**Code**:

```glsl
// k=shadow sharpness (2=very soft, 32=near hard), mint=start offset, tmax=max distance
float calcSoftshadow(vec3 ro, vec3 rd, float mint, float tmax, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 24; i++) { // Adjustable: shadow step count
        float h = map(ro + rd * t).x;
        float s = clamp(k * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.004 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res); // Smooth Hermite interpolation
}
```

### Step 7: Ambient Occlusion (AO)

**What**: Sample several points along the normal direction and compare actual SDF values with expected distances to estimate occlusion.

**Why**: SDFs naturally provide distance information for cheap AO approximation: if the SDF value at a sample point along the normal is much smaller than its distance to the surface, nearby occluding geometry exists. This method is more physically accurate than traditional SSAO and requires only 5 `map` calls.

**Code**:

```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) { // Adjustable: number of sample layers
        float h = 0.01 + 0.12 * float(i) / 4.0; // Adjustable: sample spacing
        float d = map(pos + h * nor).x;
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```

### Step 8: Camera and Rendering Pipeline

**What**: Build a look-at camera matrix, generate screen rays, and chain together the entire rendering pipeline.

**Why**: Mapping screen pixels to 3D rays is the starting point of raymarching. The look-at matrix builds an orthonormal basis from the camera position, target point, and up direction, making camera control intuitive. The final pipeline chains all steps: ray generation, ray marching, normals, lighting/shadows/AO, and post-processing.

**Code**:

```glsl
// Camera look-at matrix
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

// Render: input ray, output color
vec3 render(vec3 ro, vec3 rd) {
    // Background color (sky gradient)
    vec3 col = vec3(0.7, 0.7, 0.9) - max(rd.y, 0.0) * 0.3;

    // Raycast intersection
    vec2 res = raycast(ro, rd);
    float t = res.x;
    float m = res.y; // Material ID

    if (m > -0.5) {
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos);

        // Material color (varies by ID)
        vec3 mate = 0.2 + 0.2 * sin(m * 2.0 + vec3(0.0, 1.0, 2.0));

        // Lighting
        vec3 lig = normalize(vec3(-0.5, 0.4, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        dif *= calcSoftshadow(pos, lig, 0.02, 2.5, 8.0);
        float amb = 0.5 + 0.5 * nor.y;
        float occ = calcAO(pos, nor);

        col = mate * (dif * vec3(1.3, 1.0, 0.7) + amb * occ * vec3(0.4, 0.6, 1.0) * 0.6);

        // Fog (exponential decay)
        col = mix(col, vec3(0.7, 0.7, 0.9), 1.0 - exp(-0.0001 * t * t * t));
    }

    return clamp(col, 0.0, 1.0);
}
```

## Variant Detailed Descriptions

### Variant 1: Dynamic Organic Body (Smooth Blob Animation)

**Difference from the basic version**: Replaces static primitives with multiple animated spheres blended via `smin`, producing lava/fluid-like organic effects. A common technique for organic fluid-like effects.

**Key modified code**:

```glsl
// Replace scene definition in map()
vec2 map(vec3 p) {
    float d = 2.0;
    for (int i = 0; i < 16; i++) { // Adjustable: number of spheres
        float fi = float(i);
        float t = iTime * (fract(fi * 412.531 + 0.513) - 0.5) * 2.0;
        d = smin(
            sdSphere(p + sin(t + fi * vec3(52.5126, 64.627, 632.25)) * vec3(2.0, 2.0, 0.8),
                     mix(0.5, 1.0, fract(fi * 412.531 + 0.5124))),
            d,
            0.4 // Adjustable: blend radius
        );
    }
    return vec2(d, 1.0);
}
```

### Variant 2: Infinite Repeating Corridor (Domain Repetition)

**Difference from the basic version**: Uses `mod()` to repeat spatial coordinates infinitely. A common domain repetition technique. Can layer `hash()` to introduce random variation per repeating cell.

**Key modified code**:

```glsl
// Linear domain repetition
float repeat(float v, float c) {
    return mod(v, c) - c * 0.5;
}

// Angular domain repetition (repeat count times in polar coordinate direction)
float amod(inout vec2 p, float count) {
    float an = 6.283185 / count;
    float a = atan(p.y, p.x) + an * 0.5;
    float c = floor(a / an);
    a = mod(a, an) - an * 0.5;
    p = vec2(cos(a), sin(a)) * length(p);
    return c; // Returns sector index
}

vec2 map(vec3 p) {
    // Repeat every 4 units along the z axis
    p.z = repeat(p.z, 4.0);
    // Add bending offset along x axis
    p.x += 2.0 * sin(p.z * 0.1);

    float d = -sdBox(p, vec3(2.0, 2.0, 20.0)); // Invert = corridor interior
    d = max(d, -sdBox(p, vec3(1.8, 1.8, 1.9))); // Subtract interior space
    d = min(d, sdCylinder(p - vec3(1.5, -2.0, 0.0), vec2(0.1, 2.0))); // Add pillars
    return vec2(d, 1.0);
}
```

### Variant 3: Character/Creature Modeling (Organic Character Modeling)

**Difference from the basic version**: Uses `sdEllipsoid` + `sdCapsule` (sdStick) to compose body parts, `smin` to connect with smooth transitions, and `smax` to carve indentations (mouth). Combined with procedural animation to drive joints. A standard approach for character SDF modeling.

**Key modified code**:

```glsl
// Stick primitive (different radii at each end, suitable for limbs)
vec2 sdStick(vec3 p, vec3 a, vec3 b, float r1, float r2) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return vec2(length(pa - ba * h) - mix(r1, r2, h * h * (3.0 - 2.0 * h)), h);
}

vec2 map(vec3 pos) {
    // Body (ellipsoid)
    float d = sdEllipsoid(pos, vec3(0.25, 0.3, 0.25));

    // Head (sphere, connected with smin)
    float dHead = sdEllipsoid(pos - vec3(0.0, 0.35, 0.02), vec3(0.12, 0.15, 0.13));
    d = smin(d, dHead, 0.1);

    // Arms (sdStick)
    vec2 arm = sdStick(abs(pos.x) > 0.0 ? vec3(abs(pos.x), pos.yz) : pos,
                       vec3(0.18, 0.2, -0.05),
                       vec3(0.35, -0.1, -0.15), 0.03, 0.05);
    d = smin(d, arm.x, 0.04);

    // Mouth (carved with smax)
    float dMouth = sdEllipsoid(pos - vec3(0.0, 0.3, 0.15), vec3(0.08, 0.03, 0.1));
    d = smax(d, -dMouth, 0.03);

    return vec2(d, 1.0);
}
```

### Variant 4: Symmetry Exploitation

**Difference from the basic version**: Leverages geometric symmetry (mirror/rotational invariance) to reduce N repeated elements' SDF evaluations to N/k. For example, octahedral symmetry can reduce 18 elements to 4 evaluations. The key is mapping the input point to the symmetry's fundamental domain.

**Key modified code**:

```glsl
// Fold a point into the octahedral fundamental domain
vec2 rot45(vec2 v) {
    return vec2(v.x - v.y, v.y + v.x) * 0.707107;
}

vec2 map(vec3 p) {
    float d = sdSphere(p, 0.12); // Center sphere

    // Exploit symmetry: original 18 gears reduced to 4 evaluations
    vec3 qx = vec3(rot45(p.zy), p.x);
    if (abs(qx.x) > abs(qx.y)) qx = qx.zxy;

    vec3 qy = vec3(rot45(p.xz), p.y);
    if (abs(qy.x) > abs(qy.y)) qy = qy.zxy;

    vec3 qz = vec3(rot45(p.yx), p.z);
    if (abs(qz.x) > abs(qz.y)) qz = qz.zxy;

    vec3 qa = abs(p);
    qa = (qa.x > qa.y && qa.x > qa.z) ? p.zxy :
         (qa.z > qa.y) ? p.yzx : p.xyz;

    // Only 4 gear() evaluations needed instead of 18
    d = min(d, gear(qa, 0.0));
    d = min(d, gear(qx, 1.0));
    d = min(d, gear(qy, 1.0));
    d = min(d, gear(qz, 1.0));

    return vec2(d, 1.0);
}
```

### Variant 5: PBR Material Rendering Pipeline

**Difference from the basic version**: Replaces simplified Blinn-Phong with GGX microfacet BRDF, combined with a material ID system to assign different roughness/metalness to each primitive. A standard approach for PBR raymarching.

**Key modified code**:

```glsl
// GGX/Trowbridge-Reitz NDF
float D_GGX(float NoH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159 * d * d);
}

// Schlick Fresnel approximation
vec3 F_Schlick(float VoH, vec3 f0) {
    return f0 + (1.0 - f0) * pow(1.0 - VoH, 5.0);
}

// Replace lighting section in render()
vec3 pbrLighting(vec3 pos, vec3 nor, vec3 rd, vec3 albedo, float roughness, float metallic) {
    vec3 lig = normalize(vec3(-0.5, 0.4, -0.6));
    vec3 hal = normalize(lig - rd);
    vec3 f0 = mix(vec3(0.04), albedo, metallic);

    float NoL = max(dot(nor, lig), 0.0);
    float NoH = max(dot(nor, hal), 0.0);
    float VoH = max(dot(-rd, hal), 0.0);

    float D = D_GGX(NoH, roughness);
    vec3 F = F_Schlick(VoH, f0);

    vec3 spec = D * F * 0.25; // Simplified specular term
    vec3 diff = albedo * (1.0 - metallic) / 3.14159;

    float shadow = calcSoftshadow(pos, lig, 0.02, 2.5);
    return (diff + spec) * NoL * shadow * vec3(1.3, 1.0, 0.7) * 3.0;
}
```

## Performance Optimization in Detail

### 1. Bounding Volume Acceleration

Use an overall AABB or bounding sphere to constrain the search range. Perform analytical ray intersection first to narrow the `tmin`/`tmax` range, avoiding wasted steps in empty regions. A common optimization in advanced raymarching shaders.

```glsl
// Ray-AABB intersection (call before raycast)
vec2 iBox(vec3 ro, vec3 rd, vec3 rad) {
    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    return vec2(max(max(t1.x, t1.y), t1.z),
                min(min(t2.x, t2.y), t2.z));
}
```

### 2. Per-Object Bounding

In `map()`, first check with a cheap sdBox whether the current point is near a primitive. Only compute the precise SDF when close. A standard per-object culling technique.

```glsl
// Inside map():
if (sdBox(pos - objectCenter, boundingSize) < res.x) {
    // Only compute precise SDF when bounding box distance is closer than current nearest
    res = opU(res, vec2(sdComplexShape(pos), matID));
}
```

### 3. Adaptive Step Size

Allow larger precision tolerance at distance, stricter up close. Based on the `abs(h.x) < (0.0001 * t)` check found in nearly all advanced shaders.

### 4. Preventing Compiler Inlining

Complex `map()` functions get inlined 4 times inside `calcNormal`, causing compilation time to explode. Use a loop + `ZERO` macro to prevent inlining. A well-known technique to prevent excessive compiler inlining.

```glsl
#define ZERO (min(iFrame, 0)) // Compiler cannot prove this is 0 at compile time, so it won't unroll the loop
```

### 5. Symmetry Exploitation

If the scene has rotational/mirror symmetry, fold the point into the fundamental domain and evaluate only once. Achieves significant speedup (e.g., 18-to-4 reduction) or infinite repetition.

## Combination Suggestions in Detail

### 1. SDF + Noise Displacement

Add noise on top of the `map()` return value to add organic details to smooth surfaces (terrain, skin textures).

```glsl
float d = sdSphere(p, 1.0);
d += 0.05 * (sin(p.x * 10.0) * sin(p.y * 10.0) * sin(p.z * 10.0)); // Simple displacement
// Or use fbm noise: d += 0.1 * fbm(p * 4.0);
```

**Note**: Noise displacement breaks the SDF's Lipschitz condition (|grad f| <= 1). You need to multiply the step size by a safety factor (e.g., 0.5~0.7) to avoid penetration.

### 2. SDF + Bump Mapping

Instead of modifying the SDF itself, add detail perturbation only in the normal computation. Better performance than noise displacement since it doesn't affect ray marching. A common technique in SDF rendering.

```glsl
vec3 calcNormalBumped(vec3 pos) {
    vec3 n = calcNormal(pos);
    // Add high-frequency detail to the normal
    n += 0.1 * vec3(fbm(pos.yz * 20.0) - 0.5, 0.0, fbm(pos.xy * 20.0) - 0.5);
    return normalize(n);
}
```

### 3. SDF + Domain Warping

Warp spatial coordinates before entering `map()` to achieve bending, twisting, polar coordinate transforms, and other effects. A common spatial warping technique.

```glsl
// Cartesian to polar ring space: straight corridor becomes a ring structure
vec2 displaceLoop(vec2 p, float r) {
    return vec2(length(p) - r, atan(p.y, p.x));
}
```

### 4. SDF + Procedural Animation

Bone/joint angles vary with time, driving SDF primitive positions. `smin` ensures smooth transitions at joints. Common techniques for procedural character animation (squash & stretch, bone chain IK).

```glsl
// Squash and stretch deformation
float p = 4.0 * t1 * (1.0 - t1); // Parabolic bounce
float sy = 0.5 + 0.5 * p;        // Stretch in y direction
float sz = 1.0 / sy;              // Compress in z direction (preserve volume)
vec3 q = pos - center;
float d = sdEllipsoid(q, vec3(0.25, 0.25 * sy, 0.25 * sz));
```

### 5. SDF + Motion Blur

Average multiple frames sampled across the time dimension. A standard temporal supersampling technique.

```glsl
// Randomly offset time in mainImage
float time = iTime;
#if AA > 1
    time += 0.5 * float(m * AA + n) / float(AA * AA) / 24.0; // Intra-frame time jitter
#endif
```

## Extended SDF Primitives Reference

### Rounded Box — `sdRoundBox(vec3 p, vec3 b, float r)`

- `p`: sample point
- `b`: half-size dimensions (before rounding)
- `r`: rounding radius — edges and corners are rounded by this amount

### Box Frame — `sdBoxFrame(vec3 p, vec3 b, float e)`

- `p`: sample point
- `b`: outer half-size dimensions
- `e`: edge thickness — the wireframe thickness of the box edges

### Cone — `sdCone(vec3 p, vec2 c, float h)`

- `p`: sample point
- `c`: vec2(sin, cos) of the cone's opening angle
- `h`: height of the cone

### Capped Cone — `sdCappedCone(vec3 p, float h, float r1, float r2)`

- `p`: sample point
- `h`: half-height
- `r1`: bottom radius
- `r2`: top radius

### Round Cone — `sdRoundCone(vec3 p, float r1, float r2, float h)`

- `p`: sample point
- `r1`: bottom sphere radius
- `r2`: top sphere radius
- `h`: height between sphere centers

### Solid Angle — `sdSolidAngle(vec3 p, vec2 c, float ra)`

- `p`: sample point
- `c`: vec2(sin, cos) of the solid angle
- `ra`: radius

### Octahedron — `sdOctahedron(vec3 p, float s)`

- `p`: sample point
- `s`: size (distance from center to vertex)

### Pyramid — `sdPyramid(vec3 p, float h)`

- `p`: sample point
- `h`: height of the pyramid (base is a unit square centered at origin)

### Hex Prism — `sdHexPrism(vec3 p, vec2 h)`

- `p`: sample point
- `h.x`: hexagonal radius (circumradius)
- `h.y`: half-height along z axis

### Cut Sphere — `sdCutSphere(vec3 p, float r, float h)`

- `p`: sample point
- `r`: sphere radius
- `h`: cut plane height (cuts sphere at y=h)

### Capped Torus — `sdCappedTorus(vec3 p, vec2 sc, float ra, float rb)`

- `p`: sample point
- `sc`: vec2(sin, cos) of the cap angle
- `ra`: major radius
- `rb`: tube radius

### Link — `sdLink(vec3 p, float le, float r1, float r2)`

- `p`: sample point
- `le`: half-length of the elongation
- `r1`: major radius of the torus cross-section
- `r2`: tube radius

### Plane (arbitrary) — `sdPlane(vec3 p, vec3 n, float h)`

- `p`: sample point
- `n`: plane normal (must be normalized)
- `h`: offset from origin along the normal

### Rhombus — `sdRhombus(vec3 p, float la, float lb, float h, float ra)`

- `p`: sample point
- `la`, `lb`: half-diagonals of the rhombus in XZ plane
- `h`: half-height (extrusion in Y)
- `ra`: rounding radius

### Triangle (unsigned) — `udTriangle(vec3 p, vec3 a, vec3 b, vec3 c)`

- `p`: sample point
- `a`, `b`, `c`: triangle vertex positions
- Returns unsigned (non-negative) distance

## Deformation Operators Reference

### Round — `opRound(float d, float r)`

Softens edges of any SDF by subtracting a radius. Apply to the result of any SDF.

```glsl
// Round a box with radius 0.1
float d = opRound(sdBox(p, vec3(1.0)), 0.1);
```

### Onion — `opOnion(float d, float t)`

Hollows out any SDF into a shell of thickness `t`. Can be stacked for concentric shells.

```glsl
// Hollow sphere shell, 0.1 thick
float d = opOnion(sdSphere(p, 1.0), 0.1);
// Double shell
float d = opOnion(opOnion(sdSphere(p, 1.0), 0.1), 0.05);
```

### Elongate — `opElongate(vec3 p, vec3 h, vec3 center, vec3 size)`

Stretches a shape along one or more axes by `h`. The shape is stretched without distortion — it inserts a linear segment.

```glsl
// Elongate along Y to stretch a box
vec3 q = abs(p) - vec3(0.0, 0.5, 0.0);
float d = sdBox(max(q, 0.0), vec3(0.3)) + min(max(q.x, max(q.y, q.z)), 0.0);
```

### Twist — `opTwist(vec3 p, float k)`

Rotates the XZ cross-section around the Y axis proportionally to height. Returns transformed coordinates to pass into any SDF.

```glsl
// Twisted box: k controls twist rate (radians per unit height)
vec3 q = opTwist(p, 3.0);
float d = sdBox(q, vec3(0.5));
```

### Cheap Bend — `opCheapBend(vec3 p, float k)`

Bends geometry along the X axis. Returns transformed coordinates.

```glsl
// Bent box
vec3 q = opCheapBend(p, 2.0);
float d = sdBox(q, vec3(0.5, 0.3, 0.5));
```

### Displacement — `opDisplace(float d, vec3 p)`

Adds procedural sinusoidal surface detail. Breaks Lipschitz bound, so reduce ray march step size by 0.5-0.7.

```glsl
float d = sdSphere(p, 1.0);
d = opDisplace(d, p); // Adds bumpy surface detail
```

## 2D-to-3D Constructors Reference

### Revolution — `opRevolution(vec3 p, float sdf2d_result, float o)`

Creates a 3D solid of revolution by rotating a 2D SDF around the Y axis. Compute the 2D SDF at `vec2(length(p.xz) - o, p.y)` and pass the result.

```glsl
// Create a torus-like shape by revolving a 2D circle
vec2 q = vec2(length(p.xz) - 1.0, p.y); // offset=1.0
float d2d = length(q) - 0.3;             // 2D circle radius=0.3
float d3d = opRevolution(p, d2d, 1.0);   // revolve around Y
```

### Extrusion — `opExtrusion(vec3 p, float d2d, float h)`

Extends any 2D SDF along the Z axis with finite height `h`. The 2D SDF is evaluated in the XY plane and capped at `+/- h` along Z.

```glsl
// Extrude a 2D shape 0.2 units in both directions
float d2d = sdCircle2D(p.xy, 0.5);      // any 2D SDF
float d3d = opExtrusion(p, d2d, 0.2);    // finite extrusion
```

## Symmetry Operators Reference

### Mirror X — `opSymX(vec3 p)`

Mirrors across the X axis using `abs(p.x)`. Model only one half and get bilateral symmetry for free. Place at the start of `map()`.

```glsl
vec2 map(vec3 p) {
    p = opSymX(p); // Mirror: only model x >= 0 side
    float d = sdSphere(p - vec3(1.0, 0.5, 0.0), 0.3);
    // Automatically appears at both x=+1 and x=-1
    return vec2(d, 1.0);
}
```

### Mirror XZ — `opSymXZ(vec3 p)`

Four-fold symmetry across both X and Z axes. Model one quadrant, get four copies.

```glsl
vec2 map(vec3 p) {
    p = opSymXZ(p); // Four-fold symmetry
    float d = sdBox(p - vec3(2.0, 0.5, 2.0), vec3(0.3));
    // Appears in all four quadrants
    return vec2(d, 1.0);
}
```

### Arbitrary Mirror — `opMirror(vec3 p, vec3 dir)`

Mirrors across an arbitrary plane defined by its normal `dir` (must be normalized). Reflects any point on the negative side to the positive side.

```glsl
// Mirror across a 45-degree plane
vec3 q = opMirror(p, normalize(vec3(1.0, 0.0, 1.0)));
float d = sdSphere(q - vec3(1.0, 0.5, 0.0), 0.3);
```
