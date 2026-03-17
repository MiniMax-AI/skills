# SDF Soft Shadow Techniques

## Core Principles

March from the surface point toward the light source, using the **ratio of nearest distance to marching distance** to estimate penumbra width.

### Key Formulas

Classic formula: `shadow = min(shadow, k * h / t)`
- `h` = SDF value at current position, `t` = distance traveled, `k` = penumbra hardness

Improved formula (geometric triangulation) — eliminates sharp edge banding artifacts:
```
y = h² / (2 * ph)       // ph = SDF value from previous step
d = sqrt(h² - y²)       // true closest distance perpendicular to the ray
shadow = min(shadow, d / (w * max(0, t - y)))
```

Negative extension — allows `res` to drop to -1, remapped with a C1 continuous function to eliminate hard creases:
```
res = max(res, -1.0)
shadow = 0.25 * (1 + res)² * (2 - res)
```
This is equivalent to `smoothstep` over [-1, 1] instead of [0, 1]. The step size is clamped with `clamp(h, 0.005, 0.50)` to ensure the ray penetrates slightly into geometry, capturing both outer and inner penumbra. This produces results close to ground truth for varying light sizes.

## Implementation Steps

### Step 1: Scene SDF

```glsl
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdPlane(vec3 p) { return p.y; }
float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

float map(vec3 p) {
    float d = sdPlane(p);
    d = min(d, sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5));
    d = min(d, sdRoundBox(p - vec3(-1.2, 0.3, 0.5), vec3(0.3), 0.05));
    return d;
}
```

### Step 2: Classic Soft Shadow

```glsl
// Classic SDF soft shadow
float calcSoftShadow(vec3 ro, vec3 rd, float mint, float tmax) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float s = clamp(SHADOW_K * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, MIN_STEP, MAX_STEP);
        if (res < 0.004 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);  // smoothstep smoothing
}
```

### Step 3: Improved Soft Shadow (Geometric Triangulation)

```glsl
// Improved version - geometric triangulation using adjacent SDF values
float calcSoftShadowImproved(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;
    float ph = 1e10;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float y = h * h / (2.0 * ph);
        float d = sqrt(h * h - y * y);
        res = min(res, d / (w * max(0.0, t - y)));
        ph = h;
        t += h;
        if (res < 0.0001 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}
```

### Step 4: Negative Extension (Smoothest Penumbra)

```glsl
// Negative extension - allows res to go negative for C1 continuous penumbra
float calcSoftShadowSmooth(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        res = min(res, h / (w * t));
        t += clamp(h, MIN_STEP, MAX_STEP);
        if (res < -1.0 || t > tmax) break;
    }
    res = max(res, -1.0);
    return 0.25 * (1.0 + res) * (1.0 + res) * (2.0 - res);
}
```

### Step 5: Bounding Volume Optimization

```glsl
// plane clipping -- clip the ray to the scene's upper bound
float tp = (SCENE_Y_MAX - ro.y) / rd.y;
if (tp > 0.0) tmax = min(tmax, tp);

// AABB bounding box clipping
vec2 iBox(vec3 ro, vec3 rd, vec3 rad) {
    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF < 0.0) return vec2(-1.0);
    return vec2(tN, tF);
}

// usage: return 1.0 immediately if the ray misses the bounding box entirely
vec2 dis = iBox(ro, rd, BOUND_SIZE);
if (dis.y < 0.0) return 1.0;
tmin = max(tmin, dis.x);
tmax = min(tmax, dis.y);
```

### Step 6: Shadow Color Rendering

```glsl
// Classic colored shadow
vec3 shadowColor = vec3(sha, sha * sha * 0.5 + 0.5 * sha, sha * sha);

// per-channel power (penumbra region shifts warm)
vec3 shadowColor = pow(vec3(sha), vec3(1.0, 1.2, 1.5));
```

### Step 7: Integration with Lighting Model

```glsl
vec3 sunDir = normalize(vec3(-0.5, 0.4, -0.6));
vec3 hal = normalize(sunDir - rd);

float dif = clamp(dot(nor, sunDir), 0.0, 1.0);
if (dif > 0.0001)
    dif *= calcSoftShadow(pos + nor * 0.01, sunDir, 0.02, 8.0);

float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0);
spe *= dif;

vec3 col = vec3(0.0);
col += albedo * 2.0 * dif * vec3(1.0, 0.9, 0.8);
col += 5.0 * spe * vec3(1.0, 0.9, 0.8);
col += albedo * 0.5 * clamp(0.5 + 0.5 * nor.y, 0.0, 1.0) * vec3(0.4, 0.6, 1.0);
```

## Complete Code Template

Runs directly in ShaderToy, with A/B comparison of three soft shadow techniques.

```glsl
#define ZERO (min(iFrame, 0))

// ---- Adjustable Parameters ----
#define MAX_MARCH_STEPS   128
#define MAX_SHADOW_STEPS   64   // 16~128
#define SHADOW_K          8.0   // 4~64, higher = harder
#define SHADOW_MINT      0.02   // 0.01~0.05
#define SHADOW_TMAX      8.0
#define SHADOW_MIN_STEP  0.01
#define SHADOW_MAX_STEP  0.20
#define SHADOW_W         0.10   // improved version penumbra width

// 0=classic, 1=improved(Aaltonen), 2=negative extension
#define SHADOW_TECHNIQUE   0

// ---- SDF Primitives ----
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdPlane(vec3 p) { return p.y; }
float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

// ---- Scene SDF ----
float map(vec3 p) {
    float d = sdPlane(p);
    d = min(d, sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5));
    d = min(d, sdRoundBox(p - vec3(-1.2, 0.30, 0.5), vec3(0.25), 0.05));
    d = min(d, sdTorus(p - vec3(1.2, 0.25, -0.3), vec2(0.40, 0.08)));
    return d;
}

// ---- Normal ----
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.0005, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)));
}

// ---- Raymarching ----
float castRay(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = ZERO; i < MAX_MARCH_STEPS; i++) {
        float h = map(ro + rd * t);
        if (h < 0.0002) return t;
        t += h;
        if (t > 20.0) break;
    }
    return -1.0;
}

// ---- Bounding Volume Clipping ----
float clipTmax(vec3 ro, vec3 rd, float tmax, float yMax) {
    float tp = (yMax - ro.y) / rd.y;
    if (tp > 0.0) tmax = min(tmax, tp);
    return tmax;
}

// ---- Shadow: Classic ----
float softShadowClassic(vec3 ro, vec3 rd, float mint, float tmax) {
    tmax = clipTmax(ro, rd, tmax, 1.5);
    float res = 1.0, t = mint;
    for (int i = ZERO; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float s = clamp(SHADOW_K * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, SHADOW_MIN_STEP, SHADOW_MAX_STEP);
        if (res < 0.004 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}

// ---- Shadow: Improved ----
float softShadowImproved(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    tmax = clipTmax(ro, rd, tmax, 1.5);
    float res = 1.0, t = mint, ph = 1e10;
    for (int i = ZERO; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float y = h * h / (2.0 * ph);
        float d = sqrt(h * h - y * y);
        res = min(res, d / (w * max(0.0, t - y)));
        ph = h;
        t += h;
        if (res < 0.0001 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}

// ---- Shadow: Negative Extension ----
float softShadowSmooth(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    tmax = clipTmax(ro, rd, tmax, 1.5);
    float res = 1.0, t = mint;
    for (int i = ZERO; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        res = min(res, h / (w * t));
        t += clamp(h, SHADOW_MIN_STEP, SHADOW_MAX_STEP);
        if (res < -1.0 || t > tmax) break;
    }
    res = max(res, -1.0);
    return 0.25 * (1.0 + res) * (1.0 + res) * (2.0 - res);
}

// ---- Unified Interface ----
float calcSoftShadow(vec3 ro, vec3 rd, float mint, float tmax) {
    #if SHADOW_TECHNIQUE == 0
        return softShadowClassic(ro, rd, mint, tmax);
    #elif SHADOW_TECHNIQUE == 1
        return softShadowImproved(ro, rd, mint, tmax, SHADOW_W);
    #else
        return softShadowSmooth(ro, rd, mint, tmax, SHADOW_W);
    #endif
}

// ---- AO ----
float calcAO(vec3 p, vec3 n) {
    float occ = 0.0, sca = 1.0;
    for (int i = ZERO; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0;
        float d = map(p + h * n);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// ---- Checkerboard ----
float checkerboard(vec2 p) {
    vec2 q = floor(p);
    return mix(0.3, 1.0, mod(q.x + q.y, 2.0));
}

// ---- Render ----
vec3 render(vec3 ro, vec3 rd) {
    vec3 col = vec3(0.7, 0.75, 0.85) - 0.3 * rd.y;
    float t = castRay(ro, rd);
    if (t < 0.0) return col;

    vec3 pos = ro + rd * t;
    vec3 nor = calcNormal(pos);
    vec3 albedo = vec3(0.18);
    if (pos.y < 0.001)
        albedo = vec3(0.08 + 0.15 * checkerboard(pos.xz * 2.0));

    vec3 sunDir = normalize(vec3(-0.5, 0.4, -0.6));
    vec3 hal = normalize(sunDir - rd);

    float dif = clamp(dot(nor, sunDir), 0.0, 1.0);
    if (dif > 0.0001)
        dif *= calcSoftShadow(pos + nor * 0.001, sunDir, SHADOW_MINT, SHADOW_TMAX);

    float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0);
    spe *= dif;
    float fre = pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0);
    spe *= 0.04 + 0.96 * fre;

    float sky = clamp(0.5 + 0.5 * nor.y, 0.0, 1.0);
    float occ = calcAO(pos, nor);

    vec3 lin = vec3(0.0);
    lin += 2.5 * dif * vec3(1.30, 1.00, 0.70);
    lin += 8.0 * spe * vec3(1.30, 1.00, 0.70);
    lin += 0.5 * sky * vec3(0.40, 0.60, 1.00) * occ;
    lin += 0.25 * occ * vec3(0.40, 0.50, 0.60);

    col = albedo * lin;
    col = pow(col, vec3(0.4545));
    return col;
}

// ---- Camera ----
mat3 setCamera(vec3 ro, vec3 ta) {
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    float an = 0.3 * iTime;
    vec3 ro = vec3(3.5 * sin(an), 1.8, 3.5 * cos(an));
    vec3 ta = vec3(0.0, 0.3, 0.0);
    mat3 ca = setCamera(ro, ta);
    vec3 rd = ca * normalize(vec3(p, 1.8));
    vec3 col = render(ro, rd);
    fragColor = vec4(col, 1.0);
}
```

## Standalone HTML + WebGL2 Template

When generating standalone HTML files, use the following complete template. Key points:
- Must use `canvas.getContext('webgl2')`
- Shaders use `#version 300 es`
- Entry function is `void main()`, not `void mainImage()`
- Use `gl_FragCoord.xy` to get pixel coordinates (available in WebGL2)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Soft Shadows - SDF Raymarching</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const gl = canvas.getContext('webgl2');

        if (!gl) {
            document.body.innerHTML = '<p style="color:#fff;">WebGL2 not supported</p>';
            throw new Error('WebGL2 not supported');
        }

        // Vertex shader: fullscreen quad
        const vsSource = `#version 300 es
            in vec4 aPosition;
            void main() {
                gl_Position = aPosition;
            }
        `;

        // Fragment shader: SDF soft shadows
        const fsSource = `#version 300 es
            precision highp float;

            uniform float iTime;
            uniform vec2 iResolution;
            uniform vec4 iMouse;

            out vec4 fragColor;

            #define ZERO (min(int(iTime), 0))
            #define MAX_MARCH_STEPS 128
            #define MAX_SHADOW_STEPS 64
            #define SHADOW_MINT 0.02
            #define SHADOW_TMAX 10.0
            #define SHADOW_MIN_STEP 0.01
            #define SHADOW_MAX_STEP 0.25
            #define SHADOW_W 0.08
            #define SHADOW_K 16.0

            // SDF primitives
            float sdSphere(vec3 p, float r) { return length(p) - r; }
            float sdPlane(vec3 p) { return p.y; }
            float sdRoundBox(vec3 p, vec3 b, float r) {
                vec3 q = abs(p) - b;
                return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
            }
            float sdTorus(vec3 p, vec2 t) {
                vec2 q = vec2(length(p.xz) - t.x, p.y);
                return length(q) - t.y;
            }

            // Scene SDF
            float map(vec3 p) {
                float d = sdPlane(p);
                d = min(d, sdSphere(p - vec3(0.0, 0.6, 0.0), 0.6));
                d = min(d, sdRoundBox(p - vec3(-1.5, 0.4, 0.8), vec3(0.35), 0.08));
                d = min(d, sdTorus(p - vec3(1.6, 0.35, -0.5), vec2(0.45, 0.12)));
                return d;
            }

            // Normal
            vec3 calcNormal(vec3 p) {
                vec2 e = vec2(0.0005, 0.0);
                return normalize(vec3(
                    map(p + e.xyy) - map(p - e.xyy),
                    map(p + e.yxy) - map(p - e.yxy),
                    map(p + e.yyx) - map(p - e.yyx)));
            }

            // Raymarching
            float castRay(vec3 ro, vec3 rd) {
                float t = 0.0;
                for (int i = ZERO; i < MAX_MARCH_STEPS; i++) {
                    float h = map(ro + rd * t);
                    if (h < 0.0002) return t;
                    t += h;
                    if (t > 25.0) break;
                }
                return -1.0;
            }

            // Plane clipping
            float clipTmax(vec3 ro, vec3 rd, float tmax, float yMax) {
                float tp = (yMax - ro.y) / rd.y;
                if (tp > 0.0) tmax = min(tmax, tp);
                return tmax;
            }

            // Soft shadow (negative extension)
            float softShadow(vec3 ro, vec3 rd, float mint, float tmax, float w) {
                tmax = clipTmax(ro, rd, tmax, 2.0);
                float res = 1.0;
                float t = mint;
                for (int i = ZERO; i < MAX_SHADOW_STEPS; i++) {
                    float h = map(ro + rd * t);
                    res = min(res, h / (w * t));
                    t += clamp(h, SHADOW_MIN_STEP, SHADOW_MAX_STEP);
                    if (res < -1.0 || t > tmax) break;
                }
                res = max(res, -1.0);
                return 0.25 * (1.0 + res) * (1.0 + res) * (2.0 - res);
            }

            // Soft shadow call
            float calcSoftShadow(vec3 ro, vec3 rd) {
                return softShadow(ro, rd, SHADOW_MINT, SHADOW_TMAX, SHADOW_W);
            }

            // AO
            float calcAO(vec3 p, vec3 n) {
                float occ = 0.0, sca = 1.0;
                for (int i = ZERO; i < 5; i++) {
                    float h = 0.01 + 0.12 * float(i) / 4.0;
                    float d = map(p + h * n);
                    occ += (h - d) * sca;
                    sca *= 0.95;
                }
                return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
            }

            // Checkerboard
            float checkerboard(vec2 p) {
                vec2 q = floor(p);
                return mix(0.25, 0.35, mod(q.x + q.y, 2.0));
            }

            // Render
            vec3 render(vec3 ro, vec3 rd) {
                // sky
                vec3 col = vec3(0.65, 0.72, 0.85) - 0.4 * rd.y;
                col = mix(col, vec3(0.3, 0.35, 0.45), exp(-0.8 * max(rd.y, 0.0)));

                float t = castRay(ro, rd);
                if (t < 0.0) return col;

                vec3 pos = ro + rd * t;
                vec3 nor = calcNormal(pos);

                // material color
                vec3 albedo = vec3(0.18);
                if (pos.y < 0.01) {
                    albedo = vec3(0.12 + 0.12 * checkerboard(pos.xz * 1.5));
                } else if (pos.y > 0.5 && length(pos.xz) < 0.7) {
                    albedo = vec3(0.85, 0.25, 0.2);
                } else if (pos.x < -1.0) {
                    albedo = vec3(0.2, 0.4, 0.85);
                } else if (pos.x > 1.0) {
                    albedo = vec3(0.25, 0.75, 0.35);
                } else {
                    albedo = vec3(0.9, 0.6, 0.2);
                }

                // lighting
                vec3 sunDir = normalize(vec3(-0.6, 0.45, -0.65));
                vec3 hal = normalize(sunDir - rd);

                float dif = clamp(dot(nor, sunDir), 0.0, 1.0);
                if (dif > 0.0001) {
                    dif *= calcSoftShadow(pos + nor * 0.01, sunDir);
                }

                float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 32.0);
                spe *= dif;

                float fre = pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0);
                spe *= 0.04 + 0.96 * fre;

                float sky = clamp(0.5 + 0.5 * nor.y, 0.0, 1.0);
                float occ = calcAO(pos, nor);

                vec3 lin = vec3(0.0);
                lin += 2.2 * dif * vec3(1.35, 1.05, 0.75);
                lin += 6.0 * spe * vec3(1.35, 1.05, 0.75);
                lin += 0.4 * sky * vec3(0.45, 0.6, 0.9) * occ;
                lin += 0.25 * occ * vec3(0.5, 0.55, 0.6);

                col = albedo * lin;
                col = pow(col, vec3(0.4545));

                // vignette
                vec2 uv = gl_FragCoord.xy / iResolution.xy;
                col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.2);

                return col;
            }

            // Camera
            mat3 setCamera(vec3 ro, vec3 ta) {
                vec3 cw = normalize(ta - ro);
                vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
                vec3 cv = cross(cu, cw);
                return mat3(cu, cv, cw);
            }

            void main() {
                vec2 fragCoord = gl_FragCoord.xy;
                vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

                // slowly rotating camera
                float an = 0.15 * iTime;
                float dist = 5.5;
                vec3 ro = vec3(dist * sin(an), 2.2, dist * cos(an));
                vec3 ta = vec3(0.0, 0.3, 0.0);

                mat3 ca = setCamera(ro, ta);
                vec3 rd = ca * normalize(vec3(p, 2.0));

                vec3 col = render(ro, rd);
                fragColor = vec4(col, 1.0);
            }
        `;

        // Compile shader
        function createShader(gl, type, source) {
            const shader = gl.createShader(type);
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                console.error('Shader compile error:', gl.getShaderInfoLog(shader));
                gl.deleteShader(shader);
                return null;
            }
            return shader;
        }

        // Create program
        function createProgram(gl, vs, fs) {
            const program = gl.createProgram();
            gl.attachShader(program, vs);
            gl.attachShader(program, fs);
            gl.linkProgram(program);
            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
                console.error('Program link error:', gl.getProgramInfoLog(program));
                return null;
            }
            return program;
        }

        const vs = createShader(gl, gl.VERTEX_SHADER, vsSource);
        const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource);
        const program = createProgram(gl, vs, fs);

        // Fullscreen quad
        const positions = new Float32Array([
            -1, -1,  1, -1,  -1,  1,  1,  1
        ]);

        const posBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

        const posLoc = gl.getAttribLocation(program, 'aPosition');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

        // Uniforms
        const uTime = gl.getUniformLocation(program, 'iTime');
        const uResolution = gl.getUniformLocation(program, 'iResolution');
        const uMouse = gl.getUniformLocation(program, 'iMouse');

        // Mouse tracking
        let mouseX = 0, mouseY = 0;
        canvas.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = canvas.height - e.clientY;
        });

        // Window resize
        function resize() {
            const dpr = Math.min(window.devicePixelRatio, 2);
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            gl.viewport(0, 0, canvas.width, canvas.height);
        }
        window.addEventListener('resize', resize);
        resize();

        // Render loop
        function render(time) {
            time *= 0.001;
            gl.useProgram(program);
            gl.uniform1f(uTime, time);
            gl.uniform2f(uResolution, canvas.width, canvas.height);
            gl.uniform4f(uMouse, mouseX, mouseY, mouseX, mouseY);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            requestAnimationFrame(render);
        }
        requestAnimationFrame(render);
    </script>
</body>
</html>
```

## Common Variants

### Analytic Sphere Shadow

```glsl
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    return vec2(d, -b - sqrt(max(h, 0.0)));
}
float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph, float k) {
    vec2 r = sphDistances(ro, rd, sph);
    if (r.y > 0.0)
        return clamp(k * max(r.x, 0.0) / r.y, 0.0, 1.0);
    return 1.0;
}
```

### Terrain Heightfield Shadow

```glsl
float terrainShadow(vec3 ro, vec3 rd, float dis) {
    float minStep = clamp(dis * 0.01, 0.5, 50.0);
    float res = 1.0, t = 0.01;
    for (int i = 0; i < 80; i++) {
        vec3 p = ro + t * rd;
        float h = p.y - terrainMap(p.xz);
        res = min(res, 16.0 * h / t);
        t += max(minStep, h);
        if (res < 0.001 || p.y > MAX_TERRAIN_HEIGHT) break;
    }
    return clamp(res, 0.0, 1.0);
}
```

### Per-Material Soft/Hard Blending

```glsl
float hsha = 1.0;  // global variable, set per material in map()
float mapWithShadowHardness(vec3 p) {
    float d = sdPlane(p); hsha = 1.0;
    float dChar = sdCharacter(p);
    if (dChar < d) { d = dChar; hsha = 0.0; }
    return d;
}
// in shadow loop: res = min(res, mix(1.0, SHADOW_K * h / t, hsha));
```

### Multi-Layer Shadow Compositing

```glsl
float sha_terrain = terrainShadow(pos, sunDir, 0.02);
float sha_trees   = treesShadow(pos, sunDir);
float sha_clouds  = cloudShadow(pos, sunDir);
float sha = sha_terrain * sha_trees;
sha *= smoothstep(-0.3, -0.1, sha_clouds);
dif *= sha;
```

### Volumetric Light / God Rays

```glsl
float godRays(vec3 ro, vec3 rd, float tmax, vec3 sunDir) {
    float v = 0.0, dt = 0.15;
    float t = dt * fract(texelFetch(iChannel0, ivec2(fragCoord) & 255, 0).x);
    for (int i = 0; i < 32; i++) {
        if (t > tmax) break;
        vec3 p = ro + rd * t;
        float sha = calcSoftShadow(p, sunDir, 0.02, 8.0);
        v += sha * exp(-0.2 * t);
        t += dt;
    }
    v /= 32.0;
    return v * v;
}
// col += intensity * godRays(...) * vec3(1.0, 0.75, 0.4);
```

## Performance & Composition

**Performance optimization:**
- Bounding volume clipping (plane/AABB) can reduce 30-70% of wasted iterations
- Step clamping `clamp(h, minStep, maxStep)` prevents stalling / skipping thin objects
- Early exit: `res < 0.004` (classic) or `res < -1.0` (negative extension)
- Simplified `map()` omitting material calculations, returning distance only
- Only compute shadow when `dif > 0.0001`; skip for backlit faces
- Iteration count: simple scenes 16~32, complex FBM 64~128, terrain ~80
- `#define ZERO (min(iFrame,0))` prevents compiler loop unrolling

**Composition tips:**
- AO: shadows control direct light, AO controls indirect light, `col = diffuse * sha + ambient * ao`
- SSS: `sss *= 0.25 + 0.75 * sha` -- SSS weakens but does not vanish in shadow
- Fog: complete lit+shadowed shading first, then `mix(col, fogColor, 1.0 - exp(-0.001*t*t))`
- Normal mapping: perturbed normals for lighting, geometric normals for shadow determination
- Reflection: `refSha = calcSoftShadow(pos + nor*0.01, reflect(rd, nor), 0.02, 8.0)`

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/shadow-techniques.md)
