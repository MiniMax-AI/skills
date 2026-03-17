# Color Palette & Color Space Techniques - Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

- GLSL basic syntax: `vec3`, `mix`, `clamp`, `smoothstep`, `fract`, `mod`
- Basic properties of trigonometric functions `cos`/`sin` (periodicity, range [-1, 1])
- Color space fundamentals: RGB is a cube, HSV/HSL is cylindrical coordinates, Lab/Lch is a perceptually uniform space
- Gamma correction concept: monitors store sRGB (nonlinear), shading computations should be performed in linear space

## Step-by-Step Tutorial

### Step 1: Cosine Palette Function

**What**: Implement the most fundamental and commonly used procedural palette function

**Why**: Only 4 vec3 parameters are needed to generate infinite smooth color ramps, with extremely low computational cost (a single cos operation). This function is widely used in the ShaderToy community and is the cornerstone of procedural coloring.

**Mathematical Derivation**:
```
color(t) = a + b * cos(2pi * (c * t + d))
```

- **a** = brightness offset (center luminance of the color ramp), typically ~0.5
- **b** = amplitude (color contrast), typically ~0.5
- **c** = frequency (how many times each channel oscillates), vec3(1,1,1) means R/G/B each oscillate once
- **d** = phase offset (hue starting position per channel), this is the key parameter controlling color style

When a=b=0.5, c=(1,1,1), changing d alone generates completely different color ramps like rainbow, warm tones, cool tones, etc.

**Code**:
```glsl
// Cosine Palette
// a: offset/center color, b: amplitude, c: frequency, d: phase
// t: input scalar, typically [0,1] but can exceed this range
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}
```

### Step 2: Classic Parameter Presets

**What**: Provide ready-to-use palette parameters

**Why**: The original demo showcases 7 classic parameter combinations, covering common needs like rainbow, warm, cool, and duotone schemes. Memorizing a few parameter sets enables rapid color adjustment.

**Code**:
```glsl
// Rainbow color ramp (classic)
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,1,1) d=(0.0, 0.33, 0.67)

// Warm gradient
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,1,1) d=(0.0, 0.10, 0.20)

// Blue-purple to orange tones
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,0.7,0.4) d=(0.0, 0.15, 0.20)

// Custom warm-cool mix
// a=(.8,.5,.4) b=(.2,.4,.2) c=(2,1,1) d=(0.0, 0.25, 0.25)

// Simplified version: fix a/b/c, just adjust d
vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}
```

### Step 3: HSV to RGB Conversion (Standard + Smooth)

**What**: Implement branchless HSV to RGB conversion and its cubic smooth variant

**Why**: HSV space is ideal for rotating by hue, scaling by saturation/value. The standard implementation has C0 discontinuity (piecewise linear); the smooth version achieves C1 continuity through Hermite interpolation, producing smoother hue animation.

**Principle**: Using vectorized `mod` + `abs` + `clamp` operations avoids if/else branching:

```
rgb = clamp(abs(mod(H*6 + vec3(0,4,2), 6) - 3) - 1, 0, 1)
```

This essentially uses piecewise linear functions to model R/G/B channel variation with hue H. C1 discontinuity can be eliminated via cubic smoothing `rgb*rgb*(3-2*rgb)`.

**Code**:
```glsl
// Standard HSV -> RGB (branchless)
// c.x = Hue [0,1], c.y = Saturation [0,1], c.z = Value [0,1]
vec3 hsv2rgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return c.z * mix(vec3(1.0), rgb, c.y);
}

// Smooth HSV -> RGB (C1 continuous)
vec3 hsv2rgb_smooth(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb); // Cubic Hermite smoothing
    return c.z * mix(vec3(1.0), rgb, c.y);
}
```

### Step 4: HSL to RGB Conversion

**What**: Implement HSL color space conversion

**Why**: HSL is more intuitive than HSV — L=0 is black, L=1 is white, L=0.5 is pure color. Suitable for scenarios requiring control over "lightness" rather than "value" (e.g., mapping iteration counts to hue in data visualization).

**Code**:
```glsl
// Hue -> RGB base color (branchless)
vec3 hue2rgb(float h) {
    return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}

// HSL -> RGB
// h: Hue [0,1], s: Saturation [0,1], l: Lightness [0,1]
vec3 hsl2rgb(float h, float s, float l) {
    vec3 rgb = hue2rgb(h);
    return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}
```

### Step 5: Bidirectional RGB <-> HSV Conversion

**What**: Implement the reverse conversion from RGB back to HSV

**Why**: When blending colors in HSV space, you need to first convert both endpoint colors from RGB to HSV, interpolate, then convert back. RGB to HSV uses a classic branchless implementation.

**Code**:
```glsl
// RGB -> HSV (branchless method)
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
```

### Step 6: CIE Lab/Lch Perceptually Uniform Interpolation

**What**: Implement the complete RGB <-> Lab <-> Lch conversion pipeline

**Why**: Linear interpolation in RGB and HSV spaces is not perceptually uniform — the human eye is more sensitive to green than red. Interpolation in Lch (Lightness-Chroma-Hue) space produces the most visually natural gradients, especially suitable for UI color schemes and artistic gradients.

**Mathematical Derivation**: The conversion pipeline is RGB -> XYZ (via sRGB D65 matrix) -> Lab (via nonlinear mapping) -> Lch (via converting a,b to polar coordinates: Chroma, Hue). The inverse process reverses each step.

**Code**:
```glsl
// Helper function: XYZ nonlinear mapping
float xyzF(float t) { return mix(pow(t, 1.0/3.0), 7.787037 * t + 0.139731, step(t, 0.00885645)); }
float xyzR(float t) { return mix(t * t * t, 0.1284185 * (t - 0.139731), step(t, 0.20689655)); }

// RGB -> Lch (via XYZ -> Lab -> polar coordinates)
vec3 rgb2lch(vec3 c) {
    // RGB -> XYZ (sRGB D65 matrix)
    c *= mat3(0.4124, 0.3576, 0.1805,
              0.2126, 0.7152, 0.0722,
              0.0193, 0.1192, 0.9505);
    // XYZ -> Lab
    c = vec3(xyzF(c.x), xyzF(c.y), xyzF(c.z));
    vec3 lab = vec3(max(0.0, 116.0 * c.y - 16.0),
                    500.0 * (c.x - c.y),
                    200.0 * (c.y - c.z));
    // Lab -> Lch (convert a,b to polar: Chroma, Hue)
    return vec3(lab.x, length(lab.yz), atan(lab.z, lab.y));
}

// Lch -> RGB (inverse process)
vec3 lch2rgb(vec3 c) {
    // Lch -> Lab
    c = vec3(c.x, cos(c.z) * c.y, sin(c.z) * c.y);
    // Lab -> XYZ
    float lg = (1.0 / 116.0) * (c.x + 16.0);
    vec3 xyz = vec3(xyzR(lg + 0.002 * c.y),
                    xyzR(lg),
                    xyzR(lg - 0.005 * c.z));
    // XYZ -> RGB (inverse matrix)
    return xyz * mat3( 3.2406, -1.5372, -0.4986,
                      -0.9689,  1.8758,  0.0415,
                       0.0557, -0.2040,  1.0570);
}

// Circular hue interpolation (avoids 0/360 degree wraparound jump)
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), 6.28318) + 9.42477, 6.28318) - 3.14159;
    return ang * x + b;
}

// Lch space linear interpolation
vec3 lerpLch(vec3 a, vec3 b, float x) {
    return vec3(mix(b.xy, a.xy, x), lerpAngle(a.z, b.z, x));
}
```

### Step 7: sRGB Gamma and Linear Space Workflow

**What**: Implement correct sRGB encode/decode functions and a complete linear-space pipeline

**Why**: All lighting/blending computations must be performed in linear space. sRGB textures need to be decoded first (pow 2.2 or exact piecewise function), then encoded back to sRGB after computation. Ignoring this step causes colors to appear too dark and unnatural blending.

**Complete Pipeline**: sRGB texture decode -> linear space shading/blending -> Reinhard tonemap -> sRGB encode

**Code**:
```glsl
// Exact sRGB encode (linear -> sRGB)
float sRGB_encode(float t) {
    return mix(1.055 * pow(t, 1.0/2.4) - 0.055, 12.92 * t, step(t, 0.0031308));
}
vec3 sRGB_encode(vec3 c) {
    return vec3(sRGB_encode(c.x), sRGB_encode(c.y), sRGB_encode(c.z));
}

// Fast approximation (sufficient for most scenarios)
// Decode: pow(color, vec3(2.2))
// Encode: pow(color, vec3(1.0/2.2))

// Reinhard tone mapping (maps HDR values to [0,1])
vec3 tonemap_reinhard(vec3 col) {
    return col / (1.0 + col);
}
```

### Step 8: Blackbody Radiation Palette

**What**: Implement a physics-based temperature-to-color mapping

**Why**: Used for fire, lava, stars, hot metal, and other scenarios requiring physically realistic emission colors. More believable than manual color tuning, with intuitive parameterization (input is just temperature).

**Mathematical Derivation**: Maps temperature T to CIE chromaticity coordinates (cx, cy) via Planck locus approximation, then converts to XYZ -> RGB, combined with Stefan-Boltzmann law (T^4) brightness scaling to produce physically realistic emission colors.

**Code**:
```glsl
// Blackbody radiation palette
// t: normalized temperature [0,1], internally mapped to [0, TEMP_MAX] Kelvin
#define TEMP_MAX 4000.0 // Tunable: maximum temperature (K), affects color gamut width
vec3 blackbodyPalette(float t) {
    t *= TEMP_MAX;
    // Planck locus approximation on CIE chromaticity diagram
    float cx = (0.860117757 + 1.54118254e-4 * t + 1.28641212e-7 * t * t)
             / (1.0 + 8.42420235e-4 * t + 7.08145163e-7 * t * t);
    float cy = (0.317398726 + 4.22806245e-5 * t + 4.20481691e-8 * t * t)
             / (1.0 - 2.89741816e-5 * t + 1.61456053e-7 * t * t);
    // CIE chromaticity coordinates -> XYZ tristimulus values
    float d = 2.0 * cx - 8.0 * cy + 4.0;
    vec3 XYZ = vec3(3.0 * cx / d, 2.0 * cy / d, 1.0 - (3.0 * cx + 2.0 * cy) / d);
    // XYZ -> sRGB matrix
    vec3 RGB = mat3(3.240479, -0.969256, 0.055648,
                   -1.537150,  1.875992, -0.204043,
                   -0.498535,  0.041556,  1.057311) * vec3(XYZ.x / XYZ.y, 1.0, XYZ.z / XYZ.y);
    // Stefan-Boltzmann brightness scaling (T^4)
    return max(RGB, 0.0) * pow(t * 0.0004, 4.0);
}
```

## Variant Detailed Descriptions

### Variant 1: Multi-Harmonic Cosine Palette (Anti-Aliased)

**Difference from base version**: Extends the single cos to 9 layers of different frequencies for richer color detail; uses `fwidth()` for band-limited filtering to prevent high-frequency aliasing.

**Principle**: `fwidth()` returns the variation across adjacent pixels. When oscillation frequency exceeds pixel resolution (i.e., w approaches or exceeds one full TAU period), `smoothstep` attenuates the cos contribution to 0, achieving approximate sinc filtering.

**Complete code**:
```glsl
// Band-limited cos: automatically attenuates when oscillation frequency exceeds pixel resolution
vec3 fcos(vec3 x) {
    vec3 w = fwidth(x);
    return cos(x) * smoothstep(TAU, 0.0, w); // Approximate sinc filtering
}

// 9-layer stacked palette
vec3 getColor(float t) {
    vec3 col = vec3(0.4);
    col += 0.12 * fcos(TAU * t *   1.0 + vec3(0.0, 0.8, 1.1));
    col += 0.11 * fcos(TAU * t *   3.1 + vec3(0.3, 0.4, 0.1));
    col += 0.10 * fcos(TAU * t *   5.1 + vec3(0.1, 0.7, 1.1));
    col += 0.09 * fcos(TAU * t *   9.1 + vec3(0.2, 0.8, 1.4));
    col += 0.08 * fcos(TAU * t *  17.1 + vec3(0.2, 0.6, 0.7));
    col += 0.07 * fcos(TAU * t *  31.1 + vec3(0.1, 0.6, 0.7));
    col += 0.06 * fcos(TAU * t *  65.1 + vec3(0.0, 0.5, 0.8));
    col += 0.06 * fcos(TAU * t * 115.1 + vec3(0.1, 0.4, 0.7));
    col += 0.09 * fcos(TAU * t * 265.1 + vec3(1.1, 1.4, 2.7));
    return col;
}
```

### Variant 2: Hash-Driven Per-Tile Color Variation

**Difference from base version**: Uses a hash function to generate a unique ID for each grid/tile, feeding the ID as the palette's t value to achieve "same palette but different color per tile".

**Use cases**: Procedural tiles/brickwork/mosaics, Voronoi cell coloring, building facades.

**Complete code**:
```glsl
// Hash function (sin-free version, avoids precision issues)
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Usage in tile coloring
vec2 tileId = floor(uv);
vec3 tileColor = palette(hash12(tileId)); // Different color per tile
```

### Variant 3: Saturation-Preserving Improved RGB Interpolation

**Difference from base version**: Detects saturation decay during RGB space interpolation and displaces colors away from the gray diagonal, achieving approximate perceptually uniform interpolation at very low cost (~15 instructions).

**Principle**:
1. Compute RGB linear interpolation result `ic`
2. Compute the difference between expected saturation `mix(getsat(a), getsat(b), x)` and actual saturation `getsat(ic)`
3. Find the direction away from the gray diagonal `dir`
4. Compensate saturation loss along that direction

**Complete code**:
```glsl
float getsat(vec3 c) {
    float mi = min(min(c.x, c.y), c.z);
    float ma = max(max(c.x, c.y), c.z);
    return (ma - mi) / (ma + 1e-7);
}

vec3 iLerp(vec3 a, vec3 b, float x) {
    vec3 ic = mix(a, b, x) + vec3(1e-6, 0.0, 0.0);
    float sd = abs(getsat(ic) - mix(getsat(a), getsat(b), x));
    vec3 dir = normalize(vec3(2.0*ic.x - ic.y - ic.z,
                              2.0*ic.y - ic.x - ic.z,
                              2.0*ic.z - ic.y - ic.x));
    float lgt = dot(vec3(1.0), ic);
    float ff = dot(dir, normalize(ic));
    ic += 1.5 * dir * sd * ff * lgt; // 1.5 = DSP_STR, tunable
    return clamp(ic, 0.0, 1.0);
}
```

### Variant 4: Circular Hue Interpolation (HSV/Lch Space)

**Difference from base version**: When interpolating in color spaces with a circular hue dimension, the hue wraparound from 0.9 to 0.1 crossing through 1.0/0.0 must be handled, otherwise interpolation takes the "long way" (e.g., red -> magenta -> blue -> cyan -> green -> yellow -> red instead of directly red -> orange -> yellow).

**Complete code**:
```glsl
// HSV space circular hue interpolation (hue range [0,1])
vec3 lerpHSV(vec3 a, vec3 b, float x) {
    float hue = (mod(mod((b.x - a.x), 1.0) + 1.5, 1.0) - 0.5) * x + a.x;
    return vec3(hue, mix(a.yz, b.yz, x));
}

// Lch space circular hue interpolation (hue range [0, 2pi])
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), TAU) + PI * 3.0, TAU) - PI;
    return ang * x + b;
}
```

### Variant 5: Additive Color Stacking (Glow/HDR Effects)

**Difference from base version**: Instead of selecting a single color, additively stack palette colors from multiple iterations, producing natural HDR glow effects. Requires tone mapping.

**Use cases**: Fractal glow, halos, laser effects, particle systems, volumetric light.

**Complete code**:
```glsl
vec3 finalColor = vec3(0.0);
for (int i = 0; i < 4; i++) {
    vec3 col = palette(length(uv) + float(i) * 0.4 + iTime * 0.4);
    float glow = pow(0.01 / abs(sdfValue), 1.2); // Inverse-distance glow
    finalColor += col * glow; // Additive stacking, naturally produces HDR
}
finalColor = finalColor / (1.0 + finalColor); // Reinhard tonemap
```

## Performance Optimization Details

### 1. Branchless HSV/HSL Conversion
Use vectorized `mod`/`abs`/`clamp` operations instead of if-else. All implementations above are already branchless. Branching is expensive on GPUs (especially divergent branches within a warp/wavefront); branchless versions ensure all threads follow the same execution path.

### 2. Band-Limited Filtering for Multi-Harmonic Palettes
High-frequency cos layers produce Moire patterns at distance or small angles. Using `fwidth()` + `smoothstep` for automatic attenuation costs only ~2 extra instructions to eliminate aliasing. `fwidth()` leverages hardware partial derivative computation at nearly zero cost.

### 3. Lch Pipeline Cost Analysis
The complete RGB -> XYZ -> Lab -> Lch pipeline requires ~57 instructions, including matrix multiplication, pow, atan, etc. If you only need "slightly better than RGB" interpolation, use `iLerp` (improved RGB, ~15 instructions) instead of the full Lch pipeline for an excellent quality/performance ratio.

### 4. sRGB Gamma Approximation
The exact piecewise linear sRGB conversion requires branching. In most visual scenarios, `pow(c, 2.2)` / `pow(c, 1.0/2.2)` is sufficiently accurate (error < 0.4%) and allows better compiler optimization. The exact version uses `mix` + `step` for branchless implementation but costs a few extra instructions.

### 5. Cosine Palette Vectorization
`a + b * cos(TAU*(c*t+d))` compiles to 1 MAD + 1 COS + 1 MAD on the GPU, approximately 3-4 clock cycles, extremely efficient. All three channels (R/G/B) execute in parallel via SIMD.

### 6. Texture sRGB Decoding
If texture data is already stored as sRGB, use `pow(texture(...).rgb, vec3(2.2))` to decode to linear space before computation, avoiding color distortion from lighting in nonlinear space. In OpenGL/Vulkan, you can also use the `GL_SRGB8_ALPHA8` format for automatic hardware decoding.

## Combination Suggestions in Detail

### 1. Cosine Palette + SDF Raymarching
The most classic combination. Use the normal direction, distance, or surface attributes of ray march hit points as palette t input, producing rich surface coloring.

**Example**:
```glsl
// After SDF raymarching hit
vec3 nor = calcNormal(pos);
float t_palette = dot(nor, vec3(0.0, 1.0, 0.0)) * 0.5 + 0.5; // Normal y-component mapped to [0,1]
vec3 col = palette(t_palette + iTime * 0.1);
```

### 2. HSL/HSV + Data Visualization
Map iteration counts, distance values, or gradient directions to hue (H), encoding other dimensions via saturation/lightness. E.g., using different hues to mark each step in SDF trace visualization.

**Example**:
```glsl
// Mandelbrot iteration coloring
float h = float(iterations) / float(maxIterations);
vec3 col = hsl2rgb(h, 0.8, 0.5);
```

### 3. Cosine Palette + Fractals/Noise
Use `length(uv)` or `fbm(p)` output plus `iTime` as t, combined with additive stacking and inverse-distance glow, producing psychedelic dynamic color effects.

**Example**:
```glsl
float n = fbm(uv * 3.0 + iTime * 0.2);
vec3 col = palette(n + length(uv) * 0.5);
```

### 4. Blackbody Palette + Volume Rendering/Fire
Map a temperature field (noise-driven or physically simulated) through `blackbodyPalette()` to color, producing physically plausible fire, lava, and stellar effects.

**Example**:
```glsl
// In fire volume rendering
float temperature = fbm(pos * 2.0 - vec3(0, iTime, 0)); // Noise-driven temperature field
vec3 fireColor = blackbodyPalette(temperature);
fireColor = tonemap_reinhard(fireColor); // HDR -> LDR
```

### 5. Linear Space Workflow + Any Palette Technique
Regardless of which palette method is used, always follow: sRGB texture decode -> linear space shading/blending -> Reinhard tonemap -> sRGB encode as the complete pipeline, ensuring physically correct color computation.

**Complete pipeline example**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // 1. Decode sRGB texture to linear space
    vec3 texColor = pow(texture(iChannel0, uv).rgb, vec3(2.2));

    // 2. Perform all shading computations in linear space
    vec3 col = texColor * lighting;
    col += palette(t) * emission;

    // 3. Tone mapping (HDR -> LDR)
    col = col / (1.0 + col);

    // 4. sRGB encode
    col = pow(col, vec3(1.0/2.2));

    fragColor = vec4(col, 1.0);
}
```

### 6. Hash + Palette + Tiling System
In procedural tiles/brickwork/mosaics, use `hash(tileID)` as palette input so each tile has a different color while maintaining an overall coordinated color scheme.

**Complete example**:
```glsl
vec2 tileUV = fract(uv * 10.0);
vec2 tileID = floor(uv * 10.0);

// Base color per tile
float h = hash12(tileID);
vec3 tileColor = palette(h);

// Internal tile pattern (e.g., circle)
float d = length(tileUV - 0.5);
float mask = smoothstep(0.4, 0.38, d);

vec3 col = mix(vec3(0.05), tileColor, mask);
```
