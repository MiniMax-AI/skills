- **IMPORTANT:** All declared `uniform` variables must be used in the shader code, otherwise the compiler will optimize them away. After optimization, `gl.getUniformLocation()` returns `null`, and setting that uniform triggers a WebGL `INVALID_OPERATION` error, which may cause rendering failure. Ensure uniforms like `iTime` are actually used in `main()` (e.g., `float t = iTime * 1.0;`)

# Voronoi & Cellular Noise

## Use Cases
- Natural textures: cells, cracked soil, stone, skin pores
- Structured patterns: crystals, honeycombs, shattered glass, mosaics
- Effects: fire/nebula (fBm stacking), crack generation
- Procedural materials: cloud noise, terrain height maps, stylized partitioning

## Core Principles

Voronoi noise = **spatial partitioning**: scatter feature points, assign each pixel to the "cell" of its nearest feature point.

Algorithm flow:
1. `floor` divides into an integer grid; each cell contains a randomly offset feature point
2. Search the 3x3 (2D) or 3x3x3 (3D) neighborhood for all feature points
3. Record the nearest distance F1 (optionally second-nearest F2)
4. Map F1, F2, or F2-F1 to color/height/shape

Distance metrics:
- Euclidean: `dot(r,r)` (squared, fast) -> final `sqrt`
- Manhattan: `abs(r.x)+abs(r.y)`
- Chebyshev: `max(abs(r.x), abs(r.y))`

Exact border distance (two-pass algorithm): `dot(0.5*(mr+r), normalize(r-mr))`
Rounded borders (harmonic mean): `1/(1/(d2-d1) + 1/(d3-d1))`

## Implementation Steps

### Step 1: Hash Functions

```glsl
// sin-dot hash (suitable for most cases)
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// 3D version
vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

// High-quality integer hash (ES 3.0+, more uniform)
vec3 hash3_uint(vec3 p) {
    uvec3 q = uvec3(ivec3(p)) * uvec3(1597334673U, 3812015801U, 2798796415U);
    q = (q.x ^ q.y ^ q.z) * uvec3(1597334673U, 3812015801U, 2798796415U);
    return vec3(q) / float(0xffffffffU);
}
```

### Step 2: Basic F1 Voronoi

```glsl
// Returns (F1 distance, cell ID)
vec2 voronoi(vec2 x) {
    vec2 n = floor(x);
    vec2 f = fract(x);
    vec3 m = vec3(8.0);

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = hash2(n + g);
        vec2 r = g - f + o;
        float d = dot(r, r);
        if (d < m.x) {
            m = vec3(d, o);
        }
    }
    return vec2(sqrt(m.x), m.y + m.z);
}
```

### Step 3: F1 + F2 (Edge Detection)

```glsl
// Returns vec2(F1, F2), edge value = F2 - F1
vec2 voronoi_f1f2(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 res = vec2(8.0);

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 b = vec2(i, j);
        vec2 r = b - f + hash2(p + b);
        float d = dot(r, r);
        if (d < res.x) {
            res.y = res.x;
            res.x = d;
        } else if (d < res.y) {
            res.y = d;
        }
    }
    return sqrt(res);
}
```

### Step 4: Exact Border Distance (Two-Pass Algorithm)

```glsl
// Returns vec3(border distance, nearest point offset)
vec3 voronoi_border(vec2 x) {
    vec2 ip = floor(x);
    vec2 fp = fract(x);

    // First pass: find nearest feature point
    vec2 mg, mr;
    float md = 8.0;
    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;
        float d = dot(r, r);
        if (d < md) { md = d; mr = r; mg = g; }
    }

    // Second pass: exact border distance (5x5 range)
    md = 8.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec2 g = mg + vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;
        if (dot(mr - r, mr - r) > 0.00001)
            md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
    }
    return vec3(md, mr);
}
```

### Step 5: Feature Point Animation

```glsl
// Replace static hash inside the neighborhood search loop:
vec2 o = hash2(n + g);
o = 0.5 + 0.5 * sin(iTime + 6.2831 * o); // different phase per point
vec2 r = g - f + o;
```

### Step 6: Coloring & Visualization

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Must use iTime, otherwise the compiler will optimize away the uniform
    float time = iTime * 1.0;
    vec2 p = fragCoord.xy / iResolution.xy;
    vec2 uv = p * SCALE;

    vec2 c = voronoi(uv);
    float dist = c.x;
    float id   = c.y;

    // Cell coloring (ID-driven palette)
    vec3 col = 0.5 + 0.5 * cos(id * 6.2831 + vec3(0.0, 1.0, 2.0));
    // Distance falloff
    col *= clamp(1.0 - 0.4 * dist * dist, 0.0, 1.0);
    // Border lines
    col -= (1.0 - smoothstep(0.08, 0.09, dist));

    fragColor = vec4(col, 1.0);
}
```

## Complete Code Template

```glsl
// === Voronoi Cellular Noise — Complete ShaderToy Template ===
// Supports F1/F2/F2-F1 modes, multiple distance metrics, animation, exact borders

#define SCALE 8.0            // Cell density
#define ANIMATE 1            // 0=static, 1=animated
#define MODE 0               // 0=F1 fill, 1=F2-F1 edges, 2=exact borders
#define DIST_METRIC 0        // 0=Euclidean, 1=Manhattan, 2=Chebyshev

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

float distFunc(vec2 r) {
    #if DIST_METRIC == 0
        return dot(r, r);
    #elif DIST_METRIC == 1
        return abs(r.x) + abs(r.y);
    #elif DIST_METRIC == 2
        return max(abs(r.x), abs(r.y));
    #endif
}

vec2 getPoint(vec2 cellId) {
    vec2 o = hash2(cellId);
    #if ANIMATE
        o = 0.5 + 0.5 * sin(iTime + 6.2831 * o);
    #endif
    return o;
}

vec4 voronoi(vec2 x) {
    vec2 n = floor(x);
    vec2 f = fract(x);
    float d1 = 8.0, d2 = 8.0;
    vec2 nearestCell = vec2(0.0);

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = getPoint(n + g);
        vec2 r = g - f + o;
        float d = distFunc(r);
        if (d < d1) {
            d2 = d1; d1 = d;
            nearestCell = n + g;
        } else if (d < d2) {
            d2 = d;
        }
    }

    #if DIST_METRIC == 0
        d1 = sqrt(d1); d2 = sqrt(d2);
    #endif
    return vec4(d1, d2, nearestCell);
}

vec3 voronoiBorder(vec2 x) {
    vec2 ip = floor(x);
    vec2 fp = fract(x);

    vec2 mg, mr;
    float md = 8.0;
    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = getPoint(ip + g);
        vec2 r = g + o - fp;
        float d = dot(r, r);
        if (d < md) { md = d; mr = r; mg = g; }
    }

    md = 8.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec2 g = mg + vec2(float(i), float(j));
        vec2 o = getPoint(ip + g);
        vec2 r = g + o - fp;
        if (dot(mr - r, mr - r) > 0.00001)
            md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
    }
    return vec3(md, mr);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Must use iTime, otherwise the compiler will optimize away the uniform (especially important when ANIMATE=1)
    float time = iTime * 1.0;
    vec2 p = fragCoord.xy / iResolution.xy;
    p.x *= iResolution.x / iResolution.y;
    vec2 uv = p * SCALE;
    vec3 col = vec3(0.0);

    #if MODE == 0
        vec4 v = voronoi(uv);
        float id = dot(v.zw, vec2(127.1, 311.7));
        col = 0.5 + 0.5 * cos(id * 6.2831 + vec3(0.0, 1.0, 2.0));
        col *= clamp(1.0 - 0.4 * v.x * v.x, 0.0, 1.0);
        col -= (1.0 - smoothstep(0.08, 0.09, v.x));
    #elif MODE == 1
        vec4 v = voronoi(uv);
        float edge = v.y - v.x;
        col = vec3(1.0 - smoothstep(0.0, 0.15, edge));
        col *= vec3(0.2, 0.6, 1.0);
    #elif MODE == 2
        vec3 c = voronoiBorder(uv);
        col = c.x * (0.5 + 0.5 * sin(64.0 * c.x)) * vec3(1.0);
        col = mix(vec3(1.0, 0.6, 0.0), col, smoothstep(0.04, 0.07, c.x));
        float dd = length(c.yz);
        col = mix(vec3(1.0, 0.6, 0.1), col, smoothstep(0.0, 0.12, dd));
    #endif

    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: 3D Voronoi + fBm Fire

```glsl
#define NUM_OCTAVES 5

vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

float voronoi3D(vec3 p) {
    vec3 g = floor(p); p = fract(p);
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
        p *= 2.0; t *= 1.5;
        sum += amp; amp *= 0.5;
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

```glsl
float voronoiRounded(vec2 p) {
    vec2 g = floor(p); p -= g;
    vec3 d = vec3(1.0); // F1, F2, F3

    for (int y = -1; y <= 1; y++)
    for (int x = -1; x <= 1; x++) {
        vec2 o = vec2(x, y);
        o += hash2(g + o) - p;
        float r = dot(o, o);
        d.z = max(d.x, max(d.y, min(d.z, r)));
        d.y = max(d.x, min(d.y, r));
        d.x = min(d.x, r);
    }
    d = sqrt(d);
    return min(2.0 / (1.0 / max(d.y - d.x, 0.001)
                    + 1.0 / max(d.z - d.x, 0.001)), 1.0);
}
```

### Variant 3: Voronoise (Unified Noise-Voronoi Framework)

```glsl
#define JITTER 1.0    // 0=regular grid, 1=fully random
#define SMOOTH 0.0    // 0=sharp Voronoi, 1=smooth noise

vec3 hash3(vec2 p) {
    vec3 q = vec3(dot(p, vec2(127.1, 311.7)),
                  dot(p, vec2(269.5, 183.3)),
                  dot(p, vec2(419.2, 371.9)));
    return fract(sin(q) * 43758.5453);
}

float voronoise(vec2 p, float u, float v) {
    float k = 1.0 + 63.0 * pow(1.0 - v, 6.0);
    vec2 i = floor(p); vec2 f = fract(p);
    vec2 a = vec2(0.0);
    for (int y = -2; y <= 2; y++)
    for (int x = -2; x <= 2; x++) {
        vec2 g = vec2(x, y);
        vec3 o = hash3(i + g) * vec3(u, u, 1.0);
        vec2 d = g - f + o.xy;
        float w = pow(1.0 - smoothstep(0.0, 1.414, length(d)), k);
        a += vec2(o.z * w, w);
    }
    return a.x / a.y;
}
```

### Variant 4: Crack Texture (Multi-Layer Recursive Voronoi)

```glsl
#define CRACK_DEPTH 3.0
#define CRACK_WIDTH 0.0
#define CRACK_SLOPE 50.0

float ofs = 0.5;
#define disp(p) (-ofs + (1.0 + 2.0 * ofs) * hash2(p))

// Main loop
vec4 O = vec4(0.0);
vec2 U = uv;
for (float i = 0.0; i < CRACK_DEPTH; i++) {
    vec2 D = fbm22(U) * 0.67;
    vec3 H = voronoiBorder(U + D);
    float d = H.x;
    d = min(1.0, CRACK_SLOPE * pow(max(0.0, d - CRACK_WIDTH), 1.0));
    O += vec4(1.0 - d) / exp2(i);
    U *= 1.5 * rot(0.37);
}
```

### Variant 5: Tileable 3D Worley (Cloud Noise)

```glsl
#define TILE_FREQ 4.0

float worleyTileable(vec3 uv, float freq) {
    vec3 id = floor(uv); vec3 p = fract(uv);
    float minDist = 1e4;
    for (float x = -1.0; x <= 1.0; x++)
    for (float y = -1.0; y <= 1.0; y++)
    for (float z = -1.0; z <= 1.0; z++) {
        vec3 offset = vec3(x, y, z);
        vec3 h = hash3_uint(mod(id + offset, vec3(freq))) * 0.5 + 0.5;
        h += offset;
        vec3 d = p - h;
        minDist = min(minDist, dot(d, d));
    }
    return 1.0 - minDist;
}

float worleyFbm(vec3 p, float freq) {
    return worleyTileable(p * freq, freq) * 0.625
         + worleyTileable(p * freq * 2.0, freq * 2.0) * 0.25
         + worleyTileable(p * freq * 4.0, freq * 4.0) * 0.125;
}

float remap(float x, float a, float b, float c, float d) {
    return (((x - a) / (b - a)) * (d - c)) + c;
}
// cloud = remap(perlinNoise, worleyFbm - 1.0, 1.0, 0.0, 1.0);
```

## Performance & Composition

**Performance:**
- Use `dot(r,r)` instead of `length` during comparison; only `sqrt` for final output
- 3D loops can be manually unrolled along the z-axis to reduce nesting
- Search range: basic F1 uses 3x3; exact borders/Voronoise/extended jitter uses 5x5
- Hash choice: `sin(dot(...))` is fastest; integer hash is more uniform but requires ES 3.0+
- fBm layers: 3 is sufficient, 5 is the upper limit

**Combinations:**
- **+fBm distortion**: `uv + 0.5*fbm22(uv*2.0)` -> organic cell shapes
- **+Bump Mapping**: finite-difference normal computation -> pseudo-3D bumps
- **+Palette**: `0.5+0.5*cos(6.2831*(t+vec3(0,0.33,0.67)))` -> rich colors
- **+Raymarching**: Voronoi distance as part of the SDF -> cellular surfaces
- **+Multi-scale stacking**: Voronoi at different frequencies stacked -> primary structure + fine detail

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/voronoi-cellular-noise.md)
