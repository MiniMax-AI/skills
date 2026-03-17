# Post-Processing Effects Detailed Reference

This file is a complete supplement to [SKILL.md](SKILL.md), covering prerequisites, detailed explanations of each step (what and why), variant details, in-depth performance optimization analysis, and complete combination suggestions.

## Prerequisites

- GLSL fundamentals and the ShaderToy environment (iResolution, iTime, iChannel, textureLod, etc.)
- Basic vector and matrix operations
- Difference between linear color space and gamma correction
- Texture sampling and UV coordinate systems
- Basic concepts of convolution (kernel, weights, normalization)
- Multi-pass rendering concepts (Buffer A/B/C/D and Image pass in ShaderToy)

## Applicable Scenarios

Use this technique when you have completed the primary rendering of a scene and need screen-space image enhancement on the result. Typical applications include:

- **HDR to LDR Conversion**: After using linear HDR lighting in a scene, tone mapping is needed to compress values into the displayable range
- **Atmosphere Enhancement**: Effects like vignette, color grading, and film grain to enhance a cinematic look
- **Glow and Bloom**: Simulating lens bloom to produce soft light diffusion around bright areas
- **Motion and Defocus Blur**: Simulating physical camera characteristics through motion blur and depth of field
- **Anti-Aliasing**: Post-processing AA solutions such as FXAA and TAA
- **Chromatic Aberration and Lens Effects**: Optical simulations like chromatic aberration and lens flare

## Core Principles

### Tone Mapping

Maps HDR linear color values from [0, ∞) to the LDR display range [0, 1]. Core mathematical models:

- **Reinhard**: `color = color / (1.0 + color)`, a simple S-curve compression
- **Filmic Reinhard**: `q = (T²+1)·x² / (q + x + T²)`, with white point (W) and shoulder (T) parameters
- **ACES**: Industry standard, converts colors to the ACES color space via a 3×3 matrix, then applies a rational polynomial `(ax+b)/(cx+d)+e` for nonlinear mapping
- **General Rational Polynomial**: `(a·x²+b·x) / (c·x²+d·x+e)`, can fit various tone curves

### Gaussian Blur

2D Gaussian kernel `G(x,y) = exp(-(x²+y²)/(2σ²))`. Due to separability, it can be split into two 1D passes (horizontal + vertical), reducing O(n²) to O(2n).

### Bloom

Extracts bright pixels (bright-pass threshold), then applies multi-level Gaussian blur and adds the result back to the original image. Multi-octave approach: progressively downsample + blur, then progressively composite, producing bloom layers from narrow to wide.

### Vignette

Attenuates brightness based on the pixel's distance to the screen center. Common formulas:
- **Multiplicative**: Power of `16·u·v·(1-u)·(1-v)`
- **Radial**: `1 - pow(dist * scale, exponent)` mixed with strength

### Chromatic Aberration

Simulates the difference in lens refraction for different wavelengths. Samples the same texture with different scale factors for R/G/B channels, with offset increasing from center to edges.

## Implementation Steps

### Step 1: Tone Mapping — Map HDR to Displayable Range

**What**: Compress HDR linear color values from the render output into the [0,1] range.

**Why**: Physically correct lighting calculations produce brightness values far exceeding the display range. Direct clamping would lose highlight detail. Tone mapping uses a nonlinear curve to preserve shadow detail and highlight transitions.

Comparison of four approaches:
- **Reinhard**: Simplest, good for beginners. A single line `color / (1.0 + color)` achieves S-curve compression, but the highlight region is compressed too aggressively, lacking a smooth "shoulder" transition.
- **Filmic Reinhard**: The white point (W) parameter controls the mapping position of the brightest value, and the shoulder parameter (T2) controls how gently highlights are compressed. Higher T2 values produce softer highlight transitions.
- **ACES**: Industry standard approach. First converts linear sRGB to the ACES AP1 color space via an input matrix, applies a rational polynomial nonlinear mapping, then converts back to sRGB via an output matrix. Most accurate color representation, but slightly more computationally expensive.
- **General Rational Polynomial**: A general curve with 5 adjustable parameters that can manually fit any tone curve. Maximum flexibility, but requires manual parameter tuning.

### Step 2: Gamma Correction — Linear Space to Display Space

**What**: Convert linear color values to sRGB gamma space for correct display on monitors.

**Why**: Monitor brightness response is nonlinear (approximately γ=2.2). Directly outputting linear values would appear too dark. Gamma correction compensates with `pow(1/2.2)`.

Notes:
- The ACES approach already includes gamma correction, so no additional step is needed
- Some pipelines use 0.4545 (≈1/2.2) as the gamma value
- Gamma correction must be performed after tone mapping

### Step 3: Contrast Enhancement — Hermite S-Curve

**What**: Apply an S-curve to the tone-mapped colors to enhance midtone contrast.

**Why**: After tone mapping, the image may appear flat. An S-curve makes darks darker and brights brighter, increasing visual impact. The cubic Hermite basis function `3x² - 2x³` of `smoothstep` is a natural S-curve.

Implementation details:
- Must be performed after gamma correction, when the value range is [0,1]
- Use `clamp` to ensure input is within valid range
- The `contrast_strength` parameter controls effect intensity via `mix`, 0 for no effect, 1 for full effect
- The `smoothstep(-0.025, 1.0, color)` version provides a slight toe lift in the darks, avoiding pure black

### Step 4: Color Grading

**What**: Apply channel-level adjustments to shift the overall color tone.

**Why**: Different color temperatures and tones convey different moods. Warm tones (yellow/orange bias) give a cozy feeling, while cool tones (blue/cyan bias) give a sense of detachment.

Four approaches in detail:
- **Per-Channel Multiplication**: Simplest and most direct. `vec3(1.11, 0.89, 0.79)` boosts the red channel while reducing blue/green, producing warm tones. Swap the coefficients for cool tones.
- **Power Color Grading**: Adjusts color by changing each channel's gamma curve. Values <1 brighten that channel, >1 darken it. Gentler than multiplication, with greater impact on midtones.
- **HSV Hue Shift**: After converting to HSV, you can directly rotate the hue and adjust saturation. Suitable for scenarios requiring precise hue control.
- **Desaturation Blend**: Mixes the original color with its luminance value (grayscale). Higher blend ratios produce a more washed-out look, creating a "cinematic" or "faded" effect.

### Step 5: Vignette

**What**: Darken the edges of the image to guide the viewer's focus toward the center.

**Why**: Simulates the optical vignetting of real lenses and is a classic film composition technique.

Comparison of three approaches:
- **Approach A (Multiplicative, classic)**: `16·u·v·(1-u)·(1-v)` constructs a parabolic surface in UV space that equals 1 at the center and 0 at the corners. The power parameter controls falloff speed, 0.25 is commonly used. Advantage: minimal computation. Disadvantage: fixed rectangular gradient shape.
- **Approach B (Radial distance)**: Based on the Euclidean distance from pixel to screen center. Accounts for aspect ratio correction, producing an elliptical vignette. Three parameters control intensity, starting radius, and falloff steepness.
- **Approach C (Inverse quadratic falloff)**: `1/(1 + dot(p,p))` produces very natural optical vignetting. Squaring twice makes the falloff more pronounced. Smoothstep blending controls effect intensity.

### Step 6: Gaussian Blur — Basic Blur

**What**: Apply Gaussian convolution blur to the image. This is the fundamental building block for Bloom.

**Why**: The Gaussian kernel is the only smoothing kernel that is both isotropic and separable, producing a naturally soft blur.

Implementation details:
- `normpdf` computes the Gaussian probability density, where 0.39894 ≈ 1/√(2π)
- KERNEL_SIZE must be odd to ensure center symmetry
- First build a 1D kernel and exploit symmetry (`kernel[HALF+j] = kernel[HALF-j]`)
- Z is the normalization factor, ensuring all weights sum to 1
- 2D convolution is implemented via two nested loops, with the outer product `kernel[j] * kernel[i]` constructing 2D weights
- In production, use a separable approach (two 1D passes) instead for better performance

### Step 7: Bloom — HDR Glow

**What**: Extract bright areas from the image, apply multi-level blur, and add the result back to create a glow diffusion effect.

**Why**: Both the human eye and camera lenses see glow around strong light sources. Bloom is the most impactful post-processing effect for enhancing the "HDR feel" of an image.

Implementation details:
- Uses `textureLod` to sample from high LOD levels of the mipmap; the GPU hardware automatically handles downsampled blur
- Sampling from LOD 5/6/7 corresponds to approximately 32x/64x/128x downsampling, producing different blur radii from narrow to wide
- 2x2 neighborhood supersampling (loop from -1 to 1) reduces blockiness
- `maxBloom` cap prevents extremely bright pixels from producing excessive bloom
- `pow(bloom, vec3(1.5))` applies gamma adjustment to concentrate bloom in bright areas
- Note: ShaderToy Buffers do not generate mipmaps by default; this must be enabled in the channel settings

### Step 8: Chromatic Aberration

**What**: Sample R/G/B channels with different UV scales to simulate lens dispersion.

**Why**: Real lenses cannot focus all wavelengths of light onto the same focal plane. This "imperfection" actually adds realism and visual interest to the image.

Implementation details:
- Offset direction is calculated from the screen center
- In each iteration, R/G/B channels are sampled with different scale factors
- The red channel contracts (rf decreasing), blue channel expands (bf increasing), green channel remains nearly unchanged
- The difference in contraction/expansion rates produces the dispersion effect, increasing from center to edges
- The iterative implementation accumulates samples at different scale factors to simulate a continuous spectrum
- CA_SAMPLES: more samples produce smoother results; 4-8 is usually sufficient

### Step 9: Film Grain

**What**: Overlay pseudo-random noise to simulate film grain texture.

**Why**: Subtle random noise breaks the "perfect" feel of digital images, adds organic texture, and helps reduce color banding.

Two implementation approaches:
- **Hash Noise**: A simple `fract(sin(...) * 43758.5453)` pseudo-random function. Multiplied by iTime to ensure different noise each frame. An intensity of around 0.012 looks natural.
- **Bayer Matrix Ordered Dithering**: A 4x4 Bayer matrix provides 17 levels of ordered dithering. More uniform than random noise, particularly suitable for eliminating 8-bit color banding. `(dither - 0.5) * 4.0 / 255.0` limits the dither amount to approximately ±2 color levels.

### Step 10: Motion Blur

**What**: Apply directional blur along each pixel's motion direction.

**Why**: Static frames lack a sense of motion. Motion blur simulates the effect of object movement during shutter exposure, making animation smoother and more natural.

Implementation details:
- Motion direction is determined from a velocity buffer
- Samples uniformly along the motion direction with linearly decreasing weights (lower weight at greater distances)
- MB_STRENGTH controls the blur radius (in UV space); 0.25 means sampling up to 25% screen distance from the pixel
- 32 samples are usually sufficient; random jittering can achieve similar results with fewer samples

Camera reprojection approach:
- Requires a depth buffer and previous frame's camera matrix
- Projects the current pixel's world coordinate to the previous frame's UV to obtain the motion vector
- The shutterAngle parameter (0~1) controls the blur amount
- Randomized sample positions avoid regular stripe artifacts

### Step 11: Depth of Field

**What**: Calculate the Circle of Confusion (CoC) based on pixel depth and focal plane distance, and use disk sampling with defocus to simulate out-of-focus blur.

**Why**: Simulates a real thin lens model, producing soft bokeh for objects outside the focal plane, enhancing depth perception.

Implementation details:
- **CoC Model**: Based on the thin lens formula, CoC size is proportional to how much the pixel depth deviates from the focal plane. The aperture parameter controls the aperture size, affecting the depth of field range.
- **Fibonacci Spiral Sampling**: The golden angle (≈ 2.3998 radians) ensures sampling points are uniformly distributed on the disk. `sqrt(i)` radius increment produces uniform area density.
- **Weight Strategy**: Uses each sample point's own CoC as weight, ensuring in-focus sharp regions are not "contaminated" by out-of-focus blur.
- 64 samples produce high-quality bokeh; 32 are sufficient for most needs.

### Step 12: FXAA — Fast Approximate Anti-Aliasing

**What**: Detect aliased edges in the image and apply directional blur along edges to eliminate aliasing.

**Why**: Post-processing AA does not require modifying the rendering pipeline and has extremely low cost. FXAA detects edge direction through luminance gradients and uses a small number of texture samples for directional blurring.

Implementation details:
- Sample luminance from 4 diagonal neighbors (NW, NE, SW, SE) and the center
- Calculate the luminance range (lumaMin/lumaMax) for final quality assessment
- Edge direction is computed from horizontal/vertical luminance differences
- `dirReduce` and `rcpDirMin` control the scaling of the direction vector to prevent excessive blurring
- Two-level sampling strategy: rgbA samples at 1/3 and 2/3 positions, rgbB adds samples at -0.5 and 0.5 positions on top of that
- Final decision: if rgbB's luminance exceeds the neighborhood range (indicating an edge crossing), fall back to rgbA

## Variant Details

### Variant 1: Multi-Pass Separable Bloom

Differs from the basic single-pass mipmap bloom: uses independent Buffers for separable Gaussian blur (horizontal pass + vertical pass), providing higher bloom quality and greater control.

**Buffer A Details (Horizontal Blur + Downsampling)**:
- `BLOOM_THRESHOLD`: Brightness threshold; only pixels exceeding this value enter bloom. Lower values mean more pixels participate.
- `BLOOM_DOWNSAMPLE`: Downsampling factor; 3 means computing at 1/3 resolution. Reduces computation while expanding the effective blur radius.
- `BLUR_RADIUS`: Blur radius (in pixels); 16 means sampling 16 pixels in each direction.
- The `-8.0` in the Gaussian weight `exp(-8.0 * d * d)` controls the falloff speed; adjust to change the "softness" of the blur.
- Boundary check `xy.x >= int(iResolution.x) / BLOOM_DOWNSAMPLE` ensures computation only within the downsampled region.

**Buffer B Details (Vertical Blur)**:
- Identical structure to Buffer A, except the sampling direction changes from horizontal `ivec2(k, 0)` to vertical `ivec2(0, k)`
- Input is Buffer A's output (iChannel0 bound to Buffer A)
- The combination of two separable blur passes is equivalent to a full 2D Gaussian blur

### Variant 2: ACES + Complete Color Pipeline

Differs from the basic version: uses the complete ACES RRT+ODT pipeline, including color space matrix conversion and built-in sRGB gamma, suitable for projects pursuing cinema-grade color.

Key differences:
- Input matrix m1 converts linear sRGB to the ACES AP1 color space
- Rational polynomial `(v*(v+a)-b) / (v*(c*v+d)+e)` simulates the ACES RRT (Reference Rendering Transform)
- Output matrix m2 converts ACES AP1 back to linear sRGB
- The final `pow(..., 1/2.2)` performs sRGB gamma encoding, so a separate gamma correction step is not needed when using this approach

### Variant 3: Physical DoF + Motion Blur Combination

Differs from the basic version: uses depth buffer and previous frame camera matrix for physically correct depth of field + motion blur, sharing the same sampling loop.

Key design:
- DoF and motion blur are processed in the same for loop, avoiding two independent sampling passes
- `randomT` hash randomizes each sample point's time position, reducing regular stripe artifacts
- Motion blur: interpolates between current and previous frame UV by `shutterAngle`
- DoF: Fibonacci spiral offset, with offset amount controlled by CoC
- Both effects share the same `textureLod` sample after stacking, saving half the bandwidth

### Variant 4: TAA Temporal Anti-Aliasing

Differs from basic FXAA: leverages multi-frame history for temporal domain supersampling. Each frame uses sub-pixel jittering, blends with the previous frame, and uses neighborhood color clamping to prevent ghosting.

Key steps explained:
1. **De-jittered Sampling**: The current frame is rendered with sub-pixel jitter; during sampling, the jitter offset must be subtracted to restore the correct UV
2. **Neighborhood Clamping**: The min/max of colors in the 3x3 neighborhood defines the "reasonable color range". History frame colors outside this range indicate scene changes (occlusion/reveal)
3. **Reprojection**: Uses the current pixel's world coordinates and the previous frame's view-projection matrix to calculate the corresponding UV position in the previous frame
4. **Blend Strategy**: When the history frame is within the reasonable range, use a high weight (0.9) for temporal stability; when outside the range, use 0 weight to fully use the current frame and avoid ghosting
5. `blend = 0.9` is adjustable: higher values are smoother but more prone to trailing artifacts

### Variant 5: Lens Flare + Starburst

Differs from the basic version: overlays lens flare simulation on top of bloom, including starburst and chromatic ghosts.

Key techniques explained:
- **Starburst Pattern**: `cos(angle * NUM_APERTURE_BLADES)` creates a periodic pattern in the angular domain, simulating diffraction from aperture blades. `NUM_APERTURE_BLADES` controls the number of starburst points. `pow` controls the sharpness of the starburst, becoming less pronounced farther from the light source.
- **Octagonal Ghosts**: Multiple ghosts placed at reflected positions along the optical axis (the line from the sun to the screen center). `smoothstep` produces soft-edged disk shapes.
- **Spectral Color**: `wavelengthToRGB` converts wavelength (nm) to RGB; `fract(ghostDist * 5.0)` produces rainbow bands within the ghost, simulating the dispersion effect of real lens ghosts.

## In-Depth Performance Optimization

### 1. Separable Blur Instead of 2D Convolution

An 11×11 2D Gaussian convolution requires 121 samples; splitting into two 1D passes requires only 22. This is the primary optimization for all blur operations.

Mathematical basis: The separability of the Gaussian kernel `G(x,y) = G(x) · G(y)`, meaning a 2D Gaussian kernel equals the outer product of two 1D Gaussian kernels. This means performing horizontal blur followed by vertical blur (or vice versa) produces identical results to direct 2D convolution.

### 2. Hardware Mipmap Instead of Manual Downsampling

`textureLod(tex, uv, lod)` leverages the GPU hardware's mipmap chain for free downsampled blur, suitable for fast bloom. Note that ShaderToy Buffers do not generate mipmaps by default (you need to enable `mipmap` in the channel settings).

Each mipmap level halves the resolution, equivalent to a 2x2 box filter. LOD 5 corresponds to 32x downsampling, LOD 6 to 64x, LOD 7 to 128x. Although a box filter is not a Gaussian kernel, the results approach Gaussian when multiple levels are combined.

### 3. Downsample Before Blurring

Bloom does not need to be computed at full resolution. Downsample the image by 2-4x first, blur at low resolution, then bilinearly upsample back.

Advantages:
- Computation reduced by 4-16x (area ratio)
- The same blur kernel size covers a larger screen area at lower resolution
- Bilinear interpolation during upsampling automatically smooths the result

### 4. Reduce Sample Count

Recommended sample counts:
- Motion blur: 16-32 samples are usually sufficient; use random jittering (temporal jitter) instead of regular intervals to hide stripe artifacts from insufficient sampling
- DoF: 32-64 Fibonacci spiral samples produce high-quality bokeh. Fibonacci spirals are more uniform than random distribution, avoiding clustering
- Chromatic Aberration: 4-8 samples produce good results, since chromatic aberration is inherently a low-frequency variation

### 5. Leverage Bilinear Interpolation for Free Blur

Sampling between two texels causes the GPU hardware to automatically perform bilinear blending, equivalent to a 2-tap average. A single sample effectively obtains weighted information from 4 texels.

Application: Optimize a 5-tap Gaussian blur to 3 texture samples (1 at center + 1 on each side, with the side sample points placed between two texels).

### 6. Conditional Compilation

Use `#define` switches to control each post-processing module. Disabling unneeded effects has zero cost — the preprocessor completely removes the code, generating no instructions.

```glsl
#define ENABLE_BLOOM 0  // Disable bloom; the branch code is completely absent after compilation
```

### 7. Avoid Branching

if/else statements in post-processing should be converted to mathematical forms like `mix`/`step`/`smoothstep` whenever possible, avoiding GPU warp divergence.

Example:
```glsl
// Bad: if/else branching
if (brightness > threshold) color = bright_path; else color = dark_path;

// Good: mathematical form
float t = step(threshold, brightness);
color = mix(dark_path, bright_path, t);
```

## Combination Suggestions

### 1. Bloom + Tone Mapping (Most Basic Combination)

Bloom is computed in linear HDR space, added to the scene, then tone mapping is applied. **The order must not be reversed** — doing bloom in LDR space means highlights have already been clamped, and bloom cannot correctly extract super-bright pixels.

```glsl
// Correct order
color += bloom;          // Add bloom in HDR space
color = tonemap(color);  // Then tone map
color = pow(color, vec3(1.0/2.2)); // Finally gamma
```

### 2. TAA + Motion Blur + DoF (Physical Camera Simulation)

TAA removes aliasing first, then DoF and motion blur can share a sampling loop. TAA's sub-pixel jitter can also complement motion blur's temporal jitter.

Suggested pipeline order:
1. TAA (Buffer D): Blend current frame + history frame
2. DoF + Motion Blur (Image pass): Shared sampling loop
3. Other subsequent effects

### 3. Chromatic Aberration + Vignette + Film Grain (Lens Simulation Trio)

These three effects all simulate physical lens imperfections; when combined, the image has a strong "real footage" feel.

Execution order:
1. Chromatic Aberration (CA) is done during the sampling stage — directly replaces the normal `texture()` call
2. Vignette is applied after all color processing, multiplicatively
3. Grain is applied last, additively

### 4. Color Grading + Tone Mapping + Contrast (Color Pipeline)

Color grading (multiplication/power adjustments) is done in linear space, tone mapping handles HDR compression, and the S-curve contrast is applied in gamma space. The order of these three steps determines the final color style.

Key point: Color grading in linear space produces the most natural results, because the perceived brightness relationships are correct in linear space.

### 5. Bloom + Lens Flare (Cinematic Light Effects)

Bloom provides soft highlight diffusion; lens flare provides starburst and ghosts. Both share the same bright-pass extraction result, but flare computes directional patterns while bloom is isotropic blur.

### 6. Multi-Pass Complete Pipeline (Production-Grade)

Recommended production-grade pipeline:
- **Buffer A**: Scene rendering + velocity/depth encoding (pack motion vectors and depth into alpha channel or additional textures)
- **Buffer B**: Bloom downsampling + horizontal blur (horizontal Gaussian on Buffer A's bright-pass output)
- **Buffer C**: Bloom vertical blur (vertical Gaussian on Buffer B, completing separable bloom)
- **Buffer D**: TAA (current frame + history frame blending, needs to read Buffer D's own historical output)
- **Image**: Final compositing — DoF + Motion Blur + Bloom compositing + Tone Mapping + Color Grading + Vignette + Grain + Dithering
