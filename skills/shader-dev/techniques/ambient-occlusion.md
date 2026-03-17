## WebGL2 Adaptation Requirements

**IMPORTANT: GLSL Type Strictness**: float and vec types cannot be implicitly converted. `vec3 v = 1.0;` is illegal; you must use the vector form (e.g., `vec3(1.0)`, `vec3(1.0) * x`, `value * vec3(1.0)`).

The code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt for WebGL2:

- Use `canvas.getContext("webgl2")`
- Shader first line: `#version 300 es`, add `precision highp float;` in fragment shader
- Vertex shader: `attribute` -> `in`, `varying` -> `out`
- Fragment shader: `varying` -> `in`, `gl_FragColor` -> custom `out vec4 fragColor`, `texture2D()` -> `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` must be adapted to the standard `void main()` entry point

# SDF Ambient Occlusion

## Use Cases

- Simulating indirect light occlusion in raymarching / SDF scenes
- Adding spatial depth and contact shadows (darkening in concavities and crevices)
- From 5 samples (performance priority) to 32 hemisphere samples (quality priority)

## Core Principles

Sample the SDF along the surface normal direction at multiple distances, comparing the "expected distance" with the "actual distance" to estimate occlusion.

For surface point P, normal N, and sampling distance h:
- Expected distance = h (SDF should equal h when surroundings are open)
- Actual distance = map(P + N * h)
- Occlusion contribution = h - map(P + N * h) (larger difference = stronger occlusion)

```
AO = 1 - k * sum(weight_i * max(0, h_i - map(P + N * h_i)))
```

Result: 1.0 = no occlusion, 0.0 = fully occluded. Weights decay exponentially (closer samples have higher weight).

## Implementation Steps

### Step 1: SDF Scene

```glsl
float map(vec3 p) {
    float d = p.y; // ground
    d = min(d, length(p - vec3(0.0, 1.0, 0.0)) - 1.0); // sphere
    d = min(d, length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4); // torus
    return d;
}
```

### Step 2: Normal Calculation

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

### Step 3: Classic Normal-Direction AO (5 Samples)

```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0; // sampling distance 0.01~0.13
        float d = map(pos + h * nor);
        occ += (h - d) * sca; // (expected - actual) * weight
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```

### Step 4: Applying AO to Lighting

```glsl
float ao = calcAO(pos, nor);

// affect ambient light only (physically correct)
vec3 ambient = vec3(0.2, 0.3, 0.5) * ao;
vec3 color = diffuse * shadow + ambient;

// affect all lighting (visually stronger)
vec3 color = (diffuse * shadow + ambient) * ao;

// combined with sky visibility
float skyVis = 0.5 + 0.5 * nor.y;
vec3 color = diffuse * shadow + ambient * ao * skyVis;
```

### Step 5: Raymarching Integration

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // ... camera setup, ray generation ...
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < 0.001) break;
        t += d;
        if (t > 100.0) break;
    }

    vec3 col = vec3(0.0);
    if (t < 100.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        vec3 lig = normalize(vec3(1.0, 0.8, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sky = 0.5 + 0.5 * nor.y;
        col = vec3(1.0) * dif + vec3(0.2, 0.3, 0.5) * sky * ao;
    }
    fragColor = vec4(col, 1.0);
}
```

## Complete Code Template

Runs directly in ShaderToy:

```glsl
// SDF Ambient Occlusion — ShaderToy Template
// Synthesized from classic raymarching implementations

#define AO_STEPS 5
#define AO_MAX_DIST 0.12
#define AO_MIN_DIST 0.01
#define AO_DECAY 0.95
#define AO_STRENGTH 3.0
#define MARCH_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001

float map(vec3 p) {
    float ground = p.y;
    float sphere = length(p - vec3(0.0, 1.0, 0.0)) - 1.0;
    float torus = length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4;
    float box = length(max(abs(p - vec3(-2.5, 0.75, 0.0)) - vec3(0.75), 0.0)) - 0.05;
    float d = min(ground, sphere);
    d = min(d, torus);
    d = min(d, box);
    return d;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < AO_STEPS; i++) {
        float h = AO_MIN_DIST + AO_MAX_DIST * float(i) / float(AO_STEPS - 1);
        float d = map(pos + h * nor);
        occ += (h - d) * sca;
        sca *= AO_DECAY;
    }
    return clamp(1.0 - AO_STRENGTH * occ, 0.0, 1.0);
}

float calcShadow(vec3 ro, vec3 rd, float mint, float maxt, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd * t);
        res = min(res, k * h / t);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.001 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    float an = 0.3 * iTime;
    vec3 ro = vec3(4.0 * cos(an), 2.5, 4.0 * sin(an));
    vec3 ta = vec3(0.0, 0.5, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.8 * ww);

    float t = 0.0;
    for (int i = 0; i < MARCH_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }

    vec3 col = vec3(0.4, 0.5, 0.7) - 0.3 * rd.y;

    if (t < MAX_DIST) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        vec3 lig = normalize(vec3(0.8, 0.6, -0.5));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sha = calcShadow(pos + nor * 0.01, lig, 0.02, 20.0, 8.0);
        float sky = 0.5 + 0.5 * nor.y;

        vec3 mate = vec3(0.18);
        if (pos.y < 0.01) {
            float f = mod(floor(pos.x) + floor(pos.z), 2.0);
            mate = 0.1 + 0.08 * f * vec3(1.0);
        }

        col = vec3(0.0);
        col += mate * vec3(1.0, 0.9, 0.7) * dif * sha;
        col += mate * vec3(0.2, 0.3, 0.5) * sky * ao;
        col += mate * vec3(0.3, 0.2, 0.1) * clamp(-nor.y, 0.0, 1.0) * ao;
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Multiplicative AO (Spout / P_Malin)

```glsl
float calcAO_multiplicative(vec3 pos, vec3 nor) {
    float ao = 1.0;
    float dist = 0.0;
    for (int i = 0; i <= 5; i++) {
        dist += 0.1;
        float d = map(pos + nor * dist);
        ao *= 1.0 - max(0.0, (dist - d) * 0.2 / dist);
    }
    return ao;
}
```

### Multi-Scale Separated AO (Protophore / Eric Heitz)

Exponentially increasing sampling distances, separating short-range contact shadows from long-range ambient occlusion, fully unrolled without loops.

```glsl
float calcAO_multiscale(vec3 pos, vec3 nor) {
    float aoS = 1.0;
    aoS *= clamp(map(pos + nor * 0.1) * 10.0, 0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.2) * 5.0,  0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.4) * 2.5,  0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.8) * 1.25, 0.0, 1.0);

    float ao = aoS;
    ao *= clamp(map(pos + nor * 1.6) * 0.625,  0.0, 1.0);
    ao *= clamp(map(pos + nor * 3.2) * 0.3125, 0.0, 1.0);
    ao *= clamp(map(pos + nor * 6.4) * 0.15625,0.0, 1.0);

    return max(0.035, pow(ao, 0.3));
}
```

### Jittered Sampling AO

Hash jittering breaks banding artifacts, `1/(1+l)` distance falloff.

```glsl
float hash(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_jittered(vec3 pos, vec3 nor, float maxDist) {
    float ao = 0.0;
    const float nbIte = 6.0;
    for (float i = 1.0; i < nbIte + 0.5; i++) {
        float l = (i + hash(i)) * 0.5 / nbIte * maxDist;
        ao += (l - map(pos + nor * l)) / (1.0 + l);
    }
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}
// call: calcAO_jittered(pos, nor, 4.0)
```

### Hemisphere Random Direction AO

Random direction sampling within the normal hemisphere, closer to physically accurate, requires 32 samples.

```glsl
vec2 hash2(float n) {
    return fract(sin(vec2(n, n + 1.0)) * vec2(43758.5453, 22578.1459));
}

float calcAO_hemisphere(vec3 pos, vec3 nor, float seed) {
    float occ = 0.0;
    for (int i = 0; i < 32; i++) {
        float h = 0.01 + 4.0 * pow(float(i) / 31.0, 2.0);
        vec2 an = hash2(seed + float(i) * 13.1) * vec2(3.14159, 6.2831);
        vec3 dir = vec3(sin(an.x) * sin(an.y), sin(an.x) * cos(an.y), cos(an.x));
        dir *= sign(dot(dir, nor));
        occ += clamp(5.0 * map(pos + h * dir) / h, -1.0, 1.0);
    }
    return clamp(occ / 32.0, 0.0, 1.0);
}
```

### Fibonacci Sphere Uniform Hemisphere AO

Fibonacci sphere points for quasi-uniform hemisphere sampling, avoiding random clustering.

```glsl
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
    for (int i = 0; i < 32; i++) {
        vec3 ap = forwardSF(float(i), 32.0);
        float h = hash1(float(i));
        ap *= sign(dot(ap, nor)) * h * 0.1;
        ao += clamp(map(pos + nor * 0.01 + ap) * 3.0, 0.0, 1.0);
    }
    ao /= 32.0;
    return clamp(ao * 6.0, 0.0, 1.0);
}
```

## Performance & Composition

### Performance Tips

- **Bottleneck**: Number of `map()` calls. Each AO sample = one full SDF evaluation
- **Sample count selection**: Classic normal-direction 3~5 samples is sufficient; hemisphere sampling needs 16~32
- **Early exit**: `if (occ > 0.35) break;` skips over heavily occluded regions
- **Unroll loops**: Fixed iteration count (4~7) manually unrolled is more GPU-friendly
- **Distance degradation**: `float aoSteps = mix(5.0, 2.0, clamp(t / 50.0, 0.0, 1.0));`
- **Preprocessor toggle**: `#ifdef ENABLE_AMBIENT_OCCLUSION` for on/off control
- **SDF simplification**: AO sampling can use a simplified `map()`, ignoring fine details

### Composition Tips

- **AO + Soft Shadow**: `col = diffuse * sha + ambient * ao;`
- **AO + Sky Visibility**: `col += skyColor * ao * (0.5 + 0.5 * nor.y);`
- **AO + Bounce Light/SSS**: `col += bounceColor * bou * ao;`
- **AO + Convexity Detection**: Sample along both +N/-N to get both AO and convexity
- **AO + Fresnel Reflection**: `col += envColor * fre * ao;` reduces environment reflection in occluded areas

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/ambient-occlusion.md)
