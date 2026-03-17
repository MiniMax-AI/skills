# Voronoi & Cellular Noise — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing prerequisites, step-by-step explanations, variant descriptions, performance analysis, and complete combination code.

## Prerequisites

- **GLSL Basic Syntax**: `vec2/vec3`, `floor/fract`, `dot`, `smoothstep` and other built-in functions
- **Vector Math**: dot product, distance calculation, vector normalization
- **Pseudo-Random Hash Function Concepts**: input coordinates -> pseudo-random values, deterministic but appearing random
- **fBm (Fractional Brownian Motion) Basics**: multi-layer noise summation, used for advanced variants

## Core Principles in Detail

The essence of Voronoi noise is **spatial partitioning**: scatter a set of feature points across 2D/3D space, and each pixel belongs to the "cell" defined by its nearest feature point.

**Core Algorithm Flow:**

1. Divide space into an integer grid (`floor`), placing one randomly offset feature point in each grid cell
2. For the current pixel, search all feature points in the surrounding 3x3 (2D) or 3x3x3 (3D) neighborhood
3. Calculate the distance to each feature point, recording the nearest distance F1 (and optionally the second-nearest distance F2)
4. Use F1, F2, or their combination (e.g., F2-F1) as the output value, mapping to color/height/shape

**Key Mathematics:**
- Distance metrics: Euclidean `length(r)` or `dot(r,r)` (squared distance, faster), Manhattan `abs(r.x)+abs(r.y)`, Chebyshev `max(abs(r.x), abs(r.y))`
- Exact border distance (two-pass algorithm): `dot(0.5*(mr+r), normalize(r-mr))` (perpendicular bisector projection)
- Rounded borders (harmonic mean): `1/(1/(d2-d1) + 1/(d3-d1))`

## Implementation Steps — Detailed Explanation

### Step 1: Hash Function — Generating Pseudo-Random Feature Points

**What**: Define a hash function that maps 2D integer coordinates to a pseudo-random `vec2` in the [0,1] range.

**Why**: Feature point positions within each grid cell need to be deterministic but appear random. Hash functions provide this "reproducible randomness". Different hash functions affect distribution uniformity and visual quality.

**Code**:
```glsl
// Classic sin-dot hash (concise and efficient, suitable for most scenarios)
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// 3D version (for 3D Voronoi)
vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

// High-quality integer hash (more uniform distribution, for production-grade noise)
vec3 hash3_uint(vec3 p) {
    uvec3 q = uvec3(ivec3(p)) * uvec3(1597334673U, 3812015801U, 2798796415U);
    q = (q.x ^ q.y ^ q.z) * uvec3(1597334673U, 3812015801U, 2798796415U);
    return vec3(q) / float(0xffffffffU);
}
```

### Step 2: Grid Partitioning and Neighborhood Search — F1 Distance

**What**: Split input coordinates into integer part (grid ID) and fractional part (position within cell), iterate over the 3x3 neighborhood to compute distances to all feature points, and find the nearest distance F1.

**Why**: `floor/fract` discretizes continuous space into a grid. Since feature points are offset within the [0,1] range, the nearest point can only be in the current cell or its 8 neighbors, so a 3x3 search covers all cases.

**Code**:
```glsl
// Basic 2D Voronoi — returns (F1 distance, cell ID)
vec2 voronoi(vec2 x) {
    vec2 n = floor(x);   // Current grid coordinate
    vec2 f = fract(x);   // Offset within cell [0,1)

    vec3 m = vec3(8.0);  // (min distance, corresponding hash value) — initialized to large value

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));       // Neighbor offset
        vec2 o = hash2(n + g);                    // Feature point position in that cell [0,1)
        vec2 r = g - f + o;                       // Vector from current pixel to that feature point
        float d = dot(r, r);                      // Squared distance (avoids sqrt)

        if (d < m.x) {
            m = vec3(d, o);                       // Update nearest distance and cell ID
        }
    }

    return vec2(sqrt(m.x), m.y + m.z);  // (distance, ID)
}
```

### Step 3: F1 + F2 Tracking — Edge Detection

**What**: Simultaneously record the nearest distance F1 and second-nearest distance F2 during the search, using F2-F1 to extract cell boundaries.

**Why**: The value of F2-F1 is large inside cells (far from boundaries) and approaches 0 at cell junctions (two feature points equidistant). This is the most common Voronoi edge detection method.

**Code**:
```glsl
// F1 + F2 Voronoi — returns vec2(F1, F2)
vec2 voronoi_f1f2(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);

    vec2 res = vec2(8.0); // res.x = F1, res.y = F2

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 b = vec2(i, j);
        vec2 r = b - f + hash2(p + b);
        float d = dot(r, r); // Can substitute other distance metrics

        if (d < res.x) {
            res.y = res.x;   // Previous F1 becomes F2
            res.x = d;       // Update F1
        } else if (d < res.y) {
            res.y = d;       // Update F2
        }
    }

    res = sqrt(res);
    return res;
    // Edge value = res.y - res.x (F2 - F1)
}
```

### Step 4: Exact Border Distance — Two-Pass Algorithm

**What**: First pass finds the nearest feature point; second pass calculates the exact distance to all neighboring cell boundaries.

**Why**: Simple F2-F1 is only an approximation of the boundary. For geometrically exact equidistant lines and smooth boundary rendering, the distance to the perpendicular bisector must be computed. The second pass requires a 5x5 search range to ensure geometric correctness.

**Code**:
```glsl
// Exact border distance Voronoi — returns vec3(border distance, nearest point offset)
vec3 voronoi_border(vec2 x) {
    vec2 ip = floor(x);
    vec2 fp = fract(x);

    // === Pass 1: Find nearest feature point ===
    vec2 mg, mr;
    float md = 8.0;

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;
        float d = dot(r, r);

        if (d < md) {
            md = d;
            mr = r;    // Vector to nearest point
            mg = g;    // Grid offset of nearest point
        }
    }

    // === Pass 2: Calculate shortest distance to border ===
    md = 8.0;

    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec2 g = mg + vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;

        // Skip self
        if (dot(mr - r, mr - r) > 0.00001)
            // Distance to perpendicular bisector = midpoint projected onto direction vector
            md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
    }

    return vec3(md, mr);
}
```

### Step 5: Feature Point Animation

**What**: Make feature points move smoothly over time, producing organic dynamic effects.

**Why**: Static Voronoi is suitable for texture maps, but real-time effects usually require animation. Using `sin(iTime + 6.2831*hash)` makes each point oscillate at a different phase while staying within the [0,1] range.

**Code**:
```glsl
// Within the neighborhood search loop, replace static hash with animated version:
vec2 o = hash2(n + g);
o = 0.5 + 0.5 * sin(iTime + 6.2831 * o); // Animation: each point has a different phase
vec2 r = g - f + o;
```

### Step 6: Coloring and Visualization

**What**: Map Voronoi distance values to colors, rendering cell fills, border lines, and feature point markers.

**Why**: Different mapping methods produce dramatically different visual effects. Distance values can be used directly as grayscale, or transformed into rich colors through palette functions.

**Code**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Must use iTime, otherwise the compiler optimizes away this uniform
    float time = iTime * 1.0;
    vec2 p = fragCoord.xy / iResolution.xy;
    vec2 uv = p * SCALE; // SCALE controls cell density

    // Compute Voronoi
    vec2 c = voronoi(uv);
    float dist = c.x;   // F1 distance
    float id   = c.y;   // Cell ID

    // --- Cell coloring (ID-driven palette) ---
    vec3 col = 0.5 + 0.5 * cos(id * 6.2831 + vec3(0.0, 1.0, 2.0));

    // --- Distance falloff (cell center bright, edges dark) ---
    col *= clamp(1.0 - 0.4 * dist * dist, 0.0, 1.0);

    // --- Border lines (draw black line when distance below threshold) ---
    col -= (1.0 - smoothstep(0.08, 0.09, dist));

    fragColor = vec4(col, 1.0);
}
```

## Variant Detailed Descriptions

### Variant 1: 3D Voronoi + fBm Fire

Difference from base version: extends 2D Voronoi to 3D space, multi-layer fBm summation produces volumetric feel, combined with blackbody radiation palette for rendering fire/nebula.

Key modified code:
```glsl
#define NUM_OCTAVES 5  // Tunable: fBm layer count

vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

float voronoi3D(vec3 p) {
    vec3 g = floor(p);
    p = fract(p);
    float d = 1.0;

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++)
    for (int k = -1; k <= 1; k++) {
        vec3 b = vec3(i, j, k);
        vec3 r = b - p + hash3(g + b);
        d = min(d, dot(r, r));
    }
    return d;
}

float fbmVoronoi(vec3 p) {
    vec3 t = vec3(0.0, 0.0, p.z + iTime * 1.5);
    float tot = 0.0, sum = 0.0, amp = 1.0;
    for (int i = 0; i < NUM_OCTAVES; i++) {
        tot += voronoi3D(p + t) * amp;
        p *= 2.0;
        t *= 1.5; // Time frequency differs from spatial frequency -> parallax effect
        sum += amp;
        amp *= 0.5;
    }
    return tot / sum;
}

// Blackbody radiation palette
vec3 firePalette(float i) {
    float T = 1400.0 + 1300.0 * i;
    vec3 L = vec3(7.4, 5.6, 4.4);
    L = pow(L, vec3(5.0)) * (exp(1.43876719683e5 / (T * L)) - 1.0);
    return 1.0 - exp(-5e8 / L);
}
```

### Variant 2: Rounded Borders (3rd-Order Voronoi)

Difference from base version: simultaneously tracks F1, F2, and F3 (three nearest distances), using a harmonic mean formula to produce smoother, more uniform cell boundaries instead of standard Voronoi's sharp intersections.

Key modified code:
```glsl
float voronoiRounded(vec2 p) {
    vec2 g = floor(p);
    p -= g;
    vec3 d = vec3(1.0); // d.x=F1, d.y=F2, d.z=F3

    for (int y = -1; y <= 1; y++)
    for (int x = -1; x <= 1; x++) {
        vec2 o = vec2(x, y);
        o += hash2(g + o) - p;
        float r = dot(o, o);

        // Maintain top 3 nearest distances simultaneously
        d.z = max(d.x, max(d.y, min(d.z, r))); // F3
        d.y = max(d.x, min(d.y, r));             // F2
        d.x = min(d.x, r);                       // F1
    }

    d = sqrt(d);

    // Harmonic mean formula -> rounded borders
    return min(2.0 / (1.0 / max(d.y - d.x, 0.001)
                    + 1.0 / max(d.z - d.x, 0.001)), 1.0);
}
```

### Variant 3: Voronoise (Unified Noise-Voronoi Framework)

Difference from base version: through two parameters `u` (jitter amount) and `v` (smoothness), continuously interpolates between Cell Noise, Perlin Noise, and Voronoi. Uses weighted accumulation instead of `min()` operation, requiring a 5x5 search range.

Key modified code:
```glsl
#define JITTER 1.0    // Tunable: 0=regular grid, 1=fully random
#define SMOOTH 0.0    // Tunable: 0=sharp Voronoi, 1=smooth noise

float voronoise(vec2 p, float u, float v) {
    float k = 1.0 + 63.0 * pow(1.0 - v, 6.0); // Smoothness kernel

    vec2 i = floor(p);
    vec2 f = fract(p);

    vec2 a = vec2(0.0);
    for (int y = -2; y <= 2; y++)
    for (int x = -2; x <= 2; x++) {
        vec2 g = vec2(x, y);
        vec3 o = hash3(i + g) * vec3(u, u, 1.0); // u controls jitter
        vec2 d = g - f + o.xy;
        float w = pow(1.0 - smoothstep(0.0, 1.414, length(d)), k);
        a += vec2(o.z * w, w); // Weighted accumulation
    }

    return a.x / a.y;
}

// hash3 needs to return vec3
vec3 hash3(vec2 p) {
    vec3 q = vec3(dot(p, vec2(127.1, 311.7)),
                  dot(p, vec2(269.5, 183.3)),
                  dot(p, vec2(419.2, 371.9)));
    return fract(sin(q) * 43758.5453);
}
```

### Variant 4: Crack Textures (Multi-Layer Recursive Voronoi)

Difference from base version: uses extended jitter range to generate irregular cells, two-pass algorithm for exact boundaries, then overlays Perlin fBm perturbation on crack paths. Multi-layer recursion (rotation + scaling) produces fractal crack networks.

Key modified code:
```glsl
#define CRACK_DEPTH 3.0    // Tunable: recursion depth
#define CRACK_WIDTH 0.0    // Tunable: crack width
#define CRACK_SLOPE 50.0   // Tunable: crack sharpness

// Extended jitter range makes cell shapes more irregular
float ofs = 0.5;
#define disp(p) (-ofs + (1.0 + 2.0 * ofs) * hash2(p))

// Main loop: multi-layer crack overlay
vec4 O = vec4(0.0);
vec2 U = uv;
for (float i = 0.0; i < CRACK_DEPTH; i++) {
    vec2 D = fbm22(U) * 0.67;           // fBm perturbation of crack paths
    vec3 H = voronoiBorder(U + D);       // Exact border distance
    float d = H.x;
    d = min(1.0, CRACK_SLOPE * pow(max(0.0, d - CRACK_WIDTH), 1.0));
    O += vec4(1.0 - d) / exp2(i);       // Layer weight decay
    U *= 1.5 * rot(0.37);               // Rotate + scale into next layer
}
```

### Variant 5: Tileable 3D Worley (Cloud Noise)

Difference from base version: implements domain wrapping via `mod()` to generate seamlessly tileable 3D Worley noise. Combined with Perlin-Worley remapping for volumetric cloud rendering. Uses high-quality integer hash.

Key modified code:
```glsl
#define TILE_FREQ 4.0  // Tunable: tiling frequency

float worleyTileable(vec3 uv, float freq) {
    vec3 id = floor(uv);
    vec3 p = fract(uv);
    float minDist = 1e4;

    for (float x = -1.0; x <= 1.0; x++)
    for (float y = -1.0; y <= 1.0; y++)
    for (float z = -1.0; z <= 1.0; z++) {
        vec3 offset = vec3(x, y, z);
        // mod() implements domain wrapping -> seamless tiling
        vec3 h = hash3_uint(mod(id + offset, vec3(freq))) * 0.5 + 0.5;
        h += offset;
        vec3 d = p - h;
        minDist = min(minDist, dot(d, d));
    }
    return 1.0 - minDist; // Inverted Worley
}

// Worley fBm (GPU Pro 7 cloud approach)
float worleyFbm(vec3 p, float freq) {
    return worleyTileable(p * freq, freq) * 0.625
         + worleyTileable(p * freq * 2.0, freq * 2.0) * 0.25
         + worleyTileable(p * freq * 4.0, freq * 4.0) * 0.125;
}

// Perlin-Worley remapping
float remap(float x, float a, float b, float c, float d) {
    return (((x - a) / (b - a)) * (d - c)) + c;
}
// cloud = remap(perlinNoise, worleyFbm - 1.0, 1.0, 0.0, 1.0);
```

## Performance Optimization Details

### 1. Avoid sqrt in Distance Comparisons

Use `dot(r,r)` (squared distance) during the comparison phase, only taking `sqrt` for the final output. Saves 9 `sqrt` calls per pixel.

### 2. Unroll 3D Voronoi Loops

GPUs are not efficient with deeply nested loops. The 3x3x3 loop for 3D can be manually unrolled along the z-axis:
```glsl
// Instead of 3-level nesting, manually unroll z=-1, 0, 1
for (int j = -1; j <= 1; j++)
for (int i = -1; i <= 1; i++) {
    b = vec3(i, j, -1); r = b - p + hash3(g+b); d = min(d, dot(r,r));
    b.z = 0.0;          r = b - p + hash3(g+b); d = min(d, dot(r,r));
    b.z = 1.0;          r = b - p + hash3(g+b); d = min(d, dot(r,r));
}
```

### 3. Minimize Search Range

- Basic F1: 3x3 is sufficient
- Exact border / rounded border: second pass needs 5x5
- Voronoise (smooth blending): needs 5x5 to cover kernel radius
- Extended jitter (`ofs>0`): must use 5x5
- Don't blindly use 5x5; searching 16 extra cells means 16 extra hash computations

### 4. Hash Function Selection

- `sin(dot(...))` hash: fastest, but insufficient precision on some GPUs
- Texture lookup hash (`textureLod(iChannel0, ...)`): high quality but requires texture resources
- Integer hash (`uvec3`): high quality without textures, but requires ES 3.0+

### 5. Layer Count Control for Multi-Layer fBm

Each additional fBm layer adds a complete Voronoi search. 3 layers usually provide sufficient detail, 5 layers is the visual upper limit, and beyond 5 layers is rarely worth the performance cost.

## Combination Suggestions in Detail

### 1. Voronoi + fBm Perturbation

Use fBm noise to perturb Voronoi input coordinates, producing organic, irregular cell shapes (like stone textures, magma):
```glsl
vec2 distorted_uv = uv + 0.5 * fbm22(uv * 2.0);
vec2 v = voronoi(distorted_uv * SCALE);
```

### 2. Voronoi + Bump Mapping

Use Voronoi distance values as a height map, compute normals via finite differences for pseudo-3D bump effects:
```glsl
float h0 = voronoiRounded(uv);
float hx = voronoiRounded(uv + vec2(0.004, 0.0));
float hy = voronoiRounded(uv + vec2(0.0, 0.004));
float bump = max(hx - h0, 0.0) * 16.0; // Simple bump value
```

### 3. Voronoi + Palette Mapping

Use cell ID or distance values to drive the cosine palette, quickly producing rich procedural colors:
```glsl
vec3 palette(float t) {
    return 0.5 + 0.5 * cos(6.2831 * (t + vec3(0.0, 0.33, 0.67)));
}
col = palette(cellId * 0.1 + iTime * 0.1);
```

### 4. Voronoi + Raymarching

Use Voronoi distance as part of an SDF in raymarching scenes to sculpt cellular surface textures or crack effects.

### 5. Multi-Scale Voronoi Stacking

Compute multiple Voronoi layers at different frequencies and stack them for rich detail. Low-frequency layers control large structures, high-frequency layers add fine detail:
```glsl
float detail = voronoiRounded(uv * 6.0);       // Main structure
float fine   = voronoiRounded(uv * 16.0) * 0.5; // Fine detail
float result = detail + fine * detail;           // Stacking (detail modulated by main structure)
```
