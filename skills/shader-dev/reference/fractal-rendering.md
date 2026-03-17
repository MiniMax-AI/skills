# Fractal Rendering — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing prerequisites, step-by-step explanations, mathematical derivations, variant descriptions, in-depth performance analysis, and complete combination example code.

## Prerequisites

- **GLSL Basics**: uniform, varying, built-in functions (`dot`, `length`, `normalize`, `abs`, `fract`)
- **Complex Number Arithmetic**: representing complex numbers as `vec2`, multiplication `(a+bi)(c+di) = (ac-bd, ad+bc)`
- **Vector Math**: dot product, cross product, matrix transforms
- **Ray Marching Basics** (required for 3D fractals): stepping along a ray, using distance fields for collision detection
- **Coordinate Normalization**: mapping pixel coordinates to the `[-1, 1]` range

## Core Principles in Detail

The essence of fractal rendering is **visualization of iterative systems**. Core algorithm patterns fall into three categories:

### 1. Escape-Time Algorithm

For each point `c` on the complex plane, repeatedly iterate `Z <- Z^2 + c`, counting the number of steps needed for Z to escape (`|Z| > R`). More steps means closer to the fractal boundary.

**Distance Estimation** computes the precise distance from a point to the fractal by simultaneously tracking the derivative `Z'`:
```
Z  <- Z^2 + c       (value iteration)
Z' <- 2*Z*Z' + 1    (derivative iteration)
d(c) = |Z|*log|Z| / |Z'|  (Hubbard-Douady potential function)
```
Distance estimation produces smoother coloring than pure escape-time step counting, and is a prerequisite for ray marching in 3D fractals.

### 2. Iterated Function System (IFS)

Apply a set of transforms (folding `abs()`, scaling `Scale`, offset `Offset`) to points in space, iterating repeatedly to produce self-similar structures. Core steps of KIFS (Kaleidoscopic IFS) commonly used in 3D:
```
p = abs(p)                          // Fold (symmetrize)
sort p.xyz descending               // Sort (select symmetry axis)
p = Scale * p - Offset * (Scale-1)  // Scale and offset
```

### 3. Spherical Inversion Fractal

Apollonian-type fractals use `fract()` for space folding + spherical inversion `p *= s/dot(p,p)`:
```
p = -1.0 + 2.0 * fract(0.5*p + 0.5)   // Fold space to [-1,1]
r^2 = dot(p, p)
k = s / r^2                             // Inversion factor
p *= k; scale *= k                       // Spherical inversion
```

All 3D fractals are rendered using **Sphere Tracing (Ray Marching)**: stepping along the view ray by the distance field value at each step, until close enough to the surface.

## Implementation Steps in Detail

### Step 1: Coordinate Normalization

**What**: Map pixel coordinates to standard coordinates centered on the screen with aspect ratio correction.

**Why**: All fractal calculations must be performed in mathematical space, independent of pixel resolution.

```glsl
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
// p now has y range [-1,1], x scaled by aspect ratio
```

### Step 2: 2D Fractal — Mandelbrot Escape-Time Iteration

**What**: For each pixel point as complex number `c`, iterate `Z <- Z^2 + c` while tracking the derivative.

**Why**: Escape time produces fractal structure; derivative tracking enables distance estimation coloring.

```glsl
float distanceToMandelbrot(in vec2 c) {
    vec2 z  = vec2(0.0);
    vec2 dz = vec2(0.0);  // Derivative
    float m2 = 0.0;

    for (int i = 0; i < MAX_ITER; i++) {
        if (m2 > BAILOUT * BAILOUT) break;

        // Z' -> 2*Z*Z' + 1 (complex derivative chain rule)
        dz = 2.0 * vec2(z.x*dz.x - z.y*dz.y,
                         z.x*dz.y + z.y*dz.x) + vec2(1.0, 0.0);

        // Z -> Z^2 + c (complex squaring)
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;

        m2 = dot(z, z);
    }

    // Distance estimation: d(c) = |Z|*log|Z| / |Z'|
    return 0.5 * sqrt(dot(z,z) / dot(dz,dz)) * log(dot(z,z));
}
```

### Step 3: 3D Fractal — Distance Field Function (Mandelbulb Example)

**What**: Implement the Mandelbulb power-N iteration using spherical coordinates, returning a distance estimate.

**Why**: 3D fractals cannot be directly colored via escape-time on pixels; they require distance fields for ray marching.

```glsl
float mandelbulb(vec3 p) {
    vec3 z = p;
    float dr = 1.0;  // Derivative (distance scaling factor)
    float r;

    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > BAILOUT) break;

        // Convert to spherical coordinates
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);

        // Derivative: dr -> power * r^(power-1) * dr + 1
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;

        // z -> z^power + p (spherical coordinate exponentiation)
        r = pow(r, POWER);
        theta *= POWER;
        phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi),
                      sin(theta)*cos(phi),
                      sin(phi)) + p;
    }

    // Distance estimation
    return 0.5 * log(r) * r / dr;
}
```

### Step 4: 3D Fractal — IFS Distance Field (Menger Sponge Example)

**What**: Construct a KIFS fractal distance field through fold-sort-scale-offset iteration.

**Why**: IFS fractals produce self-similar structures through spatial transforms rather than numerical iteration; distance is tracked via `Scale^(-n)` scaling.

```glsl
float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // Infinite tiling
    float d = 1000.0;

    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);                              // Fold
        if (z.x < z.y) z.xy = z.yx;             // Sort
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0); // Scale + offset
        if (z.z < -0.5 * OFFSET.z * (SCALE - 1.0))
            z.z += OFFSET.z * (SCALE - 1.0);
        d = min(d, length(z) * pow(SCALE, float(-n) - 1.0));
    }

    return d - 0.001;
}
```

### Step 5: 3D Fractal — Spherical Inversion Distance Field (Apollonian Type)

**What**: Construct an Apollonian fractal using fract folding + spherical inversion iteration, while recording orbit traps.

**Why**: Spherical inversion `p *= s/dot(p,p)` produces sphere packing structures; orbit traps provide color and AO information.

```glsl
vec4 orb;  // Global orbit trap

float apollonianDE(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);  // Fold space to [-1,1]
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));          // Record orbit trap
        float k = s / r2;                          // Inversion factor
        p *= k;
        scale *= k;
    }

    return 0.25 * abs(p.y) / scale;
}
```

### Step 6: Ray Marching (Sphere Tracing)

**What**: Step along the ray direction, advancing by the distance field value at each step, until hitting the surface.

**Why**: The distance field guarantees safe stepping (won't pass through the surface), and is the standard method for rendering implicit 3D fractals.

```glsl
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;  // Relax precision with distance
        float h = map(ro + rd * t);
        if (h < precis || t > MAX_DIST) break;
        t += h * FUDGE_FACTOR;         // fudge < 1.0 improves safety
    }
    return (t > MAX_DIST) ? -1.0 : t;
}
```

### Step 7: Normal Calculation (Finite Differences)

**What**: Sample the distance field gradient around the hit point as the surface normal.

**Why**: Implicit surfaces have no analytical normals and require numerical approximation. Tetrahedral sampling (4-tap) saves 1/3 of the cost compared to central differences (6-tap).

```glsl
// 6-tap central difference method (more intuitive)
vec3 calcNormal_6tap(vec3 pos) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(pos + e.xyy) - map(pos - e.xyy),
        map(pos + e.yxy) - map(pos - e.yxy),
        map(pos + e.yyx) - map(pos - e.yyx)));
}

// 4-tap tetrahedral method (more efficient, recommended)
vec3 calcNormal_4tap(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx));
}
```

### Step 8: Shading and Lighting

**What**: Compute Lambertian diffuse + ambient + AO for hit surfaces.

**Why**: Lighting gives 3D fractals depth and material quality. Orbit trap values (`orb`) can serve both as color mapping and as simple AO.

```glsl
vec3 shade(vec3 pos, vec3 nor, vec3 rd, vec4 trap) {
    vec3 light1 = normalize(LIGHT_DIR);
    float diff = clamp(dot(light1, nor), 0.0, 1.0);
    float amb  = 0.7 + 0.3 * nor.y;
    float ao   = pow(clamp(trap.w * 2.0, 0.0, 1.0), 1.2); // Orbit trap AO

    vec3 brdf = vec3(0.4) * amb * ao      // Ambient
              + vec3(1.0) * diff * ao;     // Diffuse

    // Map material color from orbit trap
    vec3 rgb = vec3(1.0);
    rgb = mix(rgb, vec3(1.0, 0.8, 0.2), clamp(6.0*trap.y, 0.0, 1.0));
    rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0-2.0*trap.z, 0.0, 1.0), 8.0));

    return rgb * brdf;
}
```

### Step 9: Camera Setup

**What**: Build a look-at camera matrix, converting pixel coordinates to 3D ray directions.

**Why**: All 3D fractal ray marching requires a unified camera framework to generate rays.

```glsl
void setupCamera(vec2 uv, vec3 ro, vec3 ta, float cr,
                 out vec3 rd) {
    vec3 cw = normalize(ta - ro);                   // forward
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);          // roll
    vec3 cu = normalize(cross(cw, cp));              // right
    vec3 cv = normalize(cross(cu, cw));              // up
    rd = normalize(uv.x * cu + uv.y * cv + 2.0 * cw); // FOV ~ 2.0
}
```

## Common Variants in Detail

### 1. 2D Mandelbrot (Distance Estimation Coloring)

Difference from base version (3D Apollonian): pure 2D computation, no ray marching needed, uses complex iteration + distance coloring.

```glsl
// Replace entire mainImage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0*fragCoord - iResolution.xy) / iResolution.y;

    // Animated zoom
    float tz = 0.5 - 0.5*cos(0.225*iTime);
    float zoo = pow(0.5, 13.0*tz);
    vec2 c = vec2(-0.05, 0.6805) + p * zoo; // Tunable: zoom center point

    // Iteration
    vec2 z = vec2(0.0), dz = vec2(0.0);
    for (int i = 0; i < 300; i++) { // Tunable: iteration count
        if (dot(z,z) > 1024.0) break;
        dz = 2.0*vec2(z.x*dz.x-z.y*dz.y, z.x*dz.y+z.y*dz.x) + vec2(1.0,0.0);
        z  = vec2(z.x*z.x-z.y*z.y, 2.0*z.x*z.y) + c;
    }

    float d = 0.5*sqrt(dot(z,z)/dot(dz,dz))*log(dot(z,z));
    d = clamp(pow(4.0*d/zoo, 0.2), 0.0, 1.0); // Tunable: 0.2 controls contrast
    fragColor = vec4(vec3(d), 1.0);
}
```

### 2. Mandelbulb Power-N (3D Spherical Coordinate Fractal)

Difference from base version: uses spherical coordinate trigonometric functions instead of spherical inversion, with a tunable `POWER` parameter controlling the fractal shape.

```glsl
#define POWER 8.0   // Tunable: 2-16, higher = more complex structure
#define FRACTAL_ITER 4  // Tunable: 2-8, more = more detail

float mandelbulbDE(vec3 p) {
    vec3 z = p;
    float dr = 1.0;
    float r;
    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > 2.0) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER;
        phi   *= POWER;
        z = r * vec3(cos(theta)*cos(phi), sin(theta)*cos(phi), sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```

### 3. Menger Sponge (KIFS Folding Type)

Difference from base version: uses abs() folding + conditional sorting instead of spherical inversion, producing regular geometric fractals.

```glsl
#define SCALE 3.0                           // Tunable: scaling factor, 2.0-4.0
#define OFFSET vec3(0.92858,0.92858,0.32858) // Tunable: offset vector, changes shape
#define IFS_ITER 7                          // Tunable: iteration count

float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // Infinite tiling
    float d = 1000.0;
    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;    // Conditional sorting
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0);
        if (z.z < -0.5*OFFSET.z*(SCALE-1.0))
            z.z += OFFSET.z*(SCALE-1.0);
        d = min(d, length(z) * pow(SCALE, float(-n)-1.0));
    }
    return d - 0.001;
}
```

### 4. Quaternion Julia Set

Difference from base version: uses quaternion algebra `Z <- Z^2 + c` (4D), Julia sets use a fixed `c` parameter instead of per-point `c`, visualized by taking 3D cross-sections.

```glsl
// Quaternion squaring
vec4 qsqr(vec4 a) {
    return vec4(a.x*a.x - a.y*a.y - a.z*a.z - a.w*a.w,
                2.0*a.x*a.y, 2.0*a.x*a.z, 2.0*a.x*a.w);
}

float juliaDE(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0);
    float md2 = 1.0;
    float mz2 = dot(z, z);

    for (int i = 0; i < 11; i++) { // Tunable: iteration count
        md2 *= 4.0 * mz2;         // |dz| -> 2*|z|*|dz|
        z = qsqr(z) + c;          // z -> z^2 + c
        mz2 = dot(z, z);
        if (mz2 > 4.0) break;
    }

    return 0.25 * sqrt(mz2 / md2) * log(mz2);
}
// Animated Julia parameter c:
// vec4 c = 0.45*cos(vec4(0.5,3.9,1.4,1.1) + time*vec4(1.2,1.7,1.3,2.5)) - vec4(0.3,0,0,0);
```

### 5. Minimal IFS Field (2D, No Ray Marching)

Difference from base version: pure 2D implementation, only ~20 lines of code, using `abs(p)/dot(p,p) + offset` for iteration, producing a density field through weighted accumulation.

```glsl
float field(vec3 p) {
    float strength = 7.0 + 0.03 * log(1.e-6 + fract(sin(iTime) * 4373.11));
    float accum = 0.0, prev = 0.0, tw = 0.0;
    for (int i = 0; i < 32; ++i) {  // Tunable: iteration count
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-0.5, -0.4, -1.5); // Tunable: offset values change shape
        float w = exp(-float(i) / 7.0);             // Tunable: 7.0 controls decay
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0.0, 5.0 * accum / tw - 0.7);
}
// Sample field() directly on fragCoord as brightness/color
```

## Performance Optimization Details

### Bottleneck Analysis

The core bottleneck in fractal rendering is **nested loops**: outer ray marching steps x inner fractal iterations. A single pixel may execute `200 steps x 8 iterations = 1600` distance field evaluations.

### Optimization Techniques

#### 1. Reduce Ray Marching Steps
Lower `MAX_STEPS` from 200 to 60-100, compensating precision loss with a fudge factor (0.7-0.9).
```glsl
t += h * 0.7; // Fudge factor < 1.0, allows larger steps but reduces penetration risk
```

#### 2. Adaptive Precision
Relax the collision threshold as distance increases; far objects don't need pixel-level precision.
```glsl
float precis = 0.001 * t; // Precision grows linearly with distance
```

#### 3. Early Exit
In fractal iteration, break immediately once `|z|^2 > bailout`.
```glsl
if (m2 > 4.0) break; // Don't continue useless iterations
```

#### 4. Reduce Iteration Count
Fractal iteration counts (`INVERSION_ITER`, `IFS_ITER`) reduced from 8 to 4-5 have minimal visual impact but significant performance gains.

#### 5. Use 4-Tap Instead of 6-Tap for Normals
The tetrahedral method requires only 4 `map()` calls instead of 6, saving 33% normal computation cost.

#### 6. AA Downgrade
Use `#define AA 1` during development, switch to `AA 2` for release. `AA 3` has massive performance impact (9x overhead).

#### 7. Distance Field Scaling
For non-unit-sized fractals, scale the space first then scale the distance value to avoid precision issues.
```glsl
float z1 = 2.0;
return mandelbulb(p / z1) * z1;
```

#### 8. Avoid `pow()` Inside Loops
`pow(r, power)` in Mandelbulb is expensive; low powers (e.g., 2, 3) can be manually expanded instead.

## Combination Suggestions

### 1. Fractal + Volumetric Lighting

Accumulate scattered light passing through fractal gaps during ray marching, producing "god rays" effects.

```glsl
// Accumulate additionally in ray march loop
float glow = 0.0;
for (...) {
    float h = map(ro + rd*t);
    glow += exp(-10.0 * h); // Closer to surface = larger contribution
    ...
}
col += glowColor * glow * 0.01;
```

### 2. Fractal + Post-Processing (Tone Mapping / FXAA)

3D fractals have rich high-frequency detail, prone to aliasing. Use ACES Tone Mapping + sRGB correction + FXAA post-processing.

```glsl
// ACES tone mapping
vec3 aces_approx(vec3 v) {
    v = max(v, 0.0) * 0.6;
    float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((v*(a*v+b))/(v*(c*v+d)+e), 0.0, 1.0);
}
col = aces_approx(col);
col = pow(col, vec3(1.0/2.4)); // sRGB gamma
```

### 3. Fractal + Transparent Refraction (Multi-Bounce Refraction)

Used for "crystal ball" effects on volumetric fractals like Mandelbulb. Uses negative distance fields for reverse ray marching inside, combined with Beer's law absorption.

```glsl
// Invert distance field for interior stepping
float dfactor = isInside ? -1.0 : 1.0;
float d = dfactor * map(ro + rd * t);
// Beer's law light absorption
ragg *= exp(-st * beer); // beer = negative color vector
// Refraction direction
vec3 refr = refract(rd, sn, isInside ? 1.0/ior : ior);
```

### 4. Fractal + Orbit Trap Texture Mapping

Orbit trap values can be mapped to HSV color space for rich coloring, or mapped as self-emission for glowing fractal effects.

```glsl
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
// Map orbit trap to HSV
vec3 col = hsv2rgb(vec3(trap.x * 0.5, 0.9, 0.8));
```

### 5. Fractal + Soft Shadow

Perform an additional ray march from the fractal surface toward the light source, accumulating the minimum `h/t` ratio to generate soft shadows.

```glsl
float softshadow(vec3 ro, vec3 rd, float mint, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd*t);
        res = min(res, k * h / t); // Larger k = harder shadows
        if (res < 0.001) break;
        t += clamp(h, 0.01, 0.5);
    }
    return clamp(res, 0.0, 1.0);
}
```
