# Ray Marching

## Use Cases

- Rendering implicit surfaces (geometry defined by mathematical functions) without triangle meshes
- Creating fractals, organic forms, liquid metal, and other shapes difficult to express with traditional modeling
- Implementing volumetric effects: fire, smoke, clouds, glow
- Rapid prototyping of procedural scenes: building complex scenes by combining SDF primitives with boolean operations
- Advanced distance-field-based lighting: soft shadows, ambient occlusion, subsurface scattering

## Core Principles

Cast a ray from the camera along each pixel direction, advancing step by step using a **Signed Distance Function (SDF)** (Sphere Tracing). Each step advances by the SDF value at the current point, guaranteeing no surface penetration.

- Ray equation: `P(t) = ro + t * rd`
- Stepping logic: `t += SDF(P(t))`
- Hit test: `SDF(P) < epsilon`
- Normal estimation: `N = normalize(gradient of SDF(P))` (direction of the SDF gradient)
- Volumetric rendering: advance at fixed step size, accumulating density and color per step (front-to-back compositing)

## Implementation Steps

### Step 1: UV Normalization and Ray Direction

```glsl
// Concise version
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
vec3 ro = vec3(0.0, 0.0, -3.0);
vec3 rd = normalize(vec3(uv, 1.0));          // z=1.0 ~ 90 deg FOV

// Precise FOV control
vec2 xy = fragCoord - iResolution.xy / 2.0;
float z = iResolution.y / tan(radians(FOV) / 2.0);
vec3 rd = normalize(vec3(xy, -z));
```

### Step 2: Camera Matrix (Look-At)

```glsl
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

mat3 ca = setCamera(ro, ta, 0.0);
vec3 rd = ca * normalize(vec3(uv, FOCAL_LENGTH)); // 1.0~3.0, larger = narrower FOV
```

### Step 3: Scene SDF

```glsl
// SDF primitives
float sdSphere(vec3 p, float r) { return length(p) - r; }

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// Boolean operations
float opUnion(float a, float b)        { return min(a, b); }
float opSubtraction(float a, float b)  { return max(a, -b); }
float opIntersection(float a, float b) { return max(a, b); }

// Smooth blending, adjustable k: 0.1~0.5
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

// Scene composition
float map(vec3 p) {
    float d = sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5);
    d = opUnion(d, p.y);                                           // ground
    d = smin(d, sdBox(p - vec3(1.0, 0.3, 0.0), vec3(0.3)), 0.2); // smooth blend with box
    return d;
}
```

### Step 4: Ray Marching Loop

```glsl
#define MAX_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001

float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > MAX_DIST) break;
    }
    return -1.0;
}
```

### Step 5: Normal Estimation

```glsl
// Central differences (6 SDF evaluations)
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Tetrahedral trick (4 SDF evaluations, recommended)
vec3 calcNormal(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = 0; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.001 * e);
    }
    return normalize(n);
}
```

### Step 6: Lighting and Shading

```glsl
vec3 shade(vec3 p, vec3 rd) {
    vec3 nor = calcNormal(p);
    vec3 lightDir = normalize(vec3(0.6, 0.35, 0.5));
    vec3 halfDir = normalize(lightDir - rd);

    float diff = clamp(dot(nor, lightDir), 0.0, 1.0);
    float spec = pow(clamp(dot(nor, halfDir), 0.0, 1.0), SHININESS); // 8~64
    float sky = sqrt(clamp(0.5 + 0.5 * nor.y, 0.0, 1.0));

    vec3 col = vec3(0.2, 0.2, 0.25);
    vec3 lin = vec3(0.0);
    lin += diff * vec3(1.3, 1.0, 0.7) * 2.2;
    lin += sky  * vec3(0.4, 0.6, 1.15) * 0.6;
    lin += vec3(0.25) * 0.55;
    col *= lin;
    col += spec * vec3(1.3, 1.0, 0.7) * 5.0;
    return col;
}
```

### Step 7: Post-Processing

```glsl
col = pow(col, vec3(0.4545));                 // Gamma correction (1/2.2)
col = col / (1.0 + col);                      // Reinhard tone mapping (optional, before gamma)

// Vignette (optional)
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.25);
```

## Full Code Template

Can be pasted directly into ShaderToy. Includes SDF scene, Phong lighting, soft shadows, and ambient occlusion:

```glsl
// ============================================================
// Ray Marching Full Template — ShaderToy
// ============================================================

#define MAX_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001
#define SHADOW_STEPS 24
#define AO_STEPS 5
#define FOCAL_LENGTH 2.5
#define SHININESS 16.0

// --- SDF Primitives ---
float sdSphere(vec3 p, float r) { return length(p) - r; }

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// --- Boolean Operations ---
float opUnion(float a, float b) { return min(a, b); }
float opSubtraction(float a, float b) { return max(a, -b); }
float opIntersection(float a, float b) { return max(a, b); }

float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

mat2 rot2D(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

// --- Scene Definition ---
float map(vec3 p) {
    float ground = p.y;
    vec3 q = p - vec3(0.0, 0.8, 0.0);
    q.xz *= rot2D(iTime * 0.5);
    float body = smin(sdSphere(q, 0.5), sdTorus(q, vec2(0.8, 0.15)), 0.3);
    return opUnion(ground, body);
}

// --- Normal (Tetrahedral Trick) ---
vec3 calcNormal(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = min(iFrame,0); i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.001 * e);
    }
    return normalize(n);
}

// --- Soft Shadows ---
float calcSoftShadow(vec3 ro, vec3 rd, float tmin, float tmax) {
    float res = 1.0, t = tmin;
    for (int i = 0; i < SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float s = clamp(8.0 * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.004 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}

// --- Ambient Occlusion ---
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0, sca = 1.0;
    for (int i = 0; i < AO_STEPS; i++) {
        float h = 0.01 + 0.12 * float(i) / float(AO_STEPS - 1);
        float d = map(pos + h * nor);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// --- Ray March ---
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (abs(d) < SURF_DIST * (1.0 + t * 0.1)) return t;
        t += d;
        if (t > MAX_DIST) break;
    }
    return -1.0;
}

// --- Camera ---
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

// --- Rendering ---
vec3 render(vec3 ro, vec3 rd) {
    vec3 col = vec3(0.7, 0.7, 0.9) - max(rd.y, 0.0) * 0.3; // sky

    float t = rayMarch(ro, rd);
    if (t > 0.0) {
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos);

        // Material
        vec3 mate = vec3(0.18);
        if (pos.y < 0.001) {
            float f = mod(floor(pos.x) + floor(pos.z), 2.0);
            mate = vec3(0.1 + 0.05 * f);
        } else {
            mate = 0.2 + 0.2 * sin(vec3(0.0, 1.0, 2.0));
        }

        // Lighting
        vec3 lightDir = normalize(vec3(-0.5, 0.4, -0.6));
        float occ = calcAO(pos, nor);
        float dif = clamp(dot(nor, lightDir), 0.0, 1.0);
        dif *= calcSoftShadow(pos + nor * 0.01, lightDir, 0.02, 2.5);
        vec3 hal = normalize(lightDir - rd);
        float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), SHININESS) * dif;
        float sky = sqrt(clamp(0.5 + 0.5 * nor.y, 0.0, 1.0));

        vec3 lin = vec3(0.0);
        lin += dif * vec3(1.3, 1.0, 0.7) * 2.2;
        lin += sky * vec3(0.4, 0.6, 1.15) * 0.6 * occ;
        lin += vec3(0.25) * 0.55 * occ;
        col = mate * lin;
        col += spe * vec3(1.3, 1.0, 0.7) * 5.0;

        col = mix(col, vec3(0.7, 0.7, 0.9), 1.0 - exp(-0.0001 * t * t * t)); // distance fog
    }
    return clamp(col, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = 32.0 + iTime * 1.5;
    vec2 mo = iMouse.xy / iResolution.xy;
    vec3 ta = vec3(0.0, 0.5, 0.0);
    vec3 ro = ta + vec3(4.0*cos(0.1*time+7.0*mo.x), 1.5, 4.0*sin(0.1*time+7.0*mo.x));
    mat3 ca = setCamera(ro, ta, 0.0);

    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    vec3 rd = ca * normalize(vec3(uv, FOCAL_LENGTH));

    vec3 col = render(ro, rd);
    col = pow(col, vec3(0.4545));

    vec2 q = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.25);

    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### 1. Volumetric Ray Marching

Advance at fixed step size, accumulating density/color per step. Used for fire, smoke, and clouds.

```glsl
#define VOL_STEPS 150
#define VOL_STEP_SIZE 0.05

float fbmDensity(vec3 p) {
    float den = 0.2 - p.y;
    vec3 q = p - vec3(0.0, 1.0, 0.0) * iTime;
    float f  = 0.5000 * noise(q); q = q * 2.02 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.2500 * noise(q); q = q * 2.03 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.1250 * noise(q); q = q * 2.01 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.0625 * noise(q);
    return den + 4.0 * f;
}

vec3 volumetricMarch(vec3 ro, vec3 rd) {
    vec4 sum = vec4(0.0);
    float t = 0.05;
    for (int i = 0; i < VOL_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float den = fbmDensity(pos);
        if (den > 0.0) {
            den = min(den, 1.0);
            vec3 col = mix(vec3(1.0,0.5,0.05), vec3(0.48,0.53,0.5), clamp(pos.y*0.5,0.0,1.0));
            col *= den; col.a = den * 0.6; col.rgb *= col.a;
            sum += col * (1.0 - sum.a);
            if (sum.a > 0.99) break;
        }
        t += VOL_STEP_SIZE;
    }
    return clamp(sum.rgb, 0.0, 1.0);
}
```

### 2. CSG Scene Construction

```glsl
float sceneSDF(vec3 p) {
    p = rotateY(iTime * 0.5) * p;
    float sphere = sdSphere(p, 1.2);
    float cube = sdBox(p, vec3(0.9));
    float cyl = sdCylinder(p, vec2(0.4, 2.0));
    float cylX = sdCylinder(p.yzx, vec2(0.4, 2.0));
    float cylZ = sdCylinder(p.xzy, vec2(0.4, 2.0));
    return opSubtraction(opIntersection(sphere, cube), opUnion(cyl, opUnion(cylX, cylZ)));
}
```

### 3. Physically-Based Volumetric Scattering

```glsl
void getParticipatingMedia(out float sigmaS, out float sigmaE, vec3 pos) {
    float heightFog = 0.3 * clamp((7.0 - pos.y), 0.0, 1.0);
    sigmaS = 0.02 + heightFog;
    sigmaE = max(0.000001, sigmaS);
}

vec3 S = lightColor * sigmaS * phaseFunction() * volShadow;
vec3 Sint = (S - S * exp(-sigmaE * stepLen)) / sigmaE;
scatteredLight += transmittance * Sint;
transmittance *= exp(-sigmaE * stepLen);
```

### 4. Glow Accumulation

```glsl
vec2 rayMarchWithGlow(vec3 ro, vec3 rd) {
    float t = 0.0, dMin = MAX_DIST;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < dMin) dMin = d;
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return vec2(t, dMin);
}

float glow = 0.02 / max(dMin, 0.001);
col += glow * vec3(1.0, 0.8, 0.9);
```

### 5. Refraction and Bidirectional Marching

```glsl
float castRay(vec3 ro, vec3 rd) {
    float sign = (map(ro) < 0.0) ? -1.0 : 1.0;
    float t = 0.0;
    for (int i = 0; i < 120; i++) {
        float h = sign * map(ro + rd * t);
        if (abs(h) < 0.0001 || t > 12.0) break;
        t += h;
    }
    return t;
}

vec3 refDir = refract(rd, nor, IOR);    // IOR: index of refraction, e.g. 0.9
float t2 = 2.0;
for (int i = 0; i < 50; i++) {
    float h = map(hitPos + refDir * t2);
    t2 -= h;
    if (abs(h) > 3.0) break;
}
vec3 nor2 = calcNormal(hitPos + refDir * t2);
```

## Performance & Composition

**Performance tips:**
- Use tetrahedral trick for normals (4 SDF evaluations instead of 6)
- `min(iFrame,0)` as loop start value to prevent compiler unrolling
- AABB bounding box pre-test to skip empty regions
- Adaptive hit threshold: `SURF_DIST * (1.0 + t * 0.1)`
- Step clamping: `t += clamp(h, 0.01, 0.2)`
- Early exit for volumetric rendering when `sum.a > 0.99`
- Use cheap bounding SDF first, then compute precise SDF

**Composition directions:**
- + FBM noise: terrain/rock texture, cloud/smoke volumetric density fields
- + Domain transforms (twist/bend/repeat): infinite repeating corridors, surreal geometry
- + PBR materials (Cook-Torrance BRDF + Fresnel + environment mapping)
- + Multi-pass post-processing: depth of field, motion blur, tone mapping
- + Procedural animation: time-driven SDF parameters + smoothstep easing

## Further Reading

Full step-by-step tutorials, mathematical derivations, and advanced usage in [reference](../reference/ray-marching.md)
