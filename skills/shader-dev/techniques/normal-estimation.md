## WebGL2 Adaptation Requirements

**IMPORTANT: GLSL Type Strictness Warning**:
- GLSL is a strongly typed language with **no `string` type**; using string types is forbidden
- Common illegal types: `string`, `int` (can only use `int` literals, cannot declare variable types as `int`)
- vec2/vec3/vec4 cannot be implicitly converted between each other; explicit construction is required
- Float precision: `highp float` (recommended), `mediump float`, `lowp float`

The code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt for WebGL2:

- Use `canvas.getContext("webgl2")`
- Shader first line: `#version 300 es`, add `precision highp float;` in fragment shader
- Vertex shader: `attribute` -> `in`, `varying` -> `out`
- Fragment shader: `varying` -> `in`, `gl_FragColor` -> custom `out vec4 fragColor`, `texture2D()` -> `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` must be adapted to the standard `void main()` entry point

# SDF Normal Estimation

## Use Cases

- Lighting calculations in raymarching rendering pipelines (diffuse, specular, Fresnel, etc.)
- Any 3D scene based on SDF distance fields (fractals, parametric surfaces, boolean geometry, procedural terrain)
- Edge detection and contour rendering (Laplacian value as a byproduct of normal sampling)
- Prerequisite for ambient occlusion (AO) computation

## Core Principles

The gradient of an SDF `nabla f(p)` points in the direction of fastest distance increase, which is the outward surface normal. Numerical differentiation approximates the gradient:

$$\vec{n} = \text{normalize}\left(\nabla f(p)\right)$$

Three main strategies:

| Method | Samples | Accuracy | Recommendation |
|--------|---------|----------|----------------|
| Forward difference | 4 | O(epsilon) | Simple scenes |
| Central difference | 6 | O(epsilon^2) | When symmetry is needed |
| **Tetrahedron method** | **4** | **Between the two** | **Preferred** |

Key parameter epsilon: commonly `0.0005 ~ 0.001`; for advanced scenes, multiply by ray distance `t` for adaptive scaling.

## Implementation Steps

### Step 1: Define SDF Scene Function

```glsl
float map(vec3 p) {
    float d = length(p) - 1.0; // unit sphere
    return d;
}
```

### Step 2: Choose Differentiation Method

#### Method A: Forward Difference -- 4 Samples

```glsl
const float EPSILON = 1e-3;

vec3 getNormal(vec3 p) {
    vec3 n;
    n.x = map(vec3(p.x + EPSILON, p.y, p.z));
    n.y = map(vec3(p.x, p.y + EPSILON, p.z));
    n.z = map(vec3(p.x, p.y, p.z + EPSILON));
    return normalize(n - map(p));
}
```

#### Method B: Central Difference -- 6 Samples

```glsl
vec3 getNormal(vec3 p) {
    vec2 o = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + o.xyy) - map(p - o.xyy),
        map(p + o.yxy) - map(p - o.yxy),
        map(p + o.yyx) - map(p - o.yyx)
    ));
}
```

#### Method C: Tetrahedron Method -- 4 Samples (Recommended)

```glsl
// Classic tetrahedron method, coefficient 0.5773 ~ 1/sqrt(3)
vec3 calcNormal(vec3 pos) {
    float eps = 0.0005;
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(pos + e.xyy * eps) +
        e.yyx * map(pos + e.yyx * eps) +
        e.yxy * map(pos + e.yxy * eps) +
        e.xxx * map(pos + e.xxx * eps)
    );
}
```

### Step 3: Apply to Lighting

```glsl
vec3 pos = ro + rd * t;        // hit point
vec3 nor = calcNormal(pos);    // surface normal

vec3 lightDir = normalize(vec3(1.0, 4.0, -4.0));
float diff = max(dot(nor, lightDir), 0.0);
vec3 col = vec3(0.8) * diff;
```

## Complete Code Template

```glsl
// SDF Normal Estimation — Complete ShaderToy Template

#define MAX_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001
#define NORMAL_METHOD 2      // 0=forward diff, 1=central diff, 2=tetrahedron

// ---- SDF Scene Definition ----
float map(vec3 p) {
    float sphere = length(p - vec3(0.0, 1.0, 0.0)) - 1.0;
    float ground = p.y;
    return min(sphere, ground);
}

// ---- Normal Estimation ----

vec3 normalForward(vec3 p) {
    float eps = 0.001;
    float d = map(p);
    return normalize(vec3(
        map(p + vec3(eps, 0.0, 0.0)),
        map(p + vec3(0.0, eps, 0.0)),
        map(p + vec3(0.0, 0.0, eps))
    ) - d);
}

vec3 normalCentral(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

vec3 normalTetra(vec3 p) {
    float eps = 0.0005;
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(p + e.xyy * eps) +
        e.yyx * map(p + e.yyx * eps) +
        e.yxy * map(p + e.yxy * eps) +
        e.xxx * map(p + e.xxx * eps)
    );
}

vec3 calcNormal(vec3 p) {
#if NORMAL_METHOD == 0
    return normalForward(p);
#elif NORMAL_METHOD == 1
    return normalCentral(p);
#else
    return normalTetra(p);
#endif
}

// ---- Raymarching ----
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < SURF_DIST || t > MAX_DIST) break;
        t += d;
    }
    return t;
}

// ---- Main Function ----
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    vec3 ro = vec3(0.0, 2.0, -5.0);
    vec3 rd = normalize(vec3(uv, 1.5));

    float t = raymarch(ro, rd);
    vec3 col = vec3(0.0);

    if (t < MAX_DIST) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);

        vec3 sunDir = normalize(vec3(0.8, 0.4, -0.6));
        float diff = clamp(dot(nor, sunDir), 0.0, 1.0);
        float amb = 0.5 + 0.5 * nor.y;
        vec3 ref = reflect(rd, nor);
        float spec = pow(clamp(dot(ref, sunDir), 0.0, 1.0), 16.0);

        col = vec3(0.18) * amb + vec3(1.0, 0.95, 0.85) * diff + vec3(0.5) * spec;
    } else {
        col = vec3(0.5, 0.7, 1.0) - 0.5 * rd.y;
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: NuSan Reverse-Offset Forward Difference

```glsl
// Reverse-offset forward difference
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

```glsl
// Adaptive epsilon based on ray distance
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx)
    );
}
```

### Variant 3: Large Epsilon for Rounding / Anti-Aliasing

```glsl
// Large epsilon for rounding / anti-aliasing
vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.015, -0.015); // intentionally large epsilon
    return normalize(
        e.xyy * map(p + e.xyy) +
        e.yyx * map(p + e.yyx) +
        e.yxy * map(p + e.yxy) +
        e.xxx * map(p + e.xxx)
    );
}
```

### Variant 4: Anti-Inlining Loop

```glsl
// Anti-inlining loop — reduces compile time for complex SDFs
#define ZERO (min(iFrame, 0))

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

### Variant 5: Normal + Edge Detection

```glsl
// Central difference + Laplacian edge detection
float edge = 0.0;
vec3 normal(vec3 p) {
    vec3 e = vec3(0.0, det * 5.0, 0.0);

    float d1 = de(p - e.yxx), d2 = de(p + e.yxx);
    float d3 = de(p - e.xyx), d4 = de(p + e.xyx);
    float d5 = de(p - e.xxy), d6 = de(p + e.xxy);
    float d  = de(p);

    edge = abs(d - 0.5 * (d2 + d1))
         + abs(d - 0.5 * (d4 + d3))
         + abs(d - 0.5 * (d6 + d5));
    edge = min(1.0, pow(edge, 0.55) * 15.0);

    return normalize(vec3(d1 - d2, d3 - d4, d5 - d6));
}
```

## Performance & Composition

**Performance**:
- Default to tetrahedron method (4 samples, better accuracy than forward difference)
- Only switch to central difference (6 samples) when jagged normal artifacts appear
- Use anti-inlining loop (Variant 4) for complex SDFs to avoid compile time explosion
- Epsilon recommended `0.0005 ~ 0.001`; best practice is adaptive `eps * t`
- Too small (< 1e-5) produces floating-point noise; too large (> 0.05) loses detail
- Reuse SDF sampling results when multiple types of information are needed at the same position (e.g., Variant 5)

**Common combinations**:
- **Normal + Soft Shadow**: `calcSoftShadow(pos + nor * 0.01, sunDir, 16.0)` -- normal offset at start point to avoid self-intersection
- **Normal + AO**: Multi-step SDF sampling along the normal to estimate occlusion
- **Normal + Fresnel**: `pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0)`
- **Normal + Bump Mapping**: Overlay texture gradient perturbation on SDF normals
- **Normal + Triplanar Mapping**: Use `abs(nor)` components as triplanar blend weights

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/normal-estimation.md)
