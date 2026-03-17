# Heightfield Ray Marching Terrain Rendering — Detailed Reference

> This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, complete explanations for each step (what/why), variant details, in-depth performance optimization analysis, and complete code examples for combination suggestions.

## Prerequisites

- **GLSL Fundamentals**: uniforms, varyings, built-in functions (mix, smoothstep, clamp, fract, floor)
- **Vector Math**: dot product, cross product, matrix transforms, normal calculation
- **Basic Ray Marching Concepts**: casting rays from the camera, advancing along rays, detecting intersections
- **Noise Functions**: basic principles of Value Noise / Gradient Noise (grid sampling + interpolation)
- **FBM (Fractal Brownian Motion)**: layering multiple noise octaves to build fractal detail

## Implementation Steps

### Step 1: Noise and Hash Functions

**What**: Implement 2D Value Noise, providing the fundamental sampling capability for FBM.

**Why**: Terrain shaders build terrain from noise. Value Noise generates a continuous pseudo-random field through grid point hashing + bilinear interpolation. A rotation-based hash avoids precision issues with `sin()` on some GPUs. Interpolation uses Hermite smoothstep `3t²-2t³` to ensure C¹ continuity.

**Code**:
```glsl
// === Hash Function ===
// High-quality hash without sin
// Uses fract-dot pattern, avoiding sin() precision issues
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}

// === 2D Value Noise ===
// Grid sampling + Hermite interpolation, returns [0,1]
float noise(in vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f); // Hermite smoothstep

    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
```

### Step 2: Noise with Analytical Derivatives (Advanced)

**What**: Return the noise value along with its analytical partial derivatives `∂n/∂x` and `∂n/∂y`.

**Why**: Analytical derivatives are key to implementing "eroded terrain" — accumulating derivatives in FBM can suppress detail layering on steep slopes (used in Step 3). This technique is widely used in terrain shaders. The derivative formula comes from chain rule differentiation of Hermite interpolation: `du = 6f(1-f)`.

**Code**:
```glsl
// === 2D Value Noise with Analytical Derivatives ===
// Returns vec3: .x = noise value, .yz = partial derivatives (dn/dx, dn/dy)
vec3 noised(in vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);

    // Hermite interpolation and its derivative
    vec2 u  = f * f * (3.0 - 2.0 * f);
    vec2 du = 6.0 * f * (1.0 - f);

    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    float value = a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
    vec2  deriv = du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx);

    return vec3(value, deriv);
}
```

### Step 3: FBM Terrain Heightfield (with Derivative Erosion)

**What**: Layer multiple noise octaves to build a terrain heightfield, using derivative accumulation to simulate erosion effects.

**Why**: FBM is the terrain generation core. The key difference is **whether derivative suppression is used**:
- **Without derivatives**: simple layering, terrain appears more "rough"
- **With derivative suppression**: the `1/(1+dot(d,d))` term suppresses high-frequency detail on steep slopes, producing realistic ridge/valley structures

The rotation matrix `m2` rotates sampling coordinates between each layer, breaking axis-aligned visual banding. `mat2(0.8,-0.6, 0.6,0.8)` rotates approximately 37° with unit determinant (pure rotation, no scaling) — a standard choice for terrain FBM.

**Code**:
```glsl
#define TERRAIN_OCTAVES 9   // Tunable: 3=rough outline, 9=medium detail, 16=highest precision (for normals)
#define TERRAIN_SCALE 0.003 // Tunable: controls terrain spatial frequency, smaller = "wider" terrain
#define TERRAIN_HEIGHT 120.0 // Tunable: terrain elevation scale

// Per-layer rotation matrix: ~37° pure rotation, eliminates axis-aligned banding
const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);

// === FBM Terrain Heightfield (Derivative Erosion Version) ===
// Input: 2D world coordinates (xz plane)
// Output: scalar height value
float terrain(in vec2 p) {
    p *= TERRAIN_SCALE;

    float a = 0.0;   // Accumulated height
    float b = 1.0;   // Current amplitude
    vec2  d = vec2(0.0); // Accumulated derivatives

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        vec3 n = noised(p);          // .x=value, .yz=derivatives
        d += n.yz;                    // Accumulate gradient
        a += b * n.x / (1.0 + dot(d, d)); // Derivative suppression: contribution reduced on steep slopes
        b *= 0.5;                     // Amplitude halved per layer
        p = m2 * p * 2.0;            // Rotate + double frequency
    }

    return a * TERRAIN_HEIGHT;
}
```

### Step 4: LOD Multi-Resolution Terrain Functions

**What**: Create terrain functions at different precision levels for different purposes.

**Why**: This is a classic optimization — ray marching only needs rough height (fewer FBM layers), normal calculation needs detail (more FBM layers), and camera placement only needs the coarsest estimate. A dual-function scheme (coarse for marching, fine for normals) is standard practice in terrain shaders.

**Code**:
```glsl
#define OCTAVES_LOW 3     // Tunable: for camera placement, fastest
#define OCTAVES_MED 9     // Tunable: for ray marching
#define OCTAVES_HIGH 16   // Tunable: for normal calculation, finest detail

// Low precision (camera height, far distance)
float terrainL(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_LOW; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}

// Medium precision (ray marching)
float terrainM(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_MED; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}

// High precision (normal calculation)
float terrainH(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_HIGH; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}
```

### Step 5: Adaptive Step Size Ray Marching

**What**: Cast rays from the camera and advance along the ray with adaptive steps, finding the intersection with the terrain heightfield.

**Why**: Terrain is a heightfield (not an arbitrary SDF), so `ray.y - terrain(ray.xz)` can be used as a conservative step size estimate. Common terrain shaders employ three strategies:
- **Conservative factor approach**: `step = 0.4 × h` (conservative factor 0.4, prevents overshooting sharp ridges, 300 steps)
- **Relaxation marching**: `step = h × max(t×0.02, 1.0)`, step size automatically increases with distance (90 steps covering greater range)
- **Adaptive marching + binary refinement**: adaptive marching + 5 binary refinement steps (150 steps + precise intersection)

This template uses the conservative factor approach + distance-adaptive precision threshold, balancing accuracy and efficiency.

**Code**:
```glsl
#define MAX_STEPS 300       // Tunable: march steps, 80=fast, 300=high quality
#define MAX_DIST 5000.0     // Tunable: maximum render distance
#define STEP_FACTOR 0.4     // Tunable: march conservative factor, 0.3=safe, 0.8=aggressive

// === Ray Marching ===
// ro: ray origin, rd: ray direction (normalized)
// Returns: intersection distance t (-1.0 means miss)
float raymarch(in vec3 ro, in vec3 rd) {
    float t = 0.0;

    // Upper bound clipping: skip if ray cannot possibly hit terrain
    // Assumes terrain max height is TERRAIN_HEIGHT
    if (ro.y > TERRAIN_HEIGHT && rd.y >= 0.0) return -1.0;
    if (ro.y > TERRAIN_HEIGHT) {
        t = (ro.y - TERRAIN_HEIGHT) / (-rd.y); // Fast jump to terrain height upper bound
    }

    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float h = pos.y - terrainM(pos.xz); // Height difference = ray y - terrain height

        // Adaptive precision: tolerate larger error at distance (screen-space equivalent)
        if (abs(h) < 0.0015 * t) break;
        if (t > MAX_DIST) return -1.0;

        t += STEP_FACTOR * h; // Advance proportionally to height difference
    }

    return t;
}
```

### Step 6: Binary Refinement (Optional)

**What**: Perform binary search near the rough intersection found by ray marching to precisely locate the terrain surface.

**Why**: Ray marching only guarantees the intersection is within some interval; binary search converges the error by 2^5=32x. This is especially important for sharp ridge silhouettes. A similar "step-back-and-halve" strategy is common in terrain shaders.

**Code**:
```glsl
#define BISECT_STEPS 5 // Tunable: binary search steps, 5 steps = 32x precision improvement

// === Binary Refinement ===
// ro: ray origin, rd: ray direction
// tNear: last t above terrain, tFar: first t below terrain
float bisect(in vec3 ro, in vec3 rd, float tNear, float tFar) {
    for (int i = 0; i < BISECT_STEPS; i++) {
        float tMid = 0.5 * (tNear + tFar);
        vec3 pos = ro + tMid * rd;
        float h = pos.y - terrainM(pos.xz);
        if (h > 0.0) {
            tNear = tMid; // Still above terrain, advance forward
        } else {
            tFar = tMid;  // Below terrain, pull back
        }
    }
    return 0.5 * (tNear + tFar);
}
```

### Step 7: Normal Calculation

**What**: Compute terrain surface normals at the intersection point using finite differences.

**Why**: Normals are the foundation of all lighting calculations. A key optimization is **epsilon increasing with distance** — using coarser epsilon at distance avoids aliasing from high-frequency noise. The high-precision terrain function `terrainH` is used here for normal detail.

**Code**:
```glsl
// === Normal Calculation (Finite Differences) ===
// pos: surface intersection point, t: distance (for adaptive epsilon)
vec3 calcNormal(in vec3 pos, float t) {
    // Adaptive epsilon: fine up close, coarse at distance (avoids aliasing)
    float eps = 0.02 + 0.00005 * t * t;

    float hC = terrainH(pos.xz);
    float hR = terrainH(pos.xz + vec2(eps, 0.0));
    float hU = terrainH(pos.xz + vec2(0.0, eps));

    // Finite difference normal
    return normalize(vec3(hC - hR, eps, hC - hU));
}
```

### Step 8: Material and Color Assignment

**What**: Blend different material colors based on height, slope, noise, and other conditions.

**Why**: Natural terrain color layering is key to visual convincingness. Nearly all terrain shaders follow this layering logic:
- **Rock**: steep surfaces (small normal y component) → gray rock
- **Grass**: flat low-altitude surfaces → green
- **Snow**: high-altitude flat surfaces → white
- **Sand**: near water level → sand color

Use `smoothstep` for smooth transitions between layers and FBM noise to break up transition line regularity.

**Code**:
```glsl
#define SNOW_HEIGHT 80.0     // Tunable: snow line altitude
#define TREE_HEIGHT 45.0     // Tunable: tree line altitude
#define BEACH_HEIGHT 1.5     // Tunable: beach height

// === Material Color ===
// pos: world coordinates, nor: normal
vec3 getMaterial(in vec3 pos, in vec3 nor) {
    // Slope factor: nor.y=1 means horizontal, nor.y=0 means vertical
    float slope = nor.y;
    float h = pos.y;

    // Noise to break up transition lines
    float nz = noise(pos.xz * 0.04) * noise(pos.xz * 0.005);

    // Base rock color
    vec3 rock = vec3(0.10, 0.09, 0.08);

    // Dirt/grass color (flat surfaces)
    vec3 grass = mix(vec3(0.10, 0.08, 0.04), vec3(0.05, 0.09, 0.02), nz);

    // Snow color
    vec3 snow = vec3(0.62, 0.65, 0.70);

    // Sand color
    vec3 sand = vec3(0.50, 0.45, 0.35);

    // --- Layered blending ---
    vec3 col = rock;

    // Flat areas: rock → grass
    col = mix(col, grass, smoothstep(0.5, 0.8, slope));

    // High altitude: → snow (slope + height + noise)
    float snowMask = smoothstep(SNOW_HEIGHT - 20.0 * nz, SNOW_HEIGHT + 10.0, h)
                   * smoothstep(0.3, 0.7, slope);
    col = mix(col, snow, snowMask);

    // Low altitude: → sand
    float beachMask = smoothstep(BEACH_HEIGHT + 1.0, BEACH_HEIGHT - 0.5, h)
                    * smoothstep(0.5, 0.9, slope);
    col = mix(col, sand, beachMask);

    return col;
}
```

### Step 9: Lighting Model

**What**: Implement multi-component lighting: sun diffuse + hemisphere ambient light + backlight fill + specular.

**Why**: Terrain lighting models share consistent core components:
- **Lambert Diffuse**: `dot(N, L)` — fundamental component
- **Hemisphere Ambient**: `0.5 + 0.5 * N.y` — standard terrain ambient lighting
- **Backlight**: fill light from the horizontal direction opposite the sun
- **Fresnel Rim Light**: `pow(1+dot(rd,N), 2~5)` — edge glow effect
- **Specular**: Phong/Blinn-Phong, power ranging from 3 to 500

**Code**:
```glsl
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6)) // Tunable: sun direction
#define SUN_COL vec3(8.0, 5.0, 3.0)              // Tunable: sun color temperature (warm light)
#define SKY_COL vec3(0.5, 0.7, 1.0)              // Tunable: sky color

// === Lighting Calculation ===
vec3 calcLighting(in vec3 pos, in vec3 nor, in vec3 rd, float shadow) {
    vec3 sunDir = SUN_DIR;

    // Diffuse (Lambert)
    float dif = clamp(dot(nor, sunDir), 0.0, 1.0);

    // Hemisphere ambient: facing up=full brightness, facing down=half brightness
    float amb = 0.5 + 0.5 * nor.y;

    // Backlight fill (horizontal direction opposite the sun)
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float bac = clamp(0.2 + 0.8 * dot(nor, backDir), 0.0, 1.0);

    // Fresnel rim light
    float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);

    // Specular (Blinn-Phong)
    vec3 hal = normalize(sunDir - rd);
    float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0)
              * (0.04 + 0.96 * pow(1.0 + dot(hal, rd), 5.0)); // Fresnel term

    // Combine
    vec3 lin = vec3(0.0);
    lin += dif * shadow * SUN_COL * 0.1;          // Sun diffuse
    lin += amb * SKY_COL * 0.2;                    // Sky ambient
    lin += bac * vec3(0.15, 0.05, 0.04);           // Backlight (warm tone)
    lin += fre * SKY_COL * 0.3;                    // Rim light
    lin += spe * shadow * SUN_COL * 0.05;          // Specular

    return lin;
}
```

### Step 10: Soft Shadows

**What**: Cast a shadow ray from the surface intersection point toward the sun, computing soft shadows with penumbra.

**Why**: Soft shadows greatly enhance terrain spatial depth. The classic technique — during shadow ray marching, track `min(k*h/t)`, where h is the height distance from the terrain and t is the march distance. A smaller ratio = the ray grazes the terrain surface = penumbra region. The k parameter controls penumbra softness (k=16 for soft, k=64 for hard).

**Code**:
```glsl
#define SHADOW_STEPS 80     // Tunable: shadow ray steps, 32=fast, 80=high quality
#define SHADOW_K 16.0       // Tunable: penumbra softness, 8=very soft, 64=very hard

// === Soft Shadows ===
// pos: surface point, sunDir: sun direction
float calcShadow(in vec3 pos, in vec3 sunDir) {
    float res = 1.0;
    float t = 1.0; // Start slightly above the surface to avoid self-intersection

    for (int i = 0; i < SHADOW_STEPS; i++) {
        vec3 p = pos + t * sunDir;
        float h = p.y - terrainM(p.xz);

        if (h < 0.001) return 0.0; // Full shadow

        // Penumbra estimate: smaller h/t = ray closer to occlusion
        res = min(res, SHADOW_K * h / t);
        t += clamp(h, 2.0, 100.0); // Adaptive step size
    }

    return clamp(res, 0.0, 1.0);
}
```

### Step 11: Aerial Perspective and Fog

**What**: Blend terrain color toward fog color with increasing distance, achieving an aerial perspective effect.

**Why**: Atmospheric effects are the key visual cue for "pushing" pixels into the distance. Common approaches range from simple to complex:
- **Exponential fog**: `exp(-0.00005 * t^2)` — simplest
- **Exponential + height-decay fog**: `exp(-pow(k*t, 1.5))` — denser at low altitude, thinner at high altitude
- **Wavelength-dependent fog**: `exp(-t * vec3(1,1.5,4) * k)` — blue light attenuates faster, red light travels further, realistic atmospheric dispersion
- **Full Rayleigh+Mie scattering**: physically accurate but expensive

**Code**:
```glsl
#define FOG_DENSITY 0.00025  // Tunable: fog density
#define FOG_HEIGHT 0.001     // Tunable: height decay coefficient (0=no height dependency)

// === Atmospheric Fog ===
// col: original color, t: distance, rd: ray direction
vec3 applyFog(in vec3 col, float t, in vec3 rd) {
    // Wavelength-dependent attenuation: blue attenuates 4x faster than red
    vec3 extinction = exp(-t * FOG_DENSITY * vec3(1.0, 1.5, 4.0));

    // Fog color: base blue-gray + sun direction scattering (warm tones)
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    vec3 fogCol = mix(vec3(0.55, 0.55, 0.58),         // Base fog color
                      vec3(1.0, 0.7, 0.3),              // Sun scatter color
                      0.3 * pow(sundot, 8.0));

    return col * extinction + fogCol * (1.0 - extinction);
}
```

### Step 12: Sky Rendering

**What**: Draw the background sky, including gradients, sun disk, and horizon glow.

**Why**: The sky is an important component of atmospheric mood. All terrain shaders with 3D viewpoints include sky rendering. Key components:
- Zenith-to-horizon blue→white gradient
- Horizon glow band (`pow(1-rd.y, n)` family)
- Sun disk and halo (`pow(sundot, high power)` family)

**Code**:
```glsl
// === Sky Color ===
vec3 getSky(in vec3 rd) {
    // Base sky gradient: zenith blue → horizon white
    vec3 col = vec3(0.3, 0.5, 0.85) - rd.y * vec3(0.2, 0.15, 0.0);

    // Horizon glow
    float horizon = pow(1.0 - max(rd.y, 0.0), 4.0);
    col = mix(col, vec3(0.8, 0.75, 0.7), 0.5 * horizon);

    // Sun
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    col += vec3(1.0, 0.7, 0.3) * 0.3 * pow(sundot, 8.0);   // Large halo
    col += vec3(1.0, 0.9, 0.7) * 0.5 * pow(sundot, 64.0);   // Small halo
    col += vec3(1.0, 1.0, 0.9) * min(pow(sundot, 1150.0), 0.3); // Sun disk

    return col;
}
```

### Step 13: Camera Setup

**What**: Build a Look-At camera matrix and define a flight path.

**Why**: Terrain flythrough cameras typically follow Lissajous curves or arc paths, with altitude following the terrain. The Look-At matrix maps screen coordinates to world-space ray directions.

**Code**:
```glsl
#define CAM_ALTITUDE 20.0   // Tunable: camera height above ground
#define CAM_SPEED 0.5       // Tunable: flight speed

// === Camera Path ===
vec3 cameraPath(float t) {
    return vec3(
        100.0 * sin(0.2 * t),  // x: sine curve
        0.0,                     // y: determined by terrain height
        -100.0 * t               // z: forward direction
    );
}

// === Camera Matrix ===
mat3 setCamera(in vec3 ro, in vec3 ta) {
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}
```

## Common Variants

### Variant 1: Relaxation Marching

**Difference from the base version**: Step size automatically increases with distance, covering greater range but with slightly reduced precision. The conservative factor is replaced with a distance-adaptive relaxation factor, while the height estimate is scaled down to prevent penetration.

**Key code**:
```glsl
#define RELAX_MAX_STEPS 90       // Fewer steps needed to cover greater distance
#define RELAX_FAR 400.0

float raymarchRelax(in vec3 ro, in vec3 rd) {
    float t = 0.0;
    float d = (ro + rd * t).y - terrainM((ro + rd * t).xz);

    for (int i = 0; i < RELAX_MAX_STEPS; i++) {
        if (abs(d) < t * 0.0001 || t > RELAX_FAR) break;

        float rl = max(t * 0.02, 1.0); // Relaxation factor: larger steps at distance
        t += d * rl;
        vec3 pos = ro + rd * t;
        d = (pos.y - terrainM(pos.xz)) * 0.7; // 0.7 attenuation prevents penetration
    }
    return t;
}
```

### Variant 2: Sign-Alternating FBM

**Difference from the base version**: Flips the amplitude sign each layer (`w = -w * 0.4`), producing unique alternating ridge/valley patterns. Does not use derivative suppression — the style is distinctly different from the erosion version, producing a more "jagged and twisted" appearance.

**Key code**:
```glsl
float terrainSignFlip(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0;
    float w = 1.0; // Initial weight

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        a += w * noise(p);
        w = -w * 0.4;    // Sign flip + decay: alternating addition and subtraction
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}
```

### Variant 3: Texture-Driven Heightfield + 3D Displacement

**Difference from the base version**: Uses texture sampling as the base heightfield, with 3D FBM displacement layered on top to produce cliffs, caves, and other non-heightfield formations. Requires additional texture channel inputs but can create far more terrain diversity than pure FBM. Marching becomes true SDF sphere tracing.

**Key code**:
```glsl
// 3D Value Noise
float noise3D(in vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    // 3D→2D flattening: offset UV by p.z, sample two texture layers and interpolate
    vec2 uv = (p.xy + vec2(37.0, 17.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

// 3D FBM Displacement
const mat3 m3 = mat3(0.00, 0.80, 0.60,
                    -0.80, 0.36,-0.48,
                    -0.60,-0.48, 0.64);

float displacement(vec3 p) {
    float f = 0.5 * noise3D(p); p = m3 * p * 2.02;
    f += 0.25 * noise3D(p);    p = m3 * p * 2.03;
    f += 0.125 * noise3D(p);   p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p);
    return f;
}

// SDF: heightfield + 3D displacement (supports cliffs/caves)
float mapCanyon(vec3 p) {
    float h = terrainM(p.xz);
    float dis = displacement(0.25 * p * vec3(1.0, 4.0, 1.0)) * 3.0;
    return (dis + p.y - h) * 0.25;
}
```

### Variant 4: Directional Erosion Noise

**Difference from the base version**: Uses slope direction as the projection direction for Gabor noise. Each erosion layer adjusts the "water flow direction" based on the previous layer's derivatives, producing realistic dendritic drainage patterns. Requires multi-pass height map precomputation.

**Key code**:
```glsl
#define EROSION_OCTAVES 5
#define EROSION_BRANCH 1.5 // Tunable: branching strength, 0=parallel, 2=strong branching

// Directional Gabor noise
vec3 erosionNoise(vec2 p, vec2 dir) {
    vec2 ip = floor(p); vec2 fp = fract(p) - 0.5;
    float va = 0.0; float wt = 0.0;
    vec2 dva = vec2(0.0);

    for (int i = -2; i <= 1; i++)
    for (int j = -2; j <= 1; j++) {
        vec2 o = vec2(float(i), float(j));
        vec2 h = hash2(ip - o) * 0.5; // Grid point random offset
        vec2 pp = fp + o + h;
        float d = dot(pp, pp);
        float w = exp(-d * 2.0);       // Gaussian weight
        float mag = dot(pp, dir);       // Directional projection
        va += cos(mag * 6.283) * w;     // Directional ripple
        dva += -sin(mag * 6.283) * dir * w;
        wt += w;
    }
    return vec3(va, dva) / wt;
}

// Erosion FBM: direction evolves with slope
float terrainErosion(vec2 p, vec2 baseSlope) {
    float e = 0.0, a = 0.5;
    vec2 dir = normalize(baseSlope + vec2(0.001));

    for (int i = 0; i < EROSION_OCTAVES; i++) {
        vec3 n = erosionNoise(p * 4.0, dir);
        e += a * n.x;
        // Branching: curl of previous layer's derivative modifies water flow direction
        dir = normalize(dir + n.zy * vec2(1.0, -1.0) * EROSION_BRANCH);
        a *= 0.5;
        p *= 2.0;
    }
    return e;
}
```

### Variant 5: Volumetric Clouds + God Rays

**Difference from the base version**: Adds a volumetric cloud layer above the terrain using front-to-back alpha compositing, with god ray factor accumulated during marching. Requires 3D noise and more steps, significantly increasing cost but with excellent visual results.

**Key code**:
```glsl
#define CLOUD_STEPS 64        // Tunable: cloud march steps
#define CLOUD_BASE 200.0      // Tunable: cloud layer base height
#define CLOUD_TOP 300.0       // Tunable: cloud layer top height

vec4 raymarchClouds(vec3 ro, vec3 rd) {
    // Calculate intersections with cloud slab
    float tmin = (CLOUD_BASE - ro.y) / rd.y;
    float tmax = (CLOUD_TOP  - ro.y) / rd.y;
    if (tmin > tmax) { float tmp = tmin; tmin = tmp; tmax = tmp; } // swap
    if (tmin < 0.0) tmin = 0.0;

    float t = tmin;
    vec4 sum = vec4(0.0); // rgb=color, a=opacity
    float rays = 0.0;     // God ray accumulation

    for (int i = 0; i < CLOUD_STEPS; i++) {
        if (sum.a > 0.99 || t > tmax) break;
        vec3 pos = ro + t * rd;

        // Cloud density: slab shape × FBM carving
        float hFrac = (pos.y - CLOUD_BASE) / (CLOUD_TOP - CLOUD_BASE);
        float shape = 1.0 - 2.0 * abs(hFrac - 0.5); // Densest in the middle
        float den = shape - 1.6 * (1.0 - noise(pos.xz * 0.01)); // Simplified FBM

        if (den > 0.0) {
            // Cloud lighting: offset sample toward sun direction (self-shadowing)
            float shadowDen = shape - 1.6 * (1.0 - noise((pos.xz + SUN_DIR.xz * 30.0) * 0.01));
            float shadow = clamp(1.0 - shadowDen * 2.0, 0.0, 1.0);

            vec3 cloudCol = mix(vec3(0.4, 0.4, 0.45), vec3(1.0, 0.95, 0.8), shadow);
            float alpha = clamp(den * 0.4, 0.0, 1.0);

            // God rays: brightness of sunlight passing through thin areas
            rays += 0.02 * shadow * (1.0 - sum.a);

            // Front-to-back compositing
            cloudCol *= alpha;
            sum += vec4(cloudCol, alpha) * (1.0 - sum.a);
        }

        float dt = max(0.5, 0.05 * t);
        t += dt;
    }

    // Add god rays to color
    sum.rgb += pow(rays, 3.0) * 0.4 * vec3(1.0, 0.8, 0.7);
    return sum;
}
```

## In-Depth Performance Optimization

### 1. LOD Layering (Most Important Optimization)
**Bottleneck**: Each FBM layer requires an independent noise sample; octave count is a direct performance multiplier.
**Optimization**: Use low octaves for ray marching (3-9 layers), high octaves for normal calculation (16 layers), and lowest for camera placement (3 layers). This is standard practice in terrain shaders.

### 2. Upper Bound Clipping (Bounding Plane)
**Bottleneck**: Rays waste iterations stepping through open air.
**Optimization**: Precompute the maximum terrain height and intersect the ray with that plane before starting to march.
```glsl
if (ro.y > maxHeight && rd.y >= 0.0) return -1.0; // Skip entirely
t = (ro.y - maxHeight) / (-rd.y); // Jump to upper bound
```

### 3. Adaptive Precision Threshold
**Bottleneck**: Distant pixels still use near-field precision, wasting iterations.
**Optimization**: Hit threshold grows with distance: `abs(h) < 0.001 * t`. This is common practice, with the coefficient typically ranging from 0.0001 to 0.002.

### 4. Texture Instead of Procedural Noise
**Bottleneck**: Procedural noise requires multiple hash and interpolation operations.
**Optimization**: Pre-bake a 256x256 noise texture and sample with `textureLod`. Provides approximately 2-3x speedup over procedural noise.

### 5. Early Exit
**Bottleneck**: Rays continue iterating after exceeding range.
**Optimization**:
- `t > MAX_DIST` break out
- `alpha > 0.99` break out in volumetric rendering
- `h < 0` immediately return 0 in shadow rays

### 6. Jittered Start
**Bottleneck**: Uniform stepping produces visible banding artifacts.
**Optimization**: Add per-pixel random offset to the starting t: `t += hash(fragCoord) * step_size`. Adds no computational cost but significantly improves visual quality.

## Complete Combination Code Examples

### 1. Terrain + Water Surface
The most common terrain rendering combination. The water surface serves as a fixed y-plane — march the terrain first, and if the ray intersects terrain below the water surface, render underwater effects; otherwise render water surface reflection/refraction.
- Key: Water surface normals use multi-frequency noise perturbation to simulate waves; Fresnel controls reflection/refraction mixing

```glsl
#define WATER_LEVEL 5.0

// Water surface normal (multi-frequency noise perturbation)
vec3 waterNormal(vec2 p, float t) {
    float eps = 0.1;
    float h0 = noise(p * 0.5 + iTime * 0.3) * 0.5
             + noise(p * 1.5 - iTime * 0.2) * 0.25;
    float hx = noise((p + vec2(eps, 0.0)) * 0.5 + iTime * 0.3) * 0.5
             + noise((p + vec2(eps, 0.0)) * 1.5 - iTime * 0.2) * 0.25;
    float hz = noise((p + vec2(0.0, eps)) * 0.5 + iTime * 0.3) * 0.5
             + noise((p + vec2(0.0, eps)) * 1.5 - iTime * 0.2) * 0.25;
    return normalize(vec3(h0 - hx, eps, h0 - hz));
}

// In the main function:
// 1. Check water surface intersection first
float tWater = (ro.y - WATER_LEVEL) / (-rd.y);
// 2. Compare with terrain intersection
float tTerrain = raymarch(ro, rd);

vec3 col;
if (tWater > 0.0 && (tTerrain < 0.0 || tWater < tTerrain)) {
    // Hit water surface
    vec3 wpos = ro + tWater * rd;
    vec3 wnor = waterNormal(wpos.xz, tWater);

    // Fresnel
    float fresnel = pow(1.0 - max(dot(-rd, wnor), 0.0), 5.0);
    fresnel = 0.02 + 0.98 * fresnel;

    // Reflection
    vec3 refl = reflect(rd, wnor);
    vec3 reflCol = getSky(refl);

    // Underwater color
    vec3 waterCol = vec3(0.0, 0.04, 0.04);

    col = mix(waterCol, reflCol, fresnel);
    col = applyFog(col, tWater, rd);
} else if (tTerrain > 0.0) {
    // Hit terrain (same as original code)
    // ...
}
```

### 2. Terrain + Volumetric Clouds
Render the terrain first to get color and depth, then march the cloud slab along the ray, compositing onto the terrain using front-to-back alpha blending.
- Key: Cloud self-shadowing (offset sampling toward light direction), god ray accumulation

```glsl
// In the main function:
vec3 col;
float t = raymarch(ro, rd);

if (t > 0.0) {
    // Render terrain...
    vec3 pos = ro + t * rd;
    vec3 nor = calcNormal(pos, t);
    vec3 mate = getMaterial(pos, nor);
    float sha = calcShadow(pos + nor * 0.5, SUN_DIR);
    vec3 lin = calcLighting(pos, nor, rd, sha);
    col = mate * lin;
    col = applyFog(col, t, rd);
} else {
    col = getSky(rd);
}

// Overlay volumetric clouds
vec4 clouds = raymarchClouds(ro, rd);
col = col * (1.0 - clouds.a) + clouds.rgb;
```

### 3. Terrain + Volumetric Fog/Dust
Volumetric dust fog can be added after the main marching is complete, additionally sample a 3D FBM density field along the ray with distance-based attenuation. Suitable for desert, volcanic, and similar scenes.
- Key: Step size adapts to density — smaller steps in dense regions

### 4. Terrain + SDF Object Placement
SDF ellipsoids can be placed as trees on the terrain. Terrain marching and object marching can be separated or combined. Objects are placed on a 2D grid with hash-based jitter.
- Key: `floor(p.xz/gridSize)` determines the grid cell, `hash(cell)` determines tree position/size

```glsl
#define TREE_GRID 30.0

// Place tree SDFs in a grid
float mapTrees(vec3 p) {
    vec2 cell = floor(p.xz / TREE_GRID);
    vec2 cellCenter = (cell + 0.5) * TREE_GRID;

    // Hash to randomize position
    vec2 jitter = (hash2(cell) - 0.5) * TREE_GRID * 0.6;
    vec2 treePos = cellCenter + jitter;

    // Tree trunk height
    float groundH = terrainL(treePos);

    // SDF: ellipsoid tree canopy
    vec3 treeCenter = vec3(treePos.x, groundH + 8.0, treePos.y);
    float treeSize = 4.0 + hash(cell) * 3.0;
    vec3 q = (p - treeCenter) / vec3(treeSize, treeSize * 1.5, treeSize);
    return (length(q) - 1.0) * treeSize * 0.8;
}
```

### 5. Terrain + Temporal Anti-Aliasing (TAA)
Inter-frame reprojection blending can be used for temporal anti-aliasing. The current frame's camera matrix is stored in buffer pixels, and the next frame uses it to reproject 3D points back to the previous frame's screen coordinates, blending historical colors.
- Key: blend ratio ~10% new frame + 90% history frame, with increased new frame weight in motion areas
