# Atmospheric & Subsurface Scattering — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, mathematical derivations, variant details, and complete combination code examples.

## Prerequisites

Foundational concepts required before using this Skill:

- **GLSL Fundamentals**: uniforms, varyings, built-in functions
- **Vector Math**: dot product, cross product, vector normalization
- **Ray-Sphere Intersection**: given a ray origin and direction, find the intersection distances with a sphere surface
- **Physical Meaning of Exponential Functions** (Beer-Lambert Law): light attenuates exponentially through a medium, `I = I₀ × e^(-σ×d)`, where σ is the extinction coefficient and d is the distance
- **Basic Ray Marching Concepts**: advancing step by step along a ray direction, accumulating information at each sample point

## Core Principles

Atmospheric scattering simulates the process of photons passing through the atmosphere and colliding with gas molecules/aerosol particles, changing direction. There are three core physical mechanisms:

### 1. Rayleigh Scattering (Molecular Scattering)

Caused by particles much smaller than the wavelength of light (nitrogen, oxygen molecules). **Short wavelengths (blue light) scatter much more strongly than long wavelengths (red light)** — this is why the sky is blue and sunsets are red.

The scattering coefficient is inversely proportional to the fourth power of wavelength:
```
β_R(λ) ∝ 1/λ⁴
```
Typical sea-level values for Earth: `β_R = vec3(5.5e-6, 13.0e-6, 22.4e-6)` (RGB channels, in m⁻¹)

**Rayleigh Phase Function** (describes the angular distribution of light scattering, symmetric front-to-back):
```
P_R(θ) = 3/(16π) × (1 + cos²θ)
```

### 2. Mie Scattering (Aerosol Scattering)

Caused by particles roughly the same size as the wavelength of light (water droplets, dust). **Wavelength-independent (all colors scatter equally)**, but with strong forward scattering characteristics, forming the halo around the sun.

Typical sea-level values for Earth: `β_M = vec3(21e-6)` (same for all channels)

**Henyey-Greenstein Phase Function** (describes the strong forward scattering of Mie scattering):
```
P_HG(θ, g) = (1 - g²) / (4π × (1 + g² - 2g·cosθ)^(3/2))
```
Where `g ∈ (-1, 1)` controls forward scattering strength; typical Earth atmosphere value `g ≈ 0.76 ~ 0.88`.

### 3. Beer-Lambert Attenuation

Exponential attenuation of light through a medium:
```
T(A→B) = exp(-∫ σ_e(s) ds)   // Transmittance from A to B
```
Where `σ_e` is the extinction coefficient (extinction = scattering + absorption).

### Overall Algorithm Flow

March along the view direction (ray march), at each sample point:
1. Compute the atmospheric density at that point (decreases exponentially with altitude)
2. Perform a second march toward the light source to compute the optical depth from the sun to that point
3. Use Beer-Lambert to calculate the sun light intensity reaching that point
4. Use the phase function to compute the amount of light scattered toward the camera
5. Accumulate contributions from all sample points

## Implementation Steps

### Step 1: Ray-Sphere Intersection

**What**: Compute the intersection points of the view ray with the atmospheric shell to determine the ray march start/end range.

**Why**: The atmosphere is a spherical shell around the planet; we only integrate within the shell.

```glsl
// Ray-sphere intersection, returns distances to two intersection points (t_near, t_far)
// p: ray origin (relative to sphere center), dir: ray direction, r: sphere radius
vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5); // No intersection
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```

Derivation: sphere equation `|p + t·dir|² = r²` expands to `t² + 2t·dot(p,dir) + dot(p,p) - r² = 0`. Since `dir` is normalized, `a=1` can be omitted, and the two t values are solved directly with the quadratic formula.

### Step 2: Define Atmospheric Physical Constants

**What**: Set the scale parameters and scattering coefficients for the planet and atmosphere.

**Why**: These physical constants determine the sky's color characteristics. The different RGB values in Rayleigh produce the blue sky (blue channel has the largest scattering coefficient); Mie's uniform values produce white halos (all wavelengths scatter equally).

```glsl
#define PLANET_RADIUS 6371e3          // Earth radius (m)
#define ATMOS_RADIUS  6471e3          // Atmosphere outer radius (m), about 100km above Earth's radius
#define PLANET_CENTER vec3(0.0)       // Planet center position

// Scattering coefficients (m⁻¹), sea-level values
#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6) // Tunable: Rayleigh scattering, changes sky base color
#define BETA_MIE vec3(21e-6)                      // Tunable: Mie scattering, changes halo intensity
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6) // Tunable: ozone absorption, affects zenith deep blue

// Mie phase function anisotropy parameter
#define MIE_G 0.76   // Tunable: 0.76~0.88, larger = more concentrated sun halo

// Scale heights (m): altitude at which density drops to 1/e
#define H_RAY 8000.0  // Tunable: Rayleigh scale height, larger = thicker atmosphere
#define H_MIE 1200.0  // Tunable: Mie scale height, larger = higher haze layer

// Ozone parameters (optional)
#define H_OZONE 30e3         // Ozone peak altitude
#define OZONE_FALLOFF 4e3    // Ozone falloff width

// Sample step counts
#define PRIMARY_STEPS 32 // Tunable: primary ray steps, more = higher quality
#define LIGHT_STEPS 8    // Tunable: light direction steps
```

Parameter tuning guide:
- Increase overall `BETA_RAY` → more vivid sky color
- Modify `BETA_RAY` RGB ratios → change sky base hue (e.g., increasing the red component produces a more purple sky)
- Increase `BETA_MIE` → brighter halo around the sun, more haze
- Increase `MIE_G` → halo more concentrated toward the sun direction (narrower disk)
- Increase `H_RAY` → effective atmosphere thickness increases, sky color more uniform
- Increase `H_MIE` → haze layer higher, low-altitude fog effect weakened

### Step 3: Implement Phase Functions

**What**: Compute the probability distribution of light being scattered at different angles.

**Why**: The Rayleigh phase is symmetrically distributed (scatters both forward and backward); the Mie phase is strongly biased forward. This determines the brightness distribution across the sky — brighter facing the sun (Mie dominant), with some brightness away from the sun (Rayleigh dominant).

```glsl
// Rayleigh phase function: symmetric front-to-back
float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * 3.14159265) * (1.0 + cosTheta * cosTheta);
}

// Henyey-Greenstein phase function: forward scattering
// g: anisotropy parameter, 0 = isotropic, close to 1 = strong forward scattering
float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * 3.14159265) * num / denom;
}
```

Note: the Mie phase function here uses the Cornette-Shanks improved version (with an additional `(1 + cos²θ)` term in the numerator and `(2 + g²)` normalization correction in the denominator), which is more physically accurate than the original HG.

### Step 4: Atmospheric Density Sampling

**What**: Compute the atmospheric particle density at a given point based on altitude.

**Why**: Atmospheric density decreases exponentially with altitude, and different components (Rayleigh, Mie, ozone) have different decay rates. Rayleigh particles (gas molecules) have a scale height of about 8km, Mie particles (aerosols) are concentrated in the lower layer with a scale height of about 1.2km, and ozone peaks at approximately 30km altitude.

```glsl
// Returns vec3(rayleigh_density, mie_density, ozone_density)
vec3 atmosphereDensity(vec3 pos, float planetRadius) {
    float height = length(pos) - planetRadius;

    float densityRay = exp(-height / H_RAY);
    float densityMie = exp(-height / H_MIE);

    // Ozone: peaks at ~30km altitude, approximated with Lorentzian distribution
    float denom = (H_OZONE - height) / OZONE_FALLOFF;
    float densityOzone = (1.0 / (denom * denom + 1.0)) * densityRay;

    return vec3(densityRay, densityMie, densityOzone);
}
```

Mathematical explanation of ozone distribution: `1/(x² + 1)` is the form of a Lorentzian/Cauchy distribution, reaching its maximum value of 1 at `x=0` (i.e., `height = H_OZONE`), then symmetrically decaying on both sides. Multiplying by `densityRay` accounts for ozone also being affected by the overall atmospheric density decrease.

### Step 5: Light Direction Optical Depth

**What**: From a sample point on the primary ray, march toward the sun to the atmosphere edge, accumulating optical depth.

**Why**: This determines how much the sunlight has been attenuated before reaching that point. At sunset, the light path passes through more atmosphere, and blue light is scattered away (because Rayleigh scattering coefficient's blue component is largest), leaving only red light — this is the physical reason sunsets are red.

```glsl
// Compute optical depth from pos along sunDir to the atmosphere edge
vec3 lightOpticalDepth(vec3 pos, vec3 sunDir) {
    float atmoDist = raySphereIntersect(pos - PLANET_CENTER, sunDir, ATMOS_RADIUS).y;
    float stepSize = atmoDist / float(LIGHT_STEPS);
    float rayPos = stepSize * 0.5;

    vec3 optDepth = vec3(0.0); // (ray, mie, ozone)

    for (int i = 0; i < LIGHT_STEPS; i++) {
        vec3 samplePos = pos + sunDir * rayPos;
        float height = length(samplePos - PLANET_CENTER) - PLANET_RADIUS;

        // If sample point is below the surface, it's occluded by the planet
        if (height < 0.0) return vec3(1e10); // Fully occluded

        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS);
        optDepth += density * stepSize;

        rayPos += stepSize;
    }
    return optDepth;
}
```

`stepSize * 0.5` as the starting offset is the midpoint sampling rule, which approximates the integral more accurately than endpoint sampling.

### Step 6: Primary Scattering Integral (Core Loop)

**What**: Ray march along the view direction, computing the in-scattering contribution at each sample point and accumulating.

**Why**: This is the core of the entire algorithm — integrating all scattered light along the view direction that reaches the eye. Each point's contribution = sunlight reaching that point × density at that point × attenuation from that point to the camera.

Mathematical expression:
```
L(camera) = ∫[tStart→tEnd] sunIntensity × T(sun→s) × σ_s(s) × P(θ) × T(s→camera) ds
```
Where T is transmittance, σ_s is the scattering coefficient, and P is the phase function.

```glsl
vec3 calculateScattering(
    vec3 rayOrigin,    // Camera position
    vec3 rayDir,       // View direction
    float maxDist,     // Maximum distance (scene occlusion)
    vec3 sunDir,       // Sun direction
    vec3 sunIntensity  // Sun intensity
) {
    // Compute ray-atmosphere intersection
    vec2 atmoHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, ATMOS_RADIUS);
    if (atmoHit.x > atmoHit.y) return vec3(0.0); // Missed atmosphere

    // Compute ray-planet intersection (ground occlusion)
    vec2 planetHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, PLANET_RADIUS);

    // Determine march range
    float tStart = max(atmoHit.x, 0.0);
    float tEnd = atmoHit.y;
    if (planetHit.x > 0.0) tEnd = min(tEnd, planetHit.x); // Ground occlusion
    tEnd = min(tEnd, maxDist); // Scene object occlusion

    float stepSize = (tEnd - tStart) / float(PRIMARY_STEPS);

    // Precompute phase functions (view-sun angle is constant along the entire ray)
    float cosTheta = dot(rayDir, sunDir);
    float phaseR = phaseRayleigh(cosTheta);
    float phaseM = phaseMie(cosTheta, MIE_G);

    // Accumulators
    vec3 totalRay = vec3(0.0); // Rayleigh in-scatter
    vec3 totalMie = vec3(0.0); // Mie in-scatter
    vec3 optDepthI = vec3(0.0); // View direction optical depth (ray, mie, ozone)

    float rayPos = tStart + stepSize * 0.5;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 samplePos = rayOrigin + rayDir * rayPos;

        // 1. Sample density
        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        optDepthI += density;

        // 2. Compute light direction optical depth
        vec3 optDepthL = lightOpticalDepth(samplePos, sunDir);

        // 3. Beer-Lambert attenuation: total attenuation from sun through this point to camera
        vec3 tau = BETA_RAY * (optDepthI.x + optDepthL.x)
                 + BETA_MIE * 1.1 * (optDepthI.y + optDepthL.y) // 1.1 is Mie extinction/scattering ratio
                 + BETA_OZONE * (optDepthI.z + optDepthL.z);
        vec3 attenuation = exp(-tau);

        // 4. Accumulate in-scattering
        totalRay += density.x * attenuation;
        totalMie += density.y * attenuation;

        rayPos += stepSize;
    }

    // 5. Final color = scattering coefficient × phase function × accumulated scattering
    return sunIntensity * (
        totalRay * BETA_RAY * phaseR +
        totalMie * BETA_MIE * phaseM
    );
}
```

Key detail explanations:
- `1.1` is the Mie extinction/scattering ratio: Mie particles not only scatter light but also absorb a small amount, so the extinction coefficient ≈ 1.1 × scattering coefficient
- `optDepthI` records all three components simultaneously for correctly compositing all extinction contributions in the attenuation calculation
- Phase functions are precomputed outside the loop because the angle between view and sun directions is constant along the entire ray

### Step 7: Tone Mapping and Output

**What**: Apply tone mapping and gamma correction to the HDR scattering results.

**Why**: The scattering calculation outputs HDR linear values (potentially much greater than 1.0), which must be mapped to [0,1] for display. Different tonemapping methods affect the final look:

- **Exposure mapping `1 - exp(-x)`**: simplest, naturally saturates and never overexposes, but limited highlight detail
- **Reinhard**: preserves more highlight detail, suitable for high dynamic range scenes
- **ACES**: cinematic tone mapping, richer colors but more complex implementation

```glsl
// Method 1: Simple exposure mapping (most common)
vec3 tonemapExposure(vec3 color) {
    return 1.0 - exp(-color); // Natural saturation, never overexposes
}

// Method 2: Reinhard (preserves more highlight detail)
vec3 tonemapReinhard(vec3 color) {
    float l = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 tc = color / (color + 1.0);
    return mix(color / (l + 1.0), tc, tc);
}

// Gamma correction
vec3 gammaCorrect(vec3 color) {
    return pow(color, vec3(1.0 / 2.2));
}
```

Reinhard implementation detail: uses a blend of luminance `l` (perceptually weighted) and per-channel mapping `tc`, balancing color fidelity and highlight detail.

## Variant Details

### Variant 1: Non-Physical Analytical Approximation (No Ray March)

**Difference from the base version**: No ray marching at all — uses analytical functions to simulate sky color with extremely high performance. Not based on physical scattering equations, but uses empirical formulas to simulate visual effects.

**Use cases**: Mobile platforms, backgrounds, scenes with low physical accuracy requirements.

**How it works**:
- `zenithDensity` simulates atmospheric density variation with viewing angle (denser looking toward the horizon)
- `getSkyAbsorption` uses `exp2` to simulate atmospheric absorption (similar to Beer-Lambert)
- `getMie` uses distance falloff + smoothstep to simulate the sun halo
- The final blend considers the sun altitude's effect on the overall sky color tone

**Performance comparison**: No loops, no ray march — only a small amount of math per pixel, 10-50x faster than the base version.

### Variant 2: With Ozone Absorption Layer

**Difference from the base version**: Adds ozone absorption as a third component, making the zenith deeper blue and introducing subtle purple tones at sunset.

**Use cases**: Pursuing more physically accurate sky colors.

**Physical principle**: Ozone primarily absorbs in the Chappuis band (500-700nm, i.e., green and red), which makes the zenith direction (short light path, remaining light after Rayleigh scattering is filtered by ozone) appear deeper blue. At sunset, the long light path makes ozone absorption more significant — after red is Rayleigh-scattered and green is ozone-absorbed, only blue-purple tones remain.

**Key modification**: Set `BETA_OZONE` to a non-zero value in the complete template to enable — already built-in.

### Variant 3: Subsurface Scattering (SSS)

**Difference from the base version**: Scatters inside a semi-transparent object rather than in the atmosphere. Estimates object thickness via SDF and controls light transmission with thickness.

**Use cases**: Candles, skin, jelly, leaves, and other translucent materials.

**How it works**:
1. Use Snell's law (`refract`) to calculate the refracted direction after light enters the object
2. March along the refracted direction in the SDF, accumulating negative distance values (SDF is negative inside the object)
3. Greater accumulated negative value means a thicker object, less light transmission
4. Use a power function to control the attenuation curve (`pow` parameter is tunable)

**Tunable parameters**:
- IOR (index of refraction): 1.3 (water) ~ 1.5 (glass) ~ 2.0 (gemstone), affects refraction angle
- `MAX_SCATTER`: maximum scatter march distance, affects SSS penetration depth
- `SCATTER_STRENGTH`: scattering intensity multiplier
- Step size 0.2: smaller = more accurate but slower

**Usage**:
```glsl
float ss = max(0.0, subsurface(hitPos, viewDir, normal));
vec3 sssColor = albedo * smoothstep(0.0, 2.0, pow(ss, 0.6));
finalColor = mix(lambertian, sssColor, 0.7) + specular;
```

### Variant 4: LUT Precomputation Pipeline (Production-Grade)

**Difference from the base version**: Precomputes Transmittance, Multiple Scattering, and Sky-View into separate LUT textures; at runtime only performs lookups, with extremely high frame rates.

**Use cases**: Production-grade sky rendering in game engines and real-time applications requiring high frame rates.

**Architecture details**:

- **Buffer A (Transmittance LUT)**: 256x64 texture, parameterized by (sunCosZenith, height), storing transmittance from a certain height along a direction to the atmosphere edge. This is the most fundamental LUT; all other LUTs depend on it.

- **Buffer B (Multiple Scattering LUT)**: 32x32 texture, precomputing multiple scattering contributions. Single scattering is not accurate enough — in the real atmosphere, light is scattered multiple times. This LUT uses an iterative method to approximate the cumulative effect of multiple scattering.

- **Buffer C (Sky-View LUT)**: 200x200 texture, storing sky colors for all directions. Uses nonlinear height mapping to allocate more precision to the horizon region (where color changes are most dramatic).

- **Image Pass**: Only looks up the Sky-View LUT + overlays the sun disk; each pixel requires only one texture query.

```glsl
// Transmittance LUT query (from Hillaire 2020 implementation)
vec3 getValFromTLUT(sampler2D tex, vec2 bufferRes, vec3 pos, vec3 sunDir) {
    float height = length(pos);
    vec3 up = pos / height;
    float sunCosZenithAngle = dot(sunDir, up);
    vec2 uv = vec2(
        256.0 * clamp(0.5 + 0.5 * sunCosZenithAngle, 0.0, 1.0),
        64.0 * max(0.0, min(1.0, (height - groundRadiusMM) / (atmosphereRadiusMM - groundRadiusMM)))
    );
    uv /= bufferRes;
    return texture(tex, uv).rgb;
}
```

**Performance**: The Image Pass is nearly O(1); all heavy computation is done in low-resolution LUTs. LUTs can be incrementally updated as the sun angle changes.

### Variant 5: Analytical Fast Atmosphere (No Ray March but Supports Aerial Perspective)

**Difference from the base version**: Uses analytical exponential approximations instead of ray marching, while supporting distance-attenuated aerial perspective effects.

**Use cases**: Game scenes requiring atmospheric perspective without per-pixel ray marching.

**How it works**:
- `getRayleighMie` uses `1 - exp(-x)` form to approximate the scattering integral (analytical solution based on Beer-Lambert)
- `getLightTransmittance` uses multiple exponential term superposition to approximate optical depth at different sun altitudes
- No loops required — only a fixed number of math operations per pixel

```glsl
// Based on Felix Westin's Fast Atmosphere
void getRayleighMie(float opticalDepth, float densityR, float densityM, out vec3 R, out vec3 M) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    R = (1.0 - exp(-opticalDepth * densityR * C_RAYLEIGH / 2.5)) * 2.5;
    M = (1.0 - exp(-opticalDepth * densityM * C_MIE / 0.5)) * 0.5;
}

// Analytical approximation of light transmittance (replaces ray march)
vec3 getLightTransmittance(vec3 lightDir) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    vec3 C_OZONE = vec3(0.650, 1.881, 0.085) * 1e-6;
    float extinction = exp(-clamp(lightDir.y + 0.05, 0.0, 1.0) * 40.0)
                     + exp(-clamp(lightDir.y + 0.5, 0.0, 1.0) * 5.0) * 0.4
                     + pow(clamp(1.0 - lightDir.y, 0.0, 1.0), 2.0) * 0.02
                     + 0.002;
    return exp(-(C_RAYLEIGH + C_MIE + C_OZONE) * extinction * 1e6);
}
```

**Mathematical basis of the analytical approximation**: Treating the atmosphere as a single uniform layer, the scattering integral `∫ e^(-σx) dx` has the analytical solution `(1 - e^(-σL)) / σ`. The `2.5` and `0.5` in the code are empirical scaling factors to make the analytical result visually approximate a full ray march.

## Performance Optimization Details

### Bottleneck 1: Nested Ray March (O(N×M) Samples)

N primary ray steps × M light direction steps per step = N×M density calculations.

**Optimization approaches**:
- **Reduce step counts**: Use `PRIMARY_STEPS=12, LIGHT_STEPS=4` on mobile; visual difference is small but performance improvement is significant
- **Analytical approximation**: Replace the light direction ray march with the Fast Atmosphere approach, reducing complexity from O(N×M) to O(N)
- **Transmittance LUT**: After precomputation, runtime only performs lookups, reducing complexity to O(N) or even O(1)

### Bottleneck 2: Dense exp() and pow() Calls

Multiple exponential function calls at each sample point — these are relatively expensive operations on GPUs.

**Optimization approaches**:
- Replace Henyey-Greenstein phase function with Schlick approximation:
```glsl
// Schlick approximation, only 1 division, no pow
float k = 1.55 * g - 0.55 * g * g * g;
float phaseSchlick = (1.0 - k * k) / (4.0 * PI * pow(1.0 + k * cosTheta, 2.0));
```
- Combine multiple exp calls: `exp(a) * exp(b) = exp(a+b)`, reducing exp call count
- Use `exp2` instead of `exp` in scenarios with lower precision requirements (exp2 is faster on some GPUs)

### Bottleneck 3: Full-Screen Per-Pixel Computation

Each pixel independently computes the full scattering.

**Optimization approaches**:
- **Sky-View LUT**: Render the sky to a low-resolution LUT (e.g., 200x200), then look up at full resolution. Allocate more resolution near the horizon (nonlinear mapping)
- **Half-resolution rendering**: Compute scattering at half resolution, then bilinearly upsample. For sky — a low-frequency signal — quality loss is minimal

### Bottleneck 4: High Sample Count Needed to Avoid Banding

Low step counts lead to visible banding artifacts.

**Optimization approaches**:
- **Non-uniform stepping**: `newT = ((i + 0.3) / numSteps) * tMax`, offset by 0.3 instead of 0.5 to reduce visual artifacts
- **Jittered start offset**: `startOffset += hash(fragCoord) * stepSize`, randomly offsetting the march start per pixel
- **Temporal blue noise dithering**: Use temporal blue noise to jitter sample positions across frames; combined with TAA, banding is nearly eliminated

## Combination Suggestions

### 1. Atmospheric Scattering + Volumetric Clouds

Atmospheric scattering provides sky background color and light source color; volumetric cloud lighting uses the atmospheric transmittance to determine the sun light color reaching the cloud layer.

Key integration points:
- Setting the `maxDist` parameter of the atmospheric scattering function to the cloud layer distance achieves correct pre-cloud atmospheric effects
- During cloud layer rendering, use the transmittance LUT to get the sun light color upon reaching the cloud layer
- Sky color behind clouds should be the full atmospheric scattering result

```glsl
// Pseudo-code example
float cloudDist = rayMarchClouds(rayOrigin, rayDir);
vec3 cloudColor = calculateCloudLighting(cloudPos, sunDir, transmittance);
vec3 skyBehind = calculateScattering(rayOrigin, rayDir, 1e12, sunDir, sunIntensity);
vec3 skyBeforeCloud = calculateScattering(rayOrigin, rayDir, cloudDist, sunDir, sunIntensity);

// Compositing: pre-cloud atmosphere + cloud × cloud opacity + post-cloud sky × transmittance
vec3 final = skyBeforeCloud + cloudColor * cloudAlpha + skyBehind * (1.0 - cloudAlpha) * atmosphereTransmittance;
```

### 2. Atmospheric Scattering + SDF Scene

Pass the SDF ray march hit distance as the `maxDist` parameter to `calculateScattering()`, and the scene color as `sceneColor`, to automatically get aerial perspective effects.

```glsl
// SDF ray march yields hit information
float hitDist = sdfRayMarch(rayOrigin, rayDir);
vec3 sceneColor = shadeSurface(hitPos, normal, lightDir);

// Atmospheric scattering automatically handles perspective
vec3 final = calculateScattering(
    rayOrigin, rayDir, hitDist,
    sceneColor, sunDir, SUN_INTENSITY
);
```

### 3. Atmospheric Scattering + God Rays

Adding an occlusion parameter in the scattering integral (via shadow map or additional ray march for occlusion detection) can produce volumetric light beam effects.

```glsl
// Add occlusion detection in the main loop
for (int i = 0; i < PRIMARY_STEPS; i++) {
    // ... density sampling ...

    // God rays: check if sample point is occluded
    float occlusion = 1.0;
    if (sdfScene(samplePos + sunDir * 0.1) < 0.0) {
        occlusion = 0.0; // Occluded by scene object, no in-scattering
    }

    totalRay += density.x * attenuation * occlusion;
    totalMie += density.y * attenuation * occlusion;
}
```

The Fast Atmosphere example implements this functionality through the `occlusion` parameter.

### 4. Atmospheric Scattering + Terrain Rendering

Use aerial perspective: distant terrain colors blend into atmospheric scattering color based on distance.

Key formula:
```glsl
// Basic aerial perspective
vec3 finalColor = terrainColor * transmittance + inscattering;

// transmittance: atmospheric transmittance from camera to terrain point
// inscattering: scattered light between camera and terrain point
// Distant objects: transmittance → 0, inscattering dominates → appears blue/gray
```

### 5. SSS + PBR Materials

Combine subsurface scattering with GGX microsurface specular and Fresnel reflection. SSS contribution replaces part of the diffuse (via mix), with the specular layer added on top:

```glsl
// Complete PBR + SSS shading
float fresnel = pow(max(0.0, 1.0 + dot(normal, viewDir)), 5.0);
vec3 diffuse = mix(lambert, sssContribution, 0.7);  // SSS replaces part of diffuse
vec3 final = ambient + albedo * diffuse + specular + fresnel * envColor;
```

Layering logic:
1. Bottom layer: ambient light
2. Diffuse layer: blend of Lambert and SSS (SSS allows light to pass through dark sides)
3. Specular layer: GGX microsurface reflection
4. Fresnel layer: enhanced environment reflection at grazing angles
