## WebGL2 Adaptation Requirements

The code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt for WebGL2:

- Use `canvas.getContext("webgl2")`
- First line of shaders: `#version 300 es`, add `precision highp float;` in fragment shaders
- Vertex shader: `attribute` -> `in`, `varying` -> `out`
- Fragment shader: `varying` -> `in`, `gl_FragColor` -> custom output variable (must be declared before `void main()`, e.g. `out vec4 outColor;`), `texture2D()` -> `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` must be adapted to the standard `void main()` entry point

# CSG Boolean Operations

## Core Principles

CSG boolean operations are per-point value operations on two distance fields:

| Operation | Expression | Meaning |
|-----------|-----------|---------|
| Union | `min(d1, d2)` | Take nearest surface, keeping both shapes |
| Intersection | `max(d1, d2)` | Take farthest surface, keeping only the overlap |
| Subtraction | `max(d1, -d2)` | Cut d1 using the interior of d2 |

**Smooth booleans** (smooth min/max) introduce a blending band in the transition region. The parameter `k` controls the blend band width (larger = rounder, `k=0` degenerates to hard boolean). Multiple variants exist with different mathematical properties.

## Implementation Steps

### Step 1: Hard Boolean Operations

```glsl
float opUnion(float d1, float d2) { return min(d1, d2); }
float opIntersection(float d1, float d2) { return max(d1, d2); }
float opSubtraction(float d1, float d2) { return max(d1, -d2); }
```

### Step 2: Smooth Union (Polynomial Version)

```glsl
// k: blend radius, typical values 0.05~0.5
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}
```

### Step 3: Smooth Subtraction and Intersection (Polynomial Version)

```glsl
float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```

### Step 4: Quadratic Optimized Version (Recommended as Default)

```glsl
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Subtraction via smax
float sSub(float d1, float d2, float k) {
    return smax(d1, -d2, k);
}
```

### Step 4b: Smooth Minimum Variant Library

Different smin implementations have different mathematical properties. Choose based on your needs:

| Variant | Rigid | Associative | Best For |
|---------|-------|-------------|----------|
| Quadratic (default above) | Yes | No | General use, fastest |
| Cubic | Yes | No | Smoother C2 transitions |
| Quartic | Yes | No | Highest quality blending |
| Exponential | No | Yes | Multi-body blending (order-independent) |
| Circular Geometric | Yes | Yes | Strict local blending |

**Rigid**: preserves original SDF shape outside the blend region (no under-estimation).
**Associative**: `smin(a, smin(b, c))` == `smin(smin(a, b), c)` — important when blending many objects where evaluation order varies.

```glsl
// --- Cubic Polynomial smin (C2 continuous, smoother transitions) ---
float sminCubic(float a, float b, float k) {
    k *= 6.0;
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * h * k * (1.0 / 6.0);
}

// --- Quartic Polynomial smin (C3 continuous, highest quality) ---
float sminQuartic(float a, float b, float k) {
    k *= 16.0 / 3.0;
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * h * (4.0 - h) * k * (1.0 / 16.0);
}

// --- Exponential smin (associative — order independent for multi-body blending) ---
float sminExp(float a, float b, float k) {
    float r = exp2(-a / k) + exp2(-b / k);
    return -k * log2(r);
}

// --- Circular Geometric smin (rigid + local + associative) ---
float sminCircle(float a, float b, float k) {
    k *= 1.0 / (1.0 - sqrt(0.5));
    return max(k, min(a, b)) - length(max(k - vec2(a, b), 0.0));
}

// --- Gradient-aware smin (carries material/color through blending) ---
// x = distance, yzw = material properties or color components
vec4 sminColor(vec4 a, vec4 b, float k) {
    k *= 4.0;
    float h = max(k - abs(a.x - b.x), 0.0) / (2.0 * k);
    return vec4(
        min(a.x, b.x) - h * h * k,
        mix(a.yzw, b.yzw, (a.x < b.x) ? h : 1.0 - h)
    );
}

// --- Smooth maximum from any smin variant ---
// smax(a, b, k) = -smin(-a, -b, k)
// Smooth subtraction: smax(d1, -d2, k)
// Smooth intersection: smax(d1, d2, k)
```

### Step 5: Basic SDF Primitives

```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}
```

### Step 6: CSG Composition for Scene Building

```glsl
float mapScene(vec3 p) {
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.2);
    float cylX = sdCylinder(p.yzx, 2.0, 0.4);
    float cylY = sdCylinder(p.xyz, 2.0, 0.4);
    float cylZ = sdCylinder(p.zxy, 2.0, 0.4);

    // (cube intersect sphere) - three cylinders = nut
    float shape = opIntersection(cube, sphere);
    float holes = opUnion(cylX, opUnion(cylY, cylZ));
    return opSubtraction(shape, holes);
}
```

### Step 7: Smooth CSG Modeling for Organic Forms

```glsl
// Use different k values for different body parts: large k for major joints, small k for fine details
float mapCreature(vec3 p) {
    float body = sdSphere(p, 0.5);
    float head = sdSphere(p - vec3(0.0, 0.6, 0.3), 0.25);
    float d = smin(body, head, 0.15);          // large blend

    float leg = sdCylinder(p - vec3(0.2, -0.5, 0.0), 0.3, 0.08);
    d = smin(d, leg, 0.08);                    // medium blend

    float eye = sdSphere(p - vec3(0.05, 0.75, 0.4), 0.05);
    d = smax(d, -eye, 0.02);                  // small blend for subtraction
    return d;
}
```

### Step 8: Ray Marching Main Loop

```glsl
float rayMarch(vec3 ro, vec3 rd, float maxDist) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > maxDist) break;
    }
    return -1.0;
}
```

### Step 9: Normal Calculation (Tetrahedral Sampling, 4 Samples More Efficient Than 6 with Central Differences)

```glsl
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}
```

## Full Code Template

```glsl
// === CSG Boolean Operations - WebGL2 Full Template ===
// Note: When generating HTML with this template, pass iTime, iResolution, etc. via uniforms

#define MAX_STEPS 128
#define MAX_DIST 50.0
#define SURF_DIST 0.001
#define SMOOTH_K 0.1

// === Hard Boolean Operations ===
float opUnion(float d1, float d2) { return min(d1, d2); }
float opIntersection(float d1, float d2) { return max(d1, d2); }
float opSubtraction(float d1, float d2) { return max(d1, -d2); }

// === Smooth Boolean Operations (Quadratic Optimized) ===
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// === SDF Primitives ===
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

// === Scene Definition ===
float mapScene(vec3 p) {
    // Rotation animation
    float angle = iTime * 0.3;
    float c = cos(angle), s = sin(angle);
    p.xz = mat2(c, -s, s, c) * p.xz;

    // Primitives
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.25);
    float cylR = 0.45;
    float cylX = sdCylinder(p.yzx, 2.0, cylR);
    float cylY = sdCylinder(p.xyz, 2.0, cylR);
    float cylZ = sdCylinder(p.zxy, 2.0, cylR);

    // Hard boolean combination: nut = (cube intersect sphere) - three cylinders
    float nut = opSubtraction(
        opIntersection(cube, sphere),
        opUnion(cylX, opUnion(cylY, cylZ))
    );

    // Organic spheres -- smooth union blending
    float blob1 = sdSphere(p - vec3(1.8, 0.0, 0.0), 0.4);
    float blob2 = sdSphere(p - vec3(-1.8, 0.0, 0.0), 0.4);
    float blob3 = sdSphere(p - vec3(0.0, 1.8, 0.0), 0.4);
    float blobs = smin(blob1, smin(blob2, blob3, 0.3), 0.3);

    return smin(nut, blobs, 0.15);
}

// === Normal Calculation (Tetrahedral Sampling) ===
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}

// === Ray Marching ===
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > MAX_DIST) break;
    }
    return -1.0;
}

// === Soft Shadows ===
float calcSoftShadow(vec3 ro, vec3 rd, float k) {
    float res = 1.0;
    float t = 0.02;
    for (int i = 0; i < 64; i++) {
        float h = mapScene(ro + rd * t);
        res = min(res, k * h / t);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.001 || t > 20.0) break;
    }
    return clamp(res, 0.0, 1.0);
}

// === AO (Ambient Occlusion) ===
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i);
        float d = mapScene(pos + h * nor);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// === Main Function (WebGL2 Adapted) ===
out vec4 outColor;
void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;

    // Camera
    float camDist = 4.0;
    float camAngle = 0.3;
    vec3 ro = vec3(
        camDist * cos(iTime * 0.2),
        camDist * sin(camAngle),
        camDist * sin(iTime * 0.2)
    );
    vec3 ta = vec3(0.0, 0.0, 0.0);

    // Camera matrix
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.0 * ww);

    // Background color
    vec3 col = vec3(0.4, 0.5, 0.6) - 0.3 * rd.y;

    // Ray marching
    float t = rayMarch(ro, rd);
    if (t > 0.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);

        vec3 lightDir = normalize(vec3(0.8, 0.6, -0.3));
        float dif = clamp(dot(nor, lightDir), 0.0, 1.0);
        float sha = calcSoftShadow(pos + nor * 0.01, lightDir, 16.0);
        float ao = calcAO(pos, nor);
        float amb = 0.5 + 0.5 * nor.y;

        vec3 mate = vec3(0.2, 0.3, 0.4);
        col = vec3(0.0);
        col += mate * 2.0 * dif * sha;
        col += mate * 0.3 * amb * ao;
    }

    col = pow(col, vec3(0.4545));
    outColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Exponential Smooth Union

```glsl
float sminExp(float a, float b, float k) {
    float res = exp(-k * a) + exp(-k * b);
    return -log(res) / k;
}
```

### Variant 2: Smooth Operations with Color Blending

```glsl
// Returns blend factor for the caller to blend colors
float sminWithFactor(float a, float b, float k, out float blend) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    blend = h;
    return mix(b, a, h) - k * h * (1.0 - h);
}
// float blend;
// float d = sminWithFactor(d1, d2, 0.1, blend);
// vec3 color = mix(color2, color1, blend);

// vec3 overload of smax
vec3 smax(vec3 a, vec3 b, float k) {
    vec3 h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}
```

### Variant 3: Stepwise CSG Modeling (Architectural/Industrial)

```glsl
float sdBuilding(vec3 p) {
    float walls = sdBox(p, vec3(1.0, 0.8, 1.0));
    vec3 roofP = p;
    roofP.y -= 0.8;
    float roof = sdBox(roofP, vec3(1.2, 0.3, 1.2));
    float d = opUnion(walls, roof);

    // Cut windows (exploiting symmetry)
    vec3 winP = abs(p);
    winP -= vec3(1.01, 0.3, 0.4);
    float window = sdBox(winP, vec3(0.1, 0.15, 0.12));
    d = opSubtraction(d, window);

    // Hollow out interior
    float hollow = sdBox(p, vec3(0.95, 0.75, 0.95));
    d = opSubtraction(d, hollow);
    return d;
}
```

### Variant 4: Large-Scale Organic Character Modeling

```glsl
float mapCharacter(vec3 p) {
    float body = sdEllipsoid(p, vec3(0.5, 0.4, 0.6));
    float head = sdEllipsoid(p - vec3(0.0, 0.5, 0.5), vec3(0.25));
    float d = smin(body, head, 0.2);           // large k: wide blend

    float ear = sdEllipsoid(p - vec3(0.3, 0.6, 0.3), vec3(0.15, 0.2, 0.05));
    d = smin(d, ear, 0.08);                    // medium blend

    float nostril = sdSphere(p - vec3(0.0, 0.4, 0.7), 0.03);
    d = smax(d, -nostril, 0.02);               // small k: fine sculpting
    return d;
}
```

## Performance & Composition Tips

**Performance:**
- Bounding volume acceleration: use AABB/bounding spheres to skip distant sub-scenes, reducing `mapScene()` calls
- Tetrahedral sampling normals (4 samples) outperform central differences (6 samples)
- Step scaling `t += d * 0.9` can reduce overshoot penetration
- Prefer quadratic optimized smin/smax (fastest); use exponential version when extreme smoothness is needed
- `k` must not be zero (division by zero error); fall back to hard boolean when near zero
- For symmetric shapes, use `abs()` to fold coordinates and define only one side

**Composition techniques:**
- **+ Domain Repetition**: `mod()`/`fract()` for infinite repetition of CSG shapes (mechanical arrays, railings)
- **+ Procedural Displacement**: overlay noise displacement on SDF for surface detail
- **+ Procedural Texturing**: use smin blend factor to simultaneously blend material ID / color
- **+ 2D SDF**: equally applicable to 2D scenes (clouds, UI shape compositing)
- **+ Animation**: bind k values, positions, and radii to `iTime` for dynamic deformation

## Further Reading

Full step-by-step tutorials, mathematical derivations, and advanced usage in [reference](../reference/csg-boolean-operations.md)
