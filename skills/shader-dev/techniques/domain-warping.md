# Domain Warping

## Use Cases

- **Marble/jade textures**: multi-layer warping produces streaked stone textures
- **Fabric/silk appearance**: warping field creases simulate textile surfaces
- **Geological formations**: rock strata, lava flows, surface erosion
- **Gas giant atmospheres**: Jupiter-style banded circulation
- **Smoke/fire/explosions**: fluid effects combined with volumetric rendering
- **Abstract art backgrounds**: procedural organic patterns, suitable for UI backgrounds, music visualization
- **Electric current/plasma effects**: ridged FBM variant produces sharp arc patterns

Core advantage: relies only on math functions (no texture assets needed), outputs seamless tiling, animatable, GPU-friendly.

## Core Principles

Warp input coordinates with noise, then query the main function:

```
f(p) -> f(p + fbm(p))
```

Classic multi-layer recursive nesting:

```
result = fbm(p + fbm(p + fbm(p)))
```

Each FBM layer's output serves as a coordinate offset for the next layer; deeper nesting produces more organic deformation.

**Key mathematical structure**:

1. **Noise** `noise(p)`: pseudo-random values at integer lattice points + Hermite interpolation `f*f*(3.0-2.0*f)`
2. **FBM**: `fbm(p) = sum of (0.5^i) * noise(p * 2^i * R^i)`, where `R` is a rotation matrix for decorrelation
3. **Domain warping chain**: `fbm(p + fbm(p + fbm(p)))`

The rotation matrix `mat2(0.80, 0.60, -0.60, 0.80)` (approx 36.87 deg) is the most widely used decorrelation transform.

## Implementation Steps

### Step 1: Hash Function

```glsl
// Map 2D integer coordinates to a pseudo-random float
float hash(vec2 p) {
    p = fract(p * 0.6180339887); // golden ratio pre-perturbation
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}
```

> The classic `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)` also works; the sin-free version above has more stable precision on some GPUs.

### Step 2: Value Noise

```glsl
// Hash values at integer lattice points, Hermite smooth interpolation
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}
```

### Step 3: FBM

```glsl
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80); // rotation approx 36.87 deg

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875;
}
```

> Lacunarity uses 2.01~2.04 rather than exactly 2.0 to avoid visual artifacts caused by lattice regularity.

### Step 4: Domain Warping (Core)

```glsl
// Classic three-layer domain warping
float pattern(vec2 p) {
    return fbm(p + fbm(p + fbm(p)));
}
```

### Step 5: Time Animation

```glsl
// Inject time into the first and last octaves: low frequency drives overall flow, high frequency adds detail variation
float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p + iTime);       // lowest frequency: slow overall flow
    p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p + sin(iTime));  // highest frequency: subtle detail motion
    return f / 0.96875;
}
```

### Step 6: Coloring

```glsl
// Map scalar field (0~1) to color using a mix chain
// IMPORTANT: Note: GLSL is strictly typed. Variable declarations must be complete, e.g. vec3 col = vec3(0.2, 0.1, 0.4)
// IMPORTANT: Decimals must be written as 0.x, not .x (division by zero errors)
vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);                               // deep purple base
    col = mix(col, vec3(0.3, 0.05, 0.05), t);                     // dark red
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);                   // high values toward white
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t)); // blue highlight
    return col * t * 2.0;
}
```

## Full Code Template

```glsl
// Domain Warping — Full Runnable Template (ShaderToy)

#define WARP_DEPTH 3        // Warp nesting depth (1=subtle, 2=moderate, 3=classic)
#define NUM_OCTAVES 6       // FBM octave count (4=coarse fast, 6=fine)
#define TIME_SCALE 1.0      // Animation speed (0.05=very slow, 1.0=fluid, 2.0=fast)
#define WARP_STRENGTH 1.0   // Warp intensity (0.5=subtle, 1.0=standard, 2.0=strong)
#define BASE_SCALE 3.0      // Overall noise scale (larger = denser texture)

const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80);

float hash(vec2 p) {
    p = fract(p * 0.6180339887);
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}

float fbm(vec2 p) {
    float f = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    float norm = 0.0;

    for (int i = 0; i < NUM_OCTAVES; i++) {
        float t = 0.0;
        if (i == 0) t = iTime * TIME_SCALE;
        if (i == NUM_OCTAVES - 1) t = sin(iTime * TIME_SCALE);

        f += amp * noise(p + t);
        norm += amp;
        p = mtx * p * 2.02;
        amp *= 0.5;
    }
    return f / norm;
}

float pattern(vec2 p) {
    float val = fbm(p);

    #if WARP_DEPTH >= 2
    val = fbm(p + WARP_STRENGTH * val);
    #endif

    #if WARP_DEPTH >= 3
    val = fbm(p + WARP_STRENGTH * val);
    #endif

    return val;
}

vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);
    col = mix(col, vec3(0.3, 0.05, 0.05), t);
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t));
    return col * t * 2.0;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    uv *= BASE_SCALE;

    float shade = pattern(uv);
    vec3 col = palette(shade);

    // Vignette effect
    vec2 q = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * sqrt(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y));

    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Multi-Resolution Layered Warping

Different warp layers use FBM with different octave counts, outputting `vec2` for dual-axis displacement, with intermediate variables used for coloring.

```glsl
float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;
}

float fbm6(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875;
}

vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));
}
vec2 fbm6_2(vec2 p) {
    return vec2(fbm6(p + vec2(9.2)), fbm6(p + vec2(5.7)));
}

float func(vec2 q, out vec2 o, out vec2 n) {
    q += 0.05 * sin(vec2(0.11, 0.13) * iTime + length(q) * 4.0);
    o = 0.5 + 0.5 * fbm4_2(q);
    o += 0.02 * sin(vec2(0.13, 0.11) * iTime * length(o));
    n = fbm6_2(4.0 * o);
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p);
    f = mix(f, f * f * f * 3.5, f * abs(n.x));
    return f;
}

// Coloring uses intermediate variables o, n
vec3 col = vec3(0.2, 0.1, 0.4);
col = mix(col, vec3(0.3, 0.05, 0.05), f);
col = mix(col, vec3(0.9, 0.9, 0.9), dot(n, n));
col = mix(col, vec3(0.5, 0.2, 0.2), 0.5 * o.y * o.y);
col = mix(col, vec3(0.0, 0.2, 0.4), 0.5 * smoothstep(1.2, 1.3, abs(n.y) + abs(n.x)));
col *= f * 2.0;
```

### Variant 2: Turbulence/Ridged Warping (Electric Arc/Plasma Effect)

In FBM, apply `abs(noise - 0.5)` to produce ridged textures, with dual-axis independent displacement + time-reversed drift.

```glsl
float fbm_ridged(vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        rz += abs((noise(p) - 0.5) * 2.0) / z;
        z *= 2.0;
        p *= 2.0;
    }
    return rz;
}

float dualfbm(vec2 p) {
    vec2 p2 = p * 0.7;
    vec2 basis = vec2(
        fbm_ridged(p2 - iTime * 0.24),
        fbm_ridged(p2 + iTime * 0.26)
    );
    basis = (basis - 0.5) * 0.2;
    p += basis;
    return fbm_ridged(p * makem2(iTime * 0.03));
}

// Electric arc coloring
vec3 col = vec3(0.2, 0.1, 0.4) / rz;
```

### Variant 3: Pseudo-3D Lit Domain Warping

Estimate screen-space normals via finite differences, apply directional lighting for an embossed effect.

```glsl
float e = 2.0 / iResolution.y;
vec3 nor = normalize(vec3(
    pattern(p + vec2(e, 0.0)) - shade,
    2.0 * e,
    pattern(p + vec2(0.0, e)) - shade
));

vec3 lig = normalize(vec3(0.9, 0.2, -0.4));
float dif = clamp(0.3 + 0.7 * dot(nor, lig), 0.0, 1.0);
vec3 lin = vec3(0.70, 0.90, 0.95) * (nor.y * 0.5 + 0.5);
lin += vec3(0.15, 0.10, 0.05) * dif;

col *= 1.2 * lin;
col = 1.0 - col;
col = 1.1 * col * col;
```

### Variant 4: Flow Field Iterative Warping (Gas Giant Effect)

Compute the FBM gradient field, Euler-integrate to iteratively advect coordinates, simulating fluid convection vortices.

```glsl
#define ADVECT_ITERATIONS 5

vec2 field(vec2 p) {
    float t = 0.2 * iTime;
    p.x += t;
    float n = fbm(p, t);
    float e = 0.25;
    float nx = fbm(p + vec2(e, 0.0), t);
    float ny = fbm(p + vec2(0.0, e), t);
    return vec2(n - ny, nx - n) / e;
}

vec3 distort(vec2 p) {
    for (float i = 0.0; i < float(ADVECT_ITERATIONS); i++) {
        p += field(p) / float(ADVECT_ITERATIONS);
    }
    return vec3(fbm(p, 0.0));
}
```

### Variant 5: 3D Volumetric Domain Warping (Explosion/Fireball Effect)

Displace a sphere SDF with 3D FBM, rendered via volumetric ray marching.

```glsl
#define NOISE_FREQ 4.0
#define NOISE_AMP -0.5

mat3 m3 = mat3(0.00, 0.80, 0.60,
              -0.80, 0.36,-0.48,
              -0.60,-0.48, 0.64);

float noise3D(vec3 p) {
    vec3 fl = floor(p);
    vec3 fr = fract(p);
    fr = fr * fr * (3.0 - 2.0 * fr);
    float n = fl.x + fl.y * 157.0 + 113.0 * fl.z;
    return mix(mix(mix(hash(n+0.0),   hash(n+1.0),   fr.x),
                   mix(hash(n+157.0), hash(n+158.0), fr.x), fr.y),
               mix(mix(hash(n+113.0), hash(n+114.0), fr.x),
                   mix(hash(n+270.0), hash(n+271.0), fr.x), fr.y), fr.z);
}

float fbm3D(vec3 p) {
    float f = 0.0;
    f += 0.5000 * noise3D(p); p = m3 * p * 2.02;
    f += 0.2500 * noise3D(p); p = m3 * p * 2.03;
    f += 0.1250 * noise3D(p); p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p); p = m3 * p * 2.02;
    f += 0.03125 * abs(noise3D(p));
    return f / 0.9375;
}

float distanceFunc(vec3 p, out float displace) {
    float d = length(p) - 0.5;
    displace = fbm3D(p * NOISE_FREQ + vec3(0, -1, 0) * iTime);
    d += displace * NOISE_AMP;
    return d;
}
```

## Performance & Composition

### Performance Tips

- Three warp layers x 6 octaves = 18 noise samples per pixel; adding lit finite differences can reach 54
- **Reduce octaves**: 4 instead of 6, ~33% performance gain with minimal visual difference
- **Reduce warp depth**: two layers `fbm(p + fbm(p))` is already organic enough, saving ~33%
- **sin-product noise**: `sin(p.x)*sin(p.y)` is branchless and memory-free, suitable for mobile
- **GPU built-in derivatives**: `dFdx/dFdy` instead of finite differences, 3x faster
- **Texture noise**: pre-bake noise textures, trading computation for memory reads
- **LOD adaptive**: reduce octave count for distant pixels
- **Supersampling**: only use 2x2 when anti-aliasing is needed, 4x performance cost

### Composition Suggestions

- **Ray marching**: warped scalar field as SDF displacement function -> fire, explosions, organic forms
- **Polar coordinate transform**: domain warping in polar space -> vortices, nebulae, spirals
- **Cosine palette**: `a + b*cos(2*pi*(c*t+d))` is more flexible than mix chains
- **Post-processing**: bloom glow, tone mapping `col/(1+col)`, chromatic aberration (RGB channel offset sampling)
- **Particles/geometry**: scalar field driving particle velocity fields, vertex displacement, UV animation

## Further Reading

Full step-by-step tutorials, mathematical derivations, and advanced usage in [reference](../reference/domain-warping.md)
