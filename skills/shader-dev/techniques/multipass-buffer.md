### Standalone HTML Complete Shader Template (Must Be Strictly Followed)

**IMPORTANT: The following template can be copied directly; every line must be strictly followed**:

**Vertex Shader** (common to all shaders):
```glsl
#version 300 es
in vec4 iPosition;
void main() {
    gl_Position = iPosition;
}
```

**Fragment Shader Buffer A Example** (particle physics simulation):
```glsl
#version 300 es
precision highp float;

// IMPORTANT: Critical: uniforms must be declared; ShaderToy's iTime/iResolution etc. are global variables
uniform float iTime;
uniform vec2 iResolution;
uniform int iFrame;
uniform vec4 iMouse;

// IMPORTANT: Critical: mainImage parameters need manual extraction
// ShaderToy: void mainImage(out vec4 fragColor, in vec2 fragCoord)
// Adapted to:
out vec4 fragColor;
void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord / iResolution;

    // IMPORTANT: Critical: texture2D → texture
    vec4 prev = texture(iChannel0, uv);

    // ... particle physics logic ...

    fragColor = vec4(pos, vel);
}
```

**Fragment Shader Image Example**:
```glsl
#version 300 es
precision highp float;

uniform float iTime;
uniform vec2 iResolution;
uniform int iFrame;
uniform vec4 iMouse;
uniform sampler2D iChannel0;

out vec4 fragColor;

void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord / iResolution;

    // IMPORTANT: Critical: texture2D → texture, mainImage → standard main
    vec4 col = texture(iChannel0, uv);

    // Rendering logic
    col = col / (1.0 + col);  // Tone mapping

    fragColor = col;
}
```

**IMPORTANT: Common GLSL ES 3.00 Errors** (must be avoided):
1. **#version must be on the first line** - Any comments/blank lines will cause "version directive must occur on the first line" error
2. **in/out qualifiers** - WebGL1's attribute/varying must be changed to in/out in ES3
3. **texture function** - ES3 uses `texture(sampler, uv)`, not `texture2D(sampler, uv)`
4. **Type strictness** - `vec4 = float` is illegal, must use `vec4(v, v, v, v)` or `vec4(v)` or `vec4(vec3(v), 1.0)`

## Standalone HTML Multi-Channel Framebuffer Implementation

**IMPORTANT: Multi-Channel Rendering Pipeline Core Pitfalls**: ShaderToy code requires manual Framebuffer rendering pipeline implementation. The following template demonstrates the correct approach:

```javascript
// Correct multi-channel Framebuffer creation
const NUM_BUFFERS = 2;  // Buffer A, Buffer B
const buffers = [];
const textures = [];

// Check float texture linear filtering extension
const ext = gl.getExtension('EXT_color_buffer_float');
const floatLinear = gl.getExtension('OES_texture_float_linear');

// Each Buffer needs an independent Framebuffer + texture
for (let i = 0; i < NUM_BUFFERS; i++) {
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);

    // IMPORTANT: Critical: Must use UNSIGNED_BYTE format without EXT_color_buffer_float extension!
    // RGBA16F/RGBA32F require the extension, otherwise GL_INVALID_OPERATION
    // Float textures need EXT_color_buffer_float; RGBA16F supports HDR data
    if (ext) {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, width, height, 0, gl.RGBA, gl.FLOAT, null);
    } else {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    }

    // IMPORTANT: Critical: Texture parameters must be set, otherwise GL_INVALID_FRAMEBUFFER
    // IMPORTANT: Float textures use NEAREST, or require OES_texture_float_linear extension for LINEAR
    // IMPORTANT: Critical: Float textures must use CLAMP_TO_EDGE wrap mode; REPEAT is not supported for float textures
    // IMPORTANT: Critical: Must fall back to UNSIGNED_BYTE format without EXT_color_buffer_float extension
    const filterMode = (ext && floatLinear) ? gl.LINEAR : gl.NEAREST;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filterMode);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filterMode);
    // IMPORTANT: Must use CLAMP_TO_EDGE: float textures do not support REPEAT
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);

    // IMPORTANT: Critical: Check Framebuffer completeness
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) {
        console.error("Framebuffer incomplete:", status);
    }

    textures.push(texture);
    buffers.push(fbo);
}
gl.bindFramebuffer(gl.FRAMEBUFFER, null);

// Render loop: render to Buffer first, then render to screen
function render() {
    // 1. Render to Buffer A (self-feedback reads previous Buffer)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.viewport(0, 0, width, height);
    // Bind previous frame texture to iChannel0
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);  // Read from other Buffer
    // Set uniforms etc...
    // Execute shader rendering

    // 2. Swap Buffers (simulate self-feedback)
    // IMPORTANT: Critical: Must swap textures for next frame reading; FBO handles remain unchanged
    [textures[0], textures[1]] = [textures[1], textures[0]];

    // 3. Render to screen
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    // Bind Buffer result to texture
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);
    // Execute Image pass shader
}
```

**IMPORTANT: Common Errors** (JavaScript/WebGL side):
1. **Missing texture parameters** - Must set `TEXTURE_MIN_FILTER`, `TEXTURE_MAG_FILTER`, `TEXTURE_WRAP_S/T`
2. **Missing Framebuffer completeness check** - `gl.checkFramebufferStatus()` must return `FRAMEBUFFER_COMPLETE` before use
3. **Float texture extension** - `gl.RGBA16F` requires `EXT_color_buffer_float` extension, otherwise fall back to `gl.UNSIGNED_BYTE`
4. **Buffer ping-pong error** - Self-feedback must use 2 independent FBOs alternating read/write; a single FBO + texture swap causes "Feedback loop" error
5. **Particle system empty texture initialization** - Textures are empty before the first frame; shaders reading default values cause render failure — must execute initPass() to pre-render

# Multi-Pass Buffer Techniques

## Use Cases

When single-frame computation cannot achieve the desired effect and cross-frame data persistence or multi-stage processing pipelines are needed, use multi-pass buffers:

- **Temporal accumulation**: Motion blur, TAA, progressive rendering
- **Physics simulation**: Fluids, reaction-diffusion, particle systems
- **Persistent state**: Game state, particle positions/velocities, interaction history
- **Deferred rendering**: G-Buffer → post-processing → compositing
- **Post-processing chains**: HDR Bloom (downsample → blur → composite)
- **Iterative solvers**: Poisson solver, vorticity confinement, multi-scale computation

## Core Principles

Multi-pass buffers split the rendering pipeline into multiple Buffers, each outputting a texture as input for the next stage.

### Self-Feedback
A Buffer reads its own previous frame output, achieving cross-frame state persistence: `x(n+1) = f(x(n))`
```
Buffer A (frame N) reads → Buffer A (frame N-1) output
```

### Pipeline Chaining
Multiple Buffers process in sequence:
```
Buffer A (geometry) → Buffer B (blur H) → Buffer C (blur V) → Image (compositing)
```

### Structured Data Storage
Specific pixels serve as data registers, read precisely via `texelFetch`:
```
texel (0,0) = ball position+velocity (vec4)
texel (1,0) = paddle position
texel (x,1)-(x,12) = brick grid state
```

### Key Mathematical Patterns

- **Fluid self-advection**: `newPos = texture(buf, uv - dt * velocity * texelSize)`
- **Gaussian blur**: `sum += texture(buf, uv + offset_i) * weight_i`
- **Temporal blending**: `result = mix(newFrame, prevFrame, blendWeight)`
- **Vorticity confinement**: `vortForce = curl × normalize(gradient(|curl|))`

## Implementation Steps

### Step 1: Minimal Self-Feedback Loop

Buffer A (iChannel0 → Buffer A self-feedback):
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    vec4 prev = texture(iChannel0, uv);

    // New content: procedural noise contour lines
    float n = noise(vec3(uv * 8.0, 0.1 * iTime));
    float v = sin(6.2832 * 10.0 * n);
    v = smoothstep(1.0, 0.0, 0.5 * abs(v) / fwidth(v));
    vec4 newContent = 0.5 + 0.5 * sin(12.0 * n + vec4(0, 2.1, -2.1, 0));

    // Decay + offset blending
    vec4 decayed = exp(-33.0 / iResolution.y) * texture(iChannel0, (fragCoord + vec2(1.0, sin(iTime))) / iResolution.xy);
    fragColor = mix(decayed, newContent, v);

    // Initialization guard
    if (iFrame < 4) fragColor = vec4(0.5);
}
```

Image (iChannel0 → Buffer A):
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    fragColor = texture(iChannel0, fragCoord / iResolution.xy);
}
```

### Step 2: Fluid Self-Advection

Buffer A (iChannel0 → Buffer A self-feedback):
```glsl
#define ROT_NUM 5
#define SCALE_NUM 20

const float ang = 6.2832 / float(ROT_NUM);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

float getRot(vec2 pos, vec2 b) {
    vec2 p = b;
    float rot = 0.0;
    for (int i = 0; i < ROT_NUM; i++) {
        rot += dot(texture(iChannel0, fract((pos + p) / iResolution.xy)).xy - vec2(0.5),
                   p.yx * vec2(1, -1));
        p = m * p;
    }
    return rot / float(ROT_NUM) / dot(b, b);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pos = fragCoord;
    float rnd = fract(sin(float(iFrame) * 12.9898) * 43758.5453);
    vec2 b = vec2(cos(ang * rnd), sin(ang * rnd));

    // Multi-scale rotation sampling
    vec2 v = vec2(0);
    float bbMax = 0.7 * iResolution.y;
    bbMax *= bbMax;
    for (int l = 0; l < SCALE_NUM; l++) {
        if (dot(b, b) > bbMax) break;
        vec2 p = b;
        for (int i = 0; i < ROT_NUM; i++) {
            v += p.yx * getRot(pos + p, b);
            p = m * p;
        }
        b *= 2.0;
    }

    // Self-advection
    fragColor = texture(iChannel0, fract((pos + v * vec2(-1, 1) * 2.0) / iResolution.xy));

    // Center driving force
    vec2 scr = (fragCoord / iResolution.xy) * 2.0 - 1.0;
    fragColor.xy += 0.01 * scr / (dot(scr, scr) / 0.1 + 0.3);

    if (iFrame <= 4) fragColor = texture(iChannel1, fragCoord / iResolution.xy);
}
```

### Step 3-4: Navier-Stokes Solver + Chained Acceleration

Buffer A / B / C use identical code (via Common tab's `solveFluid`):
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec4 data = solveFluid(iChannel0, uv, w, iTime, iMouse.xyz, lastMouse.xyz);

    if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
    if (fragCoord.y < 1.0) data = iMouse;  // Mouse state storage

    fragColor = data;
}
```

iChannel bindings: A→C(prev frame), B→A, C→B — 3 iterations per frame.

### Step 5: Separable Gaussian Blur

Buffer B (horizontal, iChannel0 → source Buffer) — Buffer C vertical direction is analogous, using y-axis offset:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pixelSize = 1.0 / iResolution.xy;
    vec2 uv = fragCoord * pixelSize;
    float h = pixelSize.x;
    vec4 sum = vec4(0.0);
    // 9-tap Gaussian (sigma ≈ 2.0)
    sum += texture(iChannel0, fract(vec2(uv.x - 4.0*h, uv.y))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x - 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x - 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x - 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x,          uv.y))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x + 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x + 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x + 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x + 4.0*h, uv.y))) * 0.05;
    fragColor = vec4(sum.xyz / 0.98, 1.0);
}
```

### Step 6: Structured State Storage

```glsl
// Register address definitions
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);
const ivec4 txBricks     = ivec4(0, 1, 13, 12);

vec4 loadValue(ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

void storeValue(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 currentPixel) {
    fragColor = (currentPixel == addr) ? val : fragColor;
}

void storeValue(ivec4 rect, vec4 val, inout vec4 fragColor, ivec2 currentPixel) {
    fragColor = (currentPixel.x >= rect.x && currentPixel.y >= rect.y &&
                 currentPixel.x <= rect.z && currentPixel.y <= rect.w) ? val : fragColor;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 px = ivec2(fragCoord - 0.5);
    if (fragCoord.x > 14.0 || fragCoord.y > 14.0) discard;

    vec4 ballPosVel = loadValue(txBallPosVel);
    float paddlePos = loadValue(txPaddlePos).x;
    float points = loadValue(txPoints).x;

    if (iFrame == 0) {
        ballPosVel = vec4(0.0, -0.8, 0.6, 1.0);
        paddlePos = 0.0;
        points = 0.0;
    }

    // ... game logic update ...

    fragColor = loadValue(px);
    storeValue(txBallPosVel, ballPosVel, fragColor, px);
    storeValue(txPaddlePos, vec4(paddlePos, 0, 0, 0), fragColor, px);
    storeValue(txPoints, vec4(points, 0, 0, 0), fragColor, px);
}
```

### Step 7: Mouse State Inter-Frame Tracking

```glsl
// Method 1: First-row pixel storage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    // ... simulation logic ...
    if (fragCoord.y < 1.0) fragColor = iMouse;
}

// Method 2: Fixed UV region storage
vec2 mouseDelta() {
    vec2 pixelSize = 1.0 / iResolution.xy;
    float eighth = 1.0 / 8.0;
    vec4 oldMouse = texture(iChannel2, vec2(7.5 * eighth, 2.5 * eighth));
    vec4 nowMouse = vec4(iMouse.xy / iResolution.xy, iMouse.zw / iResolution.xy);
    if (oldMouse.z > pixelSize.x && oldMouse.w > pixelSize.y &&
        nowMouse.z > pixelSize.x && nowMouse.w > pixelSize.y) {
        return nowMouse.xy - oldMouse.xy;
    }
    return vec2(0.0);
}
```

## Complete Code Template

A fully runnable fluid simulation shader (self-feedback + vorticity confinement + mouse interaction + color advection).

### Common tab

```glsl
#define DT 0.15
#define VORTICITY_AMOUNT 0.11
#define VISCOSITY 0.55
#define PRESSURE_K 0.2
#define FORCE_RADIUS 0.001
#define FORCE_STRENGTH 0.001
#define VELOCITY_DECAY 1e-4

float mag2(vec2 p) { return dot(p, p); }

vec2 emitter1(float t) { t *= 0.62; return vec2(0.12, 0.5 + sin(t) * 0.2); }
vec2 emitter2(float t) { t *= 0.62; return vec2(0.88, 0.5 + cos(t + 1.5708) * 0.2); }

vec4 solveFluid(sampler2D smp, vec2 uv, vec2 w, float time, vec3 mouse, vec3 lastMouse) {
    vec4 data = textureLod(smp, uv, 0.0);
    vec4 tr = textureLod(smp, uv + vec2(w.x, 0), 0.0);
    vec4 tl = textureLod(smp, uv - vec2(w.x, 0), 0.0);
    vec4 tu = textureLod(smp, uv + vec2(0, w.y), 0.0);
    vec4 td = textureLod(smp, uv - vec2(0, w.y), 0.0);

    vec3 dx = (tr.xyz - tl.xyz) * 0.5;
    vec3 dy = (tu.xyz - td.xyz) * 0.5;
    vec2 densDif = vec2(dx.z, dy.z);

    data.z -= DT * dot(vec3(densDif, dx.x + dy.y), data.xyz);

    vec2 laplacian = tu.xy + td.xy + tr.xy + tl.xy - 4.0 * data.xy;
    vec2 viscForce = vec2(VISCOSITY) * laplacian;

    data.xyw = textureLod(smp, uv - DT * data.xy * w, 0.0).xyw;

    vec2 newForce = vec2(0);
    newForce += 0.75 * vec2(0.0003, 0.00015) / (mag2(uv - emitter1(time)) + 0.0001);
    newForce -= 0.75 * vec2(0.0003, 0.00015) / (mag2(uv - emitter2(time)) + 0.0001);

    if (mouse.z > 1.0 && lastMouse.z > 1.0) {
        vec2 vv = clamp((mouse.xy * w - lastMouse.xy * w) * 400.0, -6.0, 6.0);
        newForce += FORCE_STRENGTH / (mag2(uv - mouse.xy * w) + FORCE_RADIUS) * vv;
    }

    data.xy += DT * (viscForce - PRESSURE_K / DT * densDif + newForce);
    data.xy = max(vec2(0), abs(data.xy) - VELOCITY_DECAY) * sign(data.xy);

    data.w = (tr.y - tl.y - tu.x + td.x);
    vec2 vort = vec2(abs(tu.w) - abs(td.w), abs(tl.w) - abs(tr.w));
    vort *= VORTICITY_AMOUNT / length(vort + 1e-9) * data.w;
    data.xy += vort;

    data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    data = clamp(data, vec4(vec2(-10), 0.5, -10.0), vec4(vec2(10), 3.0, 10.0));

    return data;
}
```

### Buffer A / B / C (Fluid Sub-Steps 1/2/3)

iChannel bindings: A←C(prev frame), B←A, C←B

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec4 data = solveFluid(iChannel0, uv, w, iTime, iMouse.xyz, lastMouse.xyz);
    if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
    if (fragCoord.y < 1.0) data = iMouse;
    fragColor = data;
}
```

### Buffer D (Color Advection, iChannel0 → Buffer C, iChannel1 → Buffer D self-feedback)

```glsl
#define COLOR_DECAY 0.004
#define COLOR_ADVECT_SCALE 3.0

vec3 getPalette(float x, vec3 c1, vec3 c2, vec3 p1, vec3 p2) {
    float x2 = fract(x / 2.0);
    x = fract(x);
    mat3 m = mat3(c1, p1, c2);
    mat3 m2 = mat3(c2, p2, c1);
    float omx = 1.0 - x;
    vec3 pws = vec3(omx * omx, 2.0 * omx * x, x * x);
    return clamp(mix(m * pws, m2 * pws, step(x2, 0.5)), 0.0, 1.0);
}

vec4 palette1(float x) {
    return vec4(getPalette(-x, vec3(0.2, 0.5, 0.7), vec3(0.9, 0.4, 0.1),
                vec3(1.0, 1.2, 0.5), vec3(1.0, -0.4, 0.0)), 1.0);
}
vec4 palette2(float x) {
    return vec4(getPalette(-x, vec3(0.4, 0.3, 0.5), vec3(0.9, 0.75, 0.4),
                vec3(0.1, 0.8, 1.3), vec3(1.25, -0.1, 0.1)), 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec2 velo = textureLod(iChannel0, uv, 0.0).xy;
    vec4 col = textureLod(iChannel1, uv - DT * velo * w * COLOR_ADVECT_SCALE, 0.0);

    vec2 mo = iMouse.xy / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel1, ivec2(0, 0), 0);
    if (iMouse.z > 1.0 && lastMouse.z > 1.0) {
        float str = smoothstep(-0.5, 1.0, length(mo - lastMouse.xy / iResolution.xy));
        col += str * 0.0009 / (pow(length(uv - mo), 1.7) + 0.002) * palette2(-iTime * 0.7);
    }

    col += 0.0025 / (0.0005 + pow(length(uv - emitter1(iTime)), 1.75)) * DT * 0.12 * palette1(iTime * 0.05);
    col += 0.0025 / (0.0005 + pow(length(uv - emitter2(iTime)), 1.75)) * DT * 0.12 * palette2(iTime * 0.05 + 0.675);

    if (iFrame < 20) col = vec4(0.0);
    col = clamp(col, 0.0, 5.0);
    col = max(col - (0.0001 + col * COLOR_DECAY) * 0.5, 0.0);

    if (fragCoord.y < 1.0 && fragCoord.x < 1.0) col = iMouse;
    fragColor = col;
}
```

### Image (iChannel0 → Buffer D)

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 col = textureLod(iChannel0, fragCoord / iResolution.xy, 0.0);
    if (fragCoord.y < 1.0 || fragCoord.y >= iResolution.y - 1.0) col = vec4(0);
    fragColor = col;
}
```

## Common Variants

### Variant 1: TAA Temporal Accumulation Anti-Aliasing

```glsl
// Buffer A: Sub-pixel jittered rendering
vec2 jitter = vec2(rand(uv + sin(iTime)), rand(uv + 1.0 + sin(iTime))) / iResolution.xy;
vec3 eyevec = normalize(vec3(((uv + jitter) * 2.0 - 1.0) * vec2(aspect, 1.0), fov));
float blendWeight = 0.9;
color = mix(color, texture(iChannel_self, uv).rgb, blendWeight);

// Buffer C (TAA): YCoCg neighborhood clamping to prevent ghosting
vec3 newYCC = RGBToYCoCg(newFrame);
vec3 histYCC = RGBToYCoCg(history);
vec3 colorAvg = ...; vec3 colorVar = ...;
vec3 sigma = sqrt(max(vec3(0), colorVar - colorAvg * colorAvg));
histYCC = clamp(histYCC, colorAvg - 0.75 * sigma, colorAvg + 0.75 * sigma);
result = YCoCgToRGB(mix(newYCC, histYCC, 0.95));
```

### Variant 2: Deferred Rendering G-Buffer

```glsl
// Buffer A: G-Buffer output
col.xy = (normal * camMat * 0.5 + 0.5).xy;  // Normal
col.z = 1.0 - abs((t * rd) * camMat).z / DMAX;  // Depth
col.w = dot(lightDir, nor) * 0.5 + 0.5;  // Diffuse

// Buffer B: Edge detection
float checkSame(vec4 center, vec4 sample) {
    vec2 diffNormal = abs(center.xy - sample.xy) * Sensitivity.x;
    float diffDepth = abs(center.z - sample.z) * Sensitivity.y;
    return (diffNormal.x + diffNormal.y < 0.1 && diffDepth < 0.1) ? 1.0 : 0.0;
}
```

### Variant 3: HDR Bloom

```glsl
// Buffer B: MIP pyramid (multi-level downsampling packed into one texture)
vec2 CalcOffset(float octave) {
    vec2 offset = vec2(0);
    vec2 padding = vec2(10.0) / iResolution.xy;
    offset.x = -min(1.0, floor(octave / 3.0)) * (0.25 + padding.x);
    offset.y = -(1.0 - 1.0 / exp2(octave)) - padding.y * octave;
    offset.y += min(1.0, floor(octave / 3.0)) * 0.35;
    return offset;
}
// Image: Accumulate multi-level bloom + Reinhard tone mapping
bloom += Grab(coord, 1.0, CalcOffset(0.0)) * 1.0;
bloom += Grab(coord, 2.0, CalcOffset(1.0)) * 1.5;
color = pow(color, vec3(1.5));
color = color / (1.0 + color);
```

### Variant 4: Reaction-Diffusion System

```glsl
// Buffer A: Gray-Scott reaction-diffusion
vec2 uv_red = uv + vec2(dx.x, dy.x) * pixelSize * 8.0;
float new_val = texture(iChannel0, fract(uv_red)).x;
new_val += (noise.x - 0.5) * 0.0025 - 0.002;
new_val -= (texture(iChannel_blur, fract(uv_red)).x -
            texture(iChannel_self, fract(uv_red)).x) * 0.047;
```

### Variant 5: Multi-Scale MIP Fluid

```glsl
for (int i = 0; i < NUM_SCALES; i++) {
    float mip = float(i);
    float stride = float(1 << i);
    vec4 t = stride * vec4(texel, -texel.y, 0);
    vec2 d = textureLod(sampler, fract(uv + t.ww), mip).xy;
    float w = WEIGHT_FUNCTION;
    result += w * computation(neighbors);
}
```

### Variant 6: Particle System (Position-Velocity Storage)

**IMPORTANT: Particle System Implementation Key**: Particle state is stored in texture pixels, one particle per pixel. Rendering must iterate over the particle texture for sampling.

**Buffer A (Particle Physics Simulation)**:
```glsl
// Each texture pixel stores one particle: xy=position, zw=velocity

// IMPORTANT: Critical: hash function must return vec2! Returning float causes type mismatch errors
vec2 hash2(vec2 p) {
    return fract(sin(mat2(127.1, 311.7, 269.5, 183.3) * p) * 43758.5453);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 prev = texture(iChannel0, uv);

    vec2 pos = prev.xy;
    vec2 vel = prev.zw;

    // IMPORTANT: Initialization guard: use integer comparison + pixel-coordinate-based random (avoids particle overlap when time is too small)
    if (iFrame < 3) {
        // Use fragCoord (pixel coordinates) to ensure each particle has a unique position, independent of time
        // IMPORTANT: Critical: hash2 returns vec2, assign directly to pos/vel
        pos = hash2(fragCoord * 0.01 + vec2(1.7, 9.3));
        vel = (hash2(fragCoord * 0.01 + vec2(5.3, 2.8)) - 0.5) * 0.02;
        fragColor = vec4(pos, vel);
        return;
    }

    // Physics update
    vel *= 0.98;  // Damping

    // Mouse interaction
    vec2 mouse = iMouse.xy / iResolution.xy;
    if (iMouse.z > 0.0) {
        vec2 toMouse = mouse - pos;
        vel += normalize(toMouse + 0.001) * 0.0005 / (length(toMouse) + 0.1);
    }

    // Motion
    pos += vel * 60.0 * 0.016;
    pos = fract(pos);  // Boundary wrapping

    fragColor = vec4(pos, vel);
}
```

**Image (Render Particles)**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec3 color = vec3(0.02, 0.02, 0.05);  // Dark background

    // Iterate over particle texture for sampling (performance-sensitive, balance sample count)
    float glow = 0.0;
    for (float y = 0.0; y < 1.0; y += 0.02) {  // IMPORTANT: Step size determines sampling density
        for (float x = 0.0; x < 1.0; x += 0.02) {
            vec4 particle = texture(iChannel0, vec2(x, y));
            vec2 pPos = particle.xy;
            float dist = length(uv - pPos);
            float size = 0.01 + length(particle.zw) * 0.3;
            glow += exp(-dist * dist / (size * size)) * 0.15;
        }
    }

    // Particle glow
    color += vec3(0.3, 0.6, 1.0) * glow;

    // Vignette
    color *= 1.0 - length(uv - 0.5) * 0.8;

    // Tone mapping
    color = color / (1.0 + color);

    fragColor = vec4(color, 1.0);
}
```

**Key Points**:
- Buffer A self-feedback: iChannel0 → Buffer A
- Image reads: iChannel0 → Buffer A (particle state)
- Step size 0.02 produces 2500 samples; adjust based on performance
- Particle size varies with velocity: `size = 0.01 + length(vel) * 0.3`

**Complete JavaScript Rendering Pipeline (Particle System 3-Pass)**:
```javascript
// Particle system needs 4 Framebuffers (2 each for Buffer A and Buffer B ping-pong) + screen output
// Buffer A: Particle physics (self-feedback) - uses FBO 0/1 ping-pong
// Buffer B: Density accumulation (reads Buffer A) - uses FBO 2/3 ping-pong
// Image: Final rendering (reads Buffer A + Buffer B)

// IMPORTANT: Critical: Must use 2 FBOs for ping-pong! Single FBO + texture swap causes
// "Feedback loop formed between Framebuffer and active Texture" error
const buffers = [null, null, null, null];  // [A_FBO0, A_FBO1, B_FBO0, B_FBO1]
const textures = [null, null, null, null];  // [A_tex0, A_tex1, B_tex0, B_tex1]

function createBuffers() {
    // Buffer A: 2 FBOs for ping-pong
    for (let i = 0; i < 2; i++) {
        const tex = createTexture();
        textures[i] = tex;

        const fbo = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
        buffers[i] = fbo;
    }
    // Buffer B: 2 FBOs for ping-pong
    for (let i = 0; i < 2; i++) {
        const tex = createTexture();
        textures[2 + i] = tex;

        const fbo = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
        buffers[2 + i] = fbo;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}

// IMPORTANT: Critical: Initialization pre-rendering - must execute before the first frame!
// Empty textures cause particle initialization failure (reading 0,0,0,0 makes all particles overlap)
let aReadIdx = 0;  // Current read FBO index (0 or 1)
let bReadIdx = 0;  // Buffer B current read FBO index (0 or 1)

function initPass() {
    // ===== Buffer A Initialization =====
    // Render first frame using FBO 0
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.viewport(0, 0, width, height);
    gl.useProgram(programBufferA);
    setupAttribute(programBufferA);
    // Bind FBO 1's texture as input (not yet rendered, but avoids binding errors)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(programBufferA, 'iResolution'), width, height);
    gl.uniform1f(gl.getUniformLocation(programBufferA, 'iTime'), 0);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 0);
    gl.uniform4f(gl.getUniformLocation(programBufferA, 'iMouse'), 0, 0, 0, 0);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Render second frame using FBO 1 (iFrame=1)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[1]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);  // Read FBO 0's result
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 1);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Render one more frame to ensure initialization is complete
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 2);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // ===== Buffer B Initialization =====
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[2]);  // B_FBO0
    gl.viewport(0, 0, width, height);
    gl.useProgram(programBufferB);
    setupAttribute(programBufferB);

    // Bind latest Buffer A result (FBO 0's result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iChannel0'), 0);

    // Bind Buffer B previous frame (FBO 3's texture, not yet rendered)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[3]);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iChannel1'), 1);

    gl.uniform2f(gl.getUniformLocation(programBufferB, 'iResolution'), width, height);
    gl.uniform1f(gl.getUniformLocation(programBufferB, 'iTime'), 0);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iFrame'), 0);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Buffer B second frame
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[3]);  // B_FBO1
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);  // Buffer A latest
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2]);  // Buffer B FBO0 result
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iFrame'), 1);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Initialize ping-pong indices
    aReadIdx = 0;  // Next frame reads FBO 0
    bReadIdx = 0;  // Next frame reads FBO 2

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}

function render() {
    // ===== Pass 1: Buffer A (Particle Physics Self-Feedback) =====
    // aReadIdx = 0: read FBO 0, write FBO 1
    // aReadIdx = 1: read FBO 1, write FBO 0
    const aWriteIdx = 1 - aReadIdx;

    // Write to target FBO (not the current read FBO)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[aWriteIdx]);
    gl.viewport(0, 0, width, height);

    // Read previous frame Buffer A texture (from current read FBO's texture)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);
    gl.uniform1i(uniformsBufferA.iChannel0, 0);

    gl.uniform2f(uniformsBufferA.iResolution, width, height);
    gl.uniform1f(uniformsBufferA.iTime, time);
    gl.uniform1i(uniformsBufferA.iFrame, frameCount);
    gl.uniform4f(uniformsBufferA.iMouse, mouse.x, mouse.y, mouse.z, mouse.w);

    // Render particle physics
    gl.useProgram(programBufferA);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Switch read index
    aReadIdx = aWriteIdx;

    // ===== Pass 2: Buffer B (Density Field) =====
    const bWriteIdx = 1 - bReadIdx;

    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[2 + bWriteIdx]);  // B_FBO0 or B_FBO1
    gl.viewport(0, 0, width, height);

    // Bind current Buffer A particle state (use latest Buffer A result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);  // A latest result
    gl.uniform1i(uniformsBufferB.iChannel0, 0);

    // Bind previous frame Buffer B density (for accumulation)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2 + bReadIdx]);  // B_read
    gl.uniform1i(uniformsBufferB.iChannel1, 1);

    gl.uniform2f(uniformsBufferB.iResolution, width, height);
    gl.uniform1f(uniformsBufferB.iTime, time);
    gl.uniform1i(uniformsBufferB.iFrame, frameCount);

    // Render density accumulation
    gl.useProgram(programBufferB);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Switch Buffer B read index
    bReadIdx = bWriteIdx;

    // ===== Pass 3: Image (Final Rendering to Screen) =====
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, width, height);

    // Bind Buffer A particles (use latest Buffer A result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);
    gl.uniform1i(uniformsImage.iChannel0, 0);

    // Bind Buffer B density (use latest Buffer B result)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2 + bReadIdx]);
    gl.uniform1i(uniformsImage.iChannel1, 1);

    gl.uniform2f(uniformsImage.iResolution, width, height);
    gl.uniform1f(uniformsImage.iTime, time);
    gl.uniform1i(uniformsImage.iFrame, frameCount);
    gl.uniform4f(uniformsImage.iMouse, mouse.x, mouse.y, mouse.z, mouse.w);

    // Render to screen
    gl.useProgram(programImage);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
}
```

**IMPORTANT: Key Points**:
- **Must use 2 FBOs for ping-pong**: Each Buffer needs two independent FBOs (read FBO + write FBO); a single FBO + texture swap causes "Feedback loop" error
- Use FBO index switching (not texture swapping): bind target FBO when writing, bind source texture when reading
- Image pass binds the latest Buffer results (obtained via read index)

## Performance & Composition

**Performance Optimization**:
- Separable blur: N² → 2N samples
- Bilinear tap trick: 5 samples replace 9-tap Gaussian
- MIP sampling replaces large kernels: `textureLod` at high MIP levels ≈ large-range average
- `discard` outside data regions to skip unnecessary computation
- RGBA channel packing: velocity(xy) + density(z) + curl(w) in one vec4
- Chained sub-steps: A→B→C same code for 3x simulation speed
- `if (dot(b,b) > bbMax) break;` adaptive early exit
- `iFrame < 20` progressive initialization to prevent explosion

**Typical Composition Patterns**:
- **Fluid + Lighting**: Fluid buffer → Image computes gradient normals → diffuse + specular
- **Fluid + Color Advection**: Separate Buffer tracks color field, advected by velocity field
- **Scene + Bloom + TAA**: 4-Buffer pipeline (render → downsample → blur → composite tone mapping)
- **G-Buffer + Screen-Space Effects**: 2-Buffer without temporal feedback (geometry → edge/SSAO/SSR → stylized compositing)
- **State Storage + Visualization Separation**: Buffer A pure logic + Image pure rendering (`texelFetch` reads state + distance field drawing)

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/multipass-buffer.md)
