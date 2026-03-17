# Procedural Noise Skill

## Use Cases

Procedural noise is the most fundamental technique in real-time GPU graphics. It applies to natural phenomena (fire, clouds, water, lava), terrain generation, texture synthesis, volume rendering, motion effects, and more.

Core idea: use mathematical functions to generate pseudo-random, spatially continuous signals on the GPU in real time, then produce multi-scale detail through FBM and domain warping.

## Core Principles

### Noise Functions

Generate random values at integer lattice points, then smoothly interpolate between them.

- **Value Noise**: random scalars at lattice points + bilinear Hermite interpolation. `N(p) = mix(mix(h00,h10,u), mix(h01,h11,u), v)`
- **Simplex Noise**: triangular lattice gradient dot products + radial falloff kernel. Skew `K1=(sqrt(3)-1)/2`, unskew `K2=(3-sqrt(3))/6`. Fewer lattice lookups, no axis-aligned artifacts.

### Hash Functions

Map integer coordinates to pseudo-random values:

- **sin-based** (short but precision-sensitive): `fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453)`
- **sin-free** (cross-platform stable): `fract(p * 0.1031)` + dot mixing + fract

### FBM (Fractal Brownian Motion)

Multi-octave noise summation: `FBM(p) = sum of amplitude_i * noise(frequency_i * p)`

- Lacunarity ~2.0, Gain ~0.5, inter-octave rotation to eliminate artifacts

### Domain Warping

Feed noise output back as coordinate offset: `fbm(p + fbm(p))` or cascaded `fbm(p + fbm(p + fbm(p)))`

### FBM Variant Quick Reference

| Variant | Formula | Effect |
|---------|---------|--------|
| Standard | `sum a*noise(p)` | Soft clouds |
| Ridged | `sum a*abs(noise(p))` | Sharp ridges/lightning |
| Sinusoidal ridged | `sum a*sin(noise(p)*k)` | Periodic ridges/lava |
| Erosion | `sum a*noise(p)/(1+dot(d,d))` | Realistic terrain |
| Ocean waves | `sum a*sea_octave(p)` | Peaked wave crests |

## Implementation Code

### Hash Functions

```glsl
// Sin-free hash (Dave Hoskins) — cross-platform stable
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

// Sin hash — shorter code, precision-sensitive on some GPUs
float hash(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));
    return fract(sin(h) * 43758.5453123);
}

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}
```

### Value Noise

```glsl
// Hermite smooth bilinear interpolation
float noise(in vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(p + vec2(0.0, 0.0));
    float b = hash(p + vec2(1.0, 0.0));
    float c = hash(p + vec2(0.0, 1.0));
    float d = hash(p + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}
```

### Simplex Noise

```glsl
// 2D Simplex (skewed triangular grid + h^4 falloff kernel)
float noise(in vec2 p) {
    const float K1 = 0.366025404;  // (sqrt(3)-1)/2
    const float K2 = 0.211324865;  // (3-sqrt(3))/6
    vec2 i = floor(p + (p.x + p.y) * K1);
    vec2 a = p - i + (i.x + i.y) * K2;
    vec2 o = (a.x > a.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec2 b = a - o + K2;
    vec2 c = a - 1.0 + 2.0 * K2;
    vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
    vec3 n = h * h * h * h * vec3(
        dot(a, hash2(i + 0.0)),
        dot(b, hash2(i + o)),
        dot(c, hash2(i + 1.0))
    );
    return dot(n, vec3(70.0));
}
```

### Standard FBM

```glsl
#define OCTAVES 4
#define GAIN 0.5
mat2 m = mat2(1.6, 1.2, -1.2, 1.6);  // rotation+scale, |m|=2.0, ~36.87 deg

float fbm(vec2 p) {
    float f = 0.0, a = 0.5;
    for (int i = 0; i < OCTAVES; i++) {
        f += a * noise(p);
        p = m * p;
        a *= GAIN;
    }
    return f;
}
```

Manually unrolled version (slightly varying lacunarity to break self-similarity):

```glsl
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80);
float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;
}
```

### Ridged FBM

```glsl
// abs() produces V-shaped ridges at zero crossings
float fbm_ridged(in vec2 p) {
    float z = 2.0, rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        rz += abs((noise(p) - 0.5) * 2.0) / z;
        z *= 2.0;
        p *= 2.0;
    }
    return rz;
}

// Sinusoidal ridged variant — lava texture
// rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;
```

### Domain Warping

```glsl
// Basic domain warping ("2D Clouds")
float q = fbm(uv * 0.5);
uv -= q - time;
float f = fbm(uv);

// Classic three-level cascade
vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));
}
float func(vec2 q, out vec2 o, out vec2 n) {
    o = 0.5 + 0.5 * fbm4_2(q);
    n = fbm6_2(4.0 * o);
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p);
    f = mix(f, f * f * f * 3.5, f * abs(n.x));
    return f;
}

// Dual-axis domain warping
float dualfbm(in vec2 p) {
    vec2 p2 = p * 0.7;
    vec2 basis = vec2(fbm(p2 - time * 1.6), fbm(p2 + time * 1.7));
    basis = (basis - 0.5) * 0.2;
    p += basis;
    return fbm(p * makem2(time * 0.2));
}
```

### Fluid Noise

```glsl
// Per-octave gradient displacement simulating fluid transport
#define FLOW_SPEED 0.6
#define BASE_SPEED 1.9
#define ADVECTION 0.77
#define GRAD_SCALE 0.5

vec2 gradn(vec2 p) {
    float ep = 0.09;
    float gradx = noise(vec2(p.x + ep, p.y)) - noise(vec2(p.x - ep, p.y));
    float grady = noise(vec2(p.x, p.y + ep)) - noise(vec2(p.x, p.y - ep));
    return vec2(gradx, grady);
}

float flow(in vec2 p) {
    float z = 2.0, rz = 0.0;
    vec2 bp = p;
    for (float i = 1.0; i < 7.0; i++) {
        p += time * FLOW_SPEED;
        bp += time * BASE_SPEED;
        vec2 gr = gradn(i * p * 0.34 + time * 1.0);
        gr *= makem2(time * 6.0 - (0.05 * p.x + 0.03 * p.y) * 40.0);
        p += gr * GRAD_SCALE;
        rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;
        p = mix(bp, p, ADVECTION);
        z *= 1.4;
        p *= 2.0;
        bp *= 1.9;
    }
    return rz;
}
```

### Derivative FBM

```glsl
// Value noise with analytic derivatives
vec3 noised(in vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * (3.0 - 2.0 * f);
    vec2 du = 6.0 * f * (1.0 - f);
    float a = hash(p + vec2(0, 0));
    float b = hash(p + vec2(1, 0));
    float c = hash(p + vec2(0, 1));
    float d = hash(p + vec2(1, 1));
    return vec3(
        a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y,
        du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx)
    );
}

// Erosion FBM: higher gradient = lower contribution
float terrainFBM(in vec2 x) {
    const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);
    float a = 0.0, b = 1.0;
    vec2 d = vec2(0.0);
    for (int i = 0; i < 16; i++) {
        vec3 n = noised(x);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));  // 1/(1+|grad|^2) erosion factor
        b *= 0.5;
        x = m2 * x * 2.0;
    }
    return a;
}
```

### Quintic Noise with Analytical Derivatives

C2-continuous noise using quintic interpolation — eliminates visible grid artifacts in derivatives:

```glsl
// Returns vec3(value, dFdx, dFdy) — derivatives are exact, not finite-differenced
vec3 noisedQ(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    // Quintic interpolation for C2 continuity
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    vec2 du = 30.0 * f * f * (f * (f - 2.0) + 1.0);

    float a = hash12(i + vec2(0.0, 0.0));
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));

    float k0 = a, k1 = b - a, k2 = c - a, k3 = a - b - c + d;
    return vec3(
        k0 + k1 * u.x + k2 * u.y + k3 * u.x * u.y,  // value
        du * vec2(k1 + k3 * u.y, k2 + k3 * u.x)       // derivatives
    );
}
```

### FBM with Derivatives (Erosion Terrain)

Accumulates derivatives across octaves — derivative magnitude dampens amplitude, creating realistic erosion patterns:

```glsl
vec3 fbmDerivative(vec2 p, int octaves) {
    float value = 0.0;
    vec2 deriv = vec2(0.0);
    float amplitude = 0.5;
    float frequency = 1.0;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8); // inter-octave rotation

    for (int i = 0; i < octaves; i++) {
        vec3 n = noisedQ(p * frequency);
        deriv += n.yz;
        // Key: divide by (1 + dot(deriv, deriv)) for erosion effect
        value += amplitude * n.x / (1.0 + dot(deriv, deriv));
        frequency *= 2.0;
        amplitude *= 0.5;
        p = rot * p;  // rotate to break axis-aligned artifacts
    }
    return vec3(value, deriv);
}
```

Key insights:
- **Quintic interpolation**: `6t^5 - 15t^4 + 10t^3` gives C2 continuous noise (vs Hermite's C1), eliminating visible grid artifacts in derivatives
- **Erosion FBM**: The `1/(1+dot(d,d))` term causes flat areas to accumulate more detail while steep slopes stay smooth — mimicking real erosion
- **Inter-octave rotation**: The 2x2 rotation matrix between octaves prevents axis-aligned patterns especially visible in ridged noise

### Voronoise (Voronoi-Noise Hybrid)

Unified interpolation between value noise and Voronoi patterns:

```glsl
// u=0: Value noise, u=1: Voronoi, v: smoothness (0=sharp cells, 1=smooth)
vec3 hash32(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yxz + 33.33);
    return fract((p3.xxy + p3.yzz) * p3.zyx);
}

float voronoise(vec2 p, float u, float v) {
    float k = 1.0 + 63.0 * pow(1.0 - v, 6.0);
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 a = vec2(0.0);
    for (int y = -2; y <= 2; y++)
    for (int x = -2; x <= 2; x++) {
        vec2 g = vec2(float(x), float(y));
        vec3 o = hash32(i + g) * vec3(u, u, 1.0);
        vec2 d = g - f + o.xy;
        float w = pow(1.0 - smoothstep(0.0, 1.414, length(d)), k);
        a += vec2(o.z * w, w);
    }
    return a.x / a.y;
}
```

Extremely versatile — smoothly interpolates between cellular Voronoi and continuous noise.

### Preventing Aliasing in Procedural Textures

For distant surfaces, high-frequency noise octaves create moiré artifacts. Solutions:

1. **LOD-based octave count**: `int octaves = min(MAX_OCTAVES, int(log2(pixelSize)))` — skip octaves finer than pixel size
2. **Analytical filtering**: For simple patterns (checkers, stripes), use smoothstep with pixel width: `smoothstep(-fw, fw, pattern)` where `fw = fwidth(uv)`
3. **Derivative-based mip**: Use `textureGrad()` with manually computed ray differentials for texture lookups in ray-marched scenes (see texture-mapping-advanced technique)

## Complete Code Template

Ready to run in ShaderToy. Switch between standard FBM / ridged FBM / domain warping modes via `#define`:

```glsl
// ============================================================
// Procedural Noise Skill — Complete Template
// ============================================================

// ========== Mode selection (uncomment to switch) ==========
#define MODE_STANDARD_FBM     // Standard FBM clouds
//#define MODE_RIDGED_FBM     // Ridged FBM lightning texture
//#define MODE_DOMAIN_WARP    // Domain warped organic pattern

// ========== Tunable parameters ==========
#define OCTAVES 6
#define GAIN 0.5
#define LACUNARITY 2.0
#define NOISE_SCALE 3.0
#define ANIM_SPEED 0.3
#define WARP_STRENGTH 0.4

// ========== Hash function ==========
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// ========== Value noise ==========
float noise(in vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(p + vec2(0.0, 0.0));
    float b = hash(p + vec2(1.0, 0.0));
    float c = hash(p + vec2(0.0, 1.0));
    float d = hash(p + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// ========== Rotation+scale matrix ==========
const mat2 m = mat2(1.6, 1.2, -1.2, 1.6);

// ========== Standard FBM ==========
float fbm(vec2 p) {
    float f = 0.0, a = 0.5;
    for (int i = 0; i < OCTAVES; i++) {
        f += a * (-1.0 + 2.0 * noise(p));
        p = m * p;
        a *= GAIN;
    }
    return f;
}

// ========== Ridged FBM ==========
float fbm_ridged(vec2 p) {
    float f = 0.0, a = 0.5;
    for (int i = 0; i < OCTAVES; i++) {
        f += a * abs(-1.0 + 2.0 * noise(p));
        p = m * p;
        a *= GAIN;
    }
    return f;
}

// ========== Domain warping vec2 FBM ==========
vec2 fbm2(vec2 p) {
    return vec2(fbm(p + vec2(1.7, 9.2)), fbm(p + vec2(8.3, 2.8)));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    uv *= NOISE_SCALE;
    float time = iTime * ANIM_SPEED;
    float f = 0.0;
    vec3 col = vec3(0.0);

#ifdef MODE_STANDARD_FBM
    f = 0.5 + 0.5 * fbm(uv + vec2(0.0, -time));
    vec3 sky = mix(vec3(0.4, 0.7, 1.0), vec3(0.2, 0.4, 0.6), fragCoord.y / iResolution.y);
    vec3 cloud = vec3(1.1, 1.1, 0.9) * f;
    col = mix(sky, cloud, smoothstep(0.4, 0.7, f));
#endif

#ifdef MODE_RIDGED_FBM
    f = fbm_ridged(uv + vec2(time * 0.5, time * 0.3));
    col = vec3(0.2, 0.1, 0.4) / max(f, 0.05);
    col = pow(col, vec3(0.99));
#endif

#ifdef MODE_DOMAIN_WARP
    vec2 q = fbm2(uv + time * 0.1);
    vec2 r = fbm2(uv + WARP_STRENGTH * q + vec2(1.7, 9.2));
    f = 0.5 + 0.5 * fbm(uv + WARP_STRENGTH * r);
    f = mix(f, f * f * f * 3.5, f * length(r));
    col = vec3(0.2, 0.1, 0.4);
    col = mix(col, vec3(0.3, 0.05, 0.05), f);
    col = mix(col, vec3(0.9, 0.9, 0.9), dot(r, r));
    col = mix(col, vec3(0.5, 0.2, 0.2), 0.5 * q.y * q.y);
    col *= f * 2.0;
    vec2 eps = vec2(1.0 / iResolution.x, 0.0);
    float fx = 0.5 + 0.5 * fbm(uv + eps.xy + WARP_STRENGTH * fbm2(uv + eps.xy + time * 0.1));
    float fy = 0.5 + 0.5 * fbm(uv + eps.yx + WARP_STRENGTH * fbm2(uv + eps.yx + time * 0.1));
    vec3 nor = normalize(vec3(fx - f, eps.x, fy - f));
    vec3 lig = normalize(vec3(0.9, -0.2, -0.4));
    float dif = clamp(0.3 + 0.7 * dot(nor, lig), 0.0, 1.0);
    col *= vec3(0.85, 0.90, 0.95) * (nor.y * 0.5 + 0.5) + vec3(0.15, 0.10, 0.05) * dif;
#endif

    vec2 p = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * sqrt(16.0 * p.x * p.y * (1.0 - p.x) * (1.0 - p.y));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Ridged FBM

```glsl
f += a * abs(noise(p));           // V-shaped ridges
f += a * (sin(noise(p)*7.0)*0.5+0.5); // Sinusoidal ridges (lava)
```

### Domain Warped FBM

```glsl
vec2 o = 0.5 + 0.5 * vec2(fbm(q + vec2(1.0)), fbm(q + vec2(6.2)));
vec2 n = vec2(fbm(4.0 * o + vec2(9.2)), fbm(4.0 * o + vec2(5.7)));
float f = 0.5 + 0.5 * fbm(q + 2.0 * n + 1.0);
```

### Derivative Erosion FBM

```glsl
vec2 d = vec2(0.0);
for (int i = 0; i < N; i++) {
    vec3 n = noised(p);
    d += n.yz;
    a += b * n.x / (1.0 + dot(d, d));
    b *= 0.5; p = m2 * p * 2.0;
}
```

### Fluid Noise

```glsl
for (float i = 1.0; i < 7.0; i++) {
    vec2 gr = gradn(i * p * 0.34 + time);
    gr *= makem2(time * 6.0 - (0.05*p.x+0.03*p.y)*40.0);
    p += gr * 0.5;
    rz += (sin(noise(p)*7.0)*0.5+0.5) / z;
    p = mix(bp, p, 0.77);
}
```

### Ocean Wave Octave Function

```glsl
float sea_octave(vec2 uv, float choppy) {
    uv += noise(uv);
    vec2 wv = 1.0 - abs(sin(uv));
    vec2 swv = abs(cos(uv));
    wv = mix(wv, swv, wv);
    return pow(1.0 - pow(wv.x * wv.y, 0.65), choppy);
}
// Bidirectional propagation in FBM:
d  = sea_octave((uv + SEA_TIME) * freq, choppy);
d += sea_octave((uv - SEA_TIME) * freq, choppy);
choppy = mix(choppy, 1.0, 0.2);
```

## Performance & Composition

**Performance optimization:**
- Reducing octave count is the most direct optimization; use fewer octaves for distant objects: `int oct = 5 - int(log2(1.0 + t * 0.5));`
- Multi-level LOD: `terrainL` (3 oct) / `terrainM` (9 oct) / `terrainH` (16 oct)
- Texture sampling instead of math hash: `texture(iChannel0, x * 0.01).x`
- Manually unroll small loops + slightly vary lacunarity
- Adaptive step size: `float dt = max(0.05, 0.02 * t);`
- Directional derivative instead of full gradient (1 sample vs 3)
- Early termination: `if (sum.a > 0.99) break;`

**Common combinations:**
- FBM + Raymarching: noise-driven height/density fields, ray marching for intersection (terrain/ocean)
- FBM + finite-difference normals + lighting: `nor = normalize(vec3(f(p+ex)-f(p), eps, f(p+ey)-f(p)))`
- FBM + color mapping: different power curves mapping to RGB, e.g. flame `vec3(1.5*c, 1.5*c^3, c^6)` or inverse `vec3(k)/rz`
- FBM + Fresnel water surface: `fresnel = pow(1.0 - dot(n, -eye), 3.0)`
- Multi-layer FBM compositing: shape layer (low freq) + ridged layer (mid freq) + color layer (high freq)
- FBM + volumetric lighting: density difference along light direction approximates illumination

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/procedural-noise.md)
