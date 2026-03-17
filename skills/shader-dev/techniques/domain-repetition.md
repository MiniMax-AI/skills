# Domain Repetition & Space Folding

## Use Cases

- **Infinite repeating scenes**: render infinitely extending geometry from a single SDF primitive (corridors, cities, star fields)
- **Kaleidoscope/symmetry effects**: N-fold rotational symmetry, mirror symmetry, polyhedral symmetry
- **Fractal geometry**: generate self-similar structures through iterative space folding (Apollonian, Kali-set)
- **Architectural/mechanical structures**: build complex yet regular scenes using repetition + variation
- **Spiral/toroidal topology**: repeat geometry along polar or spiral paths

Core value: **define geometry in a single cell, render infinite space**.

## Core Principles

The essence of domain repetition is **coordinate transformation**: before computing the SDF, fold/map point `p` into a finite "fundamental domain".

**Three fundamental operations:**

| Operation | Formula | Effect |
|-----------|---------|--------|
| **mod repetition** | `p = mod(p + c/2, c) - c/2` | Infinite translational repetition along an axis |
| **abs mirroring** | `p = abs(p)` | Mirror symmetry across an axis plane |
| **Rotational folding** | `angle = mod(atan(p.y,p.x), TAU/N)` | N-fold rotational symmetry |

Key math: `mod(x,c)` -> periodic mapping to `[0,c)`; `abs(x)` -> reflection symmetry; `fract(x)` = `mod(x,1.0)` -> normalized period.

## Implementation Steps

### Step 1: Cartesian Domain Repetition (mod repetition)

```glsl
// Infinite translational repetition along one or more axes
vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(4.0)); // repeat every 4 units
    return sdBox(q, vec3(0.5));
}
```

### Step 2: Symmetric Folding (abs-mod triangle wave)

```glsl
// Boundary-continuous symmetric folding, coordinates oscillate 0->tile->0
vec3 symmetricFold(vec3 p, float tile) {
    return abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
}

// Star Nest classic usage
p = abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
```

### Step 3: Angular Domain Repetition (Polar Coordinate Folding)

```glsl
// N-way rotational symmetry (kaleidoscope)
vec2 pmod(vec2 p, float count) {
    float angle = atan(p.x, p.y) + PI / count;
    float sector = TAU / count;
    angle = floor(angle / sector) * sector;
    return p * rot(-angle);
}

p1.xy = pmod(p1.xy, 5.0); // 5-fold symmetry
```

### Step 4: fract Domain Folding (Fractal Iteration)

```glsl
// Apollonian fractal core loop
float map(vec3 p, float s) {
    float scale = 1.0;
    vec4 orb = vec4(1000.0);

    for (int i = 0; i < 8; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // centered fract folding
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;    // spherical inversion scaling
        p *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}
```

### Step 5: Iterative abs Folding (IFS / Kali-set)

```glsl
// IFS abs folding fractal
float ifsBox(vec3 p) {
    for (int i = 0; i < 5; i++) {
        p = abs(p) - 1.0;
        p.xy *= rot(iTime * 0.3);
        p.xz *= rot(iTime * 0.1);
    }
    return sdBox(p, vec3(0.4, 0.8, 0.3));
}

// Kali-set variant: mod repetition + IFS + dot(p,p) scaling
vec2 de(vec3 pos) {
    vec3 tpos = pos;
    tpos.xz = abs(0.5 - mod(tpos.xz, 1.0));
    vec4 p = vec4(tpos, 1.0);               // w tracks scaling
    for (int i = 0; i < 7; i++) {
        p.xyz = abs(p.xyz) - vec3(-0.02, 1.98, -0.02);
        p = p * (2.0) / clamp(dot(p.xyz, p.xyz), 0.4, 1.0)
            - vec4(0.5, 1.0, 0.4, 0.0);
        p.xz *= rot(0.416);
    }
    return vec2(length(max(abs(p.xyz)-vec3(0.1,5.0,0.1), 0.0)) / p.w, 0.0);
}
```

### Step 6: Reflection Folding (Polyhedral Symmetry)

```glsl
// Plane reflection
float pReflect(inout vec3 p, vec3 planeNormal, float offset) {
    float t = dot(p, planeNormal) + offset;
    if (t < 0.0) p = p - (2.0 * t) * planeNormal;
    return sign(t);
}

// Icosahedral folding
void pModIcosahedron(inout vec3 p) {
    vec3 nc = vec3(-0.5, -cos(PI/5.0), sqrt(0.75 - cos(PI/5.0)*cos(PI/5.0)));
    p = abs(p);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
}
```

### Step 7: Toroidal/Cylindrical Domain Warping

```glsl
// Bend the xz plane into a toroidal topology
vec2 displaceLoop(vec2 p, float radius) {
    return vec2(length(p) - radius, atan(p.y, p.x));
}

pDonut.xz = displaceLoop(pDonut.xz, donutRadius);
pDonut.z *= donutRadius; // unfold angle to linear length
```

### Step 8: 1D Centered Domain Repetition (with Cell ID)

```glsl
// Returns cell index, usable for random variations
float pMod1(inout float p, float size) {
    float halfsize = size * 0.5;
    float c = floor((p + halfsize) / size);
    p = mod(p + halfsize, size) - halfsize;
    return c;
}

float cellID = pMod1(p.x, 2.0);
float salt = fract(sin(cellID * 127.1) * 43758.5453);
```

## Full Code Template

Combined demo: Cartesian repetition + angular repetition + IFS folding. Runs directly in ShaderToy.

```glsl
#define PI 3.14159265359
#define TAU 6.28318530718
#define MAX_STEPS 100
#define MAX_DIST 50.0
#define SURF_DIST 0.001
#define PERIOD 4.0
#define ANGULAR_COUNT 6.0
#define IFS_ITERS 5
#define IFS_OFFSET 1.2

mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

vec2 pmod(vec2 p, float count) {
    float a = atan(p.x, p.y) + PI / count;
    float n = TAU / count;
    a = floor(a / n) * n;
    return p * rot(-a);
}

float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(PERIOD));
    q.xz = pmod(q.xz, ANGULAR_COUNT);
    for (int i = 0; i < IFS_ITERS; i++) {
        q = abs(q) - IFS_OFFSET;
        q.xy *= rot(0.785);
        q.yz *= rot(0.471);
    }
    return sdBox(q, vec3(0.15, 0.4, 0.15));
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        float d = map(ro + rd * t);
        if (d < SURF_DIST || t > MAX_DIST) break;
        t += d;
    }
    return t;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;

    float time = iTime * 0.5;
    vec3 ro = vec3(sin(time) * 6.0, 3.0 + sin(time * 0.7) * 2.0, cos(time) * 6.0);
    vec3 ta = vec3(0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.8 * ww);

    float t = raymarch(ro, rd);

    vec3 col = vec3(0.0);
    if (t < MAX_DIST) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        vec3 lightDir = normalize(vec3(0.5, 0.8, -0.6));
        float diff = clamp(dot(n, lightDir), 0.0, 1.0);
        float amb = 0.5 + 0.5 * n.y;
        vec3 baseColor = 0.5 + 0.5 * cos(p * 0.5 + vec3(0.0, 2.0, 4.0));
        col = baseColor * (0.2 * amb + 0.8 * diff);
        col *= exp(-0.03 * t * t);
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### 1. Volumetric Light/Glow Rendering

```glsl
float acc = 0.0, t = 0.0;
for (int i = 0; i < 99; i++) {
    float dist = map(ro + rd * t);
    dist = max(abs(dist), 0.02);
    acc += exp(-dist * 3.0);       // decay factor controls glow sharpness
    t += dist * 0.5;               // step scale <1 for denser sampling
}
vec3 col = vec3(acc * 0.01, acc * 0.011, acc * 0.012);
```

### 2. Single-Axis/Dual-Axis Selective Repetition

```glsl
q.xz = mod(q.xz + 2.0, 4.0) - 2.0; // repeat only xz, y stays unchanged
```

### 3. Fractal fract Domain Folding (Apollonian Type)

```glsl
float scale = 1.0;
for (int i = 0; i < 8; i++) {
    p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
    float k = 1.2 / dot(p, p);
    p *= k;
    scale *= k;
}
return 0.25 * abs(p.y) / scale;
```

### 4. Multi-Layer Nested Repetition

```glsl
float indexX = amod(p.xz, segments); // outer layer: angular repetition
p.x -= radius;
p.y = repeat(p.y, cellSize);         // inner layer: linear repetition
float salt = rng(vec2(indexX, floor(p.y / cellSize)));
```

### 5. Finite Domain Repetition (Clamp Limited)

```glsl
vec3 domainRepeatLimited(vec3 p, float size, vec3 limit) {
    return p - size * clamp(floor(p / size + 0.5), -limit, limit);
}
// Repeat 5 times along x, 3 times along y/z
vec3 q = domainRepeatLimited(p, 2.0, vec3(2.0, 1.0, 1.0));
```

## Performance & Composition Tips

**Performance:**
- 5-8 fractal iterations are typically sufficient; use `vec4.w` to track scaling and avoid extra variables
- Ensure geometry radius < period/2 to prevent inaccurate SDF at cell boundaries
- Volumetric light step size should increase with distance: `t += dist * (0.3 + t * 0.02)`
- Use `clamp(dot(p,p), min, max)` to prevent numerical explosion
- Avoid `normalize()` inside loops; manually divide by length instead

**Composition:**
- **Domain Repetition + Ray Marching**: the most fundamental combination, used by all reference shaders
- **Domain Repetition + Orbit Trap Coloring**: record `min(orb, abs(p))` during fractal iteration for coloring
- **Domain Repetition + Toroidal Warping**: `displaceLoop` to bend space before applying linear/angular repetition
- **Domain Repetition + Noise Variation**: cell ID -> pseudo-random number -> modulate geometry parameters
- **Domain Repetition + Polar Spiral**: `cartToPolar` combined with `pMod1` for spiral path repetition

## Further Reading

Full step-by-step tutorials, mathematical derivations, and advanced usage in [reference](../reference/domain-repetition.md)
