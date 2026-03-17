# Procedural Noise — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL Basics**: uniform, varying, built-in functions (`fract`, `floor`, `mix`, `smoothstep`, `dot`, `sin`/`cos`)
- **Vector Math**: dot product, cross product, matrix multiplication (`mat2` rotation matrix)
- **Coordinate Spaces**: UV coordinate normalization, screen aspect ratio correction
- **Interpolation Theory**: linear interpolation, Hermite interpolation `3t^2-2t^3` (smoothstep)
- **ShaderToy Environment**: `iTime`, `iResolution`, `fragCoord`, `mainImage` signature

## Use Cases in Detail

Procedural noise is the most fundamental and versatile technique in real-time GPU graphics, applicable to:

- **Natural phenomena simulation**: fire, clouds, water surfaces, lava, lightning, smoke, etc.
- **Terrain generation**: mountains, canyons, erosion landscapes, snowline distribution
- **Texture synthesis**: marble textures, wood grain, organic patterns, abstract art
- **Volume rendering**: volumetric clouds, volumetric fog, light scattering
- **Motion effects**: fluid simulation approximation, particle trajectory perturbation, domain warping animation

Core idea: instead of using pre-made textures, generate pseudo-random, spatially continuous signals in real-time on the GPU through mathematical functions, then produce rich multi-scale detail through fractal summation (FBM) and Domain Warping.

## Core Principles in Detail

### 1. Noise Functions — Building Continuous Pseudo-Random Signals

The essence of a noise function is: **generate random values at integer lattice points, then smoothly interpolate between them**.

Two mainstream implementations:

**Value Noise**: each lattice point stores a random scalar, bilinear interpolation yields a continuous field.
- Formula: `N(p) = mix(mix(h00, h10, u), mix(h01, h11, u), v)`, where `u,v` are the fractional parts after Hermite smoothing

**Simplex Noise**: uses gradient dot products + radial falloff kernels on a triangular lattice (2D) or tetrahedral lattice (3D).
- Advantages: fewer lattice lookups (2D: 3 vs 4), no axis-aligned artifacts, lower computational cost
- Core: skew transform maps square grid to triangular grid, using `K1=(sqrt(3)-1)/2` for skewing, `K2=(3-sqrt(3))/6` for unskewing

### 2. Hash Functions — Source of Lattice Random Values

Hash functions map integer coordinates to pseudo-random values in [0,1] or [-1,1]:

- **sin-based hash** (classic but has precision risks): `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)`
- **sin-free hash** (cross-platform stable): pure arithmetic `fract(p * 0.1031)` + `dot` mixing + `fract` output

### 3. FBM (Fractional Brownian Motion) — Multi-Scale Detail Summation

Sum multiple noise "octaves" at different frequencies and amplitudes:

```
FBM(p) = sum( amplitude_i * noise(frequency_i * p) )
```

Standard parameters:
- **Lacunarity (frequency multiplier)**: each octave's frequency multiplied by ~2.0
- **Persistence/Gain (amplitude decay)**: each octave's amplitude multiplied by ~0.5
- **Inter-octave rotation**: use a rotation matrix to eliminate axis-aligned artifacts

### 4. Domain Warping — Organic Distortion

Feed the output of noise back as coordinate offsets, producing distorted organic patterns:
- **Single-layer warping**: `fbm(p + fbm(p))`
- **Multi-layer cascade**: `fbm(p + fbm(p + fbm(p)))` — classic three-layer domain warping

### 5. FBM Variants — Different Visual Characteristics

| Variant | Formula | Visual Effect |
|---------|---------|---------------|
| Standard FBM | `sum( a*noise(p) )` | Smooth, soft (cloud interiors) |
| Ridged FBM | `sum( a*abs(noise(p)) )` | Sharp creases (ridges, lightning) |
| Sinusoidal ridged | `sum( a*sin(noise(p)*k) )` | Periodic ridges (lava) |
| Erosion FBM | `sum( a*noise(p)/(1+dot(d,d)) )` | Smooth ridges, fine valleys (terrain) |
| Sea wave FBM | `sum( a*octave_fn(p) )` | Sharp wave crests (ocean surface) |

## Step-by-Step Implementation Details

### Step 1: Hash Function

**What**: Implement a hash function that maps 2D integer coordinates to pseudo-random values.

**Why**: Hashing is the fundamental building block of all noise. The sin-free version is stable across GPUs; the sin version is more concise.

**Code (sin-free version)**:
```glsl
// 2D -> 1D hash, sin-free, cross-platform stable
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// 2D -> 2D hash (for gradient noise)
vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}
```

**Code (classic sin version)**:
```glsl
float hash(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));
    return fract(sin(h) * 43758.5453123);
}

// Gradient version, output [-1, 1]
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}
```

### Step 2: Value Noise

**What**: Perform Hermite-smoothed interpolation between hashed values at integer lattice points to obtain a continuous 2D noise field.

**Why**: Value noise is the simplest noise implementation with minimal code, suitable as a foundation for FBM and domain warping. Using the `smoothstep` polynomial `3t^2-2t^3` directly guarantees C1 continuity (no seam discontinuities).

**Code**:
```glsl
float noise(in vec2 x) {
    vec2 p = floor(x);    // Integer lattice point
    vec2 f = fract(x);    // Fractional part within cell
    f = f * f * (3.0 - 2.0 * f);  // Hermite smoothing (can substitute quintic: 6t^5-15t^4+10t^3)
    float a = hash(p + vec2(0.0, 0.0));
    float b = hash(p + vec2(1.0, 0.0));
    float c = hash(p + vec2(0.0, 1.0));
    float d = hash(p + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);  // Bilinear interpolation
}
```

### Step 3: Simplex Noise

**What**: Use gradient dot products and radial falloff kernels on a triangular grid to generate isotropic 2D noise.

**Why**: Compared to value noise, Simplex Noise has no axis-aligned artifacts, lower computational cost (2D requires only 3 lattice points instead of 4), and higher visual quality. Suitable for scenarios requiring high-quality noise (fire, clouds).

**Code**:
```glsl
float noise(in vec2 p) {
    const float K1 = 0.366025404;  // (sqrt(3)-1)/2 — skew factor
    const float K2 = 0.211324865;  // (3-sqrt(3))/6 — unskew factor

    vec2 i = floor(p + (p.x + p.y) * K1);  // Skew to triangular grid

    vec2 a = p - i + (i.x + i.y) * K2;     // Vertex 0 offset
    vec2 o = (a.x > a.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);  // Determine which triangle
    vec2 b = a - o + K2;                    // Vertex 1 offset
    vec2 c = a - 1.0 + 2.0 * K2;           // Vertex 2 offset

    vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);  // Radial falloff
    vec3 n = h * h * h * h * vec3(  // h^4 kernel * gradient dot product
        dot(a, hash2(i + 0.0)),
        dot(b, hash2(i + o)),
        dot(c, hash2(i + 1.0))
    );
    return dot(n, vec3(70.0));  // Normalize to ~[-1, 1]
}
```

### Step 4: Standard FBM (Fractional Brownian Motion)

**What**: Sum multiple octaves of noise with decreasing amplitudes to obtain a multi-scale fractal signal.

**Why**: A single noise octave has a single frequency and cannot produce the multi-scale detail found in nature. FBM simulates fractal self-similarity by summing noise at different frequencies. **The inter-octave rotation matrix is a key technique** that breaks axis-aligned artifacts.

**Code (4-octave loop version)**:
```glsl
#define OCTAVES 4           // Tunable: number of octaves (1-8), more = richer detail but more expensive
#define GAIN 0.5            // Tunable: amplitude decay (0.3-0.7), higher = more prominent high frequencies
#define LACUNARITY 2.0      // Tunable: frequency multiplier (1.5-3.0), higher = larger gap between octaves

float fbm(vec2 p) {
    // Encodes both rotation and scaling, eliminates axis-aligned artifacts
    // |m| = sqrt(1.6^2+1.2^2) = 2.0, rotation angle ~ 36.87 degrees
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);

    float f = 0.0;
    float a = 0.5;   // Initial amplitude
    for (int i = 0; i < OCTAVES; i++) {
        f += a * noise(p);
        p = m * p;    // Rotation + frequency scaling
        a *= GAIN;    // Amplitude decay
    }
    return f;
}
```

**Manually unrolled version (with slightly varying lacunarity)**:
```glsl
// Slightly varying lacunarity (2.01, 2.02, 2.03...) breaks exact self-similarity
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80);  // Pure rotation ~36.87 degrees

float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;  // Normalization
}
```

### Step 5: Ridged FBM

**What**: Take the absolute value of noise before summation, producing sharp "ridges" at zero crossings.

**Why**: Standard FBM produces overly smooth patterns and cannot represent sharp structures like lightning, mountain ridges, or cracks. The `abs()` operation folds the noise's zero crossings into sharp V-shaped ridge lines.

**Code**:
```glsl
float fbm_ridged(in vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        // abs((noise-0.5)*2) maps [0,1] to a V-shape in [0,1]
        rz += abs((noise(p) - 0.5) * 2.0) / z;
        z *= 2.0;   // Amplitude decay (1/z)
        p *= 2.0;   // Frequency scaling
    }
    return rz;
}
```

**Sinusoidal ridged variant**:
```glsl
// sin(noise*7) produces smoother periodic ridges, suitable for lava textures
rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;
```

### Step 6: Domain Warping

**What**: Use the output of noise/FBM to distort the input coordinates of subsequent noise, producing organic distortion patterns.

**Why**: Domain warping is the core technique for producing "painterly", "ink wash", "geological" and other organic patterns. The number of nested warping layers controls complexity.

**Basic domain warping**:
```glsl
// Low-frequency FBM as offset to distort subsequent sampling
float q = fbm(uv * 0.5);   // Low-frequency domain warping field
uv -= q - time;             // Use q to offset sampling coordinates
float f = fbm(uv);          // Sample at warped coordinates
```

**Classic three-layer cascaded domain warping**:
```glsl
// Two independent FBMs produce decorrelated vec2 offsets
vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));  // Different offsets for decorrelation
}

float func(vec2 q, out vec2 o, out vec2 n) {
    // Layer 1: q -> 4-octave FBM -> 2D offset field o
    o = 0.5 + 0.5 * fbm4_2(q);

    // Layer 2: o -> 6-octave FBM -> 2D offset field n (higher frequency)
    n = fbm6_2(4.0 * o);

    // Layer 3: original coordinates + offsets -> final FBM sampling
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p);

    // Contrast enhancement: boost contrast in heavily warped areas
    f = mix(f, f * f * f * 3.5, f * abs(n.x));
    return f;
}
```

**Dual-axis FBM domain warping**:
```glsl
float dualfbm(in vec2 p) {
    vec2 p2 = p * 0.7;
    // Two independent FBMs offset X/Y axes separately, different time offsets avoid symmetry
    vec2 basis = vec2(fbm(p2 - time * 1.6), fbm(p2 + time * 1.7));
    basis = (basis - 0.5) * 0.2;  // Center + scale
    p += basis;
    return fbm(p * makem2(time * 0.2));  // Final sampling after rotation
}
```

### Step 7: Flow Noise

**What**: Apply independent gradient field displacement within each FBM octave, simulating fluid transport effects.

**Why**: Ordinary domain warping is "global" (distorting before or after FBM), while flow noise is "per-octave" — each frequency layer has its own flow direction and speed, producing extremely realistic lava and fluid effects.

**Code**:
```glsl
#define FLOW_SPEED 0.6       // Tunable: main flow speed
#define BASE_SPEED 1.9       // Tunable: base point flow speed
#define ADVECTION 0.77       // Tunable: advection factor (0.5=stable, 0.95=turbulent)
#define GRAD_SCALE 0.5       // Tunable: gradient displacement strength

// Noise gradient (central differences)
vec2 gradn(vec2 p) {
    float ep = 0.09;
    float gradx = noise(vec2(p.x + ep, p.y)) - noise(vec2(p.x - ep, p.y));
    float grady = noise(vec2(p.x, p.y + ep)) - noise(vec2(p.x, p.y - ep));
    return vec2(gradx, grady);
}

float flow(in vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    vec2 bp = p;  // Base point (prevents advection divergence)
    for (float i = 1.0; i < 7.0; i++) {
        p += time * FLOW_SPEED;                        // Main flow displacement
        bp += time * BASE_SPEED;                       // Base flow displacement
        vec2 gr = gradn(i * p * 0.34 + time * 1.0);   // Noise gradient field
        gr *= makem2(time * 6.0 - (0.05 * p.x + 0.03 * p.y) * 40.0);  // Spatially varying rotation
        p += gr * GRAD_SCALE;                          // Gradient displacement
        rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z; // Sinusoidal ridged accumulation
        p = mix(bp, p, ADVECTION);                     // Mix back to base (prevent divergence)
        z *= 1.4;   // Amplitude decay
        p *= 2.0;   // Frequency scaling
        bp *= 1.9;  // Base frequency scaling (slightly different)
    }
    return rz;
}
```

### Step 8: Derivative FBM

**What**: Track the analytical gradient of noise during FBM accumulation, using the accumulated gradient magnitude to suppress high-frequency detail in steep areas.

**Why**: This is a signature technique for terrain rendering. Standard FBM adds detail uniformly across all areas, but natural terrain has smooth ridges due to hydraulic erosion while valleys retain fine detail. Derivative FBM automatically simulates this erosion effect through the `1/(1+|gradient|^2)` factor.

**Code**:
```glsl
// Value noise with analytical derivative: returns vec3(value, d/dx, d/dy)
vec3 noised(in vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * (3.0 - 2.0 * f);           // Hermite interpolation
    vec2 du = 6.0 * f * (1.0 - f);               // Hermite derivative (analytical)

    float a = hash(p + vec2(0, 0));
    float b = hash(p + vec2(1, 0));
    float c = hash(p + vec2(0, 1));
    float d = hash(p + vec2(1, 1));

    return vec3(
        a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y,  // Value
        du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx)                  // Gradient
    );
}

#define TERRAIN_OCTAVES 16   // Tunable: terrain octave count (5-16), more = finer detail
#define TERRAIN_GAIN 0.5     // Tunable: amplitude decay

float terrainFBM(in vec2 x) {
    const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);  // Pure rotation ~36.87 degrees
    float a = 0.0;       // Accumulated value
    float b = 1.0;       // Current amplitude
    vec2 d = vec2(0.0);  // Accumulated gradient

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        vec3 n = noised(x);    // (value, dx, dy)
        d += n.yz;             // Accumulate gradient
        a += b * n.x / (1.0 + dot(d, d));  // Key: larger gradient = smaller contribution (erosion effect)
        b *= TERRAIN_GAIN;
        x = m2 * x * 2.0;     // Rotation + frequency scaling
    }
    return a;
}
```

## Common Variants in Detail

### Variant 1: Ridged FBM (Ridged/Turbulent FBM)

- **Difference from base version**: applies `abs()` to noise values, producing sharp ridge lines at zero crossings
- **Use cases**: lightning, mountain ridges, cracks, veins, electric arcs
- **Key modified code**:
```glsl
// Standard FBM line:
f += a * noise(p);
// Changed to ridged:
f += a * abs(noise(p));
// Or sinusoidal ridged (smoother periodic ridges, suitable for lava):
f += a * (sin(noise(p) * 7.0) * 0.5 + 0.5);
```

### Variant 2: Domain Warped FBM

- **Difference from base version**: FBM output is fed back as coordinate offsets, producing organic distortion
- **Use cases**: cloud deformation, geological textures, ink wash style, abstract art
- **Key modified code**:
```glsl
// Classic three-layer domain warping
vec2 o = 0.5 + 0.5 * vec2(fbm(q + vec2(1.0)), fbm(q + vec2(6.2)));
vec2 n = vec2(fbm(4.0 * o + vec2(9.2)), fbm(4.0 * o + vec2(5.7)));
float f = 0.5 + 0.5 * fbm(q + 2.0 * n + 1.0);
```

### Variant 3: Derivative Erosion FBM

- **Difference from base version**: tracks analytical gradient, suppresses high frequencies in steep areas (simulates hydraulic erosion)
- **Use cases**: realistic terrain, mountains, canyons
- **Key modified code**:
```glsl
vec2 d = vec2(0.0);  // Accumulated gradient
for (int i = 0; i < N; i++) {
    vec3 n = noised(p);       // (value, dx, dy)
    d += n.yz;                // Accumulate gradient
    a += b * n.x / (1.0 + dot(d, d));  // Key: divide by gradient magnitude
    b *= 0.5;
    p = m2 * p * 2.0;
}
```

### Variant 4: Flow Noise

- **Difference from base version**: applies independent gradient field displacement within each octave, simulating fluid transport
- **Use cases**: lava, liquid metal, flowing magma
- **Key modified code**:
```glsl
for (float i = 1.0; i < 7.0; i++) {
    vec2 gr = gradn(i * p * 0.34 + time);                              // Gradient field
    gr *= makem2(time * 6.0 - (0.05 * p.x + 0.03 * p.y) * 40.0);     // Spatially varying rotation
    p += gr * 0.5;                                                      // Displacement
    rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;                      // Accumulation
    p = mix(bp, p, 0.77);                                               // Mix back to base
}
```

### Variant 5: Custom Sea Octave FBM

- **Difference from base version**: uses `1-abs(sin(uv))` to construct peaked waveforms, combined with bidirectional propagation and choppy decay
- **Use cases**: ocean water surface, waves
- **Key modified code**:
```glsl
float sea_octave(vec2 uv, float choppy) {
    uv += noise(uv);                      // Noise domain perturbation
    vec2 wv = 1.0 - abs(sin(uv));         // Peaked waveform
    vec2 swv = abs(cos(uv));              // Smooth waveform
    wv = mix(wv, swv, wv);               // Adaptive blending
    return pow(1.0 - pow(wv.x * wv.y, 0.65), choppy);
}
// Bidirectional propagation in FBM loop:
d  = sea_octave((uv + SEA_TIME) * freq, choppy);
d += sea_octave((uv - SEA_TIME) * freq, choppy);
choppy = mix(choppy, 1.0, 0.2);  // Higher octaves are smoother
```

## Performance Optimization Details

### 1. Reduce Octave Count (Most Direct)

Each additional octave doubles the noise sampling cost. Distant objects can use fewer octaves:
```glsl
// LOD-aware octave count
int oct = 5 - int(log2(1.0 + t * 0.5));  // Fewer octaves at greater distances
```

### 2. Multi-Level LOD Strategy

Provide functions at different precision levels for different purposes:
```glsl
float terrainL(vec2 x) { /* 3 octaves — for camera height */ }
float terrainM(vec2 x) { /* 9 octaves — for ray marching */ }
float terrainH(vec2 x) { /* 16 octaves — for normal calculation */ }
```

### 3. Use Texture Sampling Instead of Math

Store precomputed noise in textures, using hardware texture filtering instead of arithmetic hashing:
```glsl
float noise(in vec2 x) { return texture(iChannel0, x * 0.01).x; }
// Or use texelFetch for exact lookup:
float a = texelFetch(iChannel0, (p + 0) & 255, 0).x;
```

### 4. Manually Unroll Loops

GLSL compilers typically optimize manually unrolled small loops (4-6 iterations) better than `for` loops, and allow slightly varying lacunarity per octave.

### 5. Adaptive Step Size (Volume Rendering)

```glsl
// Step size grows linearly with distance
float dt = max(0.05, 0.02 * t);
```

### 6. Directional Derivative Instead of Full Gradient (Volumetric Lighting)

```glsl
// 1 extra sample vs 3
float dif = clamp((den - map(pos + 0.3 * sundir)) / 0.25, 0.0, 1.0);
```

### 7. Early Termination

```glsl
if (sum.a > 0.99) break;  // Volume is already opaque, stop marching
```

## Combination Suggestions in Detail

### 1. FBM + Ray Marching

Noise drives a height field or density field, ray marching finds intersections. This is the standard combination for terrain and ocean surface rendering:
- Height field: `height = terrainFBM(pos.xz)`, ray march to find the intersection where `pos.y == height`
- Volume field: `density = fbm(pos)`, forward-accumulate transmittance and color

### 2. FBM + Finite Difference Normals + Lighting

Use finite differences on a 2D noise field to estimate normals, adding pseudo-3D lighting effects:
```glsl
vec3 nor = normalize(vec3(f(p+ex)-f(p), epsilon, f(p+ey)-f(p)));
float dif = dot(nor, lightDir);
```

### 3. FBM + Color Mapping

Map the same scalar at different power exponents to RGB channels, producing natural color gradients:
```glsl
vec3 col = vec3(1.5*c, 1.5*c*c*c, c*c*c*c*c*c);  // Fire: red -> orange -> yellow -> white
```
Or inverse color mapping:
```glsl
vec3 col = vec3(0.2, 0.07, 0.01) / rz;  // Areas with small ridge values are brightest
```

### 4. FBM + Fresnel Water Surface Coloring

Noise drives water surface waveforms, Fresnel equations blend reflected sky and refracted water color:
```glsl
float fresnel = pow(1.0 - dot(n, -eye), 3.0);
vec3 color = mix(refracted, reflected, fresnel);
```

### 5. Multi-Layer FBM Compositing

Different FBM layers with different parameters control different properties:
- **Shape layer**: low-frequency standard FBM controls cloud shape
- **Ridged layer**: mid-frequency ridged FBM adds edge detail
- **Color layer**: high-frequency FBM controls cloud interior color variation
- **Combination**: `f *= r + f;` shape * ridged produces sharp edges

### 6. FBM + Volumetric Lighting (Directional Derivative)

In volume rendering, the density difference along the light direction approximates lighting:
```glsl
float shadow = clamp((density_here - density_toward_sun) / scale, 0.0, 1.0);
vec3 lit_color = mix(shadow_color, light_color, shadow);
```
