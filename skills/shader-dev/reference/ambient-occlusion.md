# SDF Ambient Occlusion — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing a complete step-by-step tutorial, mathematical derivations, variant analysis, and advanced usage.

## Prerequisites

- GLSL basic syntax (uniform, varying, function definitions)
- **Signed Distance Field (SDF)** concept: `map(p)` returns the distance from point p to the nearest surface
- **Raymarching** basic loop: marching along a ray to find surface intersections
- **Surface normal computation**: Obtaining the normal direction via SDF gradient (finite differences)
- Vector math fundamentals: dot product, normalization, vector addition/subtraction

## Core Principles in Detail

The core idea of SDF ambient occlusion: **Sample the SDF at multiple distances along the surface normal and compare the "expected distance" with the "actual distance" to estimate the degree of occlusion.**

For a point P on the surface with normal N, at distance h:
- **Expected distance** = h (if the surroundings are completely open, the SDF value should equal the distance to the surface)
- **Actual distance** = map(P + N × h) (real SDF value)
- **Occlusion contribution** = h - map(P + N × h) (the larger the difference, the more nearby geometry is occluding)

The final result is a weighted sum of occlusion contributions from multiple sample points, yielding a [0, 1] occlusion factor:
- 1.0 = no occlusion (bright)
- 0.0 = fully occluded (dark corner)

Key mathematical formula (additive accumulation form):

```
AO = 1 - k × Σ(weight_i × max(0, h_i - map(P + N × h_i)))
```

Where `weight_i` typically decays exponentially or geometrically (closer samples have higher weight), and `k` is a global intensity coefficient.

## Implementation Steps in Detail

### Step 1: Build the Base SDF Scene

**What**: Define a `map()` function that returns the signed distance value for any point in space.

**Why**: AO computation relies entirely on SDF queries, so a working distance field is needed first.

```glsl
float map(vec3 p) {
    float d = p.y; // Ground plane
    d = min(d, length(p - vec3(0.0, 1.0, 0.0)) - 1.0); // Sphere
    d = min(d, length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4); // Torus
    return d;
}
```

### Step 2: Compute Surface Normal

**What**: Compute the normal direction via finite difference approximation of the SDF gradient.

**Why**: AO sampling probes outward along the normal direction; the normal determines the sampling direction.

```glsl
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}
```

### Step 3: Implement Classic Normal-Direction AO (Additive Accumulation)

**What**: Sample the SDF at 5 distances along the normal direction, accumulating occlusion.

**Why**: This is a classic method — the most concise and efficient SDF-AO implementation. 5 samples strike an excellent balance between quality and performance. The weight decays at 0.95 exponentially, giving closer samples more influence (near-surface occlusion is more perceptually important).

```glsl
// Classic AO
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0; // Initial weight
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0; // Sample distance: 0.01 ~ 0.13
        float d = map(pos + h * nor);             // Actual SDF distance
        occ += (h - d) * sca;                     // Accumulate (expected - actual) × weight
        sca *= 0.95;                              // Weight decay
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```

### Step 4: Apply AO to Lighting

**What**: Multiply the AO factor into ambient and indirect light components.

**Why**: AO simulates the degree to which indirect light is occluded. Physically, it should only affect ambient/indirect light, not the direct light source's diffuse and specular (direct light occlusion is handled by shadows). However, in practice AO is often multiplied into all lighting for a stronger visual effect.

```glsl
float ao = calcAO(pos, nor);

// Method A: Affect only ambient light (physically correct)
vec3 ambient = vec3(0.2, 0.3, 0.5) * ao;
vec3 color = diffuse * shadow + ambient;

// Method B: Affect all lighting (stronger visual effect)
vec3 color = (diffuse * shadow + ambient) * ao;

// Method C: Combined with sky visibility bias
float skyVis = 0.5 + 0.5 * nor.y; // Upward-facing surfaces are brighter
vec3 color = diffuse * shadow + ambient * ao * skyVis;
```

### Step 5: Raymarching Main Loop Integration

**What**: Integrate AO into the complete raymarching pipeline.

**Why**: AO is part of the lighting computation and needs to be calculated after hitting a surface but before final output.

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // ... camera setup, ray generation ...

    // Raymarching loop
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < 0.001) break;
        t += d;
        if (t > 100.0) break;
    }

    // Compute lighting on hit
    vec3 col = vec3(0.0);
    if (t < 100.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        // Lighting
        vec3 lig = normalize(vec3(1.0, 0.8, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sky = 0.5 + 0.5 * nor.y;
        col = vec3(1.0) * dif + vec3(0.2, 0.3, 0.5) * sky * ao;
    }

    fragColor = vec4(col, 1.0);
}
```

## Variant Details

### Variant 1: Multiplicative AO

**Difference from base version**: Starts at 1.0 and progressively multiplies down, rather than using additive accumulation then inverting. The multiplicative form naturally guarantees the result stays in [0, 1], avoids the need for clamping, and provides more natural falloff for multiple overlapping occlusions.

**Source**: Multiplicative accumulation approach

```glsl
// Multiplicative AO
float calcAO_multiplicative(vec3 pos, vec3 nor) {
    float ao = 1.0;
    float dist = 0.0;
    for (int i = 0; i <= 5; i++) {
        dist += 0.1; // Uniform step of 0.1
        float d = map(pos + nor * dist);
        ao *= 1.0 - max(0.0, (dist - d) * 0.2 / dist);
    }
    return ao;
}
```

### Variant 2: Multi-Scale AO

**Difference from base version**: Exponentially increases sampling distances (0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4), computing short-range and long-range occlusion separately. Short-range AO reveals contact shadows and surface detail; long-range AO reveals large-scale environmental occlusion. Fully unrolled with no loops, making it GPU-efficient.

**Source**: Multi-scale sampling approach

```glsl
// Multi-scale AO
float calcAO_multiscale(vec3 pos, vec3 nor) {
    // Short-range AO (contact shadows)
    float aoS = 1.0;
    aoS *= clamp(map(pos + nor * 0.1) * 10.0, 0.0, 1.0);  // Adjustable: distance 0.1, weight 10.0
    aoS *= clamp(map(pos + nor * 0.2) * 5.0,  0.0, 1.0);  // Adjustable: distance 0.2, weight 5.0
    aoS *= clamp(map(pos + nor * 0.4) * 2.5,  0.0, 1.0);  // Adjustable: distance 0.4, weight 2.5
    aoS *= clamp(map(pos + nor * 0.8) * 1.25, 0.0, 1.0);  // Adjustable: distance 0.8, weight 1.25

    // Long-range AO (large-scale occlusion)
    float ao = aoS;
    ao *= clamp(map(pos + nor * 1.6) * 0.625,  0.0, 1.0); // Adjustable: distance 1.6
    ao *= clamp(map(pos + nor * 3.2) * 0.3125, 0.0, 1.0); // Adjustable: distance 3.2
    ao *= clamp(map(pos + nor * 6.4) * 0.15625,0.0, 1.0);  // Adjustable: distance 6.4

    return max(0.035, pow(ao, 0.3)); // pow compresses dynamic range, min prevents total black
}
```

### Variant 3: Jittered Sampling AO

**Difference from base version**: Adds hash-based jitter on top of uniform sample positions, breaking the banding artifacts caused by fixed sample spacing. Also uses a `1/(1+l)` distance-decay weight so farther samples have less influence.

**Source**: Jittered sampling approach

```glsl
// Jittered sampling AO
float hash(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_jittered(vec3 pos, vec3 nor, float maxDist) {
    float ao = 0.0;
    const float nbIte = 6.0;          // Adjustable: number of samples
    for (float i = 1.0; i < nbIte + 0.5; i++) {
        float l = (i + hash(i)) * 0.5 / nbIte * maxDist; // Jittered sample position
        ao += (l - map(pos + nor * l)) / (1.0 + l);       // Distance-decay weight
    }
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}
// Usage example: calcAO_jittered(pos, nor, 4.0)
```

### Variant 4: Hemispherical Random Direction AO

**Difference from base version**: Instead of sampling only along the normal direction, generates multiple random directions within the normal hemisphere. Closer to the true physical model of ambient occlusion (light arriving from all directions in the hemisphere), but requires more samples (typically 32) for smooth results.

**Source**: Hemispherical random direction approach

```glsl
// Hemispherical random direction AO
vec2 hash2(float n) {
    return fract(sin(vec2(n, n + 1.0)) * vec2(43758.5453, 22578.1459));
}

float calcAO_hemisphere(vec3 pos, vec3 nor, float seed) {
    float occ = 0.0;
    for (int i = 0; i < 32; i++) {                              // Adjustable: sample count (16~64)
        float h = 0.01 + 4.0 * pow(float(i) / 31.0, 2.0);      // Quadratic distribution biased toward near-field
        vec2 an = hash2(seed + float(i) * 13.1) * vec2(3.14159, 6.2831); // Random spherical coordinates
        vec3 dir = vec3(sin(an.x) * sin(an.y), sin(an.x) * cos(an.y), cos(an.x));
        dir *= sign(dot(dir, nor));                               // Flip to normal hemisphere
        occ += clamp(5.0 * map(pos + h * dir) / h, -1.0, 1.0); // Signed occlusion
    }
    return clamp(occ / 32.0, 0.0, 1.0);
}
```

### Variant 5: Fibonacci Sphere Uniform Hemisphere AO

**Difference from base version**: Uses Fibonacci sphere points instead of random directions, achieving quasi-uniform hemisphere sampling distribution. Avoids the clustering problem of pure random sampling, yielding higher quality at the same sample count. Can also be paired with a separate directional occlusion function (e.g., SSS/soft shadow) for multi-level occlusion.

**Source**: Fibonacci sphere sampling approach

```glsl
// Fibonacci sphere sampling AO
vec3 forwardSF(float i, float n) {
    const float PI  = 3.141592653589793;
    const float PHI = 1.618033988749895;
    float phi = 2.0 * PI * fract(i / PHI);
    float zi = 1.0 - (2.0 * i + 1.0) / n;
    float sinTheta = sqrt(1.0 - zi * zi);
    return vec3(cos(phi) * sinTheta, sin(phi) * sinTheta, zi);
}

float hash1(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_fibonacci(vec3 pos, vec3 nor) {
    float ao = 0.0;
    for (int i = 0; i < 32; i++) {                         // Adjustable: sample count
        vec3 ap = forwardSF(float(i), 32.0);
        float h = hash1(float(i));
        ap *= sign(dot(ap, nor)) * h * 0.1;                // Flip to hemisphere + random scale
        ao += clamp(map(pos + nor * 0.01 + ap) * 3.0, 0.0, 1.0);
    }
    ao /= 32.0;
    return clamp(ao * 6.0, 0.0, 1.0);
}
```

## Performance Optimization Details

### Bottleneck Analysis

The performance bottleneck of SDF-AO lies almost entirely in **SDF sample count** — each `map()` call is a full scene distance computation. For complex scenes, this can be very expensive.

### Optimization Techniques

#### 1. Reduce Sample Count

Classic normal-direction AO only needs 3~5 samples for acceptable quality. Hemispherical sampling is more physically correct but requires 16~32 samples; use it when the performance budget allows.

#### 2. Early Exit Optimization

Exit the loop early when accumulated occlusion is already large enough, avoiding unnecessary SDF computations.

```glsl
if (occ > 0.35) break; // Early exit when heavily occluded
```

#### 3. Unroll Loops

For fixed sample counts (especially 4~7), manually unrolling loops avoids branch overhead and is GPU-friendly. The multi-scale AO variant fully unrolls 7 samples.

#### 4. Simplify AO for Distant Objects

Objects far from the camera can use fewer AO samples or skip AO entirely.

```glsl
float aoSteps = mix(5.0, 2.0, clamp(t / 50.0, 0.0, 1.0));
```

#### 5. Precompilation Switches

Use `#ifdef` to disable AO in debug or low-performance modes.

```glsl
#ifdef ENABLE_AMBIENT_OCCLUSION
    float ao = calcAO(pos, nor);
#else
    float ao = 1.0;
#endif
```

#### 6. Hand-Painted Pseudo-AO Blending

For static or semi-static scenes, pseudo-AO values (based on material ID or position) can be precomputed and blended with real-time AO to reduce runtime computation.

```glsl
float focc = /* preset occlusion based on material */;
float finalAO = calcAO(pos, nor) * focc;
```

#### 7. SDF Simplification

A simplified version of `map()` (ignoring small details) can be used for AO sampling, since AO is inherently low-frequency information.

## Combination Suggestions in Detail

### 1. AO + Soft Shadow

The most common combination. AO handles indirect light occlusion (corners, crevices); soft shadows handle direct light occlusion. Simply multiply the two:

```glsl
float sha = calcShadow(pos, lightDir, 0.02, 20.0, 8.0);
float ao = calcAO(pos, nor);
col = diffuse * sha + ambient * ao; // Each handles its own domain
// Or more simply:
col = lighting * sha * ao;
```

### 2. AO + Sky Visibility

Use the normal's y component to estimate the degree of upward-facing, multiplied with AO to simulate sky light occlusion:

```glsl
float skyVis = 0.5 + 0.5 * nor.y;
col += skyColor * ao * skyVis;
```

### 3. AO + Subsurface Scattering / Bounce Light

AO can modulate bounce light and SSS intensity (occluded areas also don't receive bounce light):

```glsl
float bou = clamp(-nor.y, 0.0, 1.0); // Downward-facing surfaces receive ground bounce
col += bounceColor * bou * ao;
col += sssColor * sss * (0.05 + 0.95 * ao); // SSS also modulated by AO
```

### 4. AO + Convexity / Corner Detection

The same SDF probing loop can sample both outward (+N) and inward (-N), yielding AO and convexity information respectively, useful for edge highlights or wear effects:

```glsl
vec2 aoAndCorner = getOcclusion(pos, nor); // .x = AO, .y = convexity
col *= aoAndCorner.x;                       // AO darkening
col = mix(col, edgeColor, aoAndCorner.y);   // Convexity coloring
```

### 5. AO + Fresnel Environment Reflection

AO should also modulate the environment reflection term; otherwise concave areas will show unnatural bright environment reflections:

```glsl
float fre = pow(1.0 - max(dot(rd, nor), 0.0), 5.0);
col += envColor * fre * ao; // Reduce environment reflection in occluded areas
```
