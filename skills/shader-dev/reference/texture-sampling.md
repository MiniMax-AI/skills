# Texture Sampling Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, mathematical derivations, variant details, and complete combination code examples.

## Prerequisites

- **GLSL Basic Syntax**: `vec2`/`vec3`/`vec4`, `uniform sampler2D`, and other types and declarations
- **UV Coordinate System**: `fragCoord / iResolution.xy` normalizes to `[0,1]`, with origin at the bottom-left corner
- **Mipmap Concept**: A multi-resolution pyramid of the texture, with each level at half the resolution. The GPU automatically selects the appropriate level based on screen-space derivatives to avoid aliasing
- **ShaderToy Multi-Pass Architecture**: Image pass is the final output, Buffer A/B/C/D are intermediate computation passes, bound to textures or buffers via `iChannel0~3`

## Implementation Steps

### Step 1: Basic Texture Sampling and UV Normalization

**What**: Convert screen pixel coordinates to UV coordinates and read texture data.

**Why**: `texture()` accepts UV coordinates in the `[0,1]` range. ShaderToy provides pixel coordinates `fragCoord`, which need to be normalized by dividing by the resolution.

```glsl
// Normalize UV
vec2 uv = fragCoord / iResolution.xy;

// Basic texture sampling (hardware bilinear filtering)
vec4 col = texture(iChannel0, uv);
```

Hardware bilinear filtering automatically performs linear interpolation between the nearest 4 texels. When the UV lands exactly at a texel center, the exact value is returned; when it falls between texels, a weighted average of the surrounding four points is returned.

### Step 2: Using textureLod to Control Mipmap Level

**What**: Explicitly specify the LOD level to control sampling resolution, achieving blur or avoiding automatic mip selection in ray marching.

**Why**: In ray marching, the GPU cannot correctly estimate screen-space derivatives, which leads to incorrect mip level selection and artifacts. Using `textureLod(..., 0.0)` forces sampling at the highest resolution level; using higher LOD values produces blur effects (e.g., depth of field, bloom).

Physical meaning of LOD values:
- `lod = 0.0`: Original resolution (mip 0)
- `lod = 1.0`: Half resolution (mip 1), equivalent to a 2x2 area average
- `lod = N`: Resolution is 1/2^N of the original

```glsl
// In ray marching: force LOD 0 to avoid artifacts (from Campfire at night)
vec3 groundCol = textureLod(iChannel2, groundUv * 0.05, 0.0).rgb;

// Depth of field blur: LOD varies with distance (from Heartfelt)
float focus = mix(maxBlur - coverage, minBlur, smoothstep(.1, .2, coverage));
vec3 col = textureLod(iChannel0, uv + normal, focus).rgb;

// Bloom: explicitly sample high mip levels (from Campfire at night)
#define BLOOM_LOD_A 4.0  // Adjustable: bloom first layer mip level
#define BLOOM_LOD_B 5.0  // Adjustable: bloom second layer mip level
#define BLOOM_LOD_C 6.0  // Adjustable: bloom third layer mip level
vec3 bloom = vec3(0.0);
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_A), BLOOM_LOD_A).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_B), BLOOM_LOD_B).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_C), BLOOM_LOD_C).rgb;
bloom /= 3.0;
```

### Step 3: Using texelFetch for Exact Pixel Data Access

**What**: Read the value of a specific texel using integer coordinates, bypassing all filtering.

**Why**: When textures are used as data storage (game state, precomputed LUTs, keyboard input), exact values of specific pixels must be read — hardware filtering would corrupt data integrity. `texelFetch` uses `ivec2` integer coordinates instead of `vec2` float UVs, accessing pixels directly by address, similar to array indexing.

```glsl
// Define data storage addresses (from Bricks Game)
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);

// Read stored data
vec4 loadValue(in ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

// Write data (in buffer pass)
void storeValue(in ivec2 addr, in vec4 val, inout vec4 fragColor, in ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Read keyboard input (ShaderToy keyboard texture)
float key = texelFetch(iChannel1, ivec2(KEY_SPACE, 0), 0).x;
```

### Step 4: Manual Bilinear Interpolation + Quintic Hermite Smoothing

**What**: Bypass hardware bilinear filtering by manually sampling 4 texels and interpolating with a quintic Hermite polynomial for C² continuity.

**Why**: Hardware bilinear interpolation is linear (C⁰ continuous), which produces visible grid-like seams when layering noise FBM. Quintic Hermite interpolation has zero first and second derivatives at sample points, eliminating these artifacts.

**Mathematical Derivation**:

Standard bilinear interpolation uses linear weight `u = f` (where `f = fract(x)`), which causes derivative discontinuity at boundaries.

Quintic Hermite polynomial: `u = f³(6f² - 15f + 10)`

Verifying C² continuity:
- `u(0) = 0`, `u(1) = 1` — Correct interpolation boundaries
- `u'(f) = 30f²(f-1)²` → `u'(0) = 0`, `u'(1) = 0` — First derivative is zero at boundaries
- `u''(f) = 60f(f-1)(2f-1)` → `u''(0) = 0`, `u''(1) = 0` — Second derivative is zero at boundaries

```glsl
// Manual four-point sampling + quintic Hermite interpolation (from up in the cloud sea)
float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);

    // Quintic Hermite smoothing (C2 continuous)
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);

    // Manual sampling of four corner points (divided by texture resolution for normalization)
    #define TEX_RES 1024.0  // Adjustable: noise texture resolution
    float a = texture(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES).x;
    float b = texture(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES).x;
    float c = texture(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES).x;
    float d = texture(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES).x;

    // Bilinear blending
    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}
```

### Step 5: FBM (Fractional Brownian Motion) Noise from Textures

**What**: Build multi-scale procedural noise by layering multiple texture samples at different frequencies.

**Why**: A single noise sample lacks the multi-scale detail found in nature. FBM simulates the 1/f spectral characteristics of natural textures by layering at doubling frequencies with halving amplitudes. Most natural textures (terrain, clouds, rocks) exhibit 1/f noise characteristics — low frequencies contain most of the energy, high frequencies add detail.

FBM formula: `fbm(x) = Σ (persistence^i × noise(2^i × x))` for i = 0..N-1

Parameter effects:
- **OCTAVES (number of layers)**: More layers add more detail, but each additional layer adds one complete noise call
- **PERSISTENCE**: Controls the amplitude decay rate at higher frequencies. 0.5 is the classic value; higher values (0.6-0.7) produce rougher textures; lower values (0.3-0.4) produce smoother textures

```glsl
#define FBM_OCTAVES 5       // Adjustable: number of layers, more = richer detail
#define FBM_PERSISTENCE 0.5 // Adjustable: amplitude decay rate, higher = stronger high-frequency detail

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;          // Initial amplitude
    float totalWeight = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        totalWeight += a;
        x *= 2.0;           // Double frequency
        a *= FBM_PERSISTENCE;
    }
    return v / totalWeight;
}
```

### Step 6: Separable Gaussian Blur (Multi-Pass Convolution)

**What**: Decompose a 2D Gaussian blur into horizontal and vertical passes, each performing a 1D convolution.

**Why**: A direct NxN 2D convolution requires N² samples; after separation, only 2N are needed. This leverages the separability of the Gaussian kernel — a 2D Gaussian function can be decomposed into the product of two 1D Gaussian functions: `G(x,y) = G(x) × G(y)`. `fract()` wraps coordinates to implement torus boundary conditions, avoiding edge artifacts.

Optimization trick: Leveraging the "free" interpolation of hardware bilinear filtering — sampling between two texels gives a single `texture()` call the weighted average of both texels, achieving an N-tap effect with `(N+1)/2` samples.

```glsl
// Horizontal blur pass (from expansive reaction-diffusion)
#define BLUR_RADIUS 4  // Adjustable: blur radius (kernel width = 2*BLUR_RADIUS+1)

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 d = vec2(1.0 / iResolution.x, 0.0); // Horizontal step

    // 9-tap Gaussian weights (sigma ≈ 2.0)
    float w[9] = float[9](0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05);

    vec4 col = vec4(0.0);
    for (int i = -4; i <= 4; i++) {
        col += w[i + 4] * texture(iChannel0, fract(uv + float(i) * d));
    }
    col /= 0.98; // Weight normalization correction
    fragColor = col;
}

// Vertical blur pass: change d to vec2(0.0, 1.0/iResolution.y)
```

### Step 7: Dispersion Sampling (Wavelength-Dependent Displacement)

**What**: Sample a texture multiple times along a displacement vector with different offsets, weighted by spectral response curves, to simulate prismatic dispersion.

**Why**: Different wavelengths of real light have different refractive indices, causing spatial color separation. By progressively offsetting UV along the displacement direction and accumulating with different weights per RGB channel, this physical phenomenon can be simulated.

Design principles of spectral response weights:
- **Red channel** `t²`: Enhanced at the long wavelength end; red light is at the far end of the spectrum
- **Green channel** `46.6666 × ((1-t) × t)³`: Peak at middle wavelengths, simulating the human eye's greatest sensitivity to green
- **Blue channel** `(1-t)²`: Enhanced at the short wavelength end; blue light is at the near end of the spectrum

```glsl
#define DISP_SAMPLES 64  // Adjustable: dispersion sample count, more = smoother

// Spectral response weights (simulating human eye cone response)
vec3 sampleWeights(float i) {
    return vec3(
        i * i,                            // Red: long wavelength enhancement
        46.6666 * pow((1.0 - i) * i, 3.0), // Green: middle wavelength peak
        (1.0 - i) * (1.0 - i)             // Blue: short wavelength enhancement
    );
}

// Dispersion sampling
vec3 sampleDisp(sampler2D tex, vec2 uv, vec2 disp) {
    vec3 col = vec3(0.0);
    vec3 totalWeight = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = sampleWeights(t);
        col += w * texture(tex, fract(uv + disp * t)).rgb;
        totalWeight += w;
    }
    return col / totalWeight;
}
```

### Step 8: IBL Environment Sampling (textureLod + Roughness Mapping)

**What**: Select the cubemap mipmap level based on surface roughness for image-based lighting.

**Why**: In PBR, rough surfaces need to gather lighting from a wider range of the environment (equivalent to a blurred environment map). High mipmap levels naturally correspond to blurred versions of the environment map, so roughness can be directly mapped to LOD level. This is the split-sum approximation method popularized by Epic Games in UE4.

Complete split-sum IBL workflow:
1. Pre-filter environment map: different roughness values correspond to different mip levels
2. Pre-compute BRDF LUT: `vec2(NdotV, roughness)` -> `vec2(scale, bias)`
3. Final compositing: `specular = envColor * (F * brdf.x + brdf.y)`

```glsl
#define MAX_LOD 7.0     // Adjustable: cubemap maximum mip level
#define DIFFUSE_LOD 6.5 // Adjustable: diffuse sampling LOD (near the blurriest level)

// Specular IBL (from Old watch)
vec3 getSpecularLightColor(vec3 N, float roughness) {
    vec3 raw = textureLod(iChannel0, N, roughness * MAX_LOD).rgb;
    return pow(raw, vec3(4.5)) * 6.5; // HDR approximation boost
}

// Diffuse irradiance IBL
vec3 getDiffuseLightColor(vec3 N) {
    return textureLod(iChannel0, N, DIFFUSE_LOD).rgb;
}

// BRDF LUT query (precomputed split-sum approximation)
vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
vec3 specular = envColor * (F * brdf.x + brdf.y);
```

## Variant Details

### Variant 1: Anisotropic Flow Field Blur

**Difference from basic version**: Instead of uniform Gaussian blur, performs directional blur along a noise-driven direction field, producing a flowing brushstroke effect. The direction field can come from a noise texture, velocity field, or user-defined vector field. The parabolic weight `4h(1-h)` makes the blur strongest at the path center and weakest at both ends, producing a more natural trailing effect.

```glsl
#define BLUR_ITERATIONS 32  // Adjustable: number of samples along flow field
#define BLUR_STEP 0.008     // Adjustable: UV offset per step

vec3 flowBlur(vec2 uv) {
    vec3 col = vec3(0.0);
    float acc = 0.0;
    for (int i = 0; i < BLUR_ITERATIONS; i++) {
        float h = float(i) / float(BLUR_ITERATIONS);
        float w = 4.0 * h * (1.0 - h); // Parabolic weight
        col += w * texture(iChannel0, uv).rgb;
        acc += w;
        // Direction from noise texture (or other vector field)
        vec2 dir = texture(iChannel1, uv).xy * 2.0 - 1.0;
        uv += BLUR_STEP * dir;
    }
    return col / acc;
}
```

### Variant 2: Texture as Data Storage (Buffer-as-Data)

**Difference from basic version**: Textures store structured data (positions, velocities, state) instead of colors, using `texelFetch` for exact reads to achieve inter-frame persistent state.

The key to this pattern is the "address-value" mapping: each pixel coordinate is an "address", and the `vec4` is the stored "value". In a buffer pass, the shader executes for every pixel, but only writes a new value when `fragPos == addr`; all other pixels retain their old values. This implements selective writing.

Applicable scenarios: Game state (health, score, position), particle system parameters, physics simulation global variables.

```glsl
// Address definitions
const ivec2 txPosition = ivec2(0, 0);
const ivec2 txVelocity = ivec2(1, 0);
const ivec2 txState    = ivec2(2, 0);

// Data read/write interface
vec4 load(ivec2 addr) { return texelFetch(iChannel0, addr, 0); }

void store(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Usage in mainImage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 p = ivec2(fragCoord);
    fragColor = texelFetch(iChannel0, p, 0); // Default: keep old value

    vec4 pos = load(txPosition);
    vec4 vel = load(txVelocity);
    // ... update logic ...
    store(txPosition, pos + vel * 0.016, fragColor, p);
    store(txVelocity, vel, fragColor, p);
}
```

### Variant 3: Chromatic Dispersion

**Difference from basic version**: Samples multiple times along a displacement vector, each at a different offset with wavelength-dependent weighted RGB accumulation, producing a prismatic dispersion effect. `DISP_STRENGTH` controls the spatial range of dispersion — larger values produce more pronounced RGB separation.

```glsl
#define DISP_SAMPLES 64     // Adjustable: sample count
#define DISP_STRENGTH 0.05  // Adjustable: dispersion strength

vec3 dispersion(vec2 uv, vec2 displacement) {
    vec3 col = vec3(0.0);
    vec3 w_total = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = vec3(t * t, 46.666 * pow((1.0 - t) * t, 3.0), (1.0 - t) * (1.0 - t));
        col += w * texture(iChannel0, fract(uv + displacement * t * DISP_STRENGTH)).rgb;
        w_total += w;
    }
    return col / w_total;
}
```

### Variant 4: Triplanar Texture Mapping

**Difference from basic version**: For 3D surfaces, samples textures using three projection directions (X/Y/Z axes) and blends by normal weights, avoiding seam issues with traditional UV mapping.

`TRIPLANAR_SHARPNESS` controls the blend transition sharpness: higher values produce sharper transitions between projection faces; a value of 1.0 provides the smoothest but potentially blurry transitions. Typical values are 2.0-4.0.

Applicable scenarios: Procedural terrain (where UV unwrapping cannot be done in advance), geometry generated by SDF ray marching.

```glsl
#define TRIPLANAR_SHARPNESS 2.0  // Adjustable: blend sharpness

vec3 triplanarSample(sampler2D tex, vec3 pos, vec3 normal, float scale) {
    vec3 w = pow(abs(normal), vec3(TRIPLANAR_SHARPNESS));
    w /= (w.x + w.y + w.z); // Normalize weights

    vec3 xSample = texture(tex, pos.yz * scale).rgb;
    vec3 ySample = texture(tex, pos.xz * scale).rgb;
    vec3 zSample = texture(tex, pos.xy * scale).rgb;

    return xSample * w.x + ySample * w.y + zSample * w.z;
}
```

### Variant 5: Temporal Reprojection (TAA)

**Difference from basic version**: Calculates the current frame pixel's UV position in the previous frame, samples the previous frame data from the buffer, and blends to achieve temporal anti-aliasing or accumulation effects.

`TAA_BLEND` controls the history frame weight: higher values (e.g., 0.95) provide better temporal stability but more motion trailing; lower values (e.g., 0.8) provide faster response but more flickering. The clamp operation prevents ghosting — when the history color exceeds the current frame's neighborhood range, it indicates a large scene change, and history weight should be reduced.

```glsl
#define TAA_BLEND 0.9  // Adjustable: history frame blend ratio (higher = smoother but more trailing)

vec3 temporalBlend(vec2 currUv, vec2 prevUv, vec3 currColor) {
    vec3 history = textureLod(iChannel0, prevUv, 0.0).rgb;
    // Simple clamp to prevent ghosting
    vec3 minCol = currColor - 0.1;
    vec3 maxCol = currColor + 0.1;
    history = clamp(history, minCol, maxCol);
    return mix(currColor, history, TAA_BLEND);
}
```

## Performance Optimization Details

### Bottleneck 1: Texture Sampling Bandwidth

- **Problem**: A large number of `texture()` calls (e.g., 64 dispersion samples) is a GPU bandwidth-intensive operation
- **Optimization**: Reduce sample count and compensate with smarter weight functions; use mipmap (`textureLod` at high LOD) to reduce cache misses
- **Details**: GPU texture cache works in cache lines; cache hit rates are high when adjacent pixels access similar texture regions. Higher LOD level textures are smaller and more likely to fit entirely in cache. For dispersion sampling, consider performing dispersion in a low-resolution buffer first, then bilinearly upsampling

### Bottleneck 2: Separable Blur

- **Problem**: A 2D Gaussian blur requires N² samples
- **Optimization**: Always use a separable two-pass approach (horizontal + vertical), reducing complexity from O(N²) to O(2N)
- **Advanced trick**: Leverage hardware bilinear filtering's "free" interpolation — sampling between two texels causes the hardware to automatically return the weighted average, achieving an N-tap effect with `(N+1)/2` samples. For example, a 9-tap Gaussian requires only 5 texture samples

### Bottleneck 3: Mip Selection in Ray Marching

- **Problem**: The GPU's screen-space derivatives (`dFdx`/`dFdy`) are incorrect inside ray march loops, because adjacent pixels may be at completely different ray march steps, causing incorrect automatic mip level selection
- **Optimization**: Use `textureLod(..., 0.0)` in all texture queries within ray march loops to force the base level
- **Alternative**: If mipmap anti-aliasing is needed, manually compute the LOD: estimate screen-space coverage based on ray length and surface tilt angle, then convert to LOD with `log2()`

### Bottleneck 4: Manual Interpolation for High-Frequency Noise

- **Problem**: Manual four-point sampling + Hermite interpolation is approximately 4x slower than hardware bilinear (4 `texture()` calls + math vs. 1 hardware-filtered `texture()` call)
- **Optimization**: Only use it when the visual difference is noticeable (first 1-2 octaves of FBM); higher-frequency octaves can fall back to `texture()` since the difference is no longer visible
- **Tradeoff**: For a 6-octave FBM, using Hermite for the first 2 octaves (8 samples) and hardware bilinear for the last 4 (4 samples) totals 12 samples — half of the 24 samples needed for full Hermite

### Bottleneck 5: Multi-Buffer Feedback Latency

- **Problem**: Each buffer in a multi-pass feedback loop adds one frame of latency (because a buffer's output is only readable in the next frame)
- **Optimization**: Combine mergeable operations into a single pass whenever possible; use `texelFetch` instead of `texture` to read buffer data to avoid unnecessary filtering overhead
- **Architecture suggestion**: When designing buffer topology, minimize feedback chain length. If A→B→C→A forms a three-frame delay loop, consider whether B and C can be merged into a single pass

## Complete Combination Code Examples

### Combining with SDF Ray Marching

Texture sampling provides surface detail for SDF scenes: sampling noise textures for displacement mapping, material lookup. Key: `textureLod(..., 0.0)` must be used inside ray march loops.

```glsl
// Using texture noise for detail displacement in an SDF scene
float map(vec3 p) {
    float d = length(p) - 1.0; // Base sphere SDF

    // Texture noise displacement (must use textureLod inside ray march)
    float n = textureLod(iChannel0, p.xz * 0.5, 0.0).x;
    d += n * 0.1; // Surface detail

    return d;
}

// Material query also uses textureLod
vec3 getMaterial(vec3 p, vec3 n) {
    // Triplanar mapping for material color
    vec3 w = pow(abs(n), vec3(2.0));
    w /= (w.x + w.y + w.z);
    vec3 col = textureLod(iChannel1, p.yz * 0.5, 0.0).rgb * w.x
             + textureLod(iChannel1, p.xz * 0.5, 0.0).rgb * w.y
             + textureLod(iChannel1, p.xy * 0.5, 0.0).rgb * w.z;
    return col;
}
```

### Combining with Procedural Noise (Domain Warping)

Texture-based noise (manual Hermite + FBM) serves as the driver for domain warping, used to generate terrain, clouds, flames, and other natural effects. Texture noise is faster than pure mathematical noise (one texture sample vs. multiple hash calculations).

```glsl
// Domain warping: use FBM to warp FBM's input coordinates
float domainWarp(vec2 p) {
    // First warping layer
    vec2 q = vec2(fbm(p + vec2(0.0, 0.0)),
                  fbm(p + vec2(5.2, 1.3)));

    // Second warping layer (more complex effect)
    vec2 r = vec2(fbm(p + 4.0 * q + vec2(1.7, 9.2)),
                  fbm(p + 4.0 * q + vec2(8.3, 2.8)));

    return fbm(p + 4.0 * r);
}
```

### Combining with Post-Processing Pipeline

Multi-LOD sampling for bloom, separable Gaussian blur for depth of field, dispersion sampling for chromatic aberration. These techniques can be chained into a complete post-processing pipeline.

```glsl
// Complete post-processing chain (single-pass simplified version)
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // 1. Read scene color (from Buffer A)
    vec3 col = texture(iChannel0, uv).rgb;

    // 2. Bloom (multi-LOD sampling)
    vec3 bloom = vec3(0.0);
    bloom += textureLod(iChannel0, uv, 4.0).rgb * 0.5;
    bloom += textureLod(iChannel0, uv, 5.0).rgb * 0.3;
    bloom += textureLod(iChannel0, uv, 6.0).rgb * 0.2;
    col += bloom * 0.3;

    // 3. Chromatic aberration (simplified 3-tap)
    vec2 dir = uv - 0.5;
    float strength = length(dir) * 0.02;
    col.r = texture(iChannel0, uv + dir * strength).r;
    col.b = texture(iChannel0, uv - dir * strength).b;

    // 4. Tone mapping (Filmic)
    col = (col * (6.2 * col + 0.5)) / (col * (6.2 * col + 1.7) + 0.06);

    // 5. Vignette
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.2);

    fragColor = vec4(col, 1.0);
}
```

### Combining with PBR/IBL Lighting

`textureLod` samples the cubemap by roughness for image-based lighting, combined with a precomputed BRDF LUT (queried via `texelFetch` or `texture`), forming a complete split-sum IBL pipeline.

```glsl
// Complete IBL lighting computation
vec3 computeIBL(vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    float NdotV = max(dot(N, V), 0.0);
    vec3 R = reflect(-V, N);

    // Fresnel (Schlick approximation)
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 F = F0 + (1.0 - F0) * pow(1.0 - NdotV, 5.0);

    // Specular: sample pre-filtered environment map by roughness
    vec3 specEnv = textureLod(iChannel0, R, roughness * 7.0).rgb;
    specEnv = pow(specEnv, vec3(4.5)) * 6.5; // HDR approximation

    // BRDF LUT query
    vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
    vec3 specular = specEnv * (F * brdf.x + brdf.y);

    // Diffuse irradiance
    vec3 diffEnv = textureLod(iChannel0, N, 6.5).rgb;
    vec3 kD = (1.0 - F) * (1.0 - metallic);
    vec3 diffuse = kD * albedo * diffEnv;

    return diffuse + specular;
}
```

### Combining with Simulation/Feedback Systems

Multi-buffer texture sampling for reaction-diffusion, fluid simulation, and other iterative systems. Buffer A stores state, Buffer B/C perform separable blur diffusion, and the Image pass handles final visualization. `fract()` wraps coordinates for torus boundaries.

```glsl
// Buffer A: Reaction-diffusion state update
// iChannel0: Buffer A itself (feedback)
// iChannel1: Buffer B (result after horizontal blur)
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 px = 1.0 / iResolution.xy;

    // Read current state and diffused state
    vec2 state = texelFetch(iChannel0, ivec2(fragCoord), 0).xy;
    vec2 diffused = texture(iChannel1, uv).xy; // After separable blur

    // Gray-Scott reaction-diffusion
    float a = diffused.x;
    float b = diffused.y;
    float feed = 0.037;
    float kill = 0.06;

    float da = 1.0 * (diffused.x - state.x) - a * b * b + feed * (1.0 - a);
    float db = 0.5 * (diffused.y - state.y) + a * b * b - (kill + feed) * b;

    state += vec2(da, db) * 0.9;
    state = clamp(state, 0.0, 1.0);

    fragColor = vec4(state, 0.0, 1.0);
}
```
