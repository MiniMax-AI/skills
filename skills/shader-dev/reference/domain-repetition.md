# Domain Repetition and Spatial Folding — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, mathematical derivations, and advanced usage.

## Prerequisites

- GLSL basic syntax, `vec2/vec3/mat2` operations
- Behavior of built-in functions like `mod()`, `fract()`, `abs()`, `atan()`
- Signed Distance Field (SDF) concept — a function returning the distance from a point to the nearest surface
- Basic principles of Ray Marching
- 2D rotation matrix `mat2(cos(a), sin(a), -sin(a), cos(a))`

## Core Principles in Detail

The essence of domain repetition is **coordinate transformation**: before computing the SDF, the point `p`'s coordinates are folded/mapped into a finite "fundamental domain," so that every point in infinite space maps to the same cell. The SDF function only needs to evaluate coordinates within this single cell, and the result automatically repeats across all of space.

**Three fundamental operations:**

| Operation | Formula | Effect |
|-----------|---------|--------|
| **mod repetition** | `p = mod(p + period/2, period) - period/2` | Infinite translational repetition along an axis |
| **abs mirroring** | `p = abs(p)` | Mirror symmetry across an axis plane |
| **Rotational folding** | `angle = mod(atan(p.y, p.x), TAU/N); p = rotate(p, -angle)` | N-fold rotational symmetry |

**Key mathematics:**

- `mod(x, c)` maps x to the `[0, c)` range, providing periodicity
- `abs(x)` folds the negative half-space onto the positive half-space, providing reflective symmetry
- `fract(x) = x - floor(x)` is equivalent to `mod(x, 1.0)`, providing normalized periodicity

## Step-by-Step Details

### Step 1: Basic Cartesian Domain Repetition (mod Repetition)

**What**: Infinitely repeat 3D space along one or more axes via translation.

**Why**: `mod(p, c) - c/2` constrains coordinates to the `[-c/2, c/2)` range, dividing space into an infinite number of cells of size `c`, where each cell has identical coordinates. The SDF only needs to be defined within a single cell.

**Code**:
```glsl
// Standard 3D domain repetition (centered version)
// period is the size of each cell
vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

// Usage example: infinitely repeat a box
float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(4.0)); // Repeat every 4 units
    return sdBox(q, vec3(0.5));          // One box per cell
}
```

> This `pos = mod(pos-2., 4.) -2.;` is this exact pattern — period=4, offset=2, perfectly centered. `p1.x = mod(p1.x-5., 10.) - 5.;` follows the same logic (period=10, centered at origin).

### Step 2: Symmetric Fold Repetition (abs-mod Hybrid)

**What**: On top of mod repetition, use `abs()` to give each cell mirror symmetry, eliminating seams at cell boundaries.

**Why**: Plain `mod` repetition has coordinate discontinuity at cell boundaries (jumping from `+c/2` to `-c/2`), which can cause visible seams. `abs(tile - mod(p, tile*2))` makes coordinates fold back and forth within each tile from 0 to tile to 0, ensuring continuity at boundaries (equivalent to a "triangle wave").

**Code**:
```glsl
// Symmetric fold (triangle wave mapping)
// tile is the half-period length, full period is tile*2
vec3 symmetricFold(vec3 p, float tile) {
    return abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
}

// Usage: classic tiling fold
vec3 p = from + s * dir * 0.5;
p = abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
```

> The core line `p = abs(vec3(tile)-mod(p,vec3(tile*2.)));` is this pattern. `tpos.xz=abs(.5-mod(tpos.xz,1.));` is the 2D version of the same pattern (tile=0.5, period=1).

### Step 3: Angular Domain Repetition (Polar Coordinate Folding)

**What**: Divide space into N equal rotational sectors around an axis, achieving a kaleidoscope effect.

**Why**: After converting coordinates to polar form, applying `mod(angle, TAU/N)` folds the full 360 degrees into a single `TAU/N` sector. Rotating the coordinates back makes all sectors share the same SDF.

**Code**:
```glsl
// Angular domain repetition
// p: xz plane coordinates, count: repetition count
// Returns rotated coordinates (folded into the first sector)
vec2 pmod(vec2 p, float count) {
    float angle = atan(p.x, p.y) + PI / count;
    float sector = TAU / count;
    angle = floor(angle / sector) * sector;
    return p * rot(-angle);  // rot is a 2D rotation matrix
}

// Usage: 5-fold rotational symmetry
vec3 p1 = p;
p1.xy = pmod(p1.xy, 5.0); // 5-fold symmetry in the xy plane
```

> The `pmod()` function implements this pattern. An alternative `amod()` function follows the same idea but uses `inout` parameters to directly modify coordinates and returns the sector index (for coloring variants).

### Step 4: fract Domain Folding (For Fractal Iteration)

**What**: Use `fract()` in fractal iteration loops to repeatedly fold coordinates back into the `[0,1)` range, combined with scaling to achieve self-similar structures.

**Why**: `-1.0 + 2.0*fract(0.5*p+0.5)` maps p to the `[-1, 1)` range (centered fract). Each iteration divides space into 8 sub-cells (in 3D), each recursively undergoing the same operation. Combined with the scaling factor `k = s/dot(p,p)` (spherical inversion), this produces fractal hierarchical structure.

**Code**:
```glsl
// Core loop of an Apollonian fractal
float map(vec3 p, float s) {
    float scale = 1.0;
    vec4 orb = vec4(1000.0); // Orbit trap for coloring

    for (int i = 0; i < 8; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // Centered fract fold

        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));  // Orbit capture

        float k = s / r2;    // Spherical inversion scaling
        p *= k;
        scale *= k;
    }

    return 0.25 * abs(p.y) / scale; // Distance must be divided by accumulated scale
}
```

> `-1.0 + 2.0*fract(0.5*p+0.5)` is equivalent to `mod(p+1, 2) - 1`, mapping p to [-1,1).

### Step 5: Iterative abs Folding (IFS / Kali-set)

**What**: Repeatedly execute `p = abs(p) - offset` inside a loop, combined with rotation and scaling, to generate fractal symmetric structures.

**Why**: `abs(p)` folds space into the positive octant, `-offset` translates the origin, then `abs()` folds again... each iteration adds another layer of symmetry. This is one implementation of an Iterated Function System (IFS). Combined with rotation, it produces extremely rich fractal structures.

**Code**:
```glsl
// IFS abs folding fractal
float ifsBox(vec3 p) {
    for (int i = 0; i < 5; i++) {
        p = abs(p) - 1.0;        // Fold + offset
        p.xy *= rot(iTime * 0.3); // Rotation adds complexity
        p.xz *= rot(iTime * 0.1);
    }
    return sdBox(p, vec3(0.4, 0.8, 0.3));
}

// Kali-set variant: uses dot(p,p) scaling
vec2 de(vec3 pos) {
    vec3 tpos = pos;
    tpos.xz = abs(0.5 - mod(tpos.xz, 1.0)); // mod repetition first, then IFS
    vec4 p = vec4(tpos, 1.0);                // w component tracks scaling
    for (int i = 0; i < 7; i++) {
        p.xyz = abs(p.xyz) - vec3(-0.02, 1.98, -0.02);
        p = p * (2.0) / clamp(dot(p.xyz, p.xyz), 0.4, 1.0)
            - vec4(0.5, 1.0, 0.4, 0.0);
        p.xz *= rot(0.416);  // Intra-iteration rotation
    }
    return vec2(length(max(abs(p.xyz)-vec3(0.1,5.0,0.1), 0.0)) / p.w, 0.0);
}
```

> Note that the `de()` variant uses the `vec4`'s w component to accumulate the scaling factor (`p.w`), and the final distance is divided by `p.w` to maintain SDF validity.

### Step 6: Reflection Folding (Polyhedral Symmetry)

**What**: Fold space into the fundamental domain of a polyhedron (such as an icosahedron) through a set of reflection planes.

**Why**: Regular polyhedra have multiple symmetry planes. Reflecting along each symmetry plane via `p = p - 2*dot(p,n)*n` folds all of space into a "fundamental domain" (1/60th of the entire polyhedron for an icosahedron). Geometry only needs to be defined within this fundamental domain.

**Code**:
```glsl
// Plane reflection
float pReflect(inout vec3 p, vec3 planeNormal, float offset) {
    float t = dot(p, planeNormal) + offset;
    if (t < 0.0) {
        p = p - (2.0 * t) * planeNormal;
    }
    return sign(t);
}

// Icosahedral folding
void pModIcosahedron(inout vec3 p) {
    // nc is the third fold plane normal (the first two are the xz and yz planes)
    vec3 nc = vec3(-0.5, -cos(PI/5.0), sqrt(0.75 - cos(PI/5.0)*cos(PI/5.0)));
    p = abs(p);          // xz and yz plane reflections
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
}
```

> Full icosahedral symmetry group is achieved through alternating `abs()` and `pReflect()`.

### Step 7: Toroidal / Cylindrical Domain Warping (displaceLoop)

**What**: Bend planar space into cylindrical or toroidal topology.

**Why**: `displaceLoop` converts Cartesian coordinates `(x, z)` into `(distance_to_center - R, angle)`, "rolling" a plane into a cylinder/torus of radius R. The angular dimension can then undergo `amod` for angular repetition.

**Code**:
```glsl
// Toroidal domain warp: bend the xz plane into a torus
vec2 displaceLoop(vec2 p, float radius) {
    return vec2(length(p) - radius, atan(p.y, p.x));
}

// Usage example: architectural ring corridor
vec3 pDonut = p;
pDonut.x += donutRadius;
pDonut.xz = displaceLoop(pDonut.xz, donutRadius);
pDonut.z *= donutRadius; // Unwrap angle to linear length
// Now pDonut is "flattened" ring coordinates, ready for linear repetition
```

> The `displaceLoop` function bends an architectural scene into a ring structure.

### Step 8: 1D Centered Domain Repetition (with Cell ID)

**What**: Perform centered mod repetition along one axis and return the current cell number.

**Why**: Cell IDs can be used to assign different random properties (color, size, rotation, etc.) to each cell's geometry, breaking the uniformity of perfect repetition.

**Code**:
```glsl
// 1D centered domain repetition, returns cell index
float pMod1(inout float p, float size) {
    float halfsize = size * 0.5;
    float c = floor((p + halfsize) / size); // Cell index
    p = mod(p + halfsize, size) - halfsize; // Centered local coordinate
    return c;
}

// Usage: repeat along x axis and get cell ID
float cellID = pMod1(p.x, 2.0);
float salt = fract(sin(cellID * 127.1) * 43758.5453); // Random seed
```

> This is a standard domain repetition library function. A simpler `repeat()` function follows the same pattern (version without returning the index).

## Common Variants in Detail

### 1. Volumetric Glow Rendering

Unlike standard ray marching, this does not check for surface hits. Instead, it accumulates a "distance-to-brightness" contribution at each step.

**Difference from the basic version**: No normal computation or traditional shading needed. Each step accumulates glow via `exp(-dist * k)`.

**Key modified code**:
```glsl
// Replace hit detection in raymarch with glow accumulation
float acc = 0.0;
float t = 0.0;
for (int i = 0; i < 99; i++) {
    vec3 pos = ro + rd * t;
    float dist = map(pos);
    dist = max(abs(dist), 0.02);     // Prevent division by zero, abs allows passing through surfaces
    acc += exp(-dist * 3.0);          // Adjustable: decay coefficient controls glow sharpness
    t += dist * 0.5;                  // Adjustable: step scale (<1 means denser sampling)
}
vec3 col = vec3(acc * 0.01, acc * 0.011, acc * 0.012);
```

> This volumetric glow rendering strategy is commonly used in fractal domain repetition shaders.

### 2. Single-Axis / Dual-Axis Selective Repetition

Repeat along only certain axes while keeping others unchanged. Suitable for corridors, columns, and other directional scenes.

**Difference from the basic version**: Does not use `vec3` full-axis repetition; only applies mod to the needed components.

**Key modified code**:
```glsl
// Repeat only along x and z axes, y axis unrepeated
float map(vec3 pos) {
    vec3 q = pos;
    q.xz = mod(q.xz + 2.0, 4.0) - 2.0; // Only xz repeated
    // q.y retains original value, providing finite height
    return sdBox(q, vec3(0.3, 0.5, 0.3));
}
```

### 3. Fractal fract Domain Folding (Apollonian Type)

Uses `fract()` instead of `mod()` for iterative folding, combined with scaling and orbit trapping to create fractals.

**Difference from the basic version**: Repeatedly applies fract+scaling in a loop rather than a one-time mod; uses orbit trap coloring.

**Key modified code**:
```glsl
float scale = 1.0;
for (int i = 0; i < 8; i++) {
    p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // fract fold
    float r2 = dot(p, p);
    float k = 1.2 / r2;                      // Adjustable: scaling parameter
    p *= k;
    scale *= k;
}
return 0.25 * abs(p.y) / scale;
```

### 4. Multi-Level Nested Repetition

Apply angular repetition within a sector, then linear repetition within each sector, or vice versa.

**Difference from the basic version**: Domain repetition operations are nested across multiple levels, each providing a different spatial organization.

**Key modified code**:
```glsl
// Outer level: angular repetition
float indexX = amod(p.xz, segments); // Divide into N sectors
p.x -= radius;
// Inner level: linear repetition
p.y = repeat(p.y, cellSize);         // Repeat along y axis
// Random seed for each cell
float salt = rng(vec2(indexX, floor(p.y / cellSize)));
```

> This kind of nesting is commonly used in architectural scene shaders.

### 5. Bounded Domain Repetition (Finite Repetition)

Use `clamp` to limit the mod cell index, achieving a finite number of repetitions.

**Difference from the basic version**: Uses `clamp` to restrict the cell index to `[-N, N]`, repeating only `2N+1` times.

**Key modified code**:
```glsl
// Finite domain repetition: repeat at most N times along each axis
vec3 domainRepeatLimited(vec3 p, float size, vec3 limit) {
    return p - size * clamp(floor(p / size + 0.5), -limit, limit);
}

// Usage: repeat 5 times along x, 3 times each along y and z
vec3 q = domainRepeatLimited(p, 2.0, vec3(2.0, 1.0, 1.0));
```

## Performance Optimization Deep Dive

### Bottleneck 1: High Iteration Count in Fractal Loops

**Problem**: When IFS or fract folding loops iterate too many times, the `map()` function slows down, and `map()` is called at every step during ray marching.

**Optimization**:
- Reduce fractal iteration count (5-8 iterations are usually sufficient)
- Use the `vec4`'s w component to track the scaling factor, avoiding extra scaling variables
- Set upper and lower bounds in `clamp(dot(p,p), min, max)` to prevent numerical blowup

### Bottleneck 2: mod Repetition Causing Inaccurate Distance Fields

**Problem**: The SDF after domain repetition may be inaccurate at cell boundaries (geometry in adjacent cells may be closer), causing ray marching overshoot or extra steps.

**Optimization**:
- Ensure geometry fits entirely within the cell (radius < period/2)
- Use a smaller step factor (`t += d * 0.5` instead of `t += d`)
- For volumetric glow rendering, use `max(abs(d), minDist)` to prevent excessively small step sizes

### Bottleneck 3: Compilation Time from Nested Repetition

**Problem**: Multi-level nested domain repetition and fractal loops can cause very long shader compilation times.

**Optimization**:
- Pre-compute constant expressions in `map()`
- Avoid `normalize()` inside loops (manually divide by length instead)
- Use the loop version for normal computation instead of unrolled version to reduce compiler inlining

### Bottleneck 4: Sampling Rate for Volumetric Glow Rendering

**Problem**: Volumetric glow rendering requires dense sampling along the ray.

**Optimization**:
- Increase step size with distance: `t += dist * (0.3 + t * 0.02)`
- Reduce sampling density for distant regions; the distance decay `exp(-totdist)` naturally hides precision loss
- Use a `distfading` multiplier to gradually attenuate distant contributions (e.g., `fade *= distfading`)

## Combination Suggestions with Complete Code

### 1. Domain Repetition + Ray Marching

**The most basic and most common combination.** Domain repetition defines the geometric spatial structure; ray marching handles rendering. This is the most fundamental combination in SDF rendering.

### 2. Domain Repetition + Orbit Trap Coloring

Record intermediate values during the fractal iteration loop (e.g., `min(orb, abs(p))`), used to color fractal structures. Avoids the high cost of normal computation + lighting on fractal surfaces.

**Combination approach**:
```glsl
vec4 orb = vec4(1000.0);
for (...) {
    p = fold(p);
    orb = min(orb, vec4(abs(p), dot(p,p)));
}
// Use orb values for color mapping
vec3 color = mix(vec3(1,0.8,0.2), vec3(1,0.55,0), clamp(orb.y * 6.0, 0.0, 1.0));
```

### 3. Domain Repetition + Toroidal / Polar Coordinate Warping

First use `displaceLoop` to bend space into a toroidal topology, then perform linear and angular repetition in the flattened coordinates. Suitable for creating ring corridors, donut buildings, etc.

**Combination approach**:
```glsl
p.xz = displaceLoop(p.xz, R);  // Bend into ring
p.z *= R;                       // Angle to length
amod(p.xz, N);                  // Angular repetition
p.y = repeat(p.y, cellSize);    // Linear repetition
```

### 4. Domain Repetition + Noise / Random Variants

Generate pseudo-random numbers from cell IDs to inject variation into each repeated cell (size, rotation, color offset), breaking the uniformity.

**Combination approach**:
```glsl
float cellID = pMod1(p.x, size);
float salt = fract(sin(cellID * 127.1) * 43758.5453);
// Use salt to modulate geometric parameters
float boxSize = 0.3 + 0.2 * salt;
```

### 5. Domain Repetition + Polar Coordinate Spiral Transform

Use `cartToPolar` / `polarToCart` coordinate transforms combined with `pMod1` for repetition along spiral paths. Suitable for DNA double helices, springs, threads, etc.

**Combination approach**:
```glsl
p = cartToPolar(p);         // Convert to polar coordinates
p.y *= radius;               // Unwrap angle to length
// Repeat along spiral line
vec2 closest = closestPointOnRepeatedLine(vec2(lead, radius*TAU), p.xy);
p.xy -= closest;             // Local coordinates
```
