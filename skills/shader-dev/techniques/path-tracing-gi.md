Path tracing requires multi-pass rendering: Buffer A traces and accumulates samples each frame (iChannel0=self), Image Pass reads accumulated data and applies tone mapping for display. Below is the JS skeleton for standalone HTML:

### Standalone HTML Multi-Pass Template (Ping-Pong Accumulation)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Path Tracer</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
</head>
<body>
<canvas id="c"></canvas>
<script>
let frameCount = 0;
let mouse = [0, 0, 0, 0];

const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
const ext = gl.getExtension('EXT_color_buffer_float');

function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
        console.error(gl.getShaderInfoLog(s));
    return s;
}
function createProgram(vsSrc, fsSrc) {
    const p = gl.createProgram();
    gl.attachShader(p, createShader(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(p, createShader(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(p);
    return p;
}

const vsSource = `#version 300 es
in vec2 pos;
void main(){ gl_Position=vec4(pos,0,1); }`;

// fsBuffer: path tracing + accumulation (see "Complete Code Template - Buffer A" below)
// fsImage:  ACES tone mapping + gamma (see "Complete Code Template - Image Pass" below)
const progBuf = createProgram(vsSource, fsBuffer);
const progImg = createProgram(vsSource, fsImage);

function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // Key: check float texture extension, fall back to RGBA8 if not supported
    // Path tracing accumulation needs high precision, but RGBA8 works too (with slight banding)
    const fmt = ext ? gl.RGBA16F : gl.RGBA;
    const typ = ext ? gl.FLOAT : gl.UNSIGNED_BYTE;
    gl.texImage2D(gl.TEXTURE_2D, 0, fmt, w, h, 0, gl.RGBA, typ, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fbo, tex };
}

let W, H, bufA, bufB;

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0);
gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

function resize() {
    canvas.width = W = innerWidth;
    canvas.height = H = innerHeight;
    bufA = createFBO(W, H);
    bufB = createFBO(W, H);
    frameCount = 0;
}
addEventListener('resize', resize);
resize();

canvas.addEventListener('mousedown', e => { mouse[2] = e.clientX; mouse[3] = H - e.clientY; });
canvas.addEventListener('mouseup', () => { mouse[2] = 0; mouse[3] = 0; });
canvas.addEventListener('mousemove', e => { mouse[0] = e.clientX; mouse[1] = H - e.clientY; });

function render(t) {
    t *= 0.001;
    // Buffer pass: read bufA (previous frame accumulation) -> write bufB (current frame accumulation)
    gl.useProgram(progBuf);
    gl.bindFramebuffer(gl.FRAMEBUFFER, bufB.fbo);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(gl.getUniformLocation(progBuf, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(progBuf, 'iResolution'), W, H);
    gl.uniform1f(gl.getUniformLocation(progBuf, 'iTime'), t);
    gl.uniform1i(gl.getUniformLocation(progBuf, 'iFrame'), frameCount);
    gl.uniform4f(gl.getUniformLocation(progBuf, 'iMouse'), ...mouse);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufA, bufB] = [bufB, bufA];

    // Image pass: read bufA (accumulated result) -> screen (tone mapped)
    gl.useProgram(progImg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(gl.getUniformLocation(progImg, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(progImg, 'iResolution'), W, H);
    gl.uniform1f(gl.getUniformLocation(progImg, 'iTime'), t);
    gl.uniform1i(gl.getUniformLocation(progImg, 'iFrame'), frameCount);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frameCount++;
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
</body>
</html>
```

# Path Tracing & Global Illumination

## Use Cases
- Physically accurate global illumination: indirect lighting, color bleeding, caustics
- Complex light transport with reflection, refraction, and diffuse interreflection
- Progressive high-quality rendering with multi-frame accumulation in ShaderToy
- Scenes requiring precise light interactions such as Cornell Box and glassware

## Core Principles

Path tracing solves the rendering equation via Monte Carlo methods. For each pixel, a ray is cast from the camera and bounced through the scene; at each bounce: intersect -> shade -> sample next direction -> accumulate contribution.

Core formulas:
- **Rendering equation**: $L_o = L_e + \int f_r \cdot L_i \cdot \cos\theta \, d\omega$
- **MC estimate**: $L \approx \frac{1}{N} \sum \frac{f_r \cdot L_i \cdot \cos\theta}{p(\omega)}$
- **Schlick Fresnel**: $F = F_0 + (1 - F_0)(1 - \cos\theta)^5$
- **Cosine-weighted PDF**: $p(\omega) = \cos\theta / \pi$

Use iterative loops instead of recursion: `acc` (accumulated radiance) and `throughput` (path attenuation) track path contributions.

## Implementation Steps

### Step 1: PRNG
```glsl
// Integer hash (recommended, good quality)
int iSeed;
int irand() { iSeed = iSeed * 0x343fd + 0x269ec3; return (iSeed >> 16) & 32767; }
float frand() { return float(irand()) / 32767.0; }
void srand(ivec2 p, int frame) {
    int n = frame;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.y;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.x;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    iSeed = n;
}

// Alternative: sin-hash (simpler)
float seed;
float rand() { return fract(sin(seed++) * 43758.5453123); }
```

### Step 2: Ray-Scene Intersection
```glsl
// Analytic sphere intersection
struct Ray { vec3 o, d; };
struct Sphere { float r; vec3 p, e, c; int refl; };

float iSphere(Sphere s, Ray r) {
    vec3 op = s.p - r.o;
    float b = dot(op, r.d);
    float det = b * b - dot(op, op) + s.r * s.r;
    if (det < 0.) return 0.;
    det = sqrt(det);
    float t = b - det;
    if (t > 1e-3) return t;
    t = b + det;
    return t > 1e-3 ? t : 0.;
}

// SDF ray marching (complex geometry)
float map(vec3 p) { /* return distance to nearest surface */ }
float raymarch(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 256; i++) {
        float h = map(ro + rd * t);
        if (abs(h) < 0.0001 || t > tmax) break;
        t += h;
    }
    return t;
}
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.0001, 0.);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)));
}
```

### Step 3: Cosine-Weighted Hemisphere Sampling
```glsl
// fizzer method (most concise)
vec3 cosineDirection(vec3 n) {
    float u = frand(), v = frand();
    float a = 6.2831853 * v;
    float b = 2.0 * u - 1.0;
    vec3 dir = vec3(sqrt(1.0 - b * b) * vec2(cos(a), sin(a)), b);
    return normalize(n + dir);
}

// ONB construction method (more intuitive)
vec3 cosineDirectionONB(vec3 n) {
    vec2 r = vec2(frand(), frand());
    vec3 u = normalize(cross(n, vec3(0., 1., 1.)));
    vec3 v = cross(u, n);
    float ra = sqrt(r.y);
    return normalize(ra * cos(6.2831853 * r.x) * u + ra * sin(6.2831853 * r.x) * v + sqrt(1.0 - r.y) * n);
}
```

### Step 4: Materials and BRDF
```glsl
#define MAT_DIFF 0
#define MAT_SPEC 1
#define MAT_REFR 2

// Diffuse: throughput *= albedo; dir = cosineDirection(nl)
// Specular: throughput *= albedo; dir = reflect(rd, n)

// Refraction (glass)
void handleDielectric(inout Ray r, vec3 n, vec3 x, float ior, vec3 albedo, inout vec3 mask) {
    float a = dot(n, r.d), ddn = abs(a);
    float nnt = mix(1.0 / ior, ior, float(a > 0.));
    float cos2t = 1. - nnt * nnt * (1. - ddn * ddn);
    r = Ray(x, reflect(r.d, n));
    if (cos2t > 0.) {
        vec3 tdir = normalize(r.d * nnt + sign(a) * n * (ddn * nnt + sqrt(cos2t)));
        float R0 = (ior - 1.) * (ior - 1.) / ((ior + 1.) * (ior + 1.));
        float c = 1. - mix(ddn, dot(tdir, n), float(a > 0.));
        float Re = R0 + (1. - R0) * c * c * c * c * c;
        float P = .25 + .5 * Re;
        if (frand() < P) { mask *= Re / P; }
        else { mask *= albedo * (1. - Re) / (1. - P); r = Ray(x, tdir); }
    }
}
```

### Step 5: Direct Light Sampling (NEE)
```glsl
// Spherical light solid angle sampling
vec3 coneSample(vec3 d, float phi, float sina, float cosa) {
    vec3 w = normalize(d);
    vec3 u = normalize(cross(w.yzx, w));
    vec3 v = cross(w, u);
    return (u * cos(phi) + v * sin(phi)) * sina + w * cosa;
}

// Called at diffuse shading points:
vec3 l0 = lightPos - x;
float cos_a_max = sqrt(1. - clamp(lightR * lightR / dot(l0, l0), 0., 1.));
float cosa = mix(cos_a_max, 1., frand());
vec3 l = coneSample(l0, 6.2831853 * frand(), sqrt(1. - cosa * cosa), cosa);
// After shadow test passes:
float omega = 6.2831853 * (1. - cos_a_max);
vec3 directLight = lightEmission * clamp(dot(l, nl), 0., 1.) * omega / PI;
```

### Step 6: Path Tracing Main Loop
```glsl
#define MAX_BOUNCES 8

vec3 pathtrace(Ray r) {
    vec3 acc = vec3(0.), throughput = vec3(1.);
    for (int depth = 0; depth < MAX_BOUNCES; depth++) {
        // 1. Intersect
        float t; vec3 n, albedo, emission; int matType;
        if (!intersectScene(r, t, n, albedo, emission, matType)) break;
        vec3 x = r.o + r.d * t;
        vec3 nl = dot(n, r.d) < 0. ? n : -n;

        // 2. Accumulate self-emission
        acc += throughput * emission;

        // 3. Russian roulette (starting from bounce 3)
        if (depth > 2) {
            float p = max(throughput.r, max(throughput.g, throughput.b));
            if (frand() > p) break;
            throughput /= p;
        }

        // 4. Material branching
        if (matType == MAT_DIFF) {
            acc += throughput * directLighting(x, nl, albedo, ...); // NEE
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, cosineDirection(nl));
        } else if (matType == MAT_SPEC) {
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, reflect(r.d, n));
        } else {
            handleDielectric(r, n, x, 1.5, albedo, throughput);
        }
    }
    return acc;
}
```

### Step 7: Progressive Accumulation and Display
```glsl
// Buffer A: path tracing + accumulation
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    srand(ivec2(fragCoord), iFrame);
    // ... camera setup, ray generation ...
    vec3 color = pathtrace(ray);
    vec4 prev = texelFetch(iChannel0, ivec2(fragCoord), 0);
    if (iFrame == 0) prev = vec4(0.);
    fragColor = prev + vec4(color, 1.0);
}

// Image Pass: ACES tone mapping + Gamma
vec3 ACES(vec3 x) {
    float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return (x * (a * x + b)) / (x * (c * x + d) + e);
}
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 data = texelFetch(iChannel0, ivec2(fragCoord), 0);
    vec3 col = data.rgb / max(data.a, 1.0);
    col = ACES(col);
    col = pow(clamp(col, 0., 1.), vec3(1.0 / 2.2));
    vec2 uv = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);
    fragColor = vec4(col, 1.0);
}
```

## Complete Code Template

ShaderToy dual pass: Buffer A (path tracing + accumulation, iChannel0=self), Image (display).

**Buffer A:**
```glsl
#define PI 3.14159265359
#define MAX_BOUNCES 6
#define SAMPLES_PER_FRAME 2
#define NUM_SPHERES 9
#define IOR_GLASS 1.5
#define ENABLE_NEE

#define MAT_DIFF 0
#define MAT_SPEC 1
#define MAT_REFR 2

int iSeed;
int irand() { iSeed = iSeed * 0x343fd + 0x269ec3; return (iSeed >> 16) & 32767; }
float frand() { return float(irand()) / 32767.0; }
void srand(ivec2 p, int frame) {
    int n = frame;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.y;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.x;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    iSeed = n;
}

struct Ray { vec3 o, d; };
struct Sphere { float r; vec3 p, e, c; int refl; };

Sphere spheres[NUM_SPHERES];
void initScene() {
    spheres[0] = Sphere(1e5,  vec3(-1e5+1., 40.8, 81.6),   vec3(0.),  vec3(.75,.25,.25), MAT_DIFF);
    spheres[1] = Sphere(1e5,  vec3( 1e5+99., 40.8, 81.6),  vec3(0.),  vec3(.25,.25,.75), MAT_DIFF);
    spheres[2] = Sphere(1e5,  vec3(50., 40.8, -1e5),        vec3(0.),  vec3(.75),         MAT_DIFF);
    spheres[3] = Sphere(1e5,  vec3(50., 40.8, 1e5+170.),    vec3(0.),  vec3(0.),          MAT_DIFF);
    spheres[4] = Sphere(1e5,  vec3(50., -1e5, 81.6),        vec3(0.),  vec3(.75),         MAT_DIFF);
    spheres[5] = Sphere(1e5,  vec3(50., 1e5+81.6, 81.6),    vec3(0.),  vec3(.75),         MAT_DIFF);
    spheres[6] = Sphere(16.5, vec3(27., 16.5, 47.),         vec3(0.),  vec3(1.),          MAT_SPEC);
    spheres[7] = Sphere(16.5, vec3(73., 16.5, 78.),         vec3(0.),  vec3(.7,1.,.9),    MAT_REFR);
    spheres[8] = Sphere(600., vec3(50., 681.33, 81.6),      vec3(12.), vec3(0.),           MAT_DIFF);
}

float iSphere(Sphere s, Ray r) {
    vec3 op = s.p - r.o;
    float b = dot(op, r.d);
    float det = b * b - dot(op, op) + s.r * s.r;
    if (det < 0.) return 0.;
    det = sqrt(det);
    float t = b - det;
    if (t > 1e-3) return t;
    t = b + det;
    return t > 1e-3 ? t : 0.;
}

int intersect(Ray r, out float t, out Sphere s, int avoid) {
    int id = -1; t = 1e5;
    for (int i = 0; i < NUM_SPHERES; ++i) {
        float d = iSphere(spheres[i], r);
        if (i != avoid && d > 0. && d < t) { t = d; id = i; s = spheres[i]; }
    }
    return id;
}

vec3 cosineDirection(vec3 n) {
    float u = frand(), v = frand();
    float a = 6.2831853 * v;
    float b = 2.0 * u - 1.0;
    vec3 dir = vec3(sqrt(1.0 - b * b) * vec2(cos(a), sin(a)), b);
    return normalize(n + dir);
}

vec3 coneSample(vec3 d, float phi, float sina, float cosa) {
    vec3 w = normalize(d);
    vec3 u = normalize(cross(w.yzx, w));
    vec3 v = cross(w, u);
    return (u * cos(phi) + v * sin(phi)) * sina + w * cosa;
}

vec3 radiance(Ray r) {
    vec3 acc = vec3(0.), mask = vec3(1.);
    int id = -1;
    for (int depth = 0; depth < MAX_BOUNCES; ++depth) {
        float t; Sphere obj;
        if ((id = intersect(r, t, obj, id)) < 0) break;
        vec3 x = r.o + r.d * t;
        vec3 n = normalize(x - obj.p);
        vec3 nl = n * sign(-dot(n, r.d));

        if (depth > 3) {
            float p = max(obj.c.r, max(obj.c.g, obj.c.b));
            if (frand() > p) { acc += mask * obj.e; break; }
            mask /= p;
        }

        if (obj.refl == MAT_DIFF) {
            vec3 d = cosineDirection(nl);
            vec3 e = vec3(0.);
            #ifdef ENABLE_NEE
            {
                Sphere ls = spheres[8];
                vec3 l0 = ls.p - x;
                float cos_a_max = sqrt(1. - clamp(ls.r * ls.r / dot(l0, l0), 0., 1.));
                float cosa = mix(cos_a_max, 1., frand());
                vec3 l = coneSample(l0, 6.2831853 * frand(), sqrt(1. - cosa * cosa), cosa);
                float st; Sphere dummy;
                if (intersect(Ray(x, l), st, dummy, id) == 8) {
                    float omega = 6.2831853 * (1. - cos_a_max);
                    e = ls.e * clamp(dot(l, nl), 0., 1.) * omega / PI;
                }
            }
            #endif
            acc += mask * obj.e + mask * obj.c * e;
            mask *= obj.c;
            r = Ray(x + nl * 1e-3, d);
        } else if (obj.refl == MAT_SPEC) {
            acc += mask * obj.e;
            mask *= obj.c;
            r = Ray(x + nl * 1e-3, reflect(r.d, n));
        } else {
            acc += mask * obj.e;
            float a = dot(n, r.d), ddn = abs(a);
            float nc = 1., nt = IOR_GLASS;
            float nnt = mix(nc / nt, nt / nc, float(a > 0.));
            float cos2t = 1. - nnt * nnt * (1. - ddn * ddn);
            r = Ray(x, reflect(r.d, n));
            if (cos2t > 0.) {
                vec3 tdir = normalize(r.d * nnt + sign(a) * n * (ddn * nnt + sqrt(cos2t)));
                float R0 = (nt - nc) * (nt - nc) / ((nt + nc) * (nt + nc));
                float c = 1. - mix(ddn, dot(tdir, n), float(a > 0.));
                float Re = R0 + (1. - R0) * c * c * c * c * c;
                float P = .25 + .5 * Re;
                if (frand() < P) { mask *= Re / P; }
                else { mask *= obj.c * (1. - Re) / (1. - P); r = Ray(x, tdir); }
            }
        }
    }
    return acc;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    initScene();
    srand(ivec2(fragCoord), iFrame);
    vec2 uv = 2. * fragCoord / iResolution.xy - 1.;
    vec3 camPos = vec3(50., 40.8, 169.);
    vec3 cz = normalize(vec3(50., 40., 81.6) - camPos);
    vec3 cx = vec3(1., 0., 0.);
    vec3 cy = normalize(cross(cx, cz));
    cx = cross(cz, cy);
    vec3 color = vec3(0.);
    for (int i = 0; i < SAMPLES_PER_FRAME; i++) {
        vec2 jitter = vec2(frand(), frand()) - 0.5;
        vec2 suv = uv + jitter * 2.0 / iResolution.xy;
        float fov = 0.53135;
        vec3 rd = normalize(fov * (iResolution.x / iResolution.y * suv.x * cx + suv.y * cy) + cz);
        color += radiance(Ray(camPos, rd));
    }
    vec4 prev = texelFetch(iChannel0, ivec2(fragCoord), 0);
    if (iFrame == 0) prev = vec4(0.);
    fragColor = prev + vec4(color, float(SAMPLES_PER_FRAME));
}
```

**Image Pass** (iChannel0 = Buffer A):
```glsl
vec3 ACES(vec3 x) {
    float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return (x * (a * x + b)) / (x * (c * x + d) + e);
}
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 data = texelFetch(iChannel0, ivec2(fragCoord), 0);
    vec3 col = data.rgb / max(data.a, 1.0);
    col = ACES(col);
    col = pow(clamp(col, 0., 1.), vec3(1.0 / 2.2));
    vec2 uv = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### 1. SDF Scene Path Tracing
```glsl
float map(vec3 p) {
    float d = p.y + 0.5;
    d = min(d, length(p - vec3(0., 0.4, 0.)) - 0.4);
    return d;
}
float intersectScene(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 128; i++) {
        float h = map(ro + rd * t);
        if (h < 0.0001 || t > tmax) break;
        t += h;
    }
    return t < tmax ? t : -1.0;
}
```

### 2. Disney BRDF Path Tracing
```glsl
struct Material { vec3 albedo; float metallic, roughness; };

float D_GGX(float a2, float NoH) {
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}
float G_Smith(float NoV, float NoL, float a2) {
    float g1 = (2.0 * NoV) / (NoV + sqrt(a2 + (1.0 - a2) * NoV * NoV));
    float g2 = (2.0 * NoL) / (NoL + sqrt(a2 + (1.0 - a2) * NoL * NoL));
    return g1 * g2;
}
vec3 SampleGGXVNDF(vec3 V, float ax, float ay, float r1, float r2) {
    vec3 Vh = normalize(vec3(ax * V.x, ay * V.y, V.z));
    float lensq = Vh.x * Vh.x + Vh.y * Vh.y;
    vec3 T1 = lensq > 0. ? vec3(-Vh.y, Vh.x, 0) * inversesqrt(lensq) : vec3(1, 0, 0);
    vec3 T2 = cross(Vh, T1);
    float r = sqrt(r1), phi = 2.0 * PI * r2;
    float t1 = r * cos(phi), t2 = r * sin(phi);
    float s = 0.5 * (1.0 + Vh.z);
    t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;
    vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0., 1. - t1*t1 - t2*t2)) * Vh;
    return normalize(vec3(ax * Nh.x, ay * Nh.y, max(0., Nh.z)));
}
```

### 3. Depth of Field
```glsl
#define APERTURE 0.12
#define FOCUS_DIST 8.0

vec2 uniformDisk() {
    vec2 r = vec2(frand(), frand());
    return sqrt(r.y) * vec2(cos(6.2831853 * r.x), sin(6.2831853 * r.x));
}
// After generating the ray:
vec3 focalPoint = ro + rd * FOCUS_DIST;
vec3 offset = ca * vec3(uniformDisk() * APERTURE, 0.);
ro += offset;
rd = normalize(focalPoint - ro);
```

### 4. MIS (Multiple Importance Sampling)
```glsl
float misWeight(float pdfA, float pdfB) {
    float a2 = pdfA * pdfA, b2 = pdfB * pdfB;
    return a2 / (a2 + b2);
}
// BRDF sample hits light -> misWeight(brdfPdf, lightPdf)
// Light sample -> misWeight(lightPdf, brdfPdf)
```

### 5. Volumetric Path Tracing (Participating Media)
```glsl
vec3 transmittance = exp(-extinction * distance);
float scatterDist = -log(frand()) / extinctionMajorant;
if (scatterDist < hitDist) {
    pos += ray.d * scatterDist;
    ray.d = uniformSphereSample(); // or Henyey-Greenstein
    throughput *= albedo;
}
```

## Performance & Composition

- 1-4 spp per frame + inter-frame accumulation for convergence; Russian roulette from bounce 3-4, survival probability = max throughput component
- NEE significantly accelerates small light sources; offset along normal by 1e-3~1e-4 or record hit ID to prevent self-intersection
- `min(color, 10.)` to prevent fireflies; SDF limited to 128-256 steps + reasonable tmax; integer hash preferred over sin-hash
- **Composition**: SDF modeling / HDR environment maps / Disney BRDF (GGX+VNDF) / volume rendering (Beer-Lambert) / spectral rendering (Sellmeier+CIE XYZ) / TAA (temporal reprojection)

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/path-tracing-gi.md)
