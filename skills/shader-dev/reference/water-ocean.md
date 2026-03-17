# Water & Ocean Rendering — Detailed Reference

This document is the complete reference for [SKILL.md](SKILL.md), covering prerequisites, detailed explanations for each step, variant descriptions, in-depth performance optimization analysis, and complete code examples for combination suggestions.

## Prerequisites

- **GLSL Fundamentals**: uniforms, varyings, built-in functions
- **Vector Math**: dot product, cross product, reflection/refraction vectors
- **Basic Raymarching Concepts**
- **FBM (Fractal Brownian Motion) / Multi-octave Noise Layering Basics**
- **Physical Intuition of the Fresnel Effect**: strong reflection at grazing angles, strong transmission at normal incidence

## Core Principles

The essence of water rendering is solving three core problems: **water surface shape generation**, **light-water surface interaction**, and **water body color compositing**.

### 1. Wave Generation: Exponential Sine Layering + Derivative Domain Warping

Traditional sum-of-sines uses `sin(x)` to produce symmetric waveforms, but real ocean waves have **sharp crests and broad troughs**. The core formula:

```
wave(x) = exp(sin(x) - 1)
```

- When `sin(x) = 1` (crest): `exp(0) = 1.0`, sharp peak
- When `sin(x) = -1` (trough): `exp(-2) ≈ 0.135`, broad flat valley

This naturally produces a **trochoidal profile** similar to Gerstner waves, but at much lower computational cost.

When layering multiple waves, the key innovation is **derivative domain warping (Drag)**:

```
position += direction * derivative * weight * DRAG_MULT
```

Each wave layer's sampling position is offset by the previous layer's derivative, causing small ripples to naturally cluster on the crests of larger waves — simulating the real-ocean phenomenon of capillary waves riding on gravity waves.

### 2. Lighting Model: Schlick Fresnel + Subsurface Scattering Approximation

**Schlick Fresnel Approximation**:
```
F = F0 + (1 - F0) * (1 - dot(N, V))^5
```
Where water's F0 ≈ 0.04 (only 4% reflection at normal incidence).

**Subsurface Scattering (SSS)** is approximated through water thickness: troughs have thicker water layers with stronger blue-green scattering; crests have thinner layers with weaker scattering — naturally producing the visual effect of transparent crests and deep blue troughs.

### 3. Water Surface Intersection: Bounded Heightfield Marching

The water surface is constrained within a bounding box of `[0, -WATER_DEPTH]`, and rays only march between the intersection points of two planes. Step size is adaptive: `step = ray_y - wave_height` — large steps when far from the surface, small precise steps when close.

## Implementation Steps

### Step 1: Exponential Sine Wave Function

**What**: Define a single directional wave's value and derivative calculation function.

**Why**: `exp(sin(x) - 1)` transforms the symmetric sine into a realistic waveform with sharp crests and broad troughs. It also returns the analytical derivative, used for subsequent domain warping and normal calculation.

**Code**:
```glsl
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);     // Sharp crest, broad trough waveform
    float dx = wave * cos(x);            // Analytical derivative = exp(sin(x)-1) * cos(x)
    return vec2(wave, -dx);              // Return (value, negative derivative)
}
```

### Step 2: Multi-Octave Wave Layering with Domain Warping

**What**: Layer multiple waves with different directions, frequencies, and speeds, applying derivative-driven position offset (drag) between each layer.

**Why**: A single wave is too regular. Multi-octave layering produces natural complex waveforms. Domain warping is the key — it causes small waves to cluster on top of large waves, which is the core technique distinguishing "good-looking ocean" from "ordinary noise." The frequency growth rate of 1.18 (instead of the traditional FBM 2.0) creates smoother transitions between wave layers.

**Code**:
```glsl
#define DRAG_MULT 0.38  // Tunable: domain warp strength, 0=none, 0.5=strong clustering

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1; // Break long-distance phase synchronization
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));  // Pseudo-random wave direction

        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);

        // Core: offset sampling position based on derivative (small waves ride big waves)
        position += p * res.y * weight * DRAG_MULT;

        sumOfValues += res.x * weight;
        sumOfWeights += weight;

        weight = mix(weight, 0.0, 0.2);      // Tunable: weight decay, 0.2 = 80% retained per layer
        frequency *= 1.18;                     // Tunable: frequency growth rate
        timeMultiplier *= 1.07;                // Tunable: higher frequency waves animate faster (dispersion)
        iter += 1232.399963;                   // Large irrational increment ensures uniform direction distribution
    }
    return sumOfValues / sumOfWeights;
}
```

### Step 3: Bounded Bounding Box Ray Marching

**What**: Constrain the water surface between two horizontal planes and only march between the entry and exit points.

**Why**: Much faster than unbounded SDF marching. The step size `pos.y - height` automatically adapts — large jumps when far from the surface, fine convergence when close. Precomputing bounding box intersections avoids wasting steps in open air.

**Code**:
```glsl
#define WATER_DEPTH 1.0  // Tunable: water body thickness, affects SSS and wave amplitude

float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < 64; i++) {         // Tunable: march steps, 64 is usually sufficient
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);      // Adaptive step size
    }
    return distance(start, camera);          // If missed, assume hit at top surface
}
```

### Step 4: Normal Calculation with Distance Smoothing

**What**: Compute water surface normals using finite differences, and interpolate toward the up direction based on distance to eliminate distant aliasing.

**Why**: Normals determine all lighting details. Using more wave iterations for normals than for ray marching (36 vs 12) is a core performance technique — marching only needs coarse shape, normals need fine detail. The farther away, the more high-frequency normals cause flickering; smoothing toward `(0,1,0)` is equivalent to implicit LOD.

**Code**:
```glsl
#define ITERATIONS_RAYMARCH 12  // Tunable: wave iterations for marching (fewer = faster)
#define ITERATIONS_NORMAL 36    // Tunable: wave iterations for normals (more = finer detail)

vec3 normal(vec2 pos, float e, float depth) {
    vec2 ex = vec2(e, 0);
    float H = getwaves(pos.xy, ITERATIONS_NORMAL) * depth;
    vec3 a = vec3(pos.x, H, pos.y);
    return normalize(
        cross(
            a - vec3(pos.x - e, getwaves(pos.xy - ex.xy, ITERATIONS_NORMAL) * depth, pos.y),
            a - vec3(pos.x, getwaves(pos.xy + ex.yx, ITERATIONS_NORMAL) * depth, pos.y + e)
        )
    );
}

// Distance smoothing: distant normals approach (0,1,0)
// N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```

### Step 5: Fresnel Reflection and Subsurface Scattering

**What**: Use Schlick Fresnel approximation to calculate reflection/scattering weights, combining sky reflection with depth-dependent blue-green scattering color.

**Why**: The Fresnel effect is key to water surface realism — nearly fully transparent up close, nearly fully reflective at a distance. The SSS color `(0.0293, 0.0698, 0.1717)` comes from empirical values of deep-sea scattering spectra. Troughs have thicker water layers with stronger SSS; crests have thinner layers with weaker SSS, naturally producing light-dark variation.

**Code**:
```glsl
// Schlick Fresnel, F0 = 0.04 (water's normal incidence reflectance)
float fresnel = 0.04 + 0.96 * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

// Reflection direction, force upward to avoid self-intersection
vec3 R = normalize(reflect(ray, N));
R.y = abs(R.y);

// Sky reflection + sun specular
vec3 reflection = getAtmosphere(R) + getSun(R);

// Subsurface scattering: deeper (trough) = bluer color
vec3 scattering = vec3(0.0293, 0.0698, 0.1717) * 0.1
                * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

// Final compositing
vec3 C = fresnel * reflection + scattering;
```

### Step 6: Atmosphere and Tone Mapping

**What**: Add a cheap atmospheric scattering model and ACES tone mapping.

**Why**: The water surface reflects the sky, so sky quality directly affects the water's appearance. `1/(ray.y + 0.1)` approximates optical path length, `vec3(5.5, 13.0, 22.4)/22.4` represents Rayleigh scattering coefficient ratios. ACES tone mapping maps HDR values to display range, preserving highlight detail while compressing shadows.

**Code**:
```glsl
vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4),
                        special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002
                   * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0));
}

vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(
        0.59719, 0.07600, 0.02840,
        0.35458, 0.90834, 0.13383,
        0.04823, 0.01566, 0.83777);
    mat3 m2 = mat3(
        1.60475, -0.10208, -0.00327,
       -0.53108,  1.10813, -0.07276,
       -0.07367, -0.00605,  1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return pow(clamp(m2 * (a / b), 0.0, 1.0), vec3(1.0 / 2.2));
}
```

## Common Variants

### Variant 1: 2D Underwater Caustic Texture

Difference from the base version: No 3D ray marching — purely a 2D screen-space effect. Uses an iterative triangular feedback loop to generate caustic light patterns, suitable as a ground projection texture for underwater scenes or as an overlay layer.

Key code:
```glsl
#define TAU 6.28318530718
#define MAX_ITER 5       // Tunable: iteration count, more = finer caustics

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.5 + 23.0;
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec2 p = mod(uv * TAU, TAU) - 250.0;   // mod TAU ensures tileability
    vec2 i = vec2(p);
    float c = 1.0;
    float inten = 0.005;  // Tunable: caustic line width (smaller = thinner)

    for (int n = 0; n < MAX_ITER; n++) {
        float t = time * (1.0 - (3.5 / float(n + 1)));
        i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
        c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten), p.y / (cos(i.y + t) / inten)));
    }
    c /= float(MAX_ITER);
    c = 1.17 - pow(c, 1.4);
    vec3 colour = vec3(pow(abs(c), 8.0));
    colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0); // Aqua blue tint
    fragColor = vec4(colour, 1.0);
}
```

### Variant 2: FBM Bump-Mapped Lake Surface (Plane Intersection + Bump Mapping)

Difference from the base version: No per-pixel ray marching — uses analytical plane intersection + FBM bump mapping instead. Extremely fast, suitable for distant lake surfaces or situations where water must be embedded in complex scenes (e.g., with volumetric cloud reflections).

Key code:
```glsl
// Water surface heightmap (FBM + abs folding produces ridge-like ripples)
float waterMap(vec2 pos) {
    mat2 m2 = mat2(0.60, -0.80, 0.80, 0.60); // Rotation matrix to avoid axis alignment
    vec2 posm = pos * m2;
    return abs(fbm(vec3(8.0 * posm, iTime)) - 0.5) * 0.1;
}

// Analytical plane intersection replaces ray marching
float t = -ro.y / rd.y;  // Water surface at y=0
vec3 hitPos = ro + rd * t;

// Finite difference normals (central differencing)
float eps = 0.1;
vec3 normal = vec3(0.0, 1.0, 0.0);
normal.x = -bumpfactor * (waterMap(hitPos.xz + vec2(eps, 0.0)) - waterMap(hitPos.xz - vec2(eps, 0.0))) / (2.0 * eps);
normal.z = -bumpfactor * (waterMap(hitPos.xz + vec2(0.0, eps)) - waterMap(hitPos.xz - vec2(0.0, eps))) / (2.0 * eps);
normal = normalize(normal);

// Bump strength fades with distance (LOD)
float bumpfactor = 0.1 * (1.0 - smoothstep(0.0, 60.0, distance(ro, hitPos)));

// Refraction uses the built-in refract() function
vec3 refracted = refract(rd, normal, 1.0 / 1.333);
```

### Variant 3: Ridged Noise Coastal Waves

Difference from the base version: Uses `1 - abs(noise)` instead of `exp(sin)` to generate waveforms, combined with in-loop domain warping. Suitable for coastal scenes with sharper, more impactful waves that naturally connect to shore foam.

Key code:
```glsl
float sea(vec2 p) {
    float f = 1.0;
    float r = 0.0;
    float time = -iTime;
    for (int i = 0; i < 8; i++) {        // Tunable: 8 octaves
        r += (1.0 - abs(noise(p * f + 0.9 * time))) / f;  // Ridged noise
        f *= 2.0;
        p -= vec2(-0.01, 0.04) * (r - 0.2 * time / (0.1 - f)); // In-loop domain warping
    }
    return r / 4.0 + 0.5;
}

// Shore foam: based on distance between water surface and terrain
float dh = seaDist - rockDist; // Water-terrain SDF difference
float foam = 0.0;
if (dh < 0.0 && dh > -0.02) {
    foam = 0.5 * exp(20.0 * dh);   // Exponentially decaying shoreline glow
}
```

### Variant 4: Flow Map Water Animation (Rivers/Streams)

Difference from the base version: Adds flow-field-driven FBM animation. Uses a two-phase time cycle to eliminate texture stretching, with water flow direction procedurally generated from terrain gradients. Suitable for rivers, streams, and other water bodies with a clear flow direction.

Key code:
```glsl
// FBM with analytical derivatives + flow field offset
vec3 FBM_DXY(vec2 p, vec2 flow, float persistence, float domainWarp) {
    vec3 f = vec3(0.0);
    float tot = 0.0;
    float a = 1.0;
    for (int i = 0; i < 4; i++) {
        p += flow;
        flow *= -0.75;          // Negate + shrink each layer to prevent uniform sliding
        vec3 v = SmoothNoise_DXY(p);
        f += v * a;
        p += v.xy * domainWarp; // Gradient domain warping
        p *= 2.0;
        tot += a;
        a *= persistence;
    }
    return f / tot;
}

// Two-phase flow cycle (eliminates stretching)
float t0 = fract(time);
float t1 = fract(time + 0.5);
vec4 sample0 = SampleWaterNormal(uv + Hash2(floor(time)),     flowRate * (t0 - 0.5));
vec4 sample1 = SampleWaterNormal(uv + Hash2(floor(time+0.5)), flowRate * (t1 - 0.5));
float weight = abs(t0 - 0.5) * 2.0;
vec4 result = mix(sample0, sample1, weight);
```

### Variant 5: Beer's Law Water Absorption + Volumetric Scattering

Difference from the base version: Replaces the simple SSS approximation with physically correct Beer-Lambert exponential decay for underwater color absorption, plus a forward scattering term. Suitable for realistic scenes requiring tunable clear/turbid water.

Key code:
```glsl
// Beer-Lambert attenuation: red light absorbed fastest, blue light slowest
vec3 GetWaterExtinction(float dist) {
    float fOpticalDepth = dist * 6.0;     // Tunable: larger = more turbid water
    vec3 vExtinctCol = vec3(0.5, 0.6, 0.9); // Tunable: absorption spectrum (R decays fast, B slow)
    return exp2(-fOpticalDepth * vExtinctCol);
}

// Volumetric in-scattering
vec3 vInscatter = vSurfaceDiffuse * (1.0 - exp(-refractDist * 0.1))
               * (1.0 + dot(sunDir, viewDir));  // Forward scattering enhancement

// Final underwater color
vec3 underwaterColor = terrainColor * GetWaterExtinction(waterDepth) + vInscatter;

// Fresnel compositing
vec3 finalColor = mix(underwaterColor, reflectionColor, fresnel);
```

## In-Depth Performance Optimization

### 1. Dual Iteration Count Strategy (Most Critical Optimization)

Ray marching uses few iterations (12), normal calculation uses many (36). Marching only needs a rough intersection point; normals need fine wave detail. This single technique can halve render time with virtually no visual quality loss.

### 2. Distance-Adaptive Normal Smoothing

```glsl
N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```

Distant normals approach `(0,1,0)`, eliminating high-frequency flickering at distance (equivalent to implicit normal mipmapping), while saving expensive normal calculations at long range.

### 3. Bounding Box Clipping

Precompute ray intersections with the top and bottom horizontal planes, and only march between the two intersection points. Rays pointing skyward (`ray.y >= 0`) skip water surface calculations entirely — the simplest and most effective early-out.

### 4. Adaptive Step Size

`pos += dir * (pos.y - height)` uses the current height difference as step size — potentially jumping large distances when far from the surface, automatically shrinking when close. 3-5x faster than fixed step size.

### 5. Filter Width-Aware Normal Attenuation (Advanced)

For scenes requiring more precise LOD:
```glsl
vec2 vFilterWidth = max(abs(dFdx(uv)), abs(dFdy(uv)));
float fScale = 1.0 / (1.0 + max(vFilterWidth.x, vFilterWidth.y) * max(vFilterWidth.x, vFilterWidth.y) * 2000.0);
normalStrength *= fScale;
```

Uses screen-space derivatives to automatically detect pixel coverage area — the larger the area, the flatter the normal. This is a precise implementation of manual mipmapping.

### 6. LOD Conditional Detail

```glsl
if (distanceToSurface < threshold) {
    // Only compute high-frequency detail when close to the water surface
    for (int i = 0; i < detailOctaves; i++) { ... }
}
```

High-frequency displacement of the water surface SDF is only calculated when close to the surface; at distance, the base plane is used directly, avoiding unnecessary noise sampling.

## Combination Suggestions

### 1. Combining with Volumetric Clouds

Including cloud reflections in the water surface is key to enhancing realism. Steps: first perform volumetric cloud raymarching along the reflection direction `R`, then mix the cloud color as part of `reflection` in the Fresnel compositing. This is a common technique in water rendering shaders.

### 2. Combining with Terrain Systems

Shoreline rendering requires interaction between the water surface SDF and terrain SDF. Key technique: maintain `dh = waterSDF - terrainSDF`, and render foam when `dh ≈ 0` (`exp(k * dh)` produces exponentially decaying coastal glow). A standard technique in shoreline rendering.

### 3. Combining with Caustics

In underwater scenes, project the caustic texture from Variant 1 onto the underwater terrain surface. Modulate caustic intensity as `caustic * exp(-waterDepth * absorption)` for depth-based attenuation.

### 4. Combining with Fog/Atmospheric Scattering

Distant water surfaces must blend into atmospheric fog. Use an independent extinction + in-scatter fog model (not a simple lerp), with each RGB channel attenuating independently:
```glsl
vec3 fogExtinction = exp2(fogExtCoeffs * -distance);
vec3 fogInscatter = fogColor * (1.0 - exp2(fogInCoeffs * -distance));
finalColor = finalColor * fogExtinction + fogInscatter;
```

### 5. Combining with Post-Processing

- **Bloom**: Sun specular highlights on the water surface need bloom to look natural; Fibonacci spiral blur works better than simple Gaussian
- **Tone Mapping**: ACES is the standard choice for ocean scenes, preserving sun highlights while compressing shadows
- **Depth of Field (DOF)**: Focusing on mid-ground waves with near and far blur greatly enhances cinematic quality (post-process bokeh DOF)
