# Analytic Ray Tracing - Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisite knowledge, step-by-step tutorial, mathematical derivations, and advanced usage.

## Prerequisites

- **Vector math fundamentals**: Dot product `dot()`, cross product `cross()`, vector normalization `normalize()`
- **Quadratic equation solving**: Discriminant `b²-4ac`, meaning of the two roots
- **Ray parametric representation**: `P(t) = ro + t * rd`, where `ro` is the ray origin, `rd` is the direction, `t` is the distance
- **GLSL fundamentals**: `struct`, `inout` parameters, `vec3`/`vec4` operations
- **ShaderToy framework**: `mainImage()` function, `iResolution`, `iTime`, and other uniforms

## Use Cases (Complete List)

- When rendering scenes composed of geometric primitives (spheres, planes, boxes, cylinders, tori, etc.)
- When precise surface intersection points, normals, and distances are needed (no iterative approximation required)
- When efficient ray intersection is needed in real-time rendering (several times faster than ray marching)
- Building the underlying geometric engine for ray tracers and path tracers
- Creating visualization effects for hard-surface modeling (jewelry, mechanical parts, chess scenes, etc.)
- Scenes requiring precise shadows, reflections, and refractions (analytic solutions have no sampling error)

## Core Principles in Detail

The core idea of analytic ray tracing is: substitute the ray equation `P(t) = O + tD` into the implicit equation of the geometric body, obtaining an algebraic equation in `t`, then solve it using closed-form formulas.

### Unified Framework

All analytic intersection functions follow the same pattern:

1. **Set up equation**: Substitute the ray parametric form into the geometry's implicit equation
2. **Simplify and solve**: Use algebraic identities to reduce to a standard form (quadratic/quartic equation)
3. **Discriminant check**: Discriminant < 0 indicates no intersection
4. **Select nearest intersection**: Take the smallest positive root satisfying distance constraints
5. **Compute normal**: Evaluate the gradient of the implicit equation at the intersection point

### Key Mathematical Formulas

**Sphere** `|P-C|² = r²` → quadratic equation: `t² + 2bt + c = 0`

**Plane** `N·P + d = 0` → linear equation: `t = -(N·O + d) / (N·D)`

**Box** Intersection of three pairs of parallel planes → Slab Method: `tN = max(t1.x, t1.y, t1.z), tF = min(t2.x, t2.y, t2.z)`

**Ellipsoid** `|P/R|² = 1` → sphere intersection in scaled space

**Torus** `(|P_xy| - R)² + P_z² = r²` → quartic equation, solved via resolvent cubic

## Implementation Steps in Detail

### Step 1: Ray Generation

**What**: Generate a ray from the camera position through each pixel.

**Why**: This is the starting point of ray tracing. Each pixel corresponds to a ray from the camera through the near plane. The standard approach is to construct a camera coordinate system (right, up, forward) and map normalized screen coordinates to world-space directions.

```glsl
// Construct camera ray
vec3 generateRay(vec2 fragCoord, vec2 resolution, vec3 ro, vec3 ta) {
    vec2 p = (2.0 * fragCoord - resolution) / resolution.y;

    // Build camera coordinate system
    vec3 cw = normalize(ta - ro);               // forward
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0))); // right
    vec3 cv = cross(cu, cw);                    // up

    float fov = 1.5; // Adjustable: field of view control (larger = narrower angle)
    vec3 rd = normalize(p.x * cu + p.y * cv + fov * cw);
    return rd;
}
```

### Step 2: Ray-Sphere Intersection

**What**: Compute the exact intersection of a ray with a sphere. This is the most fundamental and commonly used intersection function.

**Why**: Substituting the ray `P = O + tD` into the sphere equation `|P - C|² = r²` and expanding yields a quadratic equation in `t`. The discriminant `h = b² - c` determines the number of intersections (0, 1, or 2); the smallest positive root is the nearest intersection.

This is a ubiquitous technique, with two common variants:

**Code (optimized version, assumes sphere centered at origin)**:
```glsl
// Ray-sphere intersection (optimized version for sphere at origin)
// ro: ray origin (sphere center offset already subtracted)
// rd: ray direction (must be normalized)
// r:  sphere radius
// Returns: intersection distance, MAX_DIST if no intersection
float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;       // Discriminant (optimized: 4a factor omitted)
    if (h < 0.0) return MAX_DIST; // No intersection

    h = sqrt(h);
    float d1 = -b - h;        // Near intersection
    float d2 = -b + h;        // Far intersection

    // Select the nearest intersection within valid range
    if (d1 >= distBound.x && d1 <= distBound.y) {
        normal = normalize(ro + rd * d1);
        return d1;
    } else if (d2 >= distBound.x && d2 <= distBound.y) {
        normal = normalize(ro + rd * d2);
        return d2;
    }
    return MAX_DIST;
}
```

**Code (general version, arbitrary sphere center)**:
```glsl
// Ray-sphere intersection (general version, supports arbitrary sphere center)
// sph: vec4(center.xyz, radius)
float sphIntersect(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    return -b - sqrt(h);  // Returns only the near intersection
}
```

### Step 3: Ray-Plane Intersection

**What**: Compute the intersection of a ray with an infinite plane.

**Why**: The plane equation `N·P + d = 0` substituted with the ray yields a linear equation, solved directly by division. This is the simplest intersection primitive, commonly used for floors, walls, Cornell Boxes, etc. Note: when `N·D ≈ 0`, the ray is parallel to the plane.

```glsl
// Ray-plane intersection
// planeNormal: plane normal (must be normalized)
// planeDist:   distance from plane to origin (N·P + planeDist = 0)
float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    // Only intersects when ray hits the front face of the plane
    if (denom > 0.0) return MAX_DIST;

    float d = -(dot(ro, planeNormal) + planeDist) / denom;

    if (d < distBound.x || d > distBound.y) return MAX_DIST;

    normal = planeNormal;
    return d;
}

// Quick version: horizontal ground plane (y-axis aligned)
float iGroundPlane(vec3 ro, vec3 rd, float height) {
    return -(ro.y - height) / rd.y;
}
```

### Step 4: Ray-Box Intersection (Slab Method)

**What**: Compute the intersection of a ray with an axis-aligned bounding box (AABB).

**Why**: The Slab Method treats the box as the intersection of three pairs of parallel planes. It computes the ray's intersection with each pair of planes `(tmin, tmax)`, then takes the maximum of all `tmin` values and the minimum of all `tmax` values. If `tN > tF` or `tF < 0`, there is no intersection. The normal is determined by which face was hit first.

```glsl
// Ray-box intersection (Slab Method, optimized version)
// boxSize: box half-size vec3(halfW, halfH, halfD)
float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8); // Avoid division by zero
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;

    vec3 t1 = -n - k;  // Near plane intersections
    vec3 t2 = -n + k;  // Far plane intersections

    float tN = max(max(t1.x, t1.y), t1.z); // Entry distance into the box
    float tF = min(min(t2.x, t2.y), t2.z); // Exit distance from the box

    if (tN > tF || tF <= 0.0) return MAX_DIST; // No intersection

    if (tN >= distBound.x && tN <= distBound.y) {
        // Normal: determine which face was hit
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tN;
    } else if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tF;
    }
    return MAX_DIST;
}
```

### Step 5: Ray-Ellipsoid Intersection

**What**: Compute the intersection of a ray with an ellipsoid.

**Why**: An ellipsoid can be viewed as a sphere scaled differently along each axis. By dividing both the ray origin and direction by the ellipsoid radii `R`, a sphere intersection is performed in scaled space, then the normal is transformed back to the original space. This "space transformation" technique is one of the core ideas of analytic intersection.

```glsl
// Ray-ellipsoid intersection
// rad: vec3(rx, ry, rz) three-axis radii
float iEllipsoid(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 rad) {
    // Transform to unit sphere space
    vec3 ocn = ro / rad;
    vec3 rdn = rd / rad;

    float a = dot(rdn, rdn);
    float b = dot(ocn, rdn);
    float c = dot(ocn, ocn);
    float h = b * b - a * (c - 1.0);

    if (h < 0.0) return MAX_DIST;

    float d = (-b - sqrt(h)) / a;

    if (d < distBound.x || d > distBound.y) return MAX_DIST;

    // Normal in original space: gradient of implicit equation |P/R|²=1 → P/(R²)
    normal = normalize((ro + d * rd) / rad);
    return d;
}
```

### Step 6: Ray-Cylinder Intersection

**What**: Compute the intersection of a ray with a finite cylinder (with end caps).

**Why**: Cylinder intersection has two parts: (1) project the problem onto a plane perpendicular to the axis, solving a quadratic equation for side surface intersections; (2) check if the intersection is within the finite length, and if not, test the end cap planes.

```glsl
// Ray-capped cylinder intersection
// pa, pb: two endpoints of the cylinder axis
// ra: cylinder radius
float iCylinder(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
                vec3 pa, vec3 pb, float ra) {
    vec3 ca = pb - pa;          // Cylinder axis vector
    vec3 oc = ro - pa;

    float caca = dot(ca, ca);
    float card = dot(ca, rd);
    float caoc = dot(ca, oc);

    // Project onto plane perpendicular to axis, build quadratic equation
    float a = caca - card * card;
    float b = caca * dot(oc, rd) - caoc * card;
    float c = caca * dot(oc, oc) - caoc * caoc - ra * ra * caca;
    float h = b * b - a * c;

    if (h < 0.0) return MAX_DIST;

    h = sqrt(h);
    float d = (-b - h) / a;

    // Check if side intersection is within finite length
    float y = caoc + d * card;
    if (y > 0.0 && y < caca && d >= distBound.x && d <= distBound.y) {
        normal = (oc + d * rd - ca * y / caca) / ra;
        return d;
    }

    // Test end caps
    d = ((y < 0.0 ? 0.0 : caca) - caoc) / card;
    if (abs(b + a * d) < h && d >= distBound.x && d <= distBound.y) {
        normal = normalize(ca * sign(y) / caca);
        return d;
    }

    return MAX_DIST;
}
```

### Step 7: Scene Intersection & Shading

**What**: Traverse all objects in the scene, find the nearest intersection, and compute lighting.

**Why**: Scene traversal in analytic ray tracing is linear — each ray tests all objects sequentially. Through the unified intersection API (`distBound` parameter), each time a nearer intersection is found, the search range is automatically shortened, achieving implicit culling.

```glsl
#define MAX_DIST 1e10

// Unified scene intersection function
// Returns vec3(current nearest distance, final intersection distance, material ID)
vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0); // (distBound.x, distBound.y, matID)
    vec3 tmpNormal;

    // Ground plane
    float t = iPlane(ro, rd, d.xy, normal, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; }

    // Sphere
    t = iSphere(ro - vec3(0, 0.5, 0), rd, d.xy, tmpNormal, 0.5);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmpNormal; }

    // Box
    t = iBox(ro - vec3(2, 0.5, 0), rd, d.xy, tmpNormal, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmpNormal; }

    return d;
}

// Basic shading (Lambertian + shadow)
vec3 shade(vec3 pos, vec3 normal, vec3 rd, vec3 albedo) {
    vec3 lightDir = normalize(vec3(-1.0, 0.75, 1.0));

    // Diffuse
    float diff = max(dot(normal, lightDir), 0.0);

    // Ambient
    float amb = 0.5 + 0.5 * normal.y;

    return albedo * (amb * 0.2 + diff * 0.8);
}
```

### Step 8: Reflection & Refraction

**What**: Implement iterative reflection/refraction for non-recursive ray bounces.

**Why**: GLSL does not support recursion, so loops are used to simulate multiple bounces. At each bounce, the intersection point plus offset (epsilon) serves as the new ray origin, with the reflected/refracted direction as the new direction. The Fresnel term determines the energy distribution between reflection and refraction.

```glsl
#define MAX_BOUNCES 4       // Adjustable: number of reflection bounces (more = more realistic but slower)
#define EPSILON 0.001        // Adjustable: self-intersection offset

// Schlick Fresnel approximation
float schlickFresnel(float cosTheta, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 radiance(vec3 ro, vec3 rd) {
    vec3 color = vec3(0.0);
    vec3 mask = vec3(1.0);
    vec3 normal;

    for (int i = 0; i < MAX_BOUNCES; i++) {
        vec3 res = worldHit(ro, rd, vec2(EPSILON, MAX_DIST), normal);

        if (res.z < 0.5) {
            // No object hit → sky color
            color += mask * vec3(0.6, 0.8, 1.0);
            break;
        }

        vec3 hitPos = ro + rd * res.y;
        vec3 albedo = getAlbedo(res.z);

        // Fresnel reflection coefficient
        float F = schlickFresnel(max(0.0, dot(normal, -rd)), 0.04);

        // Add diffuse contribution
        color += mask * (1.0 - F) * shade(hitPos, normal, rd, albedo);

        // Update mask and ray (reflection)
        mask *= F * albedo;
        rd = reflect(rd, normal);
        ro = hitPos + EPSILON * rd;
    }

    return color;
}
```

## Complete Code Template

For a complete runnable ShaderToy template, see the "Complete Code Template" section in [SKILL.md](SKILL.md), which includes sphere, plane, and box primitives with support for reflections and Blinn-Phong shading.

The following table describes the adjustable parameters in the template:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_DIST` | `1e10` | Maximum trace distance |
| `EPSILON` | `0.001` | Self-intersection offset |
| `MAX_BOUNCES` | `4` | Maximum number of reflections |
| `NUM_SPHERES` | `3` | Number of spheres |
| `FOV` | `1.5` | Field of view (larger = narrower angle) |
| `GAMMA` | `2.2` | Gamma correction value |
| `SHADOW_ENABLED` | `true` | Whether shadows are enabled |

## Variant Details

### Variant 1: Path Tracing

Difference from base version: Replaces deterministic reflection with random hemisphere sampling to achieve global illumination. Requires multi-frame accumulation and random number generation.

Key code:
```glsl
// Cosine-weighted random hemisphere direction
vec3 cosWeightedRandomHemisphereDirection(vec3 n, inout float seed) {
    vec2 r = hash2(seed);
    vec3 uu = normalize(cross(n, abs(n.y) > 0.5 ? vec3(1,0,0) : vec3(0,1,0)));
    vec3 vv = cross(uu, n);
    float ra = sqrt(r.y);
    float rx = ra * cos(6.2831 * r.x);
    float ry = ra * sin(6.2831 * r.x);
    float rz = sqrt(1.0 - r.y);
    return normalize(rx * uu + ry * vv + rz * n);
}

// Replace reflect in the bounce loop:
rd = cosWeightedRandomHemisphereDirection(normal, seed);
ro = hitPos + EPSILON * rd;
mask *= mat.albedo; // No Fresnel weighting
```

### Variant 2: Analytical Soft Shadow

Difference from base version: Uses the analytical distance from a sphere to the ray to compute soft shadow gradients, without additional sampling.

Key code:
```glsl
// Sphere soft shadow
float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    // d: closest distance from ray to sphere surface, t: distance along ray
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    float t = -b - sqrt(max(h, 0.0));
    return (t > 0.0) ? max(d, 0.0) / t : 1.0;
}
```

### Variant 3: Analytical Antialiasing

Difference from base version: Uses the analytical distance from a sphere to the ray to compute pixel coverage, achieving edge smoothing without multi-sampling.

Key code:
```glsl
// Sphere distance information (for antialiasing)
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w; // Closest distance
    return vec2(d, -b - sqrt(max(h, 0.0)));                // (distance, depth)
}

// In rendering, use coverage instead of hard boundary:
float px = 2.0 / iResolution.y; // Pixel size
vec2 dt = sphDistances(ro, rd, sph);
float coverage = 1.0 - clamp(dt.x / (dt.y * px), 0.0, 1.0);
col = mix(bgColor, sphereColor, coverage);
```

### Variant 4: Refraction (with Snell's Law)

Difference from base version: Adds refracted rays; requires detecting whether the ray hits the surface from outside or inside, and flipping the normal accordingly.

Key code:
```glsl
float refrIndex = 1.5; // Adjustable: index of refraction (glass≈1.5, water≈1.33)

// Add refraction branch in the bounce loop:
bool inside = dot(rd, normal) > 0.0;
vec3 n = inside ? -normal : normal;
float eta = inside ? refrIndex : 1.0 / refrIndex;
vec3 refracted = refract(rd, n, eta);

// Fresnel determines reflection/refraction ratio
float cosI = abs(dot(rd, n));
float F = schlick(cosI, pow((1.0 - eta) / (1.0 + eta), 2.0));

if (refracted != vec3(0.0) && hash1(seed) > F) {
    rd = refracted;
} else {
    rd = reflect(rd, n);
}
ro = hitPos + rd * EPSILON;
```

### Variant 5: Higher-Order Algebraic Surfaces (Quartic Surfaces - Sphere4, Goursat, Torus)

Difference from base version: Substitutes the ray into quartic equations, solving via the resolvent cubic method. Suitable for tori, super-ellipsoids, and similar shapes.

Key code:
```glsl
// Ray-Sphere4 intersection (|x|⁴+|y|⁴+|z|⁴ = r⁴)
float iSphere4(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float ra) {
    float r2 = ra * ra;
    vec3 d2 = rd*rd, d3 = d2*rd;
    vec3 o2 = ro*ro, o3 = o2*ro;
    float ka = 1.0 / dot(d2, d2);

    float k0 = ka * dot(ro, d3);
    float k1 = ka * dot(o2, d2);
    float k2 = ka * dot(o3, rd);
    float k3 = ka * (dot(o2, o2) - r2 * r2);

    // Reduce to depressed quartic, solve via resolvent cubic
    float c0 = k1 - k0 * k0;
    float c1 = k2 + 2.0 * k0 * (k0 * k0 - 1.5 * k1);
    float c2 = k3 - 3.0 * k0 * (k0 * (k0 * k0 - 2.0 * k1) + 4.0/3.0 * k2);

    float p = c0 * c0 * 3.0 + c2;
    float q = c0 * c0 * c0 - c0 * c2 + c1 * c1;
    float h = q * q - p * p * p * (1.0/27.0);

    if (h < 0.0) return MAX_DIST; // Convex body: only need to handle 2 real roots case

    h = sqrt(h);
    float s = sign(q+h) * pow(abs(q+h), 1.0/3.0);
    float t = sign(q-h) * pow(abs(q-h), 1.0/3.0);

    vec2 v = vec2((s+t) + c0*4.0, (s-t) * sqrt(3.0)) * 0.5;
    float r = length(v);
    float d = -abs(v.y) / sqrt(r + v.x) - c1/r - k0;

    if (d >= distBound.x && d <= distBound.y) {
        vec3 pos = ro + rd * d;
        normal = normalize(pos * pos * pos); // Gradient: 4x³
        return d;
    }
    return MAX_DIST;
}
```

## Performance Optimization Details

### 1. Distance Bound Pruning

The most important optimization. Each time a nearer intersection is found, `distBound.y` is shortened, and subsequent objects are automatically skipped:
```glsl
// distBound.y continuously shrinks with opU
d = opU(d, iSphere(..., d.xy, ...), matId);
d = opU(d, iBox(..., d.xy, ...), matId);   // Automatically skips objects farther than current hit
```

### 2. Bounding Sphere / Bounding Box Pre-Test

For complex geometry (tori, Goursat surfaces, etc.), test a simple bounding sphere first to check for possible intersection:
```glsl
// Test bounding sphere before torus intersection
if (iSphere(ro, rd, distBound, tmpNormal, torus.x + torus.y) > distBound.y) {
    return MAX_DIST; // Bounding sphere missed, skip expensive quartic equation
}
```

### 3. Shadow Ray Early Exit

Shadow detection only needs to know "whether there is an occluder," not the nearest intersection, so a simplified intersection function can be used:
```glsl
// Fast sphere occlusion test (only checks for intersection, no normal computation)
float fastSphIntersect(vec3 ro, vec3 rd, vec3 center, float r) {
    vec3 v = ro - center;
    float b = dot(v, rd);
    float c = dot(v, v) - r * r;
    float d = b * b - c;
    if (d > 0.0) {
        float t = -b - sqrt(d);
        if (t > 0.0) return t;
        t = -b + sqrt(d);
        if (t > 0.0) return t;
    }
    return -1.0;
}
```

### 4. Grid Acceleration Structure

For large numbers of identical primitives (e.g., hundreds of spheres), use a spatial grid to accelerate ray traversal:
```glsl
// 3D DDA grid traversal (for scenes with many spheres)
vec3 pos = floor(ro / GRIDSIZE) * GRIDSIZE;
vec3 ri = 1.0 / rd;
vec3 rs = sign(rd) * GRIDSIZE;
vec3 dis = (pos - ro + 0.5 * GRIDSIZE + rs * 0.5) * ri;

for (int i = 0; i < MAX_STEPS; i++) {
    // Test spheres in current cell
    testSphereInGrid(pos.xz, ro, rd, ...);
    // DDA step to next cell
    vec3 mm = step(dis.xyz, dis.zyx);
    dis += mm * rs * ri;
    pos += mm * rs;
}
```

### 5. Avoiding Unnecessary sqrt

Return early when the discriminant is negative, avoiding `sqrt()` on negative numbers. In some scenarios, the discriminant's sign can be used for coarse pre-filtering:
```glsl
// Check if ray is heading toward sphere and not inside it
if (c > 0.0 && b > 0.0) return MAX_DIST; // Fast cull
```

## Combination Suggestions in Detail

### 1. Analytic Intersection + Raymarching SDF

Use analytic primitives for large simple geometry (ground, bounding boxes), and SDF raymarching for complex details (fractals, smooth boolean operations). Analytic intersection provides precise start/end distances, accelerating marching convergence:
```glsl
float d = iBox(ro, rd, distBound, normal, boxSize); // Analytic box
if (d < MAX_DIST) {
    // Refine with SDF inside the box
    float t = d;
    for (int i = 0; i < 64; i++) {
        float h = sdfScene(ro + t * rd);
        if (h < 0.001) break;
        t += h;
    }
}
```

### 2. Analytic Intersection + Volumetric Effects

Use analytic intersection to obtain precise entry/exit distances, then perform volumetric sampling (clouds, fog, subsurface scattering) within that range:
```glsl
// Use analytic ellipsoid intersection to obtain volume bounds
float tEnter = (-b - sqrt(h)) / a;
float tExit  = (-b + sqrt(h)) / a;
float thickness = tExit - tEnter; // Analytic thickness

// Sample volume within [tEnter, tExit]
vec3 volumeColor = vec3(0.0);
float dt = (tExit - tEnter) / float(VOLUME_STEPS);
for (int i = 0; i < VOLUME_STEPS; i++) {
    vec3 p = ro + rd * (tEnter + float(i) * dt);
    volumeColor += sampleVolume(p) * dt;
}
```

### 3. Analytic Intersection + PBR Material System

Analytic intersection provides precise normals and intersection positions, feeding directly into Cook-Torrance and other PBR shading models:
```glsl
// Cook-Torrance BRDF (requires precise normals)
float D = beckmannDistribution(NdotH, roughness);
float G = geometricAttenuation(NdotV, NdotL, VdotH, NdotH);
float F = fresnelSchlick(VdotH, F0);
vec3 specular = vec3(D * G * F) / (4.0 * NdotV * NdotL);
```

### 4. Analytic Intersection + Spatial Transforms

Reuse the same intersection function for transformed geometry by rotating/translating/scaling the ray:
```glsl
// Rotate object: rotate the ray instead of the object
vec3 localRo = rotateY(ro - objectPos, angle);
vec3 localRd = rotateY(rd, angle);
float t = iBox(localRo, localRd, distBound, localNormal, boxSize);
// Transform normal back to world space
normal = rotateY(localNormal, -angle);
```

### 5. Analytic Intersection + Analytical AO / Soft Shadow / Antialiasing

A fully analytic rendering pipeline: intersection, shadows, occlusion, and edge smoothing all use closed-form formulas, producing zero noise:
```glsl
// Fully analytic pipeline (no random sampling, no noise)
float t = sphIntersect(ro, rd, sph);        // Analytic intersection
float shadow = sphSoftShadow(hitPos, ld, sph); // Analytic soft shadow
float ao = sphOcclusion(hitPos, normal, sph);  // Analytic ambient occlusion
float coverage = sphAntiAlias(ro, rd, sph, px); // Analytic antialiasing
```
