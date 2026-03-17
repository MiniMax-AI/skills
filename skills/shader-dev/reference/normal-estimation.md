# SDF Normal Estimation — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing prerequisite knowledge, step-by-step explanations, mathematical derivations, variant analysis, and complete combination code examples.

---

## Prerequisites

### GLSL Fundamentals

- **Vector types**: `vec2`/`vec3` operations, swizzle syntax (`.xyy`, `.yxy`, `.yyx`)
- Swizzle is used in normal estimation to quickly construct three-axis offset vectors from `vec2(h, 0.0)`

### Vector Calculus

- **Gradient concept**: The gradient `∇f` of a scalar field `f(x, y, z)` is a vector pointing in the direction of the fastest increase of the function value
- For an SDF, the gradient direction is the **outward surface normal direction**
- Mathematical definition of gradient: `∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z)`

### SDF Concepts

- `map(p)` returns the signed distance from point `p` to the nearest surface
- Positive = outside the surface, negative = inside, zero = exactly on the surface
- An ideal SDF has a gradient magnitude of exactly 1 (Eikonal equation), but in practice this may deviate after boolean operations or deformations

### Numerical Differentiation

- **Finite differences** to approximate derivatives: `f'(x) ≈ (f(x+h) - f(x-h)) / 2h` (central difference)
- Or `f'(x) ≈ (f(x+h) - f(x)) / h` (forward difference)
- Forward difference accuracy is O(h), central difference accuracy is O(h²)

---

## Implementation Steps in Detail

### Step 1: Define the SDF Scene Function

**What**: Create a `map(vec3 p) -> float` function that returns the signed distance from any point in space to the scene surface.

**Why**: All normal estimation methods need to repeatedly call this function to sample the distance field. The normal function itself does not care about the SDF shape — it only needs to query distance values at different positions in space.

```glsl
float map(vec3 p) {
    float d = length(p) - 1.0; // Unit sphere
    // Can compose more SDF primitives
    return d;
}
```

### Step 2: Choose a Difference Method and Implement the Normal Function

#### Method A: Forward Differences — 4 Samples

**What**: Sample the SDF at point `p` and at three axis-aligned offsets, using the differences to build the gradient.

**Why**: The simplest and most intuitive approach. Requires 4 samples (`map(p)` once + three offsets once each), suitable for beginners and performance-sensitive scenarios with lower accuracy requirements.

**Mathematical derivation**:
- `∂f/∂x ≈ (f(x+ε, y, z) - f(x, y, z)) / ε`
- Since we `normalize()` at the end, the constant denominator `ε` can be omitted
- Thus `n = normalize(map(p+εx̂) - map(p), map(p+εŷ) - map(p), map(p+εẑ) - map(p))`

```glsl
// Classic forward difference
const float EPSILON = 1e-3;

vec3 getNormal(vec3 p) {
    vec3 n;
    n.x = map(vec3(p.x + EPSILON, p.y, p.z));
    n.y = map(vec3(p.x, p.y + EPSILON, p.z));
    n.z = map(vec3(p.x, p.y, p.z + EPSILON));
    return normalize(n - map(p));
}
```

#### Method B: Central Differences — 6 Samples

**What**: Sample once in each positive and negative direction per axis, taking the difference.

**Why**: Symmetric sampling eliminates the first-order error term, improving accuracy from O(ε) to O(ε²). The cost is 6 SDF calls.

**Mathematical derivation**:
- Taylor expansion: `f(x+ε) = f(x) + εf'(x) + ε²f''(x)/2 + ...`
- `f(x-ε) = f(x) - εf'(x) + ε²f''(x)/2 - ...`
- Subtraction: `f(x+ε) - f(x-ε) = 2εf'(x) + O(ε³)`
- The first-order error term is eliminated, improving accuracy by one order

```glsl
// Compact swizzle notation
vec3 getNormal(vec3 p) {
    vec2 o = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + o.xyy) - map(p - o.xyy),
        map(p + o.yxy) - map(p - o.yxy),
        map(p + o.yyx) - map(p - o.yyx)
    ));
}
```

#### Method C: Tetrahedron Technique — 4 Samples (Recommended)

**What**: Sample the SDF along the 4 vertices of a regular tetrahedron, computing the weighted sum to obtain the gradient.

**Why**: Requires only 4 samples (2 fewer than central difference), yet is more accurate and symmetric than forward difference.

**Mathematical derivation**:
- The 4 vertices of a regular tetrahedron: `(+,+,+)`, `(+,-,-)`, `(-,+,-)`, `(-,-,+)`
- The coefficient `0.5773 ≈ 1/√3` normalizes the vertices onto the unit sphere
- The weighted sum `Σ eᵢ·map(p + eᵢ·ε)` is equivalent to a gradient estimate in 4 symmetric directions
- Due to the perfect symmetry of the tetrahedron, error distribution is more uniform than forward difference
- Actual accuracy falls between forward and central difference, but only requires 4 samples

```glsl
// Classic tetrahedron technique
vec3 calcNormal(vec3 pos) {
    float eps = 0.0005; // Adjustable: sample offset
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(pos + e.xyy * eps) +
        e.yyx * map(pos + e.yyx * eps) +
        e.yxy * map(pos + e.yxy * eps) +
        e.xxx * map(pos + e.xxx * eps)
    );
}
```

### Step 3: Normalize and Apply to Lighting

**What**: Call `normalize()` on the gradient vector to obtain the unit normal for subsequent lighting calculations.

**Why**: The gradient length obtained from finite differences depends on the local gradient magnitude of the SDF. Lighting calculations require unit vectors. For an ideal SDF (gradient magnitude of 1), normalize barely changes the direction, but for SDFs that have undergone boolean operations or deformations, the gradient magnitude may deviate from 1, and normalize ensures correct results.

```glsl
// After a raymarching hit
vec3 pos = ro + rd * t;        // Hit point
vec3 nor = calcNormal(pos);    // Surface normal

// Basic Lambertian diffuse
vec3 lightDir = normalize(vec3(1.0, 4.0, -4.0));
float diff = max(dot(nor, lightDir), 0.0);
vec3 col = vec3(0.8) * diff;
```

---

## Variant Details

### Variant 1: Reverse Offset Forward Difference

**Difference from base version**: Uses center point minus three negative-direction offset samples, rather than positive-direction offsets minus center. Functionally equivalent to forward difference, but with a more compact code structure.

**Principle**: `map(p) - map(p - εx̂)` is equivalent to the mirror version of `map(p + εx̂) - map(p)`. Since we normalize at the end, the direction is unchanged.

```glsl
// Reverse offset variant
vec2 noff = vec2(0.001, 0.0);
vec3 normal = normalize(
    map(pos) - vec3(
        map(pos - noff.xyy),
        map(pos - noff.yxy),
        map(pos - noff.yyx)
    )
);
```

### Variant 2: Adaptive Epsilon (Distance Scaling)

**Difference from base version**: Epsilon is multiplied by the ray travel distance `t`, using larger offsets for distant surfaces (avoiding floating-point noise) and smaller offsets for nearby surfaces (preserving detail).

**Principle**: The farther the ray distance, the lower the floating-point precision (since absolute error is proportional to the magnitude of the value). Meanwhile, distant pixels cover a larger world-space area and don't need high-precision normals. Adaptive epsilon naturally matches both requirements.

**Typical coefficient**: `0.001 * t`, where `0.001` can be adjusted based on scene complexity.

```glsl
// Adaptive epsilon with tetrahedron technique
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t; // Adjustable: base coefficient 0.001

    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx)
    );
}
// Usage: vec3 nor = calcNormal(pos, t);
```

### Variant 3: Large Epsilon Rounding / Anti-Aliasing Trick

**Difference from base version**: Intentionally uses a large epsilon (e.g., `0.015`), causing normals to "blur" at geometric edges, producing a visual rounding and anti-aliasing effect.

**Principle**: A large epsilon means the normal sampling spans a larger spatial range. At sharp edges of geometry, the SDF value changes on both sides are averaged out, causing normals to transition smoothly at edges, similar to a chamfer/fillet effect.

**Use cases**: Procedural architecture, mechanical parts, and other scenarios needing visual rounding without modifying the SDF geometry.

```glsl
// Large epsilon rounding technique
vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.015, -0.015); // Intentionally enlarged epsilon
    return normalize(
        e.xyy * map(p + e.xyy) +
        e.yyx * map(p + e.yyx) +
        e.yxy * map(p + e.yxy) +
        e.xxx * map(p + e.xxx)
    );
}
```

### Variant 4: Anti-Inlining Loop Trick

**Difference from base version**: Writes the tetrahedron's 4 samples as a `for` loop with bit operations to generate vertex directions, preventing the GLSL compiler from inlining `map()` 4 times, significantly reducing compile times for complex scenes.

**Principle**:
- GLSL compilers typically unroll small loops and inline function calls
- For complex `map()` functions (e.g., hundreds of lines), being inlined 4 times causes code bloat
- `#define ZERO (min(iFrame, 0))` makes the loop bound a runtime value (though it is always 0 in practice), preventing the compiler from unrolling at compile time
- Bit operations `(((i+3)>>1)&1)` etc. generate the 4 tetrahedron vertex directions at runtime, equivalent to hand-written `e.xyy`, `e.yyx`, `e.yxy`, `e.xxx`

**Bit operation correspondence**:
| i | `(((i+3)>>1)&1)` | `((i>>1)&1)` | `(i&1)` | Direction |
|---|---|---|---|---|
| 0 | 1 | 0 | 0 | (+,-,-) |
| 1 | 0 | 0 | 1 | (-,-,+) |
| 2 | 0 | 1 | 0 | (-,+,-) |
| 3 | 1 | 1 | 1 | (+,+,+) |

```glsl
// Anti-inlining loop trick
#define ZERO (min(iFrame, 0)) // Prevent compile-time constant folding

vec3 calcNormal(vec3 p, float t) {
    vec3 n = vec3(0.0);
    for (int i = ZERO; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3(
            (((i + 3) >> 1) & 1),
            ((i >> 1) & 1),
            (i & 1)
        ) - 1.0);
        n += e * map(p + e * 0.001 * t);
    }
    return normalize(n);
}
```

### Variant 5: Normal + Edge Detection (Dual-Purpose Sampling)

**Difference from base version**: On top of the 6+1 samples from central difference, additionally computes a Laplacian approximation (deviation of per-axis sample averages from the center value) for detecting surface discontinuities (edges).

**Principle**:
- The Laplacian operator `∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z²` measures local curvature
- Numerical approximation: `∂²f/∂x² ≈ (f(x+h) + f(x-h) - 2f(x)) / h²`
- At surface discontinuities (edges, cracks), the Laplacian value spikes
- In the code, `abs(d - 0.5*(d2+d1))` is the Laplacian approximation on the x axis (omitting constant factors)
- `pow(edge, 0.55) * 15.0` is an empirical contrast adjustment

```glsl
// Normal + edge detection (dual-purpose sampling)
float edge = 0.0;
vec3 normal(vec3 p) {
    vec3 e = vec3(0.0, det * 5.0, 0.0); // det = detail level

    float d1 = de(p - e.yxx), d2 = de(p + e.yxx);
    float d3 = de(p - e.xyx), d4 = de(p + e.xyx);
    float d5 = de(p - e.xxy), d6 = de(p + e.xxy);
    float d  = de(p);

    // Laplacian edge detection: deviation of center value from per-axis averages
    edge = abs(d - 0.5 * (d2 + d1))
         + abs(d - 0.5 * (d4 + d3))
         + abs(d - 0.5 * (d6 + d5));
    edge = min(1.0, pow(edge, 0.55) * 15.0);

    return normalize(vec3(d1 - d2, d3 - d4, d5 - d6));
}
```

---

## Performance Optimization In-Depth Analysis

### Bottleneck 1: SDF Sample Count

Normal estimation is the **second-largest SDF call hotspot** in the raymarching pipeline, after the marching loop itself. Every pixel calls the normal function once upon hitting a surface, and the normal function internally calls `map()` 4~7 times.

| Method | Samples | Accuracy | Recommendation |
|--------|---------|----------|----------------|
| Forward difference | 4 | O(ε) | Simple scenes |
| Reverse offset difference | 4 | O(ε) | Same as forward, more compact code |
| Tetrahedron technique | 4 | Between forward and central | **Preferred** |
| Central difference | 6 | O(ε²) | When symmetry is needed |
| Central difference + edge | 7 | O(ε²) + extra info | When edge detection is needed |

**Recommendation**: Default to the tetrahedron technique; only switch to central difference when visual artifacts (e.g., jagged normals) appear.

### Bottleneck 2: Compile Time Explosion

Complex SDFs (e.g., `map()` functions with hundreds of lines) inlined 4~6 times by the normal function can cause compile times to grow from seconds to minutes.

**Root cause**: GLSL compilers attempt to unroll small loops and inline function calls, duplicating the `map()` code 4~6 times.

**Solution**: Use the anti-inlining loop trick (Variant 4), combined with `#define ZERO (min(iFrame, 0))` to prevent the compiler from unrolling at compile time. This keeps only one copy of the `map()` code, called in a runtime loop.

### Bottleneck 3: Epsilon Selection

| Epsilon Range | Effect |
|---------------|--------|
| < 1e-5 | Insufficient floating-point precision, normals show noise spots |
| 0.0005 ~ 0.001 | **Recommended default** |
| 0.01 ~ 0.02 | Slight smoothing / rounding effect |
| > 0.05 | Detail loss, geometric edges overly smoothed |

**Best practice**: Use adaptive epsilon `eps * t`, where `eps ≈ 0.001` and `t` is the ray distance. This preserves detail up close and avoids floating-point noise at distance.

### Bottleneck 4: Avoiding Redundant Sampling

If the same position needs both normals and other information (e.g., edge detection, AO pre-estimation), reuse SDF sampling results whenever possible. Variant 5 is a good example: on top of the 6 samples for normal computation, only 1 additional center sample is needed for edge detection, saving nearly half compared to computing normals and edge detection separately (13 samples total).

---

## Combination Suggestions with Full Code

### 1. Normal + Soft Shadow

After the normal determines surface orientation, a secondary raymarch from the hit point toward the light source computes the soft shadow. The normal is used to offset the starting point to avoid self-intersection:

```glsl
float shadow = calcSoftShadow(pos + nor * 0.01, sunDir, 16.0);
```

A complete soft shadow function typically looks like this:

```glsl
float calcSoftShadow(vec3 ro, vec3 rd, float k) {
    float res = 1.0;
    float t = 0.01;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd * t);
        res = min(res, k * h / t);
        if (res < 0.001) break;
        t += clamp(h, 0.01, 0.2);
    }
    return clamp(res, 0.0, 1.0);
}
```

### 2. Normal + Ambient Occlusion (AO)

The normal direction defines the sampling hemisphere for AO. Sampling the SDF along the normal with increasing step sizes — if the actual distance is less than the expected distance (i.e., nearby geometry is occluding), the AO value decreases:

```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0;
        float d = map(pos + nor * h);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```

**Parameter notes**:
- `0.01 + 0.12 * float(i) / 4.0`: Sample step from 0.01 to 0.13, covering near-distance occlusion
- `sca *= 0.95`: Decreasing weight for farther samples
- `3.0 * occ`: Contrast adjustment coefficient

### 3. Normal + Fresnel Effect

The angle between the normal and view direction controls Fresnel reflection intensity. At grazing angles (normal nearly perpendicular to view), reflection is strongest:

```glsl
float fresnel = pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0);
col = mix(col, envColor, fresnel);
```

**Principle**: `dot(nor, rd)` is close to -1 when the surface directly faces the viewer (`rd` points in the view direction, normal points outward) and close to 0 at grazing angles. Adding 1 shifts the range to [0, 1]; taking the 5th power enhances contrast.

### 4. Normal + Bump Mapping

Procedural perturbation layered on top of SDF normals adds surface detail without modifying the geometry:

```glsl
vec3 doBumpMap(vec3 pos, vec3 nor) {
    vec2 e = vec2(0.001, 0.0);
    float bump = texture(iChannel0, pos.xz * 0.5).x;
    float bx = texture(iChannel0, (pos.xz + e.xy) * 0.5).x;
    float bz = texture(iChannel0, (pos.xz + e.yx) * 0.5).x;
    vec3 grad = vec3(bx - bump, 0.0, bz - bump) / e.x;
    return normalize(nor + grad * 0.1); // 0.1 controls bump intensity
}
```

**Principle**: Computes the height map gradient in texture space and adds it to the geometric normal. `0.1` controls the visual bump strength — larger values make the surface appear rougher.

### 5. Normal + Triplanar Mapping

The absolute values of the normal components serve as blending weights for triplanar texturing, achieving UV-free texturing:

```glsl
vec3 triplanar(sampler2D tex, vec3 pos, vec3 nor) {
    vec3 w = pow(abs(nor), vec3(4.0));
    w /= (w.x + w.y + w.z);
    return texture(tex, pos.yz).rgb * w.x
         + texture(tex, pos.zx).rgb * w.y
         + texture(tex, pos.xy).rgb * w.z;
}
```

**Principle**:
- Faces with normals pointing along the X axis use YZ plane projection
- Faces with normals pointing along the Y axis use ZX plane projection
- Faces with normals pointing along the Z axis use XY plane projection
- `pow(abs(nor), vec3(4.0))` makes blending sharper, reducing blurring in transition regions
- Normalized weights `w /= (w.x + w.y + w.z)` ensure total weight sums to 1
