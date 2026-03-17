- **Key**: Multi-pass rendering requires creating framebuffers and textures, switching the render target from screen to texture

### WebGL2 Multi-Pass Rendering Complete Template

Below is a complete standalone HTML template demonstrating how to set up WebGL2 double buffering (ping-pong) for physics simulation:

**IMPORTANT: WebGL2 ping-pong core rule: The texture bound to the write-target framebuffer must never simultaneously serve as input for any iChannel.** Violating this rule causes undefined behavior (typically all-black/all-zero output).

For simulations requiring "current frame" and "previous frame" two time steps (such as the wave equation), use **dual-channel encoding**: R channel stores current height, G channel stores previous frame height. This way only one buffer is read from (iChannel0 = currentBuf), writing to another buffer (nextBuf), avoiding read-write conflicts.

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>GPU Physics</title>
<style>body{margin:0;overflow:hidden}canvas{display:block;width:100vw;height:100vh}</style>
</head>
<body><canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', { antialias: false });
if (!gl) { document.body.innerHTML = 'WebGL2 not supported'; throw new Error('No WebGL2'); }

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(s));
        gl.deleteShader(s);
        return null;
    }
    return s;
}
function createProgram(vsSrc, fsSrc) {
    const vs = createShader(gl.VERTEX_SHADER, vsSrc);
    const fs = createShader(gl.FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs) return null;
    const p = gl.createProgram();
    gl.attachShader(p, vs);
    gl.attachShader(p, fs);
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        console.error(gl.getProgramInfoLog(p));
        return null;
    }
    return p;
}

const vsQuad = `#version 300 es
in vec2 position;
out vec2 vUv;
void main() {
    vUv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}`;

// === Buffer Pass Shader (physics simulation) ===
// IMPORTANT: Only uses iChannel0 (reads currentBuf), writes to nextBuf
// R channel = current height, G channel = previous frame height (dual-channel encoding avoids read-write conflict)
// IMPORTANT: RGBA8 compatible: use encode/decode to map signed values to [0,1], ensuring SwiftShader/no-float-texture environments work correctly
const fsBuffer = `#version 300 es
precision highp float;
uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;
uniform int iFrame;
uniform int useFloatTex;
in vec2 vUv;
out vec4 fragColor;

float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }
float encode(float v) { return useFloatTex == 1 ? v : v * 0.5 + 0.5; }

void main() {
    vec2 texel = 1.0 / iResolution;

    vec2 raw = texture(iChannel0, vUv).xy;
    float current = decode(raw.x);
    float previous = decode(raw.y);

    float left  = decode(texture(iChannel0, vUv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, vUv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, vUv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, vUv + vec2(0.0, texel.y)).x);

    float laplacian = left + right + down + up - 4.0 * current;
    float next = 2.0 * current - previous + 0.25 * laplacian;
    next *= 0.995;
    next *= min(1.0, float(iFrame));

    fragColor = vec4(encode(next), encode(current), 0.0, 1.0);
}`;

const fsImage = `#version 300 es
precision highp float;
uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform int useFloatTex;
in vec2 vUv;
out vec4 fragColor;

float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }

void main() {
    vec2 uv = vUv;
    vec2 texel = 1.0 / iResolution;

    float val = decode(texture(iChannel0, uv).x);

    vec3 col = vec3(val * 0.5 + 0.5);
    col += vec3(0.1, 0.15, 0.2);

    fragColor = vec4(col, 1.0);
}`;

const progBuffer = createProgram(vsQuad, fsBuffer);
const progImage = createProgram(vsQuad, fsImage);

const ext = gl.getExtension('EXT_color_buffer_float');
const useFloat = !!ext;

function createFramebuffer(width, height) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);

    const internalFormat = useFloat ? gl.RGBA32F : gl.RGBA8;
    const format = gl.RGBA;
    const type = useFloat ? gl.FLOAT : gl.UNSIGNED_BYTE;

    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, width, height, 0, format, type, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);

    return { fb, tex };
}

const SIM_W = 512, SIM_H = 512;
let bufA = createFramebuffer(SIM_W, SIM_H);
let bufB = createFramebuffer(SIM_W, SIM_H);

const quadVao = gl.createVertexArray();
gl.bindVertexArray(quadVao);
const quadBuf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const posLoc = gl.getAttribLocation(progBuffer, 'position');
gl.enableVertexAttribArray(posLoc);
gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

// === Render loop ===
// IMPORTANT: Key: currentBuf (read-only) and nextBuf (write-only) must be different buffers
let frame = 0;
function render(time) {
    time *= 0.001;

    const currentBuf = (frame % 2 === 0) ? bufA : bufB;
    const nextBuf = (frame % 2 === 0) ? bufB : bufA;

    // === Buffer Pass: read from currentBuf, write to nextBuf ===
    gl.bindFramebuffer(gl.FRAMEBUFFER, nextBuf.fb);
    gl.viewport(0, 0, SIM_W, SIM_H);
    gl.useProgram(progBuffer);

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, currentBuf.tex);
    gl.uniform1i(gl.getUniformLocation(progBuffer, 'iChannel0'), 0);

    gl.uniform2f(gl.getUniformLocation(progBuffer, 'iResolution'), SIM_W, SIM_H);
    gl.uniform1f(gl.getUniformLocation(progBuffer, 'iTime'), time);
    gl.uniform1i(gl.getUniformLocation(progBuffer, 'iFrame'), frame);
    gl.uniform1i(gl.getUniformLocation(progBuffer, 'useFloatTex'), useFloat ? 1 : 0);

    gl.bindVertexArray(quadVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    // === Image Pass: render to screen ===
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.useProgram(progImage);

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, nextBuf.tex);
    gl.uniform1i(gl.getUniformLocation(progImage, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(progImage, 'iResolution'), canvas.width, canvas.height);
    gl.uniform1i(gl.getUniformLocation(progImage, 'useFloatTex'), useFloat ? 1 : 0);

    gl.bindVertexArray(quadVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frame++;
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script></body></html>
```

**IMPORTANT: Common errors**:
1. **RGBA8 signed value truncation (fatal)**: Environments like SwiftShader that don't support `EXT_color_buffer_float` fall back to RGBA8 where values are clamped to [0,1]. Simulations requiring negative values (like the wave equation) will all zero out and produce a static image. **Must** use encode/decode functions: store as `v * 0.5 + 0.5`, read as `v * 2.0 - 1.0`, switching at runtime via `uniform int useFloatTex`. See the `encode()`/`decode()` functions in the template above
2. **Ping-pong read-write conflict (fatal)**: When rendering to a framebuffer, the texture bound to that framebuffer cannot simultaneously serve as input. The wave equation uses dual-channel encoding (R=current, G=previous) requiring only one input buffer; cloth/particle systems read getpos/getvel both from iChannel0
3. **Cloth rendering must use world coordinate projection (fatal)**: The cloth Image Pass cannot use `uv * vec2(SIZX, SIZY)` to map screen UV directly to grid ID. It must iterate over mesh faces, project vertex world coordinates to screen space via `worldToScreen()`, and perform triangle rasterization
4. **Smoke brightness insufficient (fatal)**: Beer-Lambert absorption must be >=3.0, background color >=`vec3(0.06, 0.07, 0.10)`, smoke base color >=`vec3(0.35)`, add gamma correction `pow(col, vec3(0.85))`, source density >=3.0, density decay >=0.9995
5. **GLSL reserved words**: `active`, `input`, `output`, `filter`, `sample`, `buffer`, `shared` cannot be used as variable names
6. **viewport/iResolution**: Buffer pass uses simulation resolution, Image pass uses screen resolution. Cloth Image Pass getpos/getvel must use `iSimResolution`
7. **GLSL type & math safety**: Cannot write `float / vec2`; `normalize(vec3(0))` produces NaN — check `length(v) > 0.0001` before calling
8. **GLSL nested functions forbidden**: Functions cannot be defined inside other functions
9. **JS variable declarations**: Ping-pong variables inside for loops must use `let`; in substeps, pass `iFrame` as `frame * substeps + substep`

# GPU Physics Simulation Skill

## Use Cases

- Real-time physics simulation: waves, fluid smoke, cloth, rigid body collision, particle fluids
- Interactive physics effects: mouse force fields, ripples, pushing/pulling rigid bodies
- Scientific visualization: chaotic attractors, vortex dynamics, ship wave dispersion
- Iterative computations requiring "previous frame → next frame" state persistence

## Core Principles

The core paradigm of GPU physics simulation is **Buffer Feedback**: physical state is stored in texture buffers, each frame reads the previous frame's state → computes → writes back, with each pixel processed independently in parallel.

### Key Mathematical Tools

```
Discrete Laplacian:       ∇²f ≈ f(x+1,y) + f(x-1,y) + f(x,y+1) + f(x,y-1) - 4·f(x,y)
Semi-Lagrangian advection: f_new(x) = f_old(x - v·dt)
Spring force:              F = k · (|Δx| - L₀) · normalize(Δx)
Damping force:             F = c · dot(normalize(Δx), Δv) · normalize(Δx)
Vorticity confinement:     curl = ∂v_x/∂y - ∂v_y/∂x
```

### Architecture Patterns

| Layer | Responsibility | ShaderToy Implementation |
|-------|---------------|--------------------------|
| **State Storage** | Encode physical quantities into textures | Buffer RGBA channels |
| **Solver** | Read old state → compute forces → integrate → write new state | Buffer Pass (can be chained iteratively) |
| **Rendering** | Visualize physical state | Image Pass |

## Implementation Steps

### Step 1: Ping-Pong Double Buffering (Correct WebGL2 Implementation)

**IMPORTANT: Key difference between ShaderToy and WebGL2**: In ShaderToy, Buffer A/B are two independent passes with separate write targets, so `iChannel0=self, iChannel1=other` doesn't conflict. But in WebGL2 with a single shader program doing ping-pong, the write-target texture cannot be read simultaneously.

**Solution: Dual-channel encoding** — R channel stores current height, G channel stores previous frame height, requiring only one input buffer:

```glsl
// WebGL2 Wave Equation Buffer Pass
// IMPORTANT: Only iChannel0 (reads currentBuf), writes to nextBuf (must be different!)
// IMPORTANT: encode/decode ensures signed values aren't truncated under RGBA8 (no float textures)

uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }
float encode(float v) { return useFloatTex == 1 ? v : v * 0.5 + 0.5; }

void main() {
    vec2 uv = vUv;
    vec2 texel = 1.0 / iResolution;

    vec2 raw = texture(iChannel0, uv).xy;
    float current = decode(raw.x);
    float previous = decode(raw.y);

    float left  = decode(texture(iChannel0, uv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, uv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, uv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, uv + vec2(0.0, texel.y)).x);

    float laplacian = left + right + down + up - 4.0 * current;
    float next = 2.0 * current - previous + 0.25 * laplacian;
    next *= 0.995;
    next *= min(1.0, float(iFrame));

    fragColor = vec4(encode(next), encode(current), 0.0, 1.0);
}
```

Corresponding JS render loop (binds only one input texture):
```js
const currentBuf = (frame % 2 === 0) ? bufA : bufB;
const nextBuf = (frame % 2 === 0) ? bufB : bufA;

gl.bindFramebuffer(gl.FRAMEBUFFER, nextBuf.fb);  // write to nextBuf
gl.activeTexture(gl.TEXTURE0);
gl.bindTexture(gl.TEXTURE_2D, currentBuf.tex);    // read from currentBuf
gl.uniform1i(gl.getUniformLocation(progBuffer, 'iChannel0'), 0);
gl.uniform1i(gl.getUniformLocation(progBuffer, 'useFloatTex'), useFloat ? 1 : 0);
// IMPORTANT: Do NOT bind iChannel1 to nextBuf/otherBuf!
```

### Step 2: Interaction-Driven (External Force Injection)

```glsl
// Insert external forces before the wave equation computation (add to next)
float force = 0.0;
if (iMouse.z > 0.0)
{
    vec2 fragCoord = vUv * iResolution;
    force = smoothstep(4.5, 0.5, length(iMouse.xy - fragCoord));
}
else
{
    // Procedural raindrops
    vec2 fragCoord = vUv * iResolution;
    float t = iTime * 2.0;
    vec2 pos = fract(floor(t) * vec2(0.456665, 0.708618)) * iResolution;
    float amp = 1.0 - step(0.05, fract(t));
    force = -amp * smoothstep(2.5, 0.5, length(pos - fragCoord));
}

// Add external force after wave equation
next += force;
```

### Step 3: Height Field Rendering (Image Pass)

```glsl
// IMPORTANT: Image Pass also needs decode
uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }

void main()
{
    vec2 uv = vUv;
    vec2 texel = 1.0 / iResolution;

    float left  = decode(texture(iChannel0, uv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, uv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, uv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, uv + vec2(0.0, texel.y)).x);

    vec3 normal = normalize(vec3((right - left) * 8.0, (up - down) * 8.0, 1.0));

    vec3 light = normalize(vec3(0.2, -0.5, 0.7));
    float diffuse = max(dot(normal, light), 0.0);
    float spec = pow(max(-reflect(light, normal).z, 0.0), 32.0);

    vec3 waterTint = vec3(0.05, 0.15, 0.3);
    vec3 color = waterTint * (0.6 + 0.5 * diffuse) + vec3(1.0) * spec * 0.6;

    fragColor = vec4(color, 1.0);
}
```

### Step 4: Chained Multi-Buffer Iteration (Fluid Solver)

Buffer A/B/C share the solver from a Common pass, iterating 3 times per frame:
```glsl
// === Common Pass ===
#define dt 0.15
#define viscosityThreshold 0.64
#define vorticityThreshold 0.25

vec4 fluidSolver(sampler2D field, vec2 uv, vec2 step,
                 vec4 mouse, vec4 prevMouse)
{
    float k = 0.2, s = k / dt;
    vec4 c  = textureLod(field, uv, 0.0);
    vec4 fr = textureLod(field, uv + vec2(step.x, 0.0), 0.0);
    vec4 fl = textureLod(field, uv - vec2(step.x, 0.0), 0.0);
    vec4 ft = textureLod(field, uv + vec2(0.0, step.y), 0.0);
    vec4 fd = textureLod(field, uv - vec2(0.0, step.y), 0.0);

    vec3 ddx = (fr - fl).xyz * 0.5;
    vec3 ddy = (ft - fd).xyz * 0.5;
    float divergence = ddx.x + ddy.y;
    vec2 densityDiff = vec2(ddx.z, ddy.z);

    c.z -= dt * dot(vec3(densityDiff, divergence), c.xyz);

    vec2 laplacian = fr.xy + fl.xy + ft.xy + fd.xy - 4.0 * c.xy;
    vec2 viscosity = viscosityThreshold * laplacian;

    vec2 densityInv = s * densityDiff;
    vec2 uvHistory = uv - dt * c.xy * step;
    c.xyw = textureLod(field, uvHistory, 0.0).xyw;

    vec2 extForce = vec2(0.0);
    if (mouse.z > 1.0 && prevMouse.z > 1.0)
    {
        vec2 drag = clamp((mouse.xy - prevMouse.xy) * step * 600.0, -10.0, 10.0);
        vec2 p = uv - mouse.xy * step;
        extForce += 0.001 / dot(p, p) * drag;
    }

    c.xy += dt * (viscosity - densityInv + extForce);
    c.xy = max(vec2(0.0), abs(c.xy) - 5e-6) * sign(c.xy);

    // Vorticity confinement
    c.w = (fd.x - ft.x + fr.y - fl.y);
    vec2 vorticity = vec2(abs(ft.w) - abs(fd.w), abs(fl.w) - abs(fr.w));
    vorticity *= vorticityThreshold / (length(vorticity) + 1e-5) * c.w;
    c.xy += vorticity;

    c.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    c.x *= smoothstep(0.5, 0.49, abs(uv.x - 0.5));
    c = clamp(c, vec4(-24.0, -24.0, 0.5, -0.25), vec4(24.0, 24.0, 3.0, 0.25));
    return c;
}

// === Buffer A / B / C ===
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 stepSize = 1.0 / iResolution.xy;
    vec4 prevMouse = textureLod(iChannel0, vec2(0.0), 0.0);
    fragColor = fluidSolver(iChannel0, uv, stepSize, iMouse, prevMouse);
    if (fragCoord.y < 1.0) fragColor = iMouse; // store mouse state
}
```

### Step 5: Particle Data Layout (Cloth/N-Body)

Texture regions are partitioned to store different attributes:
```glsl
#define SIZX 128.0
#define SIZY 64.0

// IMPORTANT: Cloth/particle systems: getpos/getvel both read from iChannel0 (not iChannel1)
// Because iChannel0 = currentBuf (read-only), write target is nextBuf (separate buffer)
// IMPORTANT: Use +0.5 to sample texel centers (not +0.01)
vec3 getpos(vec2 id) {
    return texture(iChannel0, (id + 0.5) / iResolution.xy).xyz;
}
vec3 getvel(vec2 id) {
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iResolution.xy).xyz;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 fc = floor(fragCoord);
    vec2 c = fc;
    c.x = fract(c.x / SIZX) * SIZX;

    vec3 pos = getpos(c);
    vec3 vel = getvel(c);
    // ... physics computation ...
    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```

### Step 6: Spring-Damper Constraints

```glsl
const float SPRING_K = 0.15;
const float DAMPER_C = 0.10;
const float GRAVITY  = 0.0022;

vec3 pos, vel, ovel;
vec2 c;

void edge(vec2 dif)
{
    if ((dif + c).x < 0.0 || (dif + c).x >= SIZX ||
        (dif + c).y < 0.0 || (dif + c).y >= SIZY) return;

    float restLen = length(dif);
    vec3 posdif = getpos(dif + c) - pos;
    vec3 veldif = getvel(dif + c) - ovel;

    float plen = length(posdif);
    if (plen < 0.0001) return;
    vec3 dir = posdif / plen;

    vel += dir * clamp(plen - restLen, -1.0, 1.0) * SPRING_K;
    vel += dir * dot(dir, veldif) * DAMPER_C;
}

// Call 12 edges: 4 nearest neighbors + 4 diagonal + 4 skip
// edge(vec2(0,1)); edge(vec2(0,-1)); edge(vec2(1,0)); edge(vec2(-1,0));
// edge(vec2(1,1)); edge(vec2(-1,-1));
// edge(vec2(0,2)); edge(vec2(0,-2)); edge(vec2(2,0)); edge(vec2(-2,0));
// edge(vec2(2,-2)); edge(vec2(-2,2));
```

### Step 7: N-Body Vortex Particles (Biot-Savart)

```glsl
#define N 20
#define Nf float(N)
#define MARKERS 0.90

float STRENGTH = 1e3 * 0.25 / (1.0 - MARKERS) * sqrt(30.0 / Nf);
#define tex(i,j) texture(iChannel1, (vec2(i,j) + 0.5) / iResolution.xy)
#define W(i,j)   tex(i, j + N).z

void mainImage(out vec4 O, vec2 U)
{
    vec2 T = floor(U / Nf);
    U = mod(U, Nf);
    vec2 F = vec2(0.0);

    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
        {
            float w = W(i, j);
            vec2 d = tex(i, j).xy - O.xy;
            d = (fract(0.5 + d / iResolution.xy) - 0.5) * iResolution.xy;
            float l = dot(d, d);
            if (l > 1e-5)
                F += vec2(-d.y, d.x) * w / l;
        }

    O.zw = STRENGTH * F;
    O.xy += O.zw * dt;
    O.xy = mod(O.xy, iResolution.xy);
}
```

### Step 8: Global State Storage (Specific Pixel)

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Pixel (0,0) stores global state (e.g., Lorenz attractor position)
    if (floor(fragCoord) == vec2(0, 0))
    {
        if (iFrame == 0) {
            fragColor = vec4(0.1, 0.001, 0.0, 0.0);
        } else {
            vec3 state = texture(iChannel0, vec2(0.0)).xyz;
            for (float i = 0.0; i < 96.0; i++) {
                vec3 deriv;
                deriv.x = 10.0 * (state.y - state.x);
                deriv.y = state.x * (28.0 - state.z) - state.y;
                deriv.z = state.x * state.y - 8.0/3.0 * state.z;
                state += deriv * 0.016 * 0.2;
            }
            fragColor = vec4(state, 0.0);
        }
        return;
    }

    // Other pixels: accumulate trajectory distance field
    vec3 last = texture(iChannel0, vec2(0.0)).xyz;
    float d = 1e6;
    for (float i = 0.0; i < 96.0; i++) {
        vec3 next = Integrate(last, 0.016 * 0.2);
        d = min(d, dfLine(last.xz * 0.015, next.xz * 0.015, uv));
        last = next;
    }
    float c = 0.5 * smoothstep(1.0 / iResolution.y, 0.0, d);
    vec3 prev = texture(iChannel0, fragCoord / iResolution.xy).rgb;
    fragColor = vec4(vec3(c) + prev * 0.99, 0.0);
}
```

## Complete Code Template

2D wave simulation: double buffering + mouse interaction + procedural raindrops + height field water surface rendering.

**Ping-Pong setup**: bufA and bufB alternate; the shader only reads from iChannel0 (currentBuf) and writes to nextBuf. R=current height, G=previous frame height.

```glsl
// === Buffer Pass (Wave Equation) ===
// IMPORTANT: Only uses iChannel0 = currentBuf (read-only), writes to nextBuf
// IMPORTANT: encode/decode ensures signed values aren't truncated under RGBA8 (SwiftShader compatible)

uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }
float encode(float v) { return useFloatTex == 1 ? v : v * 0.5 + 0.5; }

#define DAMPING 0.995
#define WAVE_SPEED 0.25

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;

    float current = decode(texture(iChannel0, uv).x);
    float previous = decode(texture(iChannel0, uv).y);

    float left  = decode(texture(iChannel0, uv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, uv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, uv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, uv + vec2(0.0, texel.y)).x);

    float force = 0.0;
    if (iMouse.z > 0.0) {
        force = smoothstep(4.5, 0.5, length(iMouse.xy - fragCoord));
    } else {
        float t = iTime * 2.0;
        vec2 pos = fract(floor(t) * vec2(0.456665, 0.708618)) * iResolution.xy;
        float amp = 1.0 - step(0.05, fract(t));
        force = -amp * smoothstep(2.5, 0.5, length(pos - fragCoord));
    }

    float laplacian = left + right + down + up - 4.0 * current;
    float next = 2.0 * current - previous + WAVE_SPEED * laplacian;
    next += force;
    next *= DAMPING;
    next *= min(1.0, float(iFrame));

    fragColor = vec4(encode(next), encode(current), 0.0, 0.0);
}
```

```glsl
// === Image Pass ===
// IMPORTANT: Also needs decode to correctly read signed height values

uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }

#define SPECULAR_POWER 32.0

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;

    float left  = decode(texture(iChannel0, uv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, uv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, uv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, uv + vec2(0.0, texel.y)).x);

    vec3 normal = normalize(vec3((right - left) * 8.0, (up - down) * 8.0, 1.0));

    vec3 light = normalize(vec3(0.3, 0.6, 0.8));
    vec3 viewDir = vec3(0.0, 0.0, 1.0);
    float diffuse = max(dot(normal, light), 0.0);
    vec3 reflectDir = reflect(-light, normal);
    float spec = pow(max(dot(reflectDir, viewDir), 0.0), SPECULAR_POWER);

    float h = decode(texture(iChannel0, uv).x);
    vec3 deepColor = vec3(0.02, 0.06, 0.15);
    vec3 shallowColor = vec3(0.05, 0.18, 0.30);
    vec3 waterBase = mix(deepColor, shallowColor, clamp(abs(h) * 3.0, 0.0, 1.0));

    float fresnel = pow(1.0 - max(dot(normal, viewDir), 0.0), 3.0);
    vec3 skyColor = vec3(0.4, 0.55, 0.75);
    vec3 color = waterBase * (0.6 + 0.5 * diffuse);
    color = mix(color, skyColor, fresnel * 0.3);
    color += vec3(1.0, 0.95, 0.85) * spec * 0.6;

    fragColor = vec4(color, 1.0);
}
```

## Common Variants

### Variant 1: Euler Fluid (Smoke/Ink)

Smoke/ink simulation requires a complete Buffer Pass (fluid solver) + Image Pass (volume rendering). Buffer stores xy=velocity, z=density, w=curl.

```glsl
// === Buffer Pass (Fluid Solver) ===
// Requires 3 chained buffer iterations (A→B→C→Image), each buffer executes the same fluidSolver
#define dt 0.15
#define viscosityCoeff 0.64
#define vorticityCoeff 0.25

vec4 fluidSolver(sampler2D field, vec2 uv, vec2 step, vec4 mouse, vec4 prevMouse) {
    float k = 0.2, s = k / dt;
    vec4 c  = textureLod(field, uv, 0.0);
    vec4 fr = textureLod(field, uv + vec2(step.x, 0.0), 0.0);
    vec4 fl = textureLod(field, uv - vec2(step.x, 0.0), 0.0);
    vec4 ft = textureLod(field, uv + vec2(0.0, step.y), 0.0);
    vec4 fd = textureLod(field, uv - vec2(0.0, step.y), 0.0);

    vec3 ddx = (fr - fl).xyz * 0.5;
    vec3 ddy = (ft - fd).xyz * 0.5;
    float divergence = ddx.x + ddy.y;
    vec2 densityDiff = vec2(ddx.z, ddy.z);

    c.z -= dt * dot(vec3(densityDiff, divergence), c.xyz);

    vec2 laplacian = fr.xy + fl.xy + ft.xy + fd.xy - 4.0 * c.xy;
    vec2 viscosity = viscosityCoeff * laplacian;
    vec2 densityInv = s * densityDiff;

    // Semi-Lagrangian advection
    vec2 uvHistory = uv - dt * c.xy * step;
    c.xyw = textureLod(field, uvHistory, 0.0).xyw;

    // Buoyancy (key for smoke: higher density means stronger upward force)
    float buoyancy = 0.15 * c.z;
    c.y += buoyancy * dt;

    // Wind force (horizontal offset)
    c.x += 0.02 * sin(uv.y * 6.28 + float(iFrame) * 0.02) * c.z * dt;

    // Mouse/procedural source injection
    vec2 extForce = vec2(0.0);
    float densitySource = 0.0;
    if (mouse.z > 1.0 && prevMouse.z > 1.0) {
        vec2 drag = clamp((mouse.xy - prevMouse.xy) * step * 600.0, -10.0, 10.0);
        vec2 p = uv - mouse.xy * step;
        float influence = 0.001 / (dot(p, p) + 1e-6);
        extForce += influence * drag;
        densitySource += influence * 0.5;
    } else {
        // Procedural bottom smoke sources (multi-point + wide range, ensuring dense visibility)
        float srcStrength = 0.0;
        for (float si = -1.0; si <= 1.0; si += 1.0) {
            float srcX = 0.5 + si * 0.12 + 0.08 * sin(float(iFrame) * 0.013 + si * 2.0);
            vec2 srcPos = vec2(srcX, 0.06);
            float d = length(uv - srcPos);
            srcStrength += smoothstep(0.12, 0.0, d) * 3.5;
        }
        densitySource += srcStrength;
        extForce.y += srcStrength * 0.4;
    }

    c.xy += dt * (viscosity - densityInv + extForce);
    c.z = max(c.z + densitySource * dt, 0.0);

    // Vorticity confinement (preserves smoke detail and curling structures)
    c.w = (fd.x - ft.x + fr.y - fl.y);
    vec2 vortGrad = vec2(abs(ft.w) - abs(fd.w), abs(fl.w) - abs(fr.w));
    vortGrad *= vorticityCoeff / (length(vortGrad) + 1e-5) * c.w;
    c.xy += vortGrad;

    c.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    c.x *= smoothstep(0.5, 0.49, abs(uv.x - 0.5));
    c.z *= 0.9995; // density decay (closer to 1.0 = denser and more persistent smoke)
    c = clamp(c, vec4(-24.0, -24.0, 0.0, -0.25), vec4(24.0, 24.0, 5.0, 0.25));
    return c;
}

void main() {
    vec2 uv = vUv;
    vec2 stepSize = 1.0 / iResolution;
    vec4 prevMouse = textureLod(iChannel0, vec2(0.0), 0.0);
    fragColor = fluidSolver(iChannel0, uv, stepSize, iMouse, prevMouse);
    if (floor(vUv * iResolution).y < 1.0) fragColor = iMouse;
}
```

```glsl
// === Image Pass (Smoke Rendering) ===
// Reads density (z channel) and velocity (xy channels) from buffer, renders dense layered smoke + light scattering
// IMPORTANT: Smoke brightness key: absorption coefficient must be large enough (>=3.0), background not too dark, lightTransmit must not over-attenuate

void main() {
    vec2 uv = vUv;
    vec4 data = texture(iChannel0, uv);
    float density = data.z;
    vec2 vel = data.xy;

    // Multi-layer sampling for added depth (accumulate density from nearby pixels)
    float layeredDensity = density;
    vec2 texel = 1.0 / iResolution;
    for (float i = 1.0; i <= 4.0; i += 1.0) {
        float scale = i * 3.0;
        layeredDensity += texture(iChannel0, uv + vec2(texel.x * scale, 0.0)).z * 0.4;
        layeredDensity += texture(iChannel0, uv - vec2(texel.x * scale, 0.0)).z * 0.4;
        layeredDensity += texture(iChannel0, uv + vec2(0.0, texel.y * scale)).z * 0.4;
        layeredDensity += texture(iChannel0, uv - vec2(0.0, texel.y * scale)).z * 0.4;
    }
    layeredDensity /= 4.0;

    // Beer-Lambert absorption (denser regions are more opaque)
    float absorption = 1.0 - exp(-layeredDensity * 3.5);

    // Light scattering: accumulate density from light direction for simple ray marching
    vec2 lightDir2D = normalize(vec2(0.3, 1.0));
    float lightAccum = 0.0;
    for (float s = 1.0; s <= 8.0; s += 1.0) {
        vec2 sampleUV = uv + lightDir2D * texel * s * 5.0;
        lightAccum += texture(iChannel0, sampleUV).z;
    }
    float lightTransmit = exp(-lightAccum * 0.25);

    // Velocity field drives color variation (faster flow regions are brighter)
    float speed = length(vel);

    // Smoke color: gray-white tones, affected by lighting
    vec3 smokeBase = mix(vec3(0.35, 0.32, 0.30), vec3(0.85, 0.82, 0.78), lightTransmit);
    smokeBase += vec3(1.0, 0.85, 0.6) * lightTransmit * absorption * 0.5;
    smokeBase += vec3(0.3, 0.2, 0.1) * speed * 3.0;

    // Background gradient (blue-gray, bright enough to contrast with smoke)
    vec3 bg = mix(vec3(0.06, 0.07, 0.10), vec3(0.15, 0.18, 0.25), uv.y);

    vec3 col = mix(bg, smokeBase, absorption);

    // Bottom light source glow
    float glow = smoothstep(0.3, 0.0, uv.y) * 0.4;
    col += vec3(1.0, 0.6, 0.2) * glow * (0.5 + 0.5 * absorption);

    // Gamma correction to ensure smoke visibility
    col = pow(col, vec3(0.85));

    fragColor = vec4(col, 1.0);
}
```

Smoke simulation requires 3 chained buffer iterations (same fluidSolver) for enhanced convergence. JS side creates bufA/bufB/bufC, executing A→B→C→Image each frame.

### Variant 2: Cloth Simulation (Mass-Spring-Damper)

Cloth simulation requires 2 buffers for ping-pong alternating read/write, with a JS render loop using a for loop to execute multiple substeps (e.g., 4 steps). Data structure:
- Left half of texture [0, SIZX) stores position xyz
- Right half of texture [SIZX, 2*SIZX) stores velocity xyz
- **Note**: When using substep loops, buffer variables in the render function must use `let` to allow reassignment within the loop
- **Key**: Image Pass `getpos`/`getvel` functions must use the simulation resolution (`iSimResolution`) for UV calculation, not the screen resolution

```glsl
// WebGL2-adapted cloth simulation Buffer Pass
// IMPORTANT: getpos/getvel both read from iChannel0! iChannel0 = currentBuf (read-only), writes to nextBuf

#define SIZX 128.0
#define SIZY 64.0
const float SPRING_K = 0.15;
const float DAMPER_C = 0.10;
const float GRAVITY = 0.0022;

vec3 pos, vel, ovel;
vec2 c;

vec3 getpos(vec2 id) {
    return texture(iChannel0, (id + 0.5) / iResolution.xy).xyz;
}
vec3 getvel(vec2 id) {
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iResolution.xy).xyz;
}

void edge(vec2 dif) {
    if ((dif + c).x < 0.0 || (dif + c).x >= SIZX ||
        (dif + c).y < 0.0 || (dif + c).y >= SIZY) return;
    vec3 posdif = getpos(dif + c) - pos;
    vec3 veldif = getvel(dif + c) - ovel;
    float restLen = length(dif);
    float plen = length(posdif);
    if (plen < 0.0001) return;
    vec3 dir = posdif / plen;
    vel += dir * clamp(plen - restLen, -1.0, 1.0) * SPRING_K;
    vel += dir * dot(dir, veldif) * DAMPER_C;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 fc = floor(fragCoord);
    c = fc;
    c.x = fract(c.x / SIZX) * SIZX;

    // iFrame should pass the global frame count: frame * SUBSTEPS + substep
    if (iFrame < 4) {
        vec2 p = vec2(c.x / SIZX, c.y / SIZY);
        vec3 initialPos = vec3(p.x * 1.6 - 0.3, -p.y * 0.8 + 0.6, 0.0);
        fragColor = vec4(fc.x >= SIZX ? vec3(0.0) : initialPos, 0.0);
        return;
    }

    pos = getpos(c);
    vel = getvel(c);
    ovel = vel;

    edge(vec2(0,1)); edge(vec2(0,-1)); edge(vec2(1,0)); edge(vec2(-1,0));
    edge(vec2(1,1)); edge(vec2(-1,-1));
    edge(vec2(0,2)); edge(vec2(0,-2)); edge(vec2(2,0)); edge(vec2(-2,0));

    vel.y -= GRAVITY;

    vec3 ballPos = vec3(0.35, 0.3, 0.0);
    float ballRadius = 0.15;
    vec3 toBall = pos - ballPos;
    float distToBall = length(toBall);
    if (distToBall < ballRadius && distToBall > 0.0001) {
        vec3 pushDir = toBall / distToBall;
        pos = ballPos + pushDir * ballRadius;
        vel -= pushDir * dot(pushDir, vel);
    }

    if (c.y == 0.0) {
        pos = vec3(fc.x * 0.85 / SIZX, 0.0, 0.0);
        vel = vec3(0.0);
    }

    pos += vel;

    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```

#### Cloth Rendering Pass (Image Pass) Complete Template

**IMPORTANT: Cloth rendering core principle**: After physics simulation, cloth particle world positions (pos.xy) will deviate from their initial grid positions (due to gravity, collisions, etc.). The Image Pass must render based on particles' **actual world positions** projected to the screen — you cannot use `uv * vec2(SIZX, SIZY)` to directly map screen UV to grid ID (that would produce scattered dots/fragments rather than a continuous cloth surface).

Correct approach: iterate over all cloth mesh cells, project each cell's 4 vertex world coordinates to screen space, determine if the current pixel falls within that quad, then interpolate shading.

```glsl
// IMPORTANT: Key: must pass additional uniform vec2 iSimResolution (simulation resolution)
//    getpos/getvel use iSimResolution, not iResolution
//    Rendering method: iterate cloth mesh, project world coordinates to screen coordinates

#define SIZX 128.0
#define SIZY 64.0

in vec2 vUv;
out vec4 fragColor;

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform vec2 iSimResolution;
uniform float iTime;

vec3 getpos(vec2 id) {
    return texture(iChannel0, (id + 0.5) / iSimResolution).xyz;
}
vec3 getvel(vec2 id) {
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iSimResolution).xyz;
}

vec2 worldToScreen(vec3 p) {
    return vec2(p.x * 0.5 + 0.5, 1.0 - (p.y * 0.5 + 0.5));
}

vec3 calcNormal(vec2 cell) {
    vec3 pL = getpos(vec2(max(cell.x - 1.0, 0.0), cell.y));
    vec3 pR = getpos(vec2(min(cell.x + 1.0, SIZX - 1.0), cell.y));
    vec3 pD = getpos(vec2(cell.x, max(cell.y - 1.0, 0.0)));
    vec3 pU = getpos(vec2(cell.x, min(cell.y + 1.0, SIZY - 1.0)));
    vec3 tanX = pR - pL;
    vec3 tanY = pU - pD;
    vec3 normal = cross(tanX, tanY);
    float nlen = length(normal);
    if (nlen < 0.0001) return vec3(0.0, 0.0, -1.0);
    normal /= nlen;
    if (normal.z > 0.0) normal = -normal;
    return normal;
}

float cross2d(vec2 a, vec2 b) { return a.x * b.y - a.y * b.x; }

bool pointInTriangle(vec2 p, vec2 a, vec2 b, vec2 c, out vec3 bary) {
    float d00 = dot(b - a, b - a);
    float d01 = dot(b - a, c - a);
    float d11 = dot(c - a, c - a);
    float d20 = dot(p - a, b - a);
    float d21 = dot(p - a, c - a);
    float denom = d00 * d11 - d01 * d01;
    if (abs(denom) < 1e-10) return false;
    float v = (d11 * d20 - d01 * d21) / denom;
    float w = (d00 * d21 - d01 * d20) / denom;
    float u = 1.0 - v - w;
    bary = vec3(u, v, w);
    return u >= -0.01 && v >= -0.01 && w >= -0.01;
}

void main() {
    vec2 uv = vUv;
    vec2 fragCoord = vUv * iResolution;

    vec3 bgTop = vec3(0.05, 0.08, 0.15);
    vec3 bgBot = vec3(0.02, 0.03, 0.08);
    vec3 bg = mix(bgBot, bgTop, uv.y);
    vec3 col = bg;
    float closestZ = 1e6;

    vec3 ballPos = vec3(0.35 + sin(iTime * 0.6) * 0.15, 0.3 + cos(iTime * 0.4) * 0.1, 0.0);
    float ballRadius = 0.12;
    vec2 ballScreen = worldToScreen(ballPos);
    float ballDist = length(uv - ballScreen);
    if (ballDist < ballRadius * 0.6) {
        float shade = smoothstep(ballRadius * 0.6, ballRadius * 0.15, ballDist);
        vec3 ballColor = vec3(0.95, 0.35, 0.2);
        vec2 bnXY = (uv - ballScreen) / (ballRadius * 0.6);
        float bnZ = sqrt(max(0.0, 1.0 - dot(bnXY, bnXY)));
        vec3 bn = normalize(vec3(bnXY, bnZ));
        float bdiff = max(dot(bn, normalize(vec3(0.5, 0.8, 1.0))), 0.0);
        float bspec = pow(max(dot(normalize(bn + normalize(vec3(0.5, 0.8, 1.0))), vec3(0.0, 0.0, 1.0)), 0.0), 32.0);
        col = ballColor * (0.3 + 0.7 * bdiff) + vec3(1.0) * bspec * 0.4;
        closestZ = ballPos.z - ballRadius;
    }

    for (float cy = 0.0; cy < SIZY - 1.0; cy += 1.0) {
        for (float cx = 0.0; cx < SIZX - 1.0; cx += 1.0) {
            vec3 p00 = getpos(vec2(cx, cy));
            vec3 p10 = getpos(vec2(cx + 1.0, cy));
            vec3 p01 = getpos(vec2(cx, cy + 1.0));
            vec3 p11 = getpos(vec2(cx + 1.0, cy + 1.0));

            vec2 s00 = worldToScreen(p00);
            vec2 s10 = worldToScreen(p10);
            vec2 s01 = worldToScreen(p01);
            vec2 s11 = worldToScreen(p11);

            vec2 bboxMin = min(min(s00, s10), min(s01, s11));
            vec2 bboxMax = max(max(s00, s10), max(s01, s11));
            if (uv.x < bboxMin.x - 0.01 || uv.x > bboxMax.x + 0.01 ||
                uv.y < bboxMin.y - 0.01 || uv.y > bboxMax.y + 0.01) continue;

            vec3 bary;
            vec2 cellId = vec2(cx, cy);
            bool hit = false;
            float interpZ = 0.0;

            if (pointInTriangle(uv, s00, s10, s01, bary)) {
                hit = true;
                interpZ = bary.x * p00.z + bary.y * p10.z + bary.z * p01.z;
            } else if (pointInTriangle(uv, s10, s11, s01, bary)) {
                hit = true;
                interpZ = bary.x * p10.z + bary.y * p11.z + bary.z * p01.z;
            }

            if (hit && interpZ < closestZ) {
                closestZ = interpZ;
                vec3 normal = calcNormal(cellId);
                vec3 lightDir = normalize(vec3(0.5, 0.8, 1.0));
                float diff = max(dot(normal, lightDir), 0.0);
                float diffBack = max(dot(-normal, lightDir), 0.0);
                vec3 halfDir = normalize(lightDir + vec3(0.0, 0.0, 1.0));
                float spec = pow(max(dot(normal, halfDir), 0.0), 32.0);

                float stretch = length(getvel(cellId));
                vec3 clothColor1 = vec3(0.25, 0.55, 0.95);
                vec3 clothColor2 = vec3(0.95, 0.35, 0.45);
                vec3 clothColor = mix(clothColor1, clothColor2, clamp(stretch * 10.0, 0.0, 1.0));

                vec2 gridFrac = fract(vec2(cx, cy) * 0.125);
                float checker = step(0.5, fract(gridFrac.x + gridFrac.y));
                clothColor *= 0.85 + 0.15 * checker;

                col = clothColor * (0.3 + 0.6 * diff + 0.25 * diffBack) + vec3(1.0) * spec * 0.35;
            }
        }
    }

    fragColor = vec4(col, 1.0);
}
```

**IMPORTANT: Cloth rendering performance note**: The above template uses a double loop to iterate all mesh faces for triangle rasterization. For a 128x64 mesh this is about 8000 quads per frame. If GPU performance is insufficient, reduce mesh resolution (e.g., SIZX=64, SIZY=32) or use `texelFetch` instead of `texture` for speed. Another approach is to partition the cloth into blocks (e.g., 4x4), each with an independent bounding box for early culling.

#### Cloth Simulation Complete HTML Template (Multi-Substep Iteration)

**IMPORTANT: Key notes (must-read for cloth template)**:
1. **No read-write conflict**: In the Buffer Pass, iChannel0 is bound to currentBuf (read-only), the write target is nextBuf (separate buffer). getpos/getvel both read from iChannel0
2. **iSimResolution uniform**: Image Pass must have `uniform vec2 iSimResolution` passing `(SIM_W, SIM_H)`, and `getpos`/`getvel` internally use `iSimResolution` for UV calculation
3. **iFrame value passing**: In substep loops, iFrame should pass `frame * SUBSTEPS + substep`, ensuring the initialization condition `iFrame < SUBSTEPS` only triggers on the first frame
4. **Substeps use 2-buffer ping-pong + JS for loop**: Do not use 4 buffers; use 2 buffers alternating at the JS level

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>GPU Cloth Simulation</title>
<style>body{margin:0;overflow:hidden}canvas{display:block;width:100vw;height:100vh}</style>
</head>
<body><canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', { antialias: false });
if (!gl) { document.body.innerHTML = 'WebGL2 not supported'; throw new Error('No WebGL2'); }

const ext = gl.getExtension('EXT_color_buffer_float');
const isFloat = !!ext;

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(s));
        gl.deleteShader(s);
        return null;
    }
    return s;
}
function createProgram(vsSrc, fsSrc) {
    const vs = createShader(gl.VERTEX_SHADER, vsSrc);
    const fs = createShader(gl.FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs) return null;
    const p = gl.createProgram();
    gl.attachShader(p, vs);
    gl.attachShader(p, fs);
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(p));
        return null;
    }
    return p;
}

const vsQuad = `#version 300 es
in vec2 position;
out vec2 vUv;
void main() {
    vUv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}`;

const SUBSTEPS = 4;

const fsBuffer = `#version 300 es
precision highp float;

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;
uniform int iFrame;
uniform vec4 iMouse;

in vec2 vUv;
out vec4 fragColor;

#define SIZX 128.0
#define SIZY 64.0
const float SPRING_K = 0.18;
const float DAMPER_C = 0.12;
const float GRAVITY = 0.0018;

vec3 getBallPos(float time) {
    float t = time * 0.5;
    return vec3(0.35 + sin(t * 1.2) * 0.15, 0.3 + cos(t * 0.8) * 0.1, 0.0);
}
float getBallRadius() { return 0.12; }

vec3 pos, vel, ovel;
vec2 c;

// IMPORTANT: Both read from iChannel0 (currentBuf), not iChannel1
vec3 getpos(vec2 id) {
    return texture(iChannel0, (id + 0.5) / iResolution.xy).xyz;
}

vec3 getvel(vec2 id) {
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iResolution.xy).xyz;
}

void edge(vec2 dif) {
    vec2 neighbor = c + dif;
    if (neighbor.x < 0.0 || neighbor.x >= SIZX || neighbor.y < 0.0 || neighbor.y >= SIZY) return;

    vec3 posdif = getpos(neighbor) - pos;
    vec3 veldif = getvel(neighbor) - ovel;
    float restLen = length(dif);

    float plen = length(posdif);
    if (plen < 0.0001) return;
    vec3 dir = posdif / plen;
    vel += dir * clamp(plen - restLen, -1.0, 1.0) * SPRING_K;
    vel += dir * dot(dir, veldif) * DAMPER_C;
}

void main() {
    vec2 fc = floor(vUv * iResolution.xy);
    c = fc;
    c.x = fract(c.x / SIZX) * SIZX;

    if (iFrame < ${SUBSTEPS}) {
        vec2 p = vec2(c.x / SIZX, c.y / SIZY);
        vec3 initialPos = vec3(p.x * 1.6 - 0.3, -p.y * 0.8 + 0.6, 0.0);
        fragColor = vec4(fc.x >= SIZX ? vec3(0.0) : initialPos, 0.0);
        return;
    }

    pos = getpos(c);
    vel = getvel(c);
    ovel = vel;

    edge(vec2(0.0, 1.0));
    edge(vec2(0.0, -1.0));
    edge(vec2(1.0, 0.0));
    edge(vec2(-1.0, 0.0));
    edge(vec2(1.0, 1.0));
    edge(vec2(-1.0, -1.0));
    edge(vec2(1.0, -1.0));
    edge(vec2(-1.0, 1.0));
    edge(vec2(0.0, 2.0));
    edge(vec2(0.0, -2.0));
    edge(vec2(2.0, 0.0));
    edge(vec2(-2.0, 0.0));

    vel.y -= GRAVITY;

    vec3 ballPos = getBallPos(iTime);
    float ballRadius = getBallRadius();
    vec3 toBall = pos - ballPos;
    float dist = length(toBall);
    if (dist < ballRadius && dist > 0.0001) {
        vec3 pushDir = toBall / dist;
        pos = ballPos + pushDir * ballRadius;
        vel -= pushDir * dot(pushDir, vel) * 1.2;
    }

    if (iMouse.z > 0.0) {
        vec2 mousePos = iMouse.xy / iResolution.xy;
        mousePos.y = 1.0 - mousePos.y;
        vec2 p = vec2(c.x / SIZX, c.y / SIZY);
        float mouseDist = length(p - mousePos);
        if (mouseDist < 0.15) {
            vec3 pushDir = vec3(mousePos - p, 0.2);
            float plen = length(pushDir);
            if (plen > 0.0001) {
                vel += (pushDir / plen) * (0.15 - mouseDist) * 0.5;
            }
        }
    }

    if (c.y < 1.0) {
        pos = vec3(fc.x * 1.6 / SIZX - 0.3, 0.6, 0.0);
        vel = vec3(0.0);
    }

    vel *= 0.998;
    pos += vel;

    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}`;

const fsImage = `#version 300 es
precision highp float;

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform vec2 iSimResolution;
uniform float iTime;
uniform vec4 iMouse;

in vec2 vUv;
out vec4 fragColor;

#define SIZX 128.0
#define SIZY 64.0

vec3 getBallPos(float time) {
    float t = time * 0.5;
    return vec3(0.35 + sin(t * 1.2) * 0.15, 0.3 + cos(t * 0.8) * 0.1, 0.0);
}
float getBallRadius() { return 0.12; }

vec3 getpos(vec2 id) {
    return texture(iChannel0, (id + 0.5) / iSimResolution).xyz;
}
vec3 getvel(vec2 id) {
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iSimResolution).xyz;
}

vec2 worldToScreen(vec3 p) {
    return vec2(p.x * 0.5 + 0.5, 1.0 - (p.y * 0.5 + 0.5));
}

vec3 calcNormal(vec2 cell) {
    vec3 pL = getpos(vec2(max(cell.x - 1.0, 0.0), cell.y));
    vec3 pR = getpos(vec2(min(cell.x + 1.0, SIZX - 1.0), cell.y));
    vec3 pD = getpos(vec2(cell.x, max(cell.y - 1.0, 0.0)));
    vec3 pU = getpos(vec2(cell.x, min(cell.y + 1.0, SIZY - 1.0)));
    vec3 tanX = pR - pL;
    vec3 tanY = pU - pD;
    vec3 normal = cross(tanX, tanY);
    float nlen = length(normal);
    if (nlen < 0.0001) return vec3(0.0, 0.0, -1.0);
    normal /= nlen;
    if (normal.z > 0.0) normal = -normal;
    return normal;
}

float cross2d(vec2 a, vec2 b) { return a.x * b.y - a.y * b.x; }

bool pointInTriangle(vec2 p, vec2 a, vec2 b, vec2 c, out vec3 bary) {
    float d00 = dot(b - a, b - a);
    float d01 = dot(b - a, c - a);
    float d11 = dot(c - a, c - a);
    float d20 = dot(p - a, b - a);
    float d21 = dot(p - a, c - a);
    float denom = d00 * d11 - d01 * d01;
    if (abs(denom) < 1e-10) return false;
    float v = (d11 * d20 - d01 * d21) / denom;
    float w = (d00 * d21 - d01 * d20) / denom;
    float u = 1.0 - v - w;
    bary = vec3(u, v, w);
    return u >= -0.01 && v >= -0.01 && w >= -0.01;
}

void main() {
    vec2 uv = vUv;
    vec3 bgTop = vec3(0.05, 0.08, 0.15);
    vec3 bgBot = vec3(0.02, 0.03, 0.08);
    vec3 bg = mix(bgBot, bgTop, uv.y);
    vec3 col = bg;
    float closestZ = 1e6;

    vec3 ballPos = getBallPos(iTime);
    float ballRadius = getBallRadius();
    vec2 ballScreen = worldToScreen(ballPos);
    float bsDist = length(uv - ballScreen);
    if (bsDist < ballRadius * 0.6) {
        float shade = smoothstep(ballRadius * 0.6, ballRadius * 0.15, bsDist);
        vec3 ballColor = vec3(0.95, 0.35, 0.2);
        vec2 bnXY = (uv - ballScreen) / (ballRadius * 0.6);
        float bnZ = sqrt(max(0.0, 1.0 - dot(bnXY, bnXY)));
        vec3 bn = normalize(vec3(bnXY, bnZ));
        vec3 ldir = normalize(vec3(0.5, 0.8, 1.0));
        float bdiff = max(dot(bn, ldir), 0.0);
        float bspec = pow(max(dot(normalize(bn + ldir), vec3(0.0,0.0,1.0)), 0.0), 32.0);
        col = ballColor * (0.3 + 0.7 * bdiff) + vec3(1.0) * bspec * 0.4;
        closestZ = ballPos.z - ballRadius;
    }

    for (float cy = 0.0; cy < SIZY - 1.0; cy += 1.0) {
        for (float cx = 0.0; cx < SIZX - 1.0; cx += 1.0) {
            vec3 p00 = getpos(vec2(cx, cy));
            vec3 p10 = getpos(vec2(cx + 1.0, cy));
            vec3 p01 = getpos(vec2(cx, cy + 1.0));
            vec3 p11 = getpos(vec2(cx + 1.0, cy + 1.0));
            vec2 s00 = worldToScreen(p00);
            vec2 s10 = worldToScreen(p10);
            vec2 s01 = worldToScreen(p01);
            vec2 s11 = worldToScreen(p11);
            vec2 bMin = min(min(s00, s10), min(s01, s11));
            vec2 bMax = max(max(s00, s10), max(s01, s11));
            if (uv.x < bMin.x - 0.01 || uv.x > bMax.x + 0.01 ||
                uv.y < bMin.y - 0.01 || uv.y > bMax.y + 0.01) continue;
            vec3 bary;
            bool hit = false;
            float interpZ = 0.0;
            vec2 cellId = vec2(cx, cy);
            if (pointInTriangle(uv, s00, s10, s01, bary)) {
                hit = true;
                interpZ = bary.x * p00.z + bary.y * p10.z + bary.z * p01.z;
            } else if (pointInTriangle(uv, s10, s11, s01, bary)) {
                hit = true;
                interpZ = bary.x * p10.z + bary.y * p11.z + bary.z * p01.z;
            }
            if (hit && interpZ < closestZ) {
                closestZ = interpZ;
                vec3 normal = calcNormal(cellId);
                vec3 ldir = normalize(vec3(0.5, 0.8, 1.0));
                float diff = max(dot(normal, ldir), 0.0);
                float diffBack = max(dot(-normal, ldir), 0.0);
                float spec = pow(max(dot(normalize(normal + ldir), vec3(0.0,0.0,1.0)), 0.0), 32.0);
                float stretch = length(getvel(cellId));
                vec3 cc1 = vec3(0.25, 0.55, 0.95);
                vec3 cc2 = vec3(0.95, 0.35, 0.45);
                vec3 cc = mix(cc1, cc2, clamp(stretch * 10.0, 0.0, 1.0));
                float checker = step(0.5, fract(cx * 0.125 + cy * 0.125));
                cc *= 0.85 + 0.15 * checker;
                col = cc * (0.3 + 0.6 * diff + 0.25 * diffBack) + vec3(1.0) * spec * 0.35;
            }
        }
    }

    col = col / (col + vec3(1.0));
    col = pow(col, vec3(0.9));
    fragColor = vec4(col, 1.0);
}`;

const progBuffer = createProgram(vsQuad, fsBuffer);
const progImage = createProgram(vsQuad, fsImage);

function createFramebuffer(width, height) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);

    const internalFormat = isFloat ? gl.RGBA32F : gl.RGBA8;
    const format = gl.RGBA;
    const type = isFloat ? gl.FLOAT : gl.UNSIGNED_BYTE;

    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, width, height, 0, format, type, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);

    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) {
        console.error('Framebuffer incomplete:', status);
    }

    return { fb, tex };
}

const SIM_W = 256;
const SIM_H = 128;
let bufA = createFramebuffer(SIM_W, SIM_H);
let bufB = createFramebuffer(SIM_W, SIM_H);

const quadVao = gl.createVertexArray();
gl.bindVertexArray(quadVao);
const quadBuf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const posLoc = gl.getAttribLocation(progBuffer, 'position');
gl.enableVertexAttribArray(posLoc);
gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

let mouseState = [0, 0, 0, 0];
canvas.addEventListener('mousemove', (e) => {
    mouseState[0] = e.clientX;
    mouseState[1] = e.clientY;
});
canvas.addEventListener('mousedown', () => { mouseState[2] = 1; });
canvas.addEventListener('mouseup', () => { mouseState[2] = 0; });

let frame = 0;
let globalStep = 0;
function render(time) {
    time *= 0.001;

    for (let substep = 0; substep < SUBSTEPS; substep++) {
        // IMPORTANT: ping-pong: read from currentBuf (iChannel0), write to nextBuf
        let currentBuf = (globalStep % 2 === 0) ? bufA : bufB;
        let nextBuf = (globalStep % 2 === 0) ? bufB : bufA;

        gl.bindFramebuffer(gl.FRAMEBUFFER, nextBuf.fb);
        gl.viewport(0, 0, SIM_W, SIM_H);
        gl.useProgram(progBuffer);

        // IMPORTANT: Only bind iChannel0 = currentBuf (read-only)
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, currentBuf.tex);
        gl.uniform1i(gl.getUniformLocation(progBuffer, 'iChannel0'), 0);

        gl.uniform2f(gl.getUniformLocation(progBuffer, 'iResolution'), SIM_W, SIM_H);
        gl.uniform1f(gl.getUniformLocation(progBuffer, 'iTime'), time);
        gl.uniform1i(gl.getUniformLocation(progBuffer, 'iFrame'), frame * SUBSTEPS + substep);
        gl.uniform4f(gl.getUniformLocation(progBuffer, 'iMouse'),
            mouseState[0], mouseState[1], mouseState[2], mouseState[3]);

        gl.bindVertexArray(quadVao);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        globalStep++;
    }

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.useProgram(progImage);

    const finalBuf = (globalStep % 2 === 0) ? bufA : bufB;

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, finalBuf.tex);
    gl.uniform1i(gl.getUniformLocation(progImage, 'iChannel0'), 0);

    gl.uniform2f(gl.getUniformLocation(progImage, 'iResolution'), canvas.width, canvas.height);
    gl.uniform2f(gl.getUniformLocation(progImage, 'iSimResolution'), SIM_W, SIM_H);
    gl.uniform1f(gl.getUniformLocation(progImage, 'iTime'), time);
    gl.uniform4f(gl.getUniformLocation(progImage, 'iMouse'),
        mouseState[0], mouseState[1], mouseState[2], mouseState[3]);

    gl.bindVertexArray(quadVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frame++;
    requestAnimationFrame(render);
}

requestAnimationFrame(render);
</script></body></html>
```

### Variant 3: Rigid Body Physics Engine (Box2D-lite on GPU)

```glsl
// Structured memory addressing: struct mapped to consecutive pixels
int bodyAddress(int b_id) {
    return pixel_count_of_Globals + pixel_count_of_Body * b_id;
}
Body loadBody(sampler2D buff, int b_id) {
    int addr = bodyAddress(b_id);
    vec4 d0 = texelFetch(buff, address2D(res, addr), 0);
    vec4 d1 = texelFetch(buff, address2D(res, addr+1), 0);
    b.pos = d0.xy; b.vel = d0.zw;
    b.ang = d1.x; b.ang_vel = d1.y;
}

// Contact impulse solver
float v_n = dot(dv, contact.normal);
float dp_n = contact.mass_n * (-v_n + contact.bias);
dp_n = max(0.0, dp_n);
body.vel += body.inv_mass * dp_n * contact.normal;
```

### Variant 4: N-Body Vortex Particles

```glsl
// Biot-Savart kernel: v = w * (-dy, dx) / |d|²
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = W(i, j);
        vec2 d = tex(i, j).xy - pos;
        d = (fract(0.5 + d / res) - 0.5) * res; // periodic boundary
        float l = dot(d, d);
        if (l > 1e-5) F += vec2(-d.y, d.x) * w / l;
    }
```

### Variant 5: 3D SPH Particle Fluid

```glsl
// 2D texture mapping for 3D grid
vec2 dim2from3(vec3 p3d) {
    float ny = floor(p3d.z / SCALE.x);
    float nx = floor(p3d.z) - ny * SCALE.x;
    return vec2(nx, ny) * size3d.xy + p3d.xy;
}

// SPH pressure force + friction + surface tension
float pressure = max(rho / rest_density - 1.0, 0.0);
float SPH_F = force_coef_a * GD(d, 1.5) * pressure;
float Friction = 0.45 * dot(dir, dvel) * GD(d, 1.5);
float F = surface_tension * GD(d, surface_tension_rad);
p.force += force_k * dir * (F + SPH_F + Friction) * irho / rest_density;
```

## Performance & Composition

### Performance Tips
- Use `texelFetch` instead of `texture` to skip filtering; precompute `1.0/iResolution.xy`
- N-Body: limit N to 20~30; passive marker particles (90%) skip force computation
- Cloth multi-substep: use 2 buffers + JS for loop (do not use 4-buffer chain)
- Adaptive precision: use larger time steps for distant regions
- Data packing: bit operations for compression (5-bit exponent + 3x9-bit components)
- Stability: `clamp` to prevent explosion, `smoothstep` for soft boundaries, damping 0.95~0.999

### Composition Patterns
- **Physics + post-processing**: wave refraction/caustics, fluid advection ink coloring, cloth ray tracing
- **Physics + SDF rendering**: `sdBox`/`length-radius` to render rigid bodies/particles
- **Physics + volume rendering**: density field trilinear interpolation → ray marching → lighting + shadows
- **Multi-system coupling**: fluid driving rigid bodies, cloth collision bodies, particle↔field mutual driving (SPH/Biot-Savart)
- **Physics + audio**: spectrum energy mapped as external force, low frequency drives large scale, high frequency drives small scale

## Further Reading

Full step-by-step tutorial, mathematical derivations, and advanced usage in [reference](../reference/simulation-physics.md)
