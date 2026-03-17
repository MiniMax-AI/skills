# CSG Boolean Operations — Detailed Reference

This document is a complete reference manual for [SKILL.md](SKILL.md), including step-by-step tutorials, mathematical derivations, variant details, and advanced usage.

## Use Cases

- **Geometric Modeling**: Build complex shapes from simple primitives (spheres, boxes, cylinders) through boolean combinations — nuts, buildings, mechanical parts, organic characters, etc.
- **Ray Marching Scenes**: All SDF-based ray marching rendering relies on CSG to compose scenes
- **Organic Forms**: Use smooth variants (smin/smax) to create natural transitions between shapes, suitable for character modeling (snails, elephants), clouds, terrain, etc.
- **Architectural / Industrial Design**: Use subtraction to carve windows and doorways, intersection to cut shapes
- **2D SDF Compositing**: Equally applicable to 2D scenes (cyberpunk clouds, UI shape compositing, etc.)

## Prerequisites

- GLSL basic syntax (`vec3`, `float`, `mix`, `clamp`, `min`, `max`)
- SDF (Signed Distance Field) concept: the signed distance from each point in space to the nearest surface, with negative values indicating the interior
- Basic SDF primitives: sphere `length(p) - r`, box `length(max(abs(p)-b, 0.0))`
- Ray Marching basics: stepping from the camera along the view direction, using SDF values to determine step size

## Core Principles in Detail

The essence of CSG boolean operations is **per-point value operations on two distance fields**:

| Operation | Math Expression | Meaning |
|-----------|----------------|---------|
| Union | `min(d1, d2)` | Take the nearest surface, keeping both shapes |
| Intersection | `max(d1, d2)` | Take the farthest surface, keeping only the overlap |
| Subtraction | `max(d1, -d2)` | Use d2's interior (negated) to cut d1 |

**Hard booleans** produce sharp edges at the junction. **Smooth booleans** (smooth min/max) introduce a blend band in the transition region, "fusing" the two shapes together. The key parameter `k` controls the blend band width:

- Larger `k` means wider, smoother transitions
- Smaller `k` means closer to hard boolean sharp edges
- `k = 0` degenerates to hard boolean

Three mainstream smooth formulas, each with distinct characteristics:
1. **Polynomial**: Most commonly used, fast to compute, natural transitions
2. **Quadratic optimized**: More compact and mathematically elegant
3. **Exponential**: Smoothest transitions but more expensive to compute

## Implementation Steps in Detail

### Step 1: Hard Boolean Operations

**What**: Implement the three basic boolean operations — union, intersection, subtraction.

**Why**: These are the foundation of all CSG operations. `min` selects the nearest surface to achieve union; `max` selects the farthest surface for intersection; negating the second operand and taking `max` with the first achieves subtraction (keeping the region of d1 that is not inside d2).

```glsl
// Union: keep both shapes
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

// Intersection: keep only the overlapping region
float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

// Subtraction: carve d2 out of d1
float opSubtraction(float d1, float d2) {
    return max(d1, -d2);
}
```

### Step 2: Smooth Union — Polynomial Version

**What**: Implement a union operation with a blend transition, producing rounded junctions between two shapes.

**Why**: Hard `min` produces C0 continuity (sharp creases) at the SDF junction. Polynomial smooth min interpolates within the transition band where `|d1-d2| < k`, producing C1 continuity (smooth transitions). In the formula, `h` is the normalized blend factor, and the `k*h*(1-h)` term ensures the distance field correctly dips in the transition region (producing more accurate distance values than plain `mix`).

```glsl
// Polynomial smooth union
// k: blend radius, typical values 0.05~0.5
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}
```

### Step 3: Smooth Subtraction and Smooth Intersection — Polynomial Version

**What**: Extend the smooth union approach to subtraction and intersection.

**Why**: Subtraction = intersection with an inverted SDF; intersection = inverted union of inverted inputs. The sign changes in the formulas reflect this duality. Note that subtraction uses `d2+d1` (not `d2-d1`), because d1 is negated in the operation.

```glsl
// Smooth subtraction: smoothly carve d2 out of d1
float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

// Smooth intersection: smoothly keep the overlapping region
float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```

### Step 4: Quadratic Optimized Smooth Operations

**What**: Implement smin/smax using a more compact quadratic polynomial formula.

**Why**: This version is mathematically equivalent but more concise with fewer branches. `h = max(k - abs(a-b), 0.0)` directly computes the influence within the transition band, being non-zero only when `|a-b| < k`. `h*h*0.25/k` is the quadratic correction term. smax can be derived directly through smin's duality: `smax(a,b,k) = -smin(-a,-b,k)`.

```glsl
// Quadratic optimized smooth union
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

// Quadratic optimized smooth intersection / smooth max
float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Subtraction via smax
float sSub(float d1, float d2, float k) {
    return smax(d1, -d2, k);
}
```

### Step 5: Basic SDF Primitives

**What**: Define the basic shape SDFs used for combination.

**Why**: CSG needs operands. Spheres and boxes are the most common primitives; cylinders are often used for drilling holes.

```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}
```

### Step 6: CSG Combination for Scene Construction

**What**: Combine primitives with boolean operations to build complex geometry.

**Why**: The power of CSG lies in combination. Classic example: intersecting a sphere with a cube yields a rounded cube, then subtracting three cylinders produces a nut shape.

```glsl
float mapScene(vec3 p) {
    // Primitives
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.2);
    float cylX = sdCylinder(p.yzx, 2.0, 0.4); // Along X axis
    float cylY = sdCylinder(p.xyz, 2.0, 0.4); // Along Y axis
    float cylZ = sdCylinder(p.zxy, 2.0, 0.4); // Along Z axis

    // CSG combination: (Cube ∩ Sphere) - three cylinders
    float shape = opIntersection(cube, sphere);
    float holes = opUnion(cylX, opUnion(cylY, cylZ));
    return opSubtraction(shape, holes);
}
```

### Step 7: Organic Body Modeling with Smooth CSG

**What**: Use smin/smax with different k values to blend multiple ellipsoids/capsules into organic characters.

**Why**: Different body parts need different blend amounts — large k values for broad connections (torso-legs), small k values for fine details (eyes-head). This is the core technique for organic character modeling with smooth CSG.

```glsl
float mapCreature(vec3 p) {
    // Torso
    float body = sdSphere(p, 0.5);

    // Head — larger blend radius
    float head = sdSphere(p - vec3(0.0, 0.6, 0.3), 0.25);
    float d = smin(body, head, 0.15);

    // Limbs — medium blend radius
    float leg = sdCylinder(p - vec3(0.2, -0.5, 0.0), 0.3, 0.08);
    d = smin(d, leg, 0.08);

    // Eye sockets — small blend radius for smooth subtraction
    float eye = sdSphere(p - vec3(0.05, 0.75, 0.4), 0.05);
    d = smax(d, -eye, 0.02);

    return d;
}
```

### Step 8: Ray Marching Main Loop

**What**: Render the SDF scene using the sphere tracing algorithm.

**Why**: SDF scenes cannot be rendered with traditional rasterization. Ray Marching is needed: cast a ray from each pixel, advance by the current point's distance to the nearest surface (i.e., the SDF value) at each step, until close enough to a surface or out of range.

```glsl
float rayMarch(vec3 ro, vec3 rd, float maxDist) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > maxDist) break;
    }
    return -1.0; // No hit
}
```

### Step 9: Normal Computation and Lighting

**What**: Compute the surface normal by taking the finite-difference gradient of the SDF, then apply lighting.

**Why**: The gradient direction of the SDF is the surface normal direction. Using tetrahedral sampling only requires 4 SDF samples, which is more efficient than the 6 needed for central differences.

```glsl
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}
```

## Common Variants in Detail

### Variant 1: Polynomial Smooth Union (Most Universal Version)

Differs from the basic (quadratic optimized) version by using the `clamp + mix` form, which makes the code intent more intuitive. Mathematically approximately equivalent to the quadratic version, but with slight differences in the transition curve in extreme cases.

```glsl
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```

### Variant 2: Exponential Smooth Union

**Difference from the basic version**: Uses `exp` for implementation, with smoother transitions (C-infinity continuity vs polynomial's C1). However, `exp` is more expensive. Suitable for terrain modeling (e.g., craters). The parameter `k` has a different meaning — in the exponential version, larger `k` produces sharper transitions (opposite to polynomial). Used in RME4-Crater for volcano terrain blending.

```glsl
float sminExp(float a, float b, float k) {
    float res = exp(-k * a) + exp(-k * b);
    return -log(res) / k;
}
```

### Variant 3: Smooth Operations with Color Blending

**Difference from the basic version**: Blends material colors using the same blend factor during geometric fusion. This way, the material at the junction transitions naturally rather than showing an abrupt color boundary. Useful for color gradients between organic shape junctions (e.g., shell and body).

```glsl
// vec3 overloaded smax, blending colors simultaneously
vec3 smax(vec3 a, vec3 b, float k) {
    vec3 h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Alternatively, a separated version: returns the blend factor to the caller
float sminWithFactor(float a, float b, float k, out float blend) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    blend = h;
    return mix(b, a, h) - k * h * (1.0 - h);
}
// Usage example:
// float blend;
// float d = sminWithFactor(d1, d2, 0.1, blend);
// vec3 color = mix(color2, color1, blend);
```

### Variant 4: Layered CSG Modeling (Architectural / Industrial Scenes)

**Difference from the basic version**: Does not use smooth variants; instead uses multi-level nested hard boolean operations to build precise geometric structures. An additive-then-subtractive pattern — first build the overall form with union, then carve details (windows, doorways) with subtraction. Commonly used for architectural modeling.

```glsl
float sdBuilding(vec3 p) {
    // Step 1: Additive phase — build walls
    float walls = sdBox(p, vec3(1.0, 0.8, 1.0));

    // Step 2: Additive — roof
    vec3 roofP = p;
    roofP.y -= 0.8;
    float roof = sdBox(roofP, vec3(1.2, 0.3, 1.2));
    float d = opUnion(walls, roof);

    // Step 3: Subtractive phase — carve windows
    vec3 winP = abs(p);                  // Exploit symmetry
    winP -= vec3(1.01, 0.3, 0.4);
    float window = sdBox(winP, vec3(0.1, 0.15, 0.12));
    d = opSubtraction(d, window);

    // Step 4: Hollow out the interior
    float hollow = sdBox(p, vec3(0.95, 0.75, 0.95));
    d = opSubtraction(d, hollow);

    return d;
}
```

### Variant 5: Large-Scale Organic Character Modeling

**Difference from the basic version**: Extensively uses smin/smax (100+ calls), with different k values for different body parts to control blend amounts. Large k (0.1~0.3) for torso connections, small k (0.01~0.05) for detail areas. Complex organic characters can use over 100 smooth operations to sculpt a complete form.

```glsl
float mapCharacter(vec3 p) {
    // Torso — main ellipsoid
    float body = sdEllipsoid(p, vec3(0.5, 0.4, 0.6));

    // Head — large blend, natural transition to neck
    float head = sdEllipsoid(p - vec3(0.0, 0.5, 0.5), vec3(0.25));
    float d = smin(body, head, 0.2);               // Large k: wide blend band

    // Ears — medium blend
    float ear = sdEllipsoid(p - vec3(0.3, 0.6, 0.3), vec3(0.15, 0.2, 0.05));
    d = smin(d, ear, 0.08);

    // Nostrils — small blend for smooth subtraction
    float nostril = sdSphere(p - vec3(0.0, 0.4, 0.7), 0.03);
    d = smax(d, -nostril, 0.02);                   // Small k: fine carving

    return d;
}
```

## Performance Optimization in Detail

### 1. Bounding Volume Acceleration

The biggest performance bottleneck in CSG scenes is `mapScene()` being called too many times (MAX_STEPS per pixel per frame). Use AABB bounding boxes to skip distant sub-scenes:

```glsl
float mapScene(vec3 p) {
    float d = MAX_DIST;
    // Only compute complex sub-scene when inside bounding sphere
    float bound = length(p - vec3(2.0, 0.0, 0.0)) - 1.5;
    if (bound < d) {
        d = min(d, complexSubScene(p));
    }
    return d;
}
```

Using `intersectAABB` to pre-test rays against AABBs can skip regions that cannot be hit.

### 2. Reducing SDF Sample Count

- Use tetrahedral sampling for normal computation (4 calls) instead of central differences (6 calls)
- Use `t += d * 0.9` to slightly reduce step size, preventing overshoot-induced penetration

### 3. smin/smax Selection

| Method | Performance | Accuracy | Recommended Use |
|--------|-------------|----------|----------------|
| Quadratic optimized | Fastest | Good | General first choice |
| Polynomial clamp | Fast | Good | When a separate blend factor is needed |
| Exponential | Slower | Best | Terrain, when extremely smooth transitions are needed |

### 4. Avoiding k=0 with smin

When `k` is zero, the quadratic optimized version causes a division-by-zero error. Always ensure `k > 0`, or fall back to hard boolean when k approaches zero:

```glsl
float safeSmin(float a, float b, float k) {
    if (k < 0.0001) return min(a, b);
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}
```

### 5. Symmetry Exploitation

For symmetric shapes, use `abs()` to fold coordinates and only define one side. Useful for symmetric windows, limbs, and other mirrored features:

```glsl
vec3 q = vec3(p.xy, abs(p.z)); // Mirror along Z axis
```

## Combination Suggestions in Detail

### 1. CSG + Domain Repetition

CSG shapes can be infinitely repeated in space via `mod()` or `fract()`, suitable for mechanical arrays, architectural railings, etc.:

```glsl
float mapRepeated(vec3 p) {
    vec3 q = p;
    q.x = mod(q.x + 1.0, 2.0) - 1.0; // Repeat every 2 units along X axis
    return mapSinglePiston(q);
}
```

### 2. CSG + Procedural Displacement

Add noise displacement on top of SDF results to give smooth CSG shapes surface detail textures, adding a flowing or organic appearance:

```glsl
float mapWithDisplacement(vec3 p) {
    float base = smin(body, limb, 0.1);
    float noise = 0.02 * sin(10.0 * p.x) * sin(10.0 * p.y) * sin(10.0 * p.z);
    return base + noise;
}
```

### 3. CSG + Procedural Texturing

Use smin's blend factor to blend not just geometry but also material IDs or colors, achieving cross-shape material gradients:

```glsl
vec2 mapWithMaterial(vec3 p) {
    float d1 = sdSphere(p, 0.5);
    float d2 = sdBox(p - vec3(0.3), vec3(0.3));
    float blend;
    float d = sminWithFactor(d1, d2, 0.1, blend);
    float matId = mix(1.0, 2.0, blend); // Blend material ID
    return vec2(d, matId);
}
```

### 4. CSG + 2D SDF

CSG is not limited to 3D. In 2D scenes, smooth union can similarly create organic shapes, like stylized cloud effects:

```glsl
float sdCloud2D(vec2 p) {
    float d = sdBox(p, vec2(0.5, 0.1));
    d = opSmoothUnion(d, length(p - vec2(-0.3, 0.1)) - 0.15, 0.1);
    d = opSmoothUnion(d, length(p - vec2(0.1, 0.15)) - 0.12, 0.1);
    d = opSmoothUnion(d, length(p - vec2(0.3, 0.08)) - 0.1, 0.1);
    return d;
}
```

### 5. CSG + Animation

By binding CSG parameters (k values, primitive positions, primitive radii) to `iTime`, you can achieve dynamic shape deformation and blend animations:

```glsl
float mapAnimated(vec3 p) {
    float k = 0.1 + 0.15 * sin(iTime);            // Dynamic blend radius
    float r = 0.3 + 0.1 * sin(iTime * 2.0);       // Dynamic radius
    float d1 = sdSphere(p, 0.5);
    float d2 = sdSphere(p - vec3(0.8 * sin(iTime), 0.0, 0.0), r);
    return smin(d1, d2, k);
}
```
