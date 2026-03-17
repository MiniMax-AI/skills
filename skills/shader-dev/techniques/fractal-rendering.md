# Fractal Rendering Skill

## Use Cases
- Rendering self-similar mathematical structures: Mandelbrot/Julia sets (2D), Mandelbulb (3D), IFS fractals (Menger/Apollonian)
- Procedural textures or backgrounds requiring infinite detail
- Real-time generation of complex geometric visual effects (music visualization, sci-fi scenes, abstract art)
- Suitable for ShaderToy, demo scene, procedural content generation

## Core Principles

Fractal rendering is essentially **visualization of iterative systems**, falling into three categories:

### 1. Escape-Time Algorithm
Iterate `Z <- Z^2 + c`, count escape steps. Distance estimation by simultaneously tracking the derivative `Z'`:
```
Z  <- Z^2 + c
Z' <- 2*Z*Z' + 1
d(c) = |Z|*log|Z| / |Z'|
```

### 2. Iterated Function System (IFS / KIFS)
Fold-sort-scale-offset iteration produces self-similar structures:
```
p = abs(p)                          // fold
sort p.xyz descending               // sort
p = Scale * p - Offset * (Scale-1)  // scale and offset
```

### 3. Spherical Inversion Fractals
`fract()` space folding + spherical inversion `p *= s/dot(p,p)`:
```
p = -1.0 + 2.0 * fract(0.5*p + 0.5)
k = s / dot(p, p)
p *= k; scale *= k
```

All 3D fractals are rendered via **Sphere Tracing (Ray Marching)**.

## Implementation Steps

### Step 1: Coordinate Normalization
```glsl
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
```

### Step 2: 2D Mandelbrot Escape-Time Iteration
```glsl
float distanceToMandelbrot(in vec2 c) {
    vec2 z  = vec2(0.0);
    vec2 dz = vec2(0.0);
    float m2 = 0.0;

    for (int i = 0; i < MAX_ITER; i++) {
        if (m2 > BAILOUT * BAILOUT) break;
        // Z' -> 2*Z*Z' + 1
        dz = 2.0 * vec2(z.x*dz.x - z.y*dz.y,
                         z.x*dz.y + z.y*dz.x) + vec2(1.0, 0.0);
        // Z -> Z^2 + c
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        m2 = dot(z, z);
    }
    return 0.5 * sqrt(dot(z,z) / dot(dz,dz)) * log(dot(z,z));
}
```

### Step 3: Mandelbulb Distance Field (Spherical Coordinate Power-N)
```glsl
float mandelbulb(vec3 p) {
    vec3 z = p;
    float dr = 1.0;
    float r;

    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > BAILOUT) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER;
        phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi),
                      sin(theta)*cos(phi),
                      sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```

### Step 4: Menger Sponge Distance Field (KIFS)
```glsl
float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // infinite tiling
    float d = 1000.0;

    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0);
        if (z.z < -0.5 * OFFSET.z * (SCALE - 1.0))
            z.z += OFFSET.z * (SCALE - 1.0);
        d = min(d, length(z) * pow(SCALE, float(-n) - 1.0));
    }
    return d - 0.001;
}
```

### Step 5: Apollonian Distance Field (Spherical Inversion)
```glsl
vec4 orb;  // orbit trap

float apollonianDE(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;
        p *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}
```

### Step 6: Ray Marching
```glsl
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;
        float h = map(ro + rd * t);
        if (h < precis || t > MAX_DIST) break;
        t += h * FUDGE_FACTOR;
    }
    return (t > MAX_DIST) ? -1.0 : t;
}
```

### Step 7: Normal Calculation
```glsl
// 4-tap tetrahedral method (recommended)
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx));
}
```

### Step 8: Shading & Lighting
```glsl
vec3 shade(vec3 pos, vec3 nor, vec3 rd, vec4 trap) {
    vec3 light1 = normalize(LIGHT_DIR);
    float diff = clamp(dot(light1, nor), 0.0, 1.0);
    float amb  = 0.7 + 0.3 * nor.y;
    float ao   = pow(clamp(trap.w * 2.0, 0.0, 1.0), 1.2);

    vec3 brdf = vec3(0.4) * amb * ao + vec3(1.0) * diff * ao;

    vec3 rgb = vec3(1.0);
    rgb = mix(rgb, vec3(1.0, 0.8, 0.2), clamp(6.0*trap.y, 0.0, 1.0));
    rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0-2.0*trap.z, 0.0, 1.0), 8.0));
    return rgb * brdf;
}
```

### Step 9: Camera
```glsl
void setupCamera(vec2 uv, vec3 ro, vec3 ta, float cr, out vec3 rd) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = normalize(cross(cu, cw));
    rd = normalize(uv.x * cu + uv.y * cv + 2.0 * cw);
}
```

## Complete Code Template

3D Apollonian fractal (spherical inversion type) with full ray marching pipeline, orbit trap coloring, and AO. Ready to run in ShaderToy.

```glsl
// Fractal Rendering — Apollonian (Spherical Inversion) Template

#define MAX_STEPS 200
#define MAX_DIST 30.0
#define PRECISION 0.001
#define INVERSION_ITER 8    // Tunable: 5-12
#define AA 1                // Tunable: 1=no AA, 2=4xSSAA

vec4 orb;

float map(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;
        p     *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}

float trace(vec3 ro, vec3 rd, float s) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;
        float h = map(ro + rd * t, s);
        if (h < precis || t > MAX_DIST) break;
        t += h;
    }
    return (t > MAX_DIST) ? -1.0 : t;
}

vec3 calcNormal(vec3 pos, float t, float s) {
    float precis = PRECISION * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy, s) +
        e.yyx * map(pos + e.yyx, s) +
        e.yxy * map(pos + e.yxy, s) +
        e.xxx * map(pos + e.xxx, s));
}

vec3 render(vec3 ro, vec3 rd, float anim) {
    vec3 col = vec3(0.0);
    float t = trace(ro, rd, anim);

    if (t > 0.0) {
        vec4 tra = orb;
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos, t, anim);

        vec3 light1 = normalize(vec3(0.577, 0.577, -0.577));
        vec3 light2 = normalize(vec3(-0.707, 0.0, 0.707));
        float key = clamp(dot(light1, nor), 0.0, 1.0);
        float bac = clamp(0.2 + 0.8 * dot(light2, nor), 0.0, 1.0);
        float amb = 0.7 + 0.3 * nor.y;
        float ao  = pow(clamp(tra.w * 2.0, 0.0, 1.0), 1.2);

        vec3 brdf = vec3(0.40) * amb * ao
                  + vec3(1.00) * key * ao
                  + vec3(0.40) * bac * ao;

        vec3 rgb = vec3(1.0);
        rgb = mix(rgb, vec3(1.0, 0.80, 0.2), clamp(6.0 * tra.y, 0.0, 1.0));
        rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0 - 2.0*tra.z, 0.0, 1.0), 8.0));

        col = rgb * brdf * exp(-0.2 * t);
    }
    return sqrt(col);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.25;
    float anim = 1.1 + 0.5 * smoothstep(-0.3, 0.3, cos(0.1 * iTime));

    vec3 tot = vec3(0.0);

    #if AA > 1
    for (int jj = 0; jj < AA; jj++)
    for (int ii = 0; ii < AA; ii++)
    #else
    int ii = 1, jj = 1;
    #endif
    {
        vec2 q = fragCoord.xy + vec2(float(ii), float(jj)) / float(AA);
        vec2 p = (2.0 * q - iResolution.xy) / iResolution.y;

        vec3 ro = vec3(2.8*cos(0.1 + 0.33*time),
                       0.4 + 0.3*cos(0.37*time),
                       2.8*cos(0.5 + 0.35*time));
        vec3 ta = vec3(1.9*cos(1.2 + 0.41*time),
                       0.4 + 0.1*cos(0.27*time),
                       1.9*cos(2.0 + 0.38*time));
        float roll = 0.2 * cos(0.1 * time);

        vec3 cw = normalize(ta - ro);
        vec3 cp = vec3(sin(roll), cos(roll), 0.0);
        vec3 cu = normalize(cross(cw, cp));
        vec3 cv = normalize(cross(cu, cw));
        vec3 rd = normalize(p.x*cu + p.y*cv + 2.0*cw);

        tot += render(ro, rd, anim);
    }

    tot /= float(AA * AA);
    fragColor = vec4(tot, 1.0);
}
```

## Common Variants

### 1. 2D Mandelbrot (Distance Estimation Coloring)
Pure 2D, no ray marching needed. Complex iteration + distance coloring.
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0*fragCoord - iResolution.xy) / iResolution.y;
    float tz = 0.5 - 0.5*cos(0.225*iTime);
    float zoo = pow(0.5, 13.0*tz);
    vec2 c = vec2(-0.05, 0.6805) + p * zoo; // Tunable: zoom center point

    vec2 z = vec2(0.0), dz = vec2(0.0);
    for (int i = 0; i < 300; i++) {
        if (dot(z,z) > 1024.0) break;
        dz = 2.0*vec2(z.x*dz.x-z.y*dz.y, z.x*dz.y+z.y*dz.x) + vec2(1.0,0.0);
        z  = vec2(z.x*z.x-z.y*z.y, 2.0*z.x*z.y) + c;
    }

    float d = 0.5*sqrt(dot(z,z)/dot(dz,dz))*log(dot(z,z));
    d = clamp(pow(4.0*d/zoo, 0.2), 0.0, 1.0);
    fragColor = vec4(vec3(d), 1.0);
}
```

### 2. Mandelbulb Power-N
Spherical coordinate trigonometric functions; `POWER` parameter controls morphology.
```glsl
#define POWER 8.0       // Tunable: 2-16
#define FRACTAL_ITER 4  // Tunable: 2-8

float mandelbulbDE(vec3 p) {
    vec3 z = p;
    float dr = 1.0, r;
    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > 2.0) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER; phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi), sin(theta)*cos(phi), sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```

### 3. Menger Sponge (KIFS)
`abs()` folding + conditional sorting, regular geometric fractal.
```glsl
#define SCALE 3.0
#define OFFSET vec3(0.92858,0.92858,0.32858)
#define IFS_ITER 7

float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));
    float d = 1000.0;
    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;
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
Quaternion `Z <- Z^2 + c` (4D), with fixed `c` parameter; visualized by taking a 3D slice.
```glsl
vec4 qsqr(vec4 a) {
    return vec4(a.x*a.x - a.y*a.y - a.z*a.z - a.w*a.w,
                2.0*a.x*a.y, 2.0*a.x*a.z, 2.0*a.x*a.w);
}

float juliaDE(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0);
    float md2 = 1.0, mz2 = dot(z, z);
    for (int i = 0; i < 11; i++) {
        md2 *= 4.0 * mz2;
        z = qsqr(z) + c;
        mz2 = dot(z, z);
        if (mz2 > 4.0) break;
    }
    return 0.25 * sqrt(mz2 / md2) * log(mz2);
}
// Animated c: vec4 c = 0.45*cos(vec4(0.5,3.9,1.4,1.1)+time*vec4(1.2,1.7,1.3,2.5))-vec4(0.3,0,0,0);
```

### 5. Minimal IFS Field (2D, No Ray Marching)
`abs(p)/dot(p,p) + offset` iteration, weighted accumulation produces a density field.
```glsl
float field(vec3 p) {
    float strength = 7.0 + 0.03 * log(1.e-6 + fract(sin(iTime) * 4373.11));
    float accum = 0.0, prev = 0.0, tw = 0.0;
    for (int i = 0; i < 32; ++i) {
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-0.5, -0.4, -1.5); // Tunable: offset values
        float w = exp(-float(i) / 7.0);
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0.0, 5.0 * accum / tw - 0.7);
}
```

## Performance & Composition

### Performance Tips
- Core bottleneck: outer ray marching x inner fractal iteration (e.g., `200 x 8 = 1600` map calls per pixel)
- Reduce `MAX_STEPS` to 60-100, compensate with fudge factor 0.7-0.9
- Hit threshold `precis = 0.001 * t` relaxes with distance
- Fractal iteration: break immediately when `|z|^2 > bailout`
- Reducing iterations from 8 to 4-5 has minimal visual impact
- Use 4-tap normals instead of 6-tap to save 33%
- Use AA=1 during development, AA=2 for release (AA=3 = 9x overhead)
- Avoid `pow()` inside loops; manually expand for low powers

### Composition Techniques
- **Volumetric light**: accumulate `exp(-10.0 * h)` during ray march for god rays
- **Tone Mapping**: ACES + sRGB gamma for handling high-frequency detail
- **Transparent refraction**: negative distance field reverse ray march + Beer's law absorption
- **Orbit Trap coloring**: map trap values to HSV or emissive colors
- **Soft shadows**: ray march toward light, accumulate `min(k * h / t)` for soft shadows

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/fractal-rendering.md)
