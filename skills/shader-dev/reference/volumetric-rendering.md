# Volumetric Rendering — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL Fundamentals**: uniforms, varyings, built-in functions
- **Vector Math**: dot product, cross product, normalize
- **Ray Representation**: `P = ro + t * rd` (ray origin + t × ray direction)
- **Noise Function Basics**: value noise, Perlin noise, fBM (Fractal Brownian Motion)
- **Basic Optical Concepts**:
  - Transmittance: the fraction of light remaining after passing through a medium
  - Scattering: light changing direction within a medium
  - Absorption: light energy being converted to heat by the medium

## Core Principles

The core of volumetric rendering is **Ray Marching**: along each view ray, advancing with fixed or adaptive step sizes, querying medium density at each sample point, and accumulating color and opacity.

### Key Mathematical Formulas

#### 1. Beer-Lambert Transmittance Law

Transmittance of light passing through a medium of thickness `d` with extinction coefficient `σe`:

```
T = exp(-σe × d)
```

Where `σe = σs + σa` (scattering coefficient + absorption coefficient).

**Physical meaning**: the larger the extinction coefficient or thicker the medium, the less light passes through. This is the fundamental law of all volumetric rendering.

#### 2. Front-to-Back Alpha Compositing

Standard form:
```
color_acc += sample_color × sample_alpha × (1.0 - alpha_acc)
alpha_acc += sample_alpha × (1.0 - alpha_acc)
```

Equivalent premultiplied alpha form (most commonly used in actual code):
```glsl
col.rgb *= col.a;           // Premultiply
sum += col * (1.0 - sum.a); // Front-to-back compositing
```

**Why front-to-back?** Because it allows early exit (early ray termination) when accumulated opacity approaches 1.0, saving significant computation.

#### 3. Henyey-Greenstein Phase Function

Describes the directional distribution of light scattering in a medium:

```
HG(cosθ, g) = (1 - g²) / (1 + g² - 2g·cosθ)^(3/2)
```

- `g > 0`: forward scattering (e.g., the silver lining effect in clouds) — light primarily continues along its original direction
- `g < 0`: backward scattering — light primarily reflects back
- `g = 0`: isotropic scattering — light scatters uniformly in all directions

**Practical application**: Clouds typically use a dual-lobe HG function, mixing a forward scattering lobe (g≈0.8) and a backward scattering lobe (g≈-0.2) to simulate the real light scattering characteristics of cloud layers. Forward scattering produces the silver lining, while backward scattering provides volume definition.

#### 4. Frostbite Improved Integration Formula

In each step, the scattered light is not simply `S × dt`, but a more precise integral:

```
Sint = (S - S × exp(-σe × dt)) / σe
```

**Why is improvement needed?** The naive `S × dt` integration overestimates scattered light at larger step sizes or stronger scattering, leading to energy non-conservation (image too bright or too dark). The Frostbite formula ensures energy conservation at any step size through precise integration of the Beer-Lambert law.

## Implementation Steps

### Step 1: Camera and Ray Construction

**What**: Generate a ray from the camera for each pixel.

**Why**: This is the starting point for all ray marching techniques. Camera position determines the viewing angle; ray direction determines the sampling path.

```glsl
// Normalize screen coordinates to [-1,1], correcting for aspect ratio
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Camera parameters
vec3 ro = vec3(0.0, 1.0, -5.0);  // Tunable: camera position
vec3 ta = vec3(0.0, 0.0, 0.0);   // Tunable: look-at target

// Build camera matrix
vec3 ww = normalize(ta - ro);
vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
vec3 vv = cross(uu, ww);

// Generate ray direction
float fl = 1.5; // Tunable: focal length, larger = narrower FOV
vec3 rd = normalize(uv.x * uu + uv.y * vv + fl * ww);
```

**Key parameter notes**:
- `ro`: camera position — changing it orbits around the volume
- `ta`: look-at target — the camera points toward this position
- `fl`: focal length — 1.0 ≈ 90° FOV, 1.5 ≈ 67° FOV, 2.0 ≈ 53° FOV
- Normalizing with `iResolution.y` ensures circles don't distort

### Step 2: Volume Boundary Intersection

**What**: Compute distances `tmin`/`tmax` where the ray enters and exits the volume, limiting the marching range.

**Why**: Avoids wasting samples in empty regions. Different volume shapes use different intersection methods.

```glsl
// --- Method A: Horizontal plane boundaries (cloud layers) ---
float yBottom = -1.0; // Tunable: volume bottom Y coordinate
float yTop    =  2.0; // Tunable: volume top Y coordinate
float tmin = (yBottom - ro.y) / rd.y;
float tmax = (yTop    - ro.y) / rd.y;
if (tmin > tmax) { float tmp = tmin; tmin = tmp; tmax = tmin; tmin = tmp; }
// In practice, handle edge cases like ray direction parallel to plane

// --- Method B: Sphere boundary (explosions, fur balls, atmospheres) ---
// Returns intersection distances of ray with sphere centered at origin with radius r
vec2 intersectSphere(vec3 ro, vec3 rd, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5); // No hit
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```

**Selection guide**:
- Use plane boundaries (Method A) for horizontally distributed volumes like cloud layers
- Use sphere intersection (Method B) for spherical volumes like explosions or planetary atmospheres
- AABB (axis-aligned bounding box) intersection can also be used for cuboid-shaped volumes

### Step 3: Density Field Definition

**What**: Define the medium density at each point in space. This is the most core and flexible part of volumetric rendering.

**Why**: The density field determines the volume's shape, texture, and dynamic characteristics. Different density functions produce completely different visual effects.

```glsl
// 3D Value Noise (classic texture-lookup-based implementation)
float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f); // smoothstep interpolation

    vec2 uv = (p.xy + vec2(37.0, 239.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

// fBM (Fractal Brownian Motion) — layering multiple frequency noises
float fbm(vec3 p) {
    float f = 0.0;
    f += 0.50000 * noise(p); p *= 2.02;
    f += 0.25000 * noise(p); p *= 2.03;
    f += 0.12500 * noise(p); p *= 2.01;
    f += 0.06250 * noise(p); p *= 2.02;
    f += 0.03125 * noise(p);
    return f;
}

// Cloud density function example
float cloudDensity(vec3 p) {
    vec3 q = p - vec3(0.0, 0.1, 1.0) * iTime; // Wind direction animation
    float f = fbm(q);
    // Use Y coordinate to limit cloud height range
    return clamp(1.5 - p.y - 2.0 + 1.75 * f, 0.0, 1.0);
}
```

**Density field design points**:
- The `noise` function uses texture lookup (`iChannel0`) to implement 3D value noise, faster than pure arithmetic implementations
- `fbm` layers 5 octaves of noise to produce natural fractal detail
- Non-integer frequency multipliers (2.02, 2.03) break repetitiveness
- In `cloudDensity`, `1.5 - p.y - 2.0` establishes a base density field that decreases with height
- Time offset `iTime` produces a wind-blown effect

### Step 4: Ray Marching Main Loop

**What**: March along the ray from `tmin` to `tmax`, sampling density at each step and accumulating color and opacity.

**Why**: This is the core loop of volumetric rendering. Step count and step size directly affect quality and performance.

```glsl
#define NUM_STEPS 64        // Tunable: march steps, more = finer
#define STEP_SIZE 0.05      // Tunable: fixed step size (or use adaptive)

vec4 raymarch(vec3 ro, vec3 rd, float tmin, float tmax, vec3 bgCol) {
    vec4 sum = vec4(0.0); // rgb = accumulated color (premultiplied alpha), a = accumulated opacity

    // Jitter starting position to eliminate banding artifacts
    float t = tmin + STEP_SIZE * fract(sin(dot(fragCoord, vec2(12.9898, 78.233))) * 43758.5453);

    for (int i = 0; i < NUM_STEPS; i++) {
        if (t > tmax || sum.a > 0.99) break; // Early exit: out of range or fully opaque

        vec3 pos = ro + t * rd;
        float den = cloudDensity(pos);

        if (den > 0.01) {
            // --- Color and lighting (see Step 5) ---
            vec4 col = vec4(1.0, 0.95, 0.8, den); // Placeholder color

            // Opacity scaling
            col.a *= 0.4; // Tunable: density scale factor
            // Can also multiply by step size: col.a = min(col.a * 8.0 * dt, 1.0);

            // Premultiply alpha and front-to-back compositing
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);
        }

        t += STEP_SIZE;
        // Adaptive step variant: t += max(0.05, 0.02 * t);
    }

    return clamp(sum, 0.0, 1.0);
}
```

**Key design decisions**:
- **Steps vs step size**: fixed step count suits known volume sizes; fixed step size suits uncertain volume sizes
- **Jittering**: without jittering, visible banding artifacts appear; adding pixel-dependent random offset converts banding into invisible noise
- **Early exit condition**: `sum.a > 0.99` is one of the most important performance optimizations
- **Density threshold**: `den > 0.01` skips empty regions, avoiding unnecessary lighting calculations
- **Adaptive step size**: `max(0.05, 0.02 * t)` gives small steps up close (good detail) and large steps at distance (fast)

### Step 5: Lighting Calculation

**What**: Compute lighting color for each sample point within the volume.

**Why**: Lighting is the determining factor for visual quality in volumetric rendering. Different lighting models suit different scenarios.

```glsl
// === Method A: Directional derivative lighting (simplest, single extra sample) ===
// Classic directional derivative method, requires only 1 extra noise sample
vec3 sundir = normalize(vec3(1.0, 0.0, -1.0)); // Tunable: sun direction
float dif = clamp((den - cloudDensity(pos + 0.3 * sundir)) / 0.6, 0.0, 1.0);
vec3 lin = vec3(1.0, 0.6, 0.3) * dif + vec3(0.91, 0.98, 1.05); // Sunlight color + sky light
```

**Method A details**: Estimates lighting by comparing density at the current point with an offset position along the light direction. The direction where density decreases indicates the light source. This is an approximate method — extremely fast but not very physically accurate. Suitable for stylized clouds or performance-critical scenarios.

```glsl
// === Method B: Volumetric shadow (secondary ray march) ===
// Volumetric shadow (Frostbite-style)
float volumetricShadow(vec3 from, vec3 lightDir) {
    float shadow = 1.0;
    float dt = 0.5;            // Tunable: shadow step size
    float d = dt * 0.5;
    for (int s = 0; s < 6; s++) { // Tunable: shadow steps (6-16)
        vec3 pos = from + lightDir * d;
        float muE = cloudDensity(pos);
        shadow *= exp(-muE * dt); // Beer-Lambert
        dt *= 1.3;               // Tunable: step size increase factor
        d += dt;
    }
    return shadow;
}
```

**Method B details**: For each sample point, performs a second ray march toward the light source, accumulating transmittance. This is the more physically accurate method but computationally expensive (each primary step requires an additional 6-16 shadow steps). The increasing step size (`dt *= 1.3`) is because distant regions contribute less to shadowing.

```glsl
// === Method C: Henyey-Greenstein phase function scattering ===
float HenyeyGreenstein(float cosTheta, float g) {
    float gg = g * g;
    return (1.0 - gg) / pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
}
// Mix forward and backward scattering
float sundotrd = dot(rd, -sundir);
float scattering = mix(
    HenyeyGreenstein(sundotrd, 0.8),   // Tunable: forward scattering g value
    HenyeyGreenstein(sundotrd, -0.2),  // Tunable: backward scattering g value
    0.5                                 // Tunable: blend ratio
);
```

**Method C details**: The phase function describes the probability distribution of light scattering in different directions. The dual-lobe HG function mixes forward and backward scattering, simulating the cloud silver lining effect (forward scattering lobe) and dark-side volume definition (backward scattering lobe). Forward scattering with `g=0.8` makes the lit side very bright — an important visual characteristic of real clouds.

### Step 6: Color Mapping

**What**: Map density values to colors.

**Why**: Different media (clouds, flames, explosions) require different coloring strategies.

```glsl
// === Method A: Density interpolation coloring (clouds) ===
vec3 cloudColor = mix(vec3(1.0, 0.95, 0.8),   // Lit side color (tunable)
                      vec3(0.25, 0.3, 0.35),   // Dark side color (tunable)
                      den);
```

**Method A details**: Low density areas show bright color (near white, simulating thin cloud translucency), high density areas show dark color (gray-blue, simulating thick cloud light blocking). Simple and efficient.

```glsl
// === Method B: Radial gradient coloring (explosions, flames) ===
vec3 computeColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8),
                      vec3(0.4, 0.15, 0.1), density);
    vec3 colCenter = 7.0 * vec3(0.8, 1.0, 1.0);  // Tunable: core highlight color
    vec3 colEdge = 1.5 * vec3(0.48, 0.53, 0.5);   // Tunable: edge color
    result *= mix(colCenter, colEdge, min(radius / 0.9, 1.15));
    return result;
}
```

**Method B details**: Explosion/flame cores are extremely bright (HDR values > 1.0, multiplied by 7.0), while edges are darker. Both density and distance from center determine the color. The core color multiplied by 7.0 creates an overexposure effect that, combined with post-processing tone mapping, produces a searing heat look.

```glsl
// === Method C: Height-based ambient gradient (production-grade clouds) ===
vec3 ambientLight = mix(
    vec3(39., 67., 87.) * (1.5 / 255.),   // Bottom ambient color (tunable)
    vec3(149., 167., 200.) * (1.5 / 255.), // Top ambient color (tunable)
    normalizedHeight
);
```

**Method C details**: Real cloud bottoms are darker blue (receiving ground reflection and sky scattering), while tops are brighter gray-blue (receiving more sky light). Using normalized height for interpolation produces a natural vertical gradient.

### Step 7: Final Compositing and Post-Processing

**What**: Blend volumetric rendering results with the background, applying tone mapping and post-processing.

**Why**: Post-processing significantly affects final visual quality.

```glsl
// Background sky
vec3 bgCol = vec3(0.6, 0.71, 0.75) - rd.y * 0.2 * vec3(1.0, 0.5, 1.0);
float sun = clamp(dot(sundir, rd), 0.0, 1.0);
bgCol += 0.2 * vec3(1.0, 0.6, 0.1) * pow(sun, 8.0); // Sun halo

// Composite volume with background
vec4 vol = raymarch(ro, rd, tmin, tmax, bgCol);
vec3 col = bgCol * (1.0 - vol.a) + vol.rgb;

// Sun flare
col += vec3(0.2, 0.08, 0.04) * pow(sun, 3.0);

// Tone mapping (simple smoothstep version)
col = smoothstep(0.15, 1.1, col);

// Optional: distance fog (inside the marching loop)
// col.xyz = mix(col.xyz, bgCol, 1.0 - exp(-0.003 * t * t));

// Optional: vignette
float vignette = 0.25 + 0.75 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);
col *= vignette;
```

**Post-processing details**:
- **Sky gradient**: `rd.y` controls sky color variation from horizon to zenith
- **Sun halo**: `pow(sun, 8.0)` produces a narrow, bright halo; higher exponent = narrower halo
- **Sun flare**: `pow(sun, 3.0)` produces a wider warm-colored flare
- **Distance fog**: `exp(-0.003 * t * t)` gradually blends distant volumes into the background
- **Tone mapping**: `smoothstep(0.15, 1.1, col)` lifts shadows, compresses highlights, and increases contrast
- **Vignette**: simulates lens vignette effect, guiding visual focus to the center of the frame

## Variant Details

### Variant 1: Emissive Volume (Flames/Explosions)

**Difference from the base version**: No external light source; color is entirely determined by density and position. Density maps to emissive color.

**Design concept**: Flames and explosions are self-luminous — no external lighting calculation needed. The core region is extremely bright (HDR), while edges are dim. Color is mapped through a combination of density and distance from center. Bloom effects are achieved by adding distance-attenuated light source contributions in the accumulation loop.

**Key code**:
```glsl
// Replace lighting calculation with emissive color mapping
vec3 emissionColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8), vec3(0.4, 0.15, 0.1), density);
    vec3 colCenter = 7.0 * vec3(0.8, 1.0, 1.0);
    vec3 colEdge = 1.5 * vec3(0.48, 0.53, 0.5);
    result *= mix(colCenter, colEdge, min(radius / 0.9, 1.15));
    return result;
}
// Use bloom effect in the accumulation loop
vec3 lightColor = vec3(1.0, 0.5, 0.25);
sum.rgb += lightColor / exp(lDist * lDist * lDist * 0.08) / 30.0;
```

### Variant 2: Physical Scattering Atmosphere (Rayleigh + Mie)

**Difference from the base version**: Uses nested ray marching to compute optical depth; separates Rayleigh and Mie scattering channels; uses precise Beer-Lambert transmittance.

**Design concept**: Atmospheric scattering requires handling two scattering mechanisms separately:
- **Rayleigh scattering**: wavelength-dependent (shorter wavelengths scatter more), producing the blue sky effect. Scattering coefficient proportional to λ⁻⁴.
- **Mie scattering**: wavelength-independent, primarily caused by aerosols/large particles, producing the orange-red of sunsets and white halos around the sun.

Density decreases exponentially with altitude, using different scale height parameters to control the altitude distribution of both scattering types. Nested ray marching (marching toward the sun for each sample point) computes optical depth for precise Beer-Lambert transmittance.

**Key code**:
```glsl
// Atmospheric density decreases exponentially with altitude
float density(vec3 p, float scaleHeight) {
    return exp(-max(length(p) - R_INNER, 0.0) / scaleHeight);
}
// Nested ray march to compute optical depth
float opticDepth(vec3 from, vec3 to, float scaleHeight) {
    vec3 s = (to - from) / float(NUM_STEPS_LIGHT);
    vec3 v = from + s * 0.5;
    float sum = 0.0;
    for (int i = 0; i < NUM_STEPS_LIGHT; i++) {
        sum += density(v, scaleHeight);
        v += s;
    }
    return sum * length(s);
}
// Rayleigh phase function
float phaseRayleigh(float cc) { return (3.0 / 16.0 / PI) * (1.0 + cc); }
// Combined Rayleigh + Mie
vec3 scatter = sumRay * kRay * phaseRayleigh(cc) + sumMie * kMie * phaseMie(-0.78, c, cc);
```

### Variant 3: Frostbite Energy-Conserving Integration

**Difference from the base version**: Uses an improved scattering integration formula that maintains energy conservation in strongly scattering media.

**Design concept**: Naive Euler integration `S × dt` is inaccurate at large step sizes or in dense media. The Frostbite formula performs precise exponential integration for each step's scattering, ensuring that the sum of accumulated scattering and transmittance never exceeds the incident light regardless of step size. This is especially important for dense fog, volumetric lighting, and similar scenarios.

**Key code**:
```glsl
// Replace naive integration with Frostbite formula
vec3 S = evaluateLight(p) * sigmaS * phaseFunction() * volumetricShadow(p, lightPos);
vec3 Sint = (S - S * exp(-sigmaE * dt)) / sigmaE; // Improved integration
scatteredLight += transmittance * Sint;
transmittance *= exp(-sigmaE * dt);
```

### Variant 4: Production-Grade Clouds (Horizon Zero Dawn Style)

**Difference from the base version**: Uses Perlin-Worley noise textures instead of procedural noise; layered density modeling (base shape + detail erosion); dual-lobe HG phase function; temporal reprojection anti-aliasing.

**Design concept**: Production-grade cloud rendering uses a layered approach:
1. **Low-frequency shape layer** (`cloudMapBase`): uses Perlin-Worley 3D texture to define the rough cloud shape
2. **Height gradient** (`cloudGradient`): controls density distribution with altitude based on cloud type (cumulus, stratus, etc.)
3. **High-frequency detail layer** (`cloudMapDetail`): higher frequency noise erodes edges, adding detail
4. **Coverage control** (`COVERAGE`): global parameter controlling the proportion of cloud coverage in the sky

Temporal reprojection is key to the production-grade approach: each frame renders only 1/16 of pixels (checkerboard pattern), then reprojects results to the current frame. Combined with 95% historical frame blending, it achieves high-quality results with minimal marching steps.

**Key code**:
```glsl
// Layered noise modeling
float m = cloudMapBase(pos, norY);          // Low-frequency shape
m *= cloudGradient(norY);                    // Height gradient
m -= cloudMapDetail(pos) * dstrength * 0.225; // High-frequency detail erosion
m = smoothstep(0.0, 0.1, m + (COVERAGE - 1.0));
// Dual-lobe HG scattering
float scattering = mix(
    HenyeyGreenstein(sundotrd, 0.8),   // Forward
    HenyeyGreenstein(sundotrd, -0.2),  // Backward
    0.5
);
// Temporal reprojection (between Buffers)
vec2 spos = reprojectPos(ro + rd * dist, iResolution.xy, iChannel1);
vec4 ocol = texture(iChannel1, spos, 0.0);
col = mix(ocol, col, 0.05); // 5% new frame + 95% history frame
```

### Variant 5: Gradient Normal Surface Lighting (Fur Ball / Volume Surface)

**Difference from the base version**: Uses central differencing to compute gradient normals within the volume, then applies diffuse + specular lighting as if it were a surface. Suitable for volume objects with a clear "surface" feel (fur, translucent spheres).

**Design concept**: Some volume objects (fur balls, fuzzy surfaces) are volumetric data but visually resemble surfaced objects. In this case, central differencing in the density field computes the gradient (the direction of fastest density change), which serves as the normal for traditional surface lighting models.

- **Half-Lambert**: `dot(N, L) * 0.5 + 0.5` compresses the dark side range, simulating subsurface scattering
- **Blinn-Phong**: provides specular reflection, adding material definition

**Key code**:
```glsl
// Central differencing for normals
vec3 furNormal(vec3 pos, float density) {
    float eps = 0.01;
    vec3 n;
    n.x = sampleDensity(pos + vec3(eps, 0, 0)) - density;
    n.y = sampleDensity(pos + vec3(0, eps, 0)) - density;
    n.z = sampleDensity(pos + vec3(0, 0, eps)) - density;
    return normalize(n);
}
// Half-Lambert diffuse + Blinn-Phong specular
vec3 N = -furNormal(pos, density);
float diff = max(0.0, dot(N, L) * 0.5 + 0.5);  // Half-Lambert
float spec = pow(max(0.0, dot(N, H)), 50.0);     // Tunable: specular sharpness
```

## In-Depth Performance Optimization

### 1. Early Ray Termination

Immediately break from the loop when accumulated opacity exceeds a threshold (e.g., 0.99). This is the most important optimization — used by all analyzed shaders.

**Effect**: For dense volumes (such as thick cloud layers), many rays can exit within 20-30 steps instead of completing all 80+ steps, achieving 2-4x performance improvement.

### 2. LOD Noise

Reduce the fBM octave count based on ray distance. Distant areas don't need high-frequency detail:
```glsl
int lod = 5 - int(log2(1.0 + t * 0.5));
```

**Effect**: Distant areas use only 2-3 fBM octaves (vs 5 up close), reducing noise sampling by 40-60%. Since distant pixels cover a larger spatial range, high-frequency detail wouldn't be visible anyway.

### 3. Adaptive Step Size

Small steps up close (fine detail), large steps at distance (speed):
```glsl
float dt = max(0.05, 0.02 * t);
```

**Effect**: Significantly reduces the number of distant steps without noticeably degrading near-field quality. However, abrupt step size changes may cause visual discontinuities.

### 4. Dithering

Add pixel-dependent random offset at the ray starting position to eliminate stepping banding artifacts:
```glsl
t += STEP_SIZE * hash(fragCoord);
```

**Note**: Dithering doesn't improve performance but significantly improves visual quality — converting visible banding artifacts into imperceptible high-frequency noise.

### 5. Bounding Volume Clipping

Only march within the interval where the ray intersects the volume (plane clipping, sphere intersection, AABB clipping).

**Effect**: For volumes that occupy a small portion of the screen, many rays can skip marching entirely. Performance improvement depends on the volume's screen coverage area.

### 6. Density Threshold Skip

Skip lighting calculations when density is below a threshold (lighting is often the most expensive part):
```glsl
if (den > 0.01) { /* compute lighting and compositing */ }
```

**Effect**: Lighting calculations (especially secondary volumetric shadow marching) are the most time-consuming part. Skipping lighting for low-density regions saves significant computation.

### 7. Minimal Shadow Step Count

Volumetric self-shadow step counts can be far fewer than the main loop (6-16 steps suffice), with increasing step sizes to cover greater distances.

**Reason**: Human eyes are less sensitive to shadow detail than to shape detail. 6 steps with 1.3x increasing step size can cover approximately 20 units of distance.

### 8. Temporal Reprojection

Reproject the previous frame's results to the current frame for blending, dramatically reducing the required marching steps per frame.

**Typical configuration**: Using only 12 steps + 95% historical frame blending (`mix(oldColor, newColor, 0.05)`) can produce quality far exceeding 12-step single-frame rendering.

**Caveats**:
- Requires an additional Buffer for storing the historical frame
- Fast motion may cause ghosting
- Requires correct reprojection matrix handling for camera movement

## Combination Suggestions

### 1. SDF Terrain + Volumetric Clouds

Render ground/mountains with SDF ray marching, then render cloud layers above using volumetric marching. The two mutually occlude through depth values.

**Implementation points**:
- Render SDF terrain first, recording hit depth
- During volumetric marching, stop at the depth value (ground occludes clouds)
- If the ray passes through the cloud layer before hitting the ground, march within the cloud interval and terminate at the ground

### 2. Volumetric Fog + Scene Lighting

Overlay volumetric fog on existing SDF/polygon scenes, applying `color = color * transmittance + scatteredLight` to already-rendered scenes.

**Implementation points**:
- After rendering the scene, march fog along the ray for each pixel
- Accumulate fog scattering and transmittance
- Final color = scene color × transmittance + fog scattered light

### 3. Multi-Layer Volumes

Different heights or regions use different density functions (e.g., high-altitude cumulus + low-altitude fog layer), each marched independently then composited.

**Implementation points**:
- Each layer has its own boundaries and density function
- Can be processed in the same marching loop (checking which layer the current point is in), or marched separately then composited
- Separate marching is more flexible but requires correct inter-layer occlusion handling

### 4. Particle System + Volume

Particles provide macro-scale motion and shape; volumetric rendering adds internal detail and lighting to particles.

### 5. Post-Process Light Shafts (God Rays)

After volumetric rendering, add light shaft effects using radial blur or screen-space ray marching to enhance volume definition.

**Implementation points**:
- In screen space, sample radially outward from the sun position, accumulating brightness
- Or for each pixel, march a short distance along the light source direction, sampling occluder depth
- Light shaft intensity is multiplied by the dot product of light direction and view direction to control visible angles

### 6. Procedural Sky + Volumetric Clouds

First render a procedural sky/atmospheric scattering as background, then overlay volumetric clouds on top. The transition between the two is achieved through distance fog for natural blending.

**Implementation points**:
- Use an atmospheric scattering model (Variant 2) or a simplified gradient model for the sky
- Apply distance fog within the volumetric marching loop: `mix(litCol, bgCol, 1.0 - exp(-0.003 * t * t))`
- Distant clouds naturally blend into the sky color, avoiding abrupt boundaries
