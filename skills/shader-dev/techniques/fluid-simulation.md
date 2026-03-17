**IMPORTANT: Common Error When Extracting Shaders from HTML Script Tags**: When extracting source from `<script type="x-shader/x-fragment">`, you must ensure `#version` is the **very first character** of the string, with no leading whitespace or newlines:
```javascript
// WRONG: indentation/newline inside script tag
// <script id="fs">
//     #version 300 es  <-- leading newline here!
// </script>
const source = document.getElementById('fs').textContent; // contains leading whitespace

// CORRECT: use .trim() or place template string flush with the start
const source = document.getElementById('fs').textContent.trim();
// Or in HTML, place content directly after the tag:
// <script id="fs">#version 300 es
// ...
```

### IMPORTANT: Float Texture Compatibility (Most Critical Issue for Fluid Simulation)

Fluid simulation requires float textures to store velocity (can be negative), pressure, and ink concentration (can exceed 1.0).

**IMPORTANT: Must use RGBA16F instead of RGBA32F**: Many environments (headless Chrome, SwiftShader, mobile) do not support `RGBA32F` render targets. Even when the `EXT_color_buffer_float` extension claims to be available, `RGBA32F` FBOs may silently fail (framebuffer reports complete but renders all zeros or all ones). `RGBA16F + HALF_FLOAT` has far better compatibility than `RGBA32F`, and its precision is more than sufficient for fluid simulation.

```javascript
const gl = canvas.getContext("webgl2");
if (!gl) { /* error handling */ }

const ext = gl.getExtension("EXT_color_buffer_float");
// IMPORTANT: Continue even if ext is null — some environments support RGBA16F without this extension

function createFloatTexture(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // IMPORTANT: Must use RGBA16F + HALF_FLOAT, do NOT use RGBA32F + FLOAT
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
}

function createFBO(w, h) {
    const tex = createFloatTexture(w, h);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) {
        console.error("FBO incomplete:", status);
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fbo, tex };
}
```

### Mouse Interaction Implementation

Fluid simulation requires tracking mouse position and drag direction. iMouse uniform convention: **xy=current mouse position, z=mouse down flag (>0 means pressed), w=unused**. Mouse velocity is calculated from the position difference between current and previous frames:

```javascript
// IMPORTANT: iMouse convention: xy=current position, z=pressed flag (1.0=down, 0.0=up), w=0
// Mouse velocity is computed via prevMouse on the JS side, passed through a separate uniform
let iMouse = [0, 0, 0, 0]; // [x, y, pressed, 0]
let prevMouse = [0, 0];
let mouseDown = false;

canvas.addEventListener('mousemove', (e) => {
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = canvas.height - e.clientY * dpr; // WebGL Y-axis is flipped
    if (mouseDown) {
        prevMouse[0] = iMouse[0];
        prevMouse[1] = iMouse[1];
        iMouse[0] = x;
        iMouse[1] = y;
    }
});

canvas.addEventListener('mousedown', (e) => {
    mouseDown = true;
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = canvas.height - e.clientY * dpr;
    iMouse[0] = x; iMouse[1] = y;
    iMouse[2] = 1.0; // Flag: mouse pressed
    prevMouse[0] = x; prevMouse[1] = y;
});

canvas.addEventListener('mouseup', () => {
    mouseDown = false;
    iMouse[2] = 0.0; // Flag: mouse released
});

// Pass uniforms in render loop
// iMouse: xy=position, z=pressed flag, w=0
gl.uniform4f(uMouse, iMouse[0], iMouse[1], iMouse[2], 0.0);
// IMPORTANT: Mouse velocity must be clamped, otherwise fast dragging produces huge velocity deltas causing NaN explosion
const mvx = Math.max(-50, Math.min(50, iMouse[0] - prevMouse[0]));
const mvy = Math.max(-50, Math.min(50, iMouse[1] - prevMouse[1]));
gl.uniform2f(uMouseVel, mvx, mvy);
```

### Handling WebGL 2 Unavailability

```javascript
const gl = canvas.getContext("webgl2");
if (!gl) {
    document.body.innerHTML = `
        <div style="color:#fff;padding:20px;font-family:sans-serif;">
            <h2>WebGL 2 Not Supported</h2>
            <p>Fluid simulation requires WebGL 2. Please use a modern browser (Chrome 56+, Firefox 51+, Safari 15+).</p>
        </div>
    `;
    throw new Error('WebGL2 not supported');
}
```

# Real-Time Fluid Simulation

## Use Cases
- Real-time 2D fluid effects in ShaderToy/WebGL (smoke, liquids, ink diffusion)
- Interactive fluid: mouse/touch-driven fluid response
- **Ink diffusion/curling vortex effects in water**: vorticity confinement + high diffusion coefficient + single or multi-color ink
- **Multi-color ink mixing**: multiple ink colors interpenetrating and blending (requires Buffer B to store RGB ink, see multi-color ink mixing template)
- Decorative fluid backgrounds, particle systems, vortex visualization
- **Lava/fire/magma effects**: fluid simulation + FBM noise texture + temperature color mapping
- **Water surface ripple effects**: wave equation + click-generated concentric ripples + interference and damping
- Core: solving simplified Navier-Stokes equations or wave equations in GPU fragment shaders

## Core Principles

Incompressible Navier-Stokes equation discretization:

```
Momentum equation: ∂v/∂t = -(v·∇)v - ∇p + ν∇²v + f
Continuity equation: ∇·v = 0
```

Term meanings: `-(v·∇)v` advection, `-∇p` pressure gradient, `ν∇²v` viscous diffusion, `f` external forces.
Zero divergence = incompressibility constraint, achieved by projecting the velocity field through the pressure Poisson equation.

**ShaderToy implementation strategy**: texture buffer inter-frame feedback, each frame executes: advection → diffusion → external forces → pressure projection. Each pixel stores grid point physical quantities (velocity, pressure, density).

### Water Surface Ripple Principles (Wave Equation)

Water surface ripples use the 2D wave equation rather than Navier-Stokes:

```
∂²h/∂t² = c² * ∇²h - damping * ∂h/∂t
```

Discretized using Verlet integration: `next = speed * (2*curr - prev + laplacian) * damping`.

Data encoding: `.r = previous frame height (prev)`, `.g = current frame height (curr)`. Each frame computes the Laplacian to advance the wavefront, with ping-pong buffers alternating read/write.

## Implementation Steps

### Step 1: Data Encoding & Neighborhood Sampling
```glsl
// Data layout: .xy=velocity, .z=pressure/density, .w=ink
#define T(p) texture(iChannel0, (p) / iResolution.xy)

vec4 c = T(p);                    // center
vec4 n = T(p + vec2(0, 1));       // north
vec4 e = T(p + vec2(1, 0));       // east
vec4 s = T(p - vec2(0, 1));       // south
vec4 w = T(p - vec2(1, 0));       // west
```

### Step 2: Discrete Differential Operators
```glsl
// Laplacian (weighted 3x3 stencil)
const float _K0 = -20.0 / 6.0;
const float _K1 =   4.0 / 6.0;
const float _K2 =   1.0 / 6.0;
vec4 laplacian = _K0 * c
    + _K1 * (n + e + s + w)
    + _K2 * (T(p+vec2(1,1)) + T(p+vec2(-1,1)) + T(p+vec2(1,-1)) + T(p+vec2(-1,-1)));

// Gradient (central difference)
vec4 dx = (e - w) / 2.0;
vec4 dy = (n - s) / 2.0;

// Divergence & Curl
float div = dx.x + dy.y;
float curl = dx.y - dy.x;
```

### Step 3: Semi-Lagrangian Advection
```glsl
#define DT 0.15  // time step
// Backward trace: sample from upstream, unconditionally stable
vec4 advected = T(p - DT * c.xy);
c.xyw = advected.xyw;
```

### Step 4: Viscous Diffusion
```glsl
#define NU 0.5     // kinematic viscosity (0.01=water, 1.0=syrup)
#define KAPPA 0.1  // ink diffusion coefficient

c.xy += DT * NU * laplacian.xy;
c.w  += DT * KAPPA * laplacian.w;
```

### Step 5: Pressure Projection
```glsl
#define K 0.2  // pressure correction strength
c.xy -= K * vec2(dx.z, dy.z);
c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
```

### Step 6: Mouse Interaction
```glsl
// IMPORTANT: iMouse.z is the mouse-down flag (>0=pressed), not a position coordinate
// iMouseVel is mouse movement velocity, passed via a separate uniform
// IMPORTANT: Must clamp mouseVel to prevent NaN explosion
if (iMouse.z > 0.0) {
    vec2 mouseVel = clamp(iMouseVel, vec2(-50.0), vec2(50.0));
    float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
    float influence = exp(-dist2 / 50.0);  // 50.0=influence radius
    c.xy += DT * influence * mouseVel;
    c.w  += DT * influence * 0.5;
}
```

### Step 6b: Vorticity Confinement (Required for Ink Curling Effects)
```glsl
// IMPORTANT: Ink diffusion/swirl effects require vorticity confinement, otherwise small vortices dissipate quickly leaving only smooth flow
// Vorticity confinement re-injects energy into small-scale vortices, producing characteristic curling textures
#define VORT_STR 0.035  // [0.01=subtle, 0.05=noticeable, 0.1=strong]
float curl_c = dx.y - dy.x;
float curl_n = (T(p + vec2(1,1)).y - T(p + vec2(-1,1)).y) / 2.0
             - (T(p + vec2(0,2)).x - T(p).x) / 2.0;
float curl_s = (T(p + vec2(1,-1)).y - T(p + vec2(-1,-1)).y) / 2.0
             - (T(p).x - T(p + vec2(0,-2)).x) / 2.0;
float curl_e = (T(p + vec2(2,0)).y - T(p).y) / 2.0
             - (T(p + vec2(1,1)).x - T(p + vec2(1,-1)).x) / 2.0;
float curl_w = (T(p).y - T(p + vec2(-2,0)).y) / 2.0
             - (T(p + vec2(-1,1)).x - T(p + vec2(-1,-1)).x) / 2.0;
vec2 eta = normalize(vec2(abs(curl_e)-abs(curl_w), abs(curl_n)-abs(curl_s)) + vec2(1e-5));
c.xy += DT * VORT_STR * vec2(eta.y, -eta.x) * curl_c;
```

### Step 7: Automatic Ink Sources (Critical: Ensures Visible Output Without Interaction)
```glsl
// IMPORTANT: Must have automatic ink sources! Otherwise the screen is completely black without mouse interaction
// IMPORTANT: Ink injection and decay must be balanced! Too-strong injection or too-weak decay causes ink saturation across the entire screen → solid color with no features
// IMPORTANT: Gaussian denominator controls emitter radius — larger denominator means larger emitter!
//     Denominator > 300 makes emitter cover most of the screen, ink saturates quickly
//     Recommended 100~200, keeping it locally concentrated with visible gradient falloff at distance
float t = iTime;

// Emitter positions should move over time for dynamic effects
vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));

// Gaussian influence radius controls locality (smaller denominator = more concentrated, 100~200 is reasonable)
float r1 = exp(-dot(p - em1, p - em1) / 150.0);
float r2 = exp(-dot(p - em2, p - em2) / 150.0);
float r3 = exp(-dot(p - em3, p - em3) / 120.0);

// Inject velocity (rotating, crossing directions make fluid motion more interesting)
c.xy += DT * r1 * vec2(cos(t), sin(t * 1.3)) * 3.0;
c.xy += DT * r2 * vec2(-cos(t * 0.8), sin(t * 0.6)) * 3.0;
c.xy += DT * r3 * vec2(sin(t * 1.1), -cos(t)) * 2.0;

// Inject ink (note: injection amount must balance with INK_DECAY, otherwise screen saturates)
c.w += DT * (r1 + r2 + r3) * 2.0;
```

### Step 8: Boundaries & Stability
```glsl
// No-slip boundary
if (p.x < 1.0 || p.y < 1.0 ||
    iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
    c.xyw *= 0.0;
}

// IMPORTANT: Ink decay — must use multiplicative decay (e.g., *= 0.99), NOT subtractive decay (-= constant)
// Subtractive decay zeros out quickly at small ink values and decays too slowly at large values, causing saturation
// Multiplicative decay scales proportionally, maintaining contrast at any concentration
c.w *= 0.99;  // 1% decay per frame, adjustable [0.98=fast dissipation, 0.995=persistent]

c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));
```

### Step 9: Visualization (Image Pass) — General Fluid
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces [0,1] range bright colors
    // Never use vec3(0.02, 0.01, 0.08) or similar near-zero base colors — they become invisible when multiplied by ink
    float angle = atan(c.y, c.x);
    vec3 col = 0.5 + 0.5 * cos(angle + vec3(0.0, 2.1, 4.2));

    // IMPORTANT: Use smoothstep to map ink concentration; upper limit should exceed actual ink range to preserve gradients
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // Pressure highlights
    col += vec3(0.05) * clamp(c.z - 1.0, 0.0, 1.0);

    // IMPORTANT: Background color must be visible (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```

### Step 9b: Visualization (Image Pass) — Lava/Fire/Magma Effects

Lava/fire requires FBM noise for turbulent textures + temperature color band mapping. **Key: Must use FBM noise to distort UV coordinates and temperature values, otherwise the image is too smooth and looks like a plain gradient rather than lava.**

```glsl
// IMPORTANT: FBM noise is the core of lava/fire visualization! Without it the image is a smooth gradient with no lava texture
// These noise functions must be defined in the Image Pass

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // smoothstep hermite
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// IMPORTANT: octaves=4~6 produces sufficient detail; fewer than 3 gives too-coarse textures
float fbm(vec2 p, int octaves) {
    float val = 0.0;
    float amp = 0.5;
    for (int i = 0; i < octaves; i++) {
        val += amp * noise(p);
        p *= 2.0;
        amp *= 0.5;
    }
    return val;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);
    float t = iTime;

    // Use fluid velocity field to distort noise sampling coordinates so noise moves with the fluid
    vec2 distortedUV = uv + c.xy * 0.002;
    // FBM noise: multi-octave superposition produces turbulent detail
    float n1 = fbm(distortedUV * 8.0 + t * 0.3, 5);
    float n2 = fbm(distortedUV * 4.0 - t * 0.2 + 5.0, 4);

    float ink = smoothstep(0.0, 2.0, c.w);
    float speed = length(c.xy);

    // Temperature = ink concentration + noise perturbation + speed contribution
    // IMPORTANT: Noise perturbation amplitude of 0.2~0.4 produces visible texture without becoming noisy
    float temp = ink * 0.7 + n1 * 0.25 + speed * 0.1;
    // Second noise layer for cracks/dark veins
    temp -= (1.0 - n2) * 0.15 * ink;
    temp = clamp(temp, 0.0, 1.0);

    // Lava temperature color band: black → dark red → orange → yellow → white-hot
    vec3 col;
    if (temp < 0.15) {
        col = mix(vec3(0.05, 0.0, 0.0), vec3(0.5, 0.05, 0.0), temp / 0.15);
    } else if (temp < 0.4) {
        col = mix(vec3(0.5, 0.05, 0.0), vec3(1.0, 0.35, 0.0), (temp - 0.15) / 0.25);
    } else if (temp < 0.7) {
        col = mix(vec3(1.0, 0.35, 0.0), vec3(1.0, 0.75, 0.1), (temp - 0.4) / 0.3);
    } else {
        col = mix(vec3(1.0, 0.75, 0.1), vec3(1.0, 0.95, 0.7), clamp((temp - 0.7) / 0.3, 0.0, 1.0));
    }

    // Glow effect: additional additive glow in high-temperature regions
    float glow = smoothstep(0.5, 1.0, temp) * 0.4;
    col += vec3(1.0, 0.5, 0.1) * glow;

    // HDR tone mapping
    col = 1.0 - exp(-col * 1.5);

    col = max(col, vec3(0.03, 0.005, 0.0));
    fragColor = vec4(col, 1.0);
}
```

### Step 9c: Visualization (Image Pass) — Water Surface Ripple Effects

The water ripple Image Pass computes normals from the height field, then applies lighting + environment reflection. **Key: Normal perturbation strength must be large enough (50~100), water base color must be bright (blue component > 0.15), and specular highlights must be prominent.**

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;

    // IMPORTANT: Sample from wave height field: .g channel stores current frame height
    float h = texture(iChannel0, uv).g;
    float hn = texture(iChannel0, uv + vec2(0.0, texel.y)).g;
    float hs = texture(iChannel0, uv - vec2(0.0, texel.y)).g;
    float he = texture(iChannel0, uv + vec2(texel.x, 0.0)).g;
    float hw = texture(iChannel0, uv - vec2(texel.x, 0.0)).g;

    // IMPORTANT: Normal perturbation factor must be large enough (50~100), otherwise ripples are invisible
    // If drop strength is 1.0 and radius is 8~15px, using 80.0 produces clearly visible ripples
    vec3 normal = normalize(vec3((hw - he) * 80.0, (hs - hn) * 80.0, 1.0));

    vec3 lightDir = normalize(vec3(0.3, 0.5, 1.0));
    vec3 viewDir = vec3(0.0, 0.0, 1.0);
    vec3 halfVec = normalize(lightDir + viewDir);

    float diffuse = max(dot(normal, lightDir), 0.0);
    float specular = pow(max(dot(normal, halfVec), 0.0), 64.0);

    // IMPORTANT: Water base color must be bright enough! Deep color no darker than vec3(0.02, 0.08, 0.2), shallow color use vec3(0.1, 0.3, 0.6)
    vec3 deepColor = vec3(0.02, 0.08, 0.22);
    vec3 shallowColor = vec3(0.1, 0.35, 0.65);
    vec3 waterColor = mix(deepColor, shallowColor, 0.5 + h * 5.0);

    float fresnel = pow(1.0 - max(dot(normal, viewDir), 0.0), 3.0);

    vec3 col = waterColor * (0.4 + 0.6 * diffuse);
    col += vec3(0.9, 0.95, 1.0) * specular * 2.0;
    col += vec3(0.15, 0.25, 0.45) * fresnel * 0.6;

    // Caustic effect
    float caustic = pow(max(diffuse, 0.0), 8.0) * abs(h) * 5.0;
    col += vec3(0.15, 0.35, 0.55) * caustic;

    col = max(col, vec3(0.02, 0.06, 0.15));
    col = pow(col, vec3(0.95));

    fragColor = vec4(col, 1.0);
}
```

## IMPORTANT: Common Fatal Errors

1. **RGBA32F silently fails in headless/SwiftShader environments**: Must use `RGBA16F + HALF_FLOAT`
2. **Ink saturates entire screen**: Gaussian denominator too large (>300) or decay too weak (>0.995). Fix: denominator 100~200, decay `*= 0.99`
3. **Image Pass colors too dark causing all-black screen**: Use `0.5 + 0.5 * cos(...)` color base to ensure bright range
4. **Unclamped mouse velocity causing NaN crash**: Fast dragging or first-frame clicks produce huge velocity deltas → velocity explosion → NaN propagates across entire screen. **Both JS side and shader side must clamp mouseVel to [-50, 50]**
5. **Using single scalar for multi-color ink prevents mixing**: A single `c.w` can only do single-color. Multi-color ink requires Buffer B to store RGB three channels (see multi-color ink mixing template)
6. **GLSL strict typing**: `vec2 = float` is illegal, must use `vec2(float)`; integers and floats cannot be mixed

## Complete Code Template

Setup: Buffer A's iChannel0 points to Buffer A itself (feedback loop).

### Standalone HTML JS Skeleton (Ping-Pong Render Pipeline)

Fluid simulation requires framebuffer self-feedback + float textures. The following JS skeleton demonstrates the correct WebGL2 multi-pass ping-pong structure:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluid Simulation</title>
<style>
/* IMPORTANT: Critical: canvas must fill the viewport, otherwise it may be invisible or clipped */
*{margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#000}
canvas{display:block;width:100%;height:100%}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
let frameCount = 0;
// IMPORTANT: iMouse convention: [x, y, pressedFlag, 0] — z is the pressed flag (1 or 0), not a coordinate
let mouse = [0, 0, 0, 0];
let prevMouse = [0, 0];
let mouseDown = false;

const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
if (!gl) {
    document.body.innerHTML = '<div style="color:#fff;padding:20px;font-family:sans-serif;"><h2>WebGL 2 not supported</h2></div>';
    throw new Error('WebGL2 not supported');
}
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
    if (!gl.getProgramParameter(p, gl.LINK_STATUS))
        console.error(gl.getProgramInfoLog(p));
    return p;
}

const vsSource = `#version 300 es
in vec2 pos;
void main(){ gl_Position=vec4(pos,0,1); }`;

// fsBuffer / fsImage: adapt from the Buffer A / Image templates below
// IMPORTANT: Fragment shaders must declare these uniforms:
//   uniform sampler2D iChannel0;
//   uniform vec2 iResolution;
//   uniform float iTime;
//   uniform int iFrame;
//   uniform vec4 iMouse;    // xy=position, z=pressed flag, w=0
//   uniform vec2 iMouseVel; // mouse movement velocity (only needed in Buffer pass)

const progBuf = createProgram(vsSource, fsBuffer);
const progImg = createProgram(vsSource, fsImage);

// IMPORTANT: Must use RGBA16F + HALF_FLOAT, do NOT use RGBA32F + FLOAT
// RGBA32F may render all zeros in headless Chrome / SwiftShader even when framebuffer reports complete
function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
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
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    canvas.width = W = Math.floor(innerWidth * dpr);
    canvas.height = H = Math.floor(innerHeight * dpr);
    bufA = createFBO(W, H);
    bufB = createFBO(W, H);
    frameCount = 0;
}
addEventListener('resize', resize);
resize();

canvas.addEventListener('mousemove', e => {
    const dpr = Math.min(devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = H - e.clientY * dpr;
    if (mouseDown) {
        prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
        mouse[0] = x; mouse[1] = y;
    }
});
canvas.addEventListener('mousedown', e => {
    mouseDown = true;
    const dpr = Math.min(devicePixelRatio, 1.5);
    mouse[0] = e.clientX * dpr;
    mouse[1] = H - e.clientY * dpr;
    mouse[2] = 1.0; // IMPORTANT: Pressed flag, not a coordinate
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
});
canvas.addEventListener('mouseup', () => {
    mouseDown = false;
    mouse[2] = 0.0; // IMPORTANT: Released flag
});

// Touch events (mobile)
canvas.addEventListener('touchstart', e => {
    e.preventDefault(); mouseDown = true;
    const t = e.touches[0], dpr = Math.min(devicePixelRatio, 1.5);
    mouse[0] = t.clientX * dpr; mouse[1] = H - t.clientY * dpr;
    mouse[2] = 1.0;
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
}, {passive:false});
canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = e.touches[0], dpr = Math.min(devicePixelRatio, 1.5);
    if (mouseDown) {
        prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
        mouse[0] = t.clientX * dpr; mouse[1] = H - t.clientY * dpr;
    }
}, {passive:false});
canvas.addEventListener('touchend', () => { mouseDown = false; mouse[2] = 0.0; });

// Cache uniform locations (avoid per-frame lookups)
const uBuf = {
    ch0: gl.getUniformLocation(progBuf, 'iChannel0'),
    res: gl.getUniformLocation(progBuf, 'iResolution'),
    time: gl.getUniformLocation(progBuf, 'iTime'),
    frame: gl.getUniformLocation(progBuf, 'iFrame'),
    mouse: gl.getUniformLocation(progBuf, 'iMouse'),
    mouseVel: gl.getUniformLocation(progBuf, 'iMouseVel')
};
const uImg = {
    ch0: gl.getUniformLocation(progImg, 'iChannel0'),
    res: gl.getUniformLocation(progImg, 'iResolution'),
    time: gl.getUniformLocation(progImg, 'iTime')
};

function render(t) {
    t *= 0.001;

    // Buffer pass: read bufA → write bufB
    gl.useProgram(progBuf);
    gl.bindFramebuffer(gl.FRAMEBUFFER, bufB.fbo);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(uBuf.ch0, 0);
    gl.uniform2f(uBuf.res, W, H);
    gl.uniform1f(uBuf.time, t);
    gl.uniform1i(uBuf.frame, frameCount);
    gl.uniform4f(uBuf.mouse, mouse[0], mouse[1], mouse[2], 0.0);
    // IMPORTANT: Must clamp mouse velocity! Fast movement or first-frame clicks can produce huge velocity values,
    // causing shader velocity explosion → NaN propagation → page crash
    const mvx = Math.max(-50, Math.min(50, mouse[0] - prevMouse[0]));
    const mvy = Math.max(-50, Math.min(50, mouse[1] - prevMouse[1]));
    gl.uniform2f(uBuf.mouseVel, mvx, mvy);
    gl.bindVertexArray(vao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufA, bufB] = [bufB, bufA];

    // Reset prevMouse each frame to avoid velocity accumulation
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];

    // Image pass: read bufA → screen
    gl.useProgram(progImg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(uImg.ch0, 0);
    gl.uniform2f(uImg.res, W, H);
    gl.uniform1f(uImg.time, t);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frameCount++;
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
```

**Buffer A (Fluid Computation)**:
```glsl
// Grid-Based Euler Fluid Solver — Buffer A
// Data layout: .xy=velocity, .z=pressure/density, .w=ink
// iChannel0 = Buffer A (self-feedback)

#define DT 0.15          // time step [0.05 - 0.3]
#define K 0.2            // pressure correction strength [0.1 - 0.4]
#define NU 0.5           // viscosity coefficient [0.01=water, 1.0=syrup]
#define KAPPA 0.1        // ink diffusion coefficient [0.0 - 0.5]
#define MOUSE_RAD 50.0   // mouse influence radius [10.0 - 200.0]

#define T(p) texture(iChannel0, (p) / iResolution.xy)

void mainImage(out vec4 fragColor, in vec2 p) {
    // Initial frames: add slight noise to break symmetry lock
    if (iFrame < 10) {
        vec2 uv = p / iResolution.xy;
        float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
        fragColor = vec4(noise * 1e-4, noise * 1e-4, 1.0, 0.0);
        return;
    }

    vec4 c = T(p);

    vec4 n = T(p + vec2(0, 1));
    vec4 e = T(p + vec2(1, 0));
    vec4 s = T(p - vec2(0, 1));
    vec4 w = T(p - vec2(1, 0));

    vec4 laplacian = (n + e + s + w - 4.0 * c);
    vec4 dx = (e - w) / 2.0;
    vec4 dy = (n - s) / 2.0;
    float div = dx.x + dy.y;

    c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
    c.xyw = T(p - DT * c.xy).xyw;
    c.xyw += DT * vec3(NU, NU, KAPPA) * laplacian.xyw;
    c.xy -= K * vec2(dx.z, dy.z);

    // Mouse interaction: iMouse.z is the pressed flag (>0), velocity obtained via iMouseVel uniform
    // IMPORTANT: mouseVel must be clamped to prevent NaN explosion (JS side should also clamp — double safety)
    if (iMouse.z > 0.0) {
        vec2 mouseVel = clamp(iMouseVel, vec2(-50.0), vec2(50.0));
        float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
        float influence = exp(-dist2 / MOUSE_RAD);
        c.xy += DT * influence * mouseVel;
        c.w  += DT * influence * 0.5;
    }

    // Vorticity confinement: prevents small vortices from dissipating too quickly, producing curling textures
    // IMPORTANT: Ink diffusion/swirl effects (e.g., ink diffusing in water) require vorticity confinement, otherwise curl dissipates quickly leaving only smooth flow
    float curl_c = dx.y - dy.x;
    float curl_n = (T(p + vec2(1,1)).y - T(p + vec2(-1,1)).y) / 2.0
                 - (T(p + vec2(0,2)).x - T(p).x) / 2.0;
    float curl_s = (T(p + vec2(1,-1)).y - T(p + vec2(-1,-1)).y) / 2.0
                 - (T(p).x - T(p + vec2(0,-2)).x) / 2.0;
    float curl_e = (T(p + vec2(2,0)).y - T(p).y) / 2.0
                 - (T(p + vec2(1,1)).x - T(p + vec2(1,-1)).x) / 2.0;
    float curl_w = (T(p).y - T(p + vec2(-2,0)).y) / 2.0
                 - (T(p + vec2(-1,1)).x - T(p + vec2(-1,-1)).x) / 2.0;
    vec2 eta = vec2(abs(curl_e) - abs(curl_w), abs(curl_n) - abs(curl_s));
    eta = normalize(eta + vec2(1e-5));
    c.xy += DT * 0.035 * vec2(eta.y, -eta.x) * curl_c;

    // IMPORTANT: Automatic ink sources: ensure visible fluid motion without mouse interaction
    // Emitter positions must move over time, and Gaussian radius must be small enough to maintain locality
    float t = iTime;
    vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
    vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
    vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));

    float r1 = exp(-dot(p - em1, p - em1) / 150.0);
    float r2 = exp(-dot(p - em2, p - em2) / 150.0);
    float r3 = exp(-dot(p - em3, p - em3) / 120.0);

    c.xy += DT * r1 * vec2(cos(t), sin(t * 1.3)) * 3.0;
    c.xy += DT * r2 * vec2(-cos(t * 0.8), sin(t * 0.6)) * 3.0;
    c.xy += DT * r3 * vec2(sin(t * 1.1), -cos(t)) * 2.0;
    c.w += DT * (r1 + r2 + r3) * 2.0;

    // IMPORTANT: Ink decay: must use multiplicative decay, do NOT use subtractive (subtractive causes saturation)
    c.w *= 0.99;

    c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));

    if (p.x < 1.0 || p.y < 1.0 ||
        iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
        c.xyw *= 0.0;
    }

    fragColor = c;
}
```

**Image (Visualization Rendering)**:
```glsl
// Fluid Visualization — Image Pass
// iChannel0 = Buffer A

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces [0,1] range bright colors
    // Never use vec3(0.02, 0.01, 0.08) or similar extremely dark base colors — they become invisible when multiplied by ink
    float angle = atan(c.y, c.x);
    vec3 col = 0.5 + 0.5 * cos(angle + vec3(0.0, 2.1, 4.2));

    // IMPORTANT: smoothstep upper limit should cover actual ink range to preserve gradient variation
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // Pressure highlights
    col += vec3(0.05) * clamp(c.z - 1.0, 0.0, 1.0);

    // IMPORTANT: Background color must be visible (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```

## Water Surface Ripple Complete Template

Water surface ripples use the wave equation rather than Navier-Stokes. Clicks/touches generate concentric ripples that interfere with each other and gradually decay.

**IMPORTANT: Water ripple drop injection must be implemented directly in the shader using iMouse**, do not use custom uniform arrays to pass click positions — that adds complexity on both JS/GLSL sides and is error-prone (uniform location not found, array length mismatch, etc.).

### Water Ripple Buffer Pass (Wave Equation Solver)

```glsl
// Water Ripple — Buffer Pass (Wave Equation Solver)
// Data encoding: .r = previous frame height (prev), .g = current frame height (curr)
// iChannel0 = self-feedback (ping-pong)
// IMPORTANT: Drop injection is done directly in the shader via iMouse, no custom uniforms needed

void main() {
    vec2 p = gl_FragCoord.xy;
    vec2 uv = p / iResolution.xy;

    if (iFrame < 2) {
        fragColor = vec4(0.0);
        return;
    }

    float prev = texture(iChannel0, uv).r;
    float curr = texture(iChannel0, uv).g;

    vec2 texel = 1.0 / iResolution.xy;
    float n = texture(iChannel0, uv + vec2(0.0, texel.y)).g;
    float s = texture(iChannel0, uv - vec2(0.0, texel.y)).g;
    float e = texture(iChannel0, uv + vec2(texel.x, 0.0)).g;
    float w = texture(iChannel0, uv - vec2(texel.x, 0.0)).g;

    float laplacian = n + s + e + w - 4.0 * curr;

    // Verlet integration: next = 2*curr - prev + c²*laplacian
    float speed = 0.45;
    float next = 2.0 * curr - prev + speed * laplacian;

    // damping: 0.995~0.998 lets ripples propagate several rings before disappearing
    float damping = 0.996;
    next *= damping;

    // IMPORTANT: Mouse click drop injection — directly using iMouse, simple and reliable
    // iMouse.z > 0 indicates mouse is pressed
    if (iMouse.z > 0.0) {
        float dist = length(p - iMouse.xy);
        float radius = 12.0;
        float strength = 1.5;
        next += strength * exp(-dist * dist / (2.0 * radius * radius));
    }

    // IMPORTANT: Automatic ripples: ensure visible ripples even without interaction
    // Use periodic functions of iTime to control auto-drop position and timing
    float autoPhase = iTime * 0.5;
    float autoPeriod = fract(autoPhase);
    // Only inject during phase < 0.05 each cycle (avoid continuous injection)
    if (autoPeriod < 0.05) {
        float idx = floor(autoPhase);
        // Pseudo-random position
        vec2 autoPos = iResolution.xy * vec2(
            0.2 + 0.6 * fract(sin(idx * 12.9898) * 43758.5453),
            0.2 + 0.6 * fract(sin(idx * 78.233) * 43758.5453)
        );
        float dist = length(p - autoPos);
        next += 1.2 * exp(-dist * dist / (2.0 * 10.0 * 10.0));
    }

    // Boundary absorption
    if (p.x < 2.0 || p.y < 2.0 ||
        iResolution.x - p.x < 2.0 || iResolution.y - p.y < 2.0) {
        next *= 0.0;
    }

    // IMPORTANT: Output: .r = current frame (becomes next frame's prev), .g = newly computed (becomes next frame's curr)
    fragColor = vec4(curr, next, 0.0, 1.0);
}
```

### Water Ripple JS Side

The water ripple JS structure is identical to the fluid simulation skeleton (ping-pong FBO + render loop), with only these differences:
- Buffer pass shader is the wave equation solver (template above)
- Image pass is the water surface lighting renderer (Step 9c)
- **No custom uniform arrays needed**, drop injection is done entirely in the shader via iMouse
- JS side only needs to pass standard uniforms: `iChannel0, iResolution, iTime, iFrame, iMouse`

When dragging the mouse, ripples are continuously injected (because iMouse.z > 0 remains true), and faster dragging produces denser ripples (a natural effect).

### Water Ripple Image Pass

See Step 9c above.

## Multi-Color Ink Mixing Template (Ink Diffusion in Water / Multi-Color Blending)

When multiple ink colors need to interpenetrate and blend, a single scalar `c.w` is insufficient. You need **two Buffers**: Buffer A stores velocity/pressure (same as above), Buffer B stores RGB three-channel ink concentration, sharing the same velocity field for advection.

**IMPORTANT: Key for multi-color ink: Buffer B's RGB channels independently store the concentration of each ink color, using Buffer A's velocity field for semi-Lagrangian advection. Different ink colors naturally blend during advection and diffusion.**

### JS Side Changes (Three Buffer Ping-Pong)

Two sets of ping-pong FBOs are needed: `bufA/bufB` (velocity field) and `bufC/bufD` (ink RGB). In the render loop, first render Buffer A (velocity field), then Buffer B (ink advection), and finally the Image pass reads Buffer B for visualization:

```javascript
// Create additional ink FBO pair
let bufC, bufD;
function resize() {
    // ... same as above for bufA/bufB ...
    bufC = createFBO(W, H);
    bufD = createFBO(W, H);
}

// Buffer B shader needs two input textures:
// iChannel0 = Buffer B self (ink RGB)
// iChannel1 = Buffer A (velocity field)
const uBufInk = {
    ch0: gl.getUniformLocation(progBufInk, 'iChannel0'),
    ch1: gl.getUniformLocation(progBufInk, 'iChannel1'),
    res: gl.getUniformLocation(progBufInk, 'iResolution'),
    time: gl.getUniformLocation(progBufInk, 'iTime'),
    frame: gl.getUniformLocation(progBufInk, 'iFrame'),
    mouse: gl.getUniformLocation(progBufInk, 'iMouse'),
};

function render(t) {
    t *= 0.001;
    // Pass 1: Buffer A (velocity) — read bufA, write bufB
    // ... same as above ...
    [bufA, bufB] = [bufB, bufA];

    // Pass 2: Buffer B (ink RGB) — read bufC(ink)+bufA(velocity), write bufD
    gl.useProgram(progBufInk);
    gl.bindFramebuffer(gl.FRAMEBUFFER, bufD.fbo);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufC.tex);  // previous frame ink
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);  // current velocity field
    gl.uniform1i(uBufInk.ch0, 0);
    gl.uniform1i(uBufInk.ch1, 1);
    gl.uniform2f(uBufInk.res, W, H);
    gl.uniform1f(uBufInk.time, t);
    gl.uniform1i(uBufInk.frame, frameCount);
    gl.uniform4f(uBufInk.mouse, mouse[0], mouse[1], mouse[2], 0.0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufC, bufD] = [bufD, bufC];

    // Pass 3: Image — read bufC(ink) to screen
    gl.useProgram(progImg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufC.tex);
    // ...
}
```

### Buffer B — Multi-Color Ink Advection Shader

```glsl
// Multi-Color Ink — Buffer B (Ink Advection)
// .rgb = concentrations of three ink colors
// iChannel0 = Buffer B self (ink RGB)
// iChannel1 = Buffer A (velocity field, .xy=velocity)

#define DT 0.15
#define INK_KAPPA 0.3        // ink diffusion coefficient (higher than single-color template for faster blending)
#define INK_DECAY 0.995      // ink decay (slower than single-color to maintain richness)

#define TINK(p) texture(iChannel0, (p) / iResolution.xy)
#define TVEL(p) texture(iChannel1, (p) / iResolution.xy)

void mainImage(out vec4 fragColor, in vec2 p) {
    if (iFrame < 10) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }

    vec2 vel = TVEL(p).xy;

    // Semi-Lagrangian advection: backward trace using velocity field
    vec3 ink = TINK(p - DT * vel).rgb;

    // Diffusion: Laplacian operator
    vec3 inkC = TINK(p).rgb;
    vec3 inkN = TINK(p + vec2(0,1)).rgb;
    vec3 inkE = TINK(p + vec2(1,0)).rgb;
    vec3 inkS = TINK(p - vec2(0,1)).rgb;
    vec3 inkW = TINK(p - vec2(1,0)).rgb;
    vec3 lapInk = inkN + inkE + inkS + inkW - 4.0 * inkC;
    ink += DT * INK_KAPPA * lapInk;

    // Automatic ink sources: multiple emitters with different colors
    float t = iTime;
    vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
    vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
    vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));
    vec2 em4 = iResolution.xy * vec2(0.5, 0.7 + 0.15 * cos(t * 0.5));

    float r1 = exp(-dot(p - em1, p - em1) / 200.0);
    float r2 = exp(-dot(p - em2, p - em2) / 200.0);
    float r3 = exp(-dot(p - em3, p - em3) / 180.0);
    float r4 = exp(-dot(p - em4, p - em4) / 180.0);

    // Each emitter injects a different color
    ink.r += DT * (r1 * 3.0 + r4 * 1.5);          // red/magenta
    ink.g += DT * (r2 * 3.0 + r3 * 1.5);          // green/cyan
    ink.b += DT * (r3 * 3.0 + r1 * 0.8 + r2 * 0.8); // blue/mixed

    // Mouse stirring injects white ink (all channels)
    if (iMouse.z > 0.0) {
        float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
        float influence = exp(-dist2 / 80.0);
        ink += vec3(DT * influence * 2.0);
    }

    // Decay + clamp
    ink *= INK_DECAY;
    ink = clamp(ink, vec3(0.0), vec3(5.0));

    // Boundary clear
    if (p.x < 1.0 || p.y < 1.0 ||
        iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
        ink = vec3(0.0);
    }

    fragColor = vec4(ink, 1.0);
}
```

### Step 9d: Visualization (Image Pass) — Multi-Color Ink Mixing

```glsl
// Multi-Color Ink Visualization — Image Pass
// iChannel0 = Buffer B (ink RGB)

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 ink = texture(iChannel0, uv).rgb;

    // Use smoothstep to map each channel, preserving concentration gradients
    vec3 mapped = smoothstep(vec3(0.0), vec3(2.5), ink);

    // Color mapping: map RGB concentrations to actual visible colors
    // IMPORTANT: Base colors must be bright, do not use extremely dark values
    vec3 col1 = vec3(0.9, 0.15, 0.2);  // red ink
    vec3 col2 = vec3(0.1, 0.8, 0.3);   // green ink
    vec3 col3 = vec3(0.15, 0.3, 0.95); // blue ink

    vec3 col = col1 * mapped.r + col2 * mapped.g + col3 * mapped.b;

    // Mixing regions produce new hues (additive blending naturally creates gradients)
    // HDR tone mapping to prevent overexposure
    col = 1.0 - exp(-col * 1.2);

    // Background color
    float totalInk = mapped.r + mapped.g + mapped.b;
    vec3 bg = vec3(0.02, 0.015, 0.04);
    col = mix(bg, col, smoothstep(0.0, 0.3, totalInk));

    fragColor = vec4(col, 1.0);
}
```

**IMPORTANT: The multi-color ink Buffer A velocity field template is identical to the single-color version**, except `c.w` is no longer used for ink (ink is in Buffer B). Buffer A only handles velocity + pressure.

## Common Variants

### Variant 1: Rotational Self-Advection
Does not use pressure projection; achieves naturally divergence-free advection through multi-scale rotational sampling.
```glsl
#define RotNum 3
#define angRnd 1.0

const float ang = 2.0 * 3.14159 / float(RotNum);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

float getRot(vec2 uv, float sc) {
    float ang2 = angRnd * randS(uv).x * ang;
    vec2 p = vec2(cos(ang2), sin(ang2));
    float rot = 0.0;
    for (int i = 0; i < RotNum; i++) {
        vec2 p2 = p * sc;
        vec2 v = texture(iChannel0, fract(uv + p2)).xy - vec2(0.5);
        rot += cross(vec3(v, 0.0), vec3(p2, 0.0)).z / dot(p2, p2);
        p = m * p;
    }
    return rot / float(RotNum);
}

// Multi-scale advection superposition
vec2 v = vec2(0);
float sc = 1.0 / max(iResolution.x, iResolution.y);
for (int level = 0; level < 20; level++) {
    if (sc > 0.7) break;
    vec2 p = vec2(cos(ang2), sin(ang2));
    for (int i = 0; i < RotNum; i++) {
        vec2 p2 = p * sc;
        float rot = getRot(uv + p2, sc);
        v += p2.yx * rot * vec2(-1, 1);
        p = m * p;
    }
    sc *= 2.0;
}
fragColor = texture(iChannel0, fract(uv + v * 3.0 / iResolution.x));
```

### Variant 2: Vorticity Confinement
Adds vorticity confinement force on top of the basic solver, preventing small vortices from dissipating too quickly.
```glsl
#define VORT_STRENGTH 0.01  // [0.001 - 0.1]

float curl_c = curl_at(uv);
float curl_n = abs(curl_at(uv + vec2(0, texel.y)));
float curl_s = abs(curl_at(uv - vec2(0, texel.y)));
float curl_e = abs(curl_at(uv + vec2(texel.x, 0)));
float curl_w = abs(curl_at(uv - vec2(texel.x, 0)));

vec2 eta = normalize(vec2(curl_e - curl_w, curl_n - curl_s) + 1e-5);
vec2 conf = VORT_STRENGTH * vec2(eta.y, -eta.x) * curl_c;
c.xy += DT * conf;
```

### Variant 3: Viscous Fingering
Rotation-driven self-amplification + Laplacian diffusion, producing reaction-diffusion style organic patterns.
```glsl
const float cs = 0.25;   // curl→rotation scale
const float ls = 0.24;   // Laplacian diffusion strength
const float ps = -0.06;  // divergence-pressure feedback
const float amp = 1.0;   // self-amplification coefficient
const float pwr = 0.2;   // curl power exponent

float sc = cs * sign(curl) * pow(abs(curl), pwr);
float ta = amp * uv.x + ls * lapl.x + norm.x * sp + uv.x * sd;
float tb = amp * uv.y + ls * lapl.y + norm.y * sp + uv.y * sd;
float a = ta * cos(sc) - tb * sin(sc);
float b = ta * sin(sc) + tb * cos(sc);
fragColor = clamp(vec4(a, b, div, 1), -1.0, 1.0);
```

### Variant 4: Gaussian Kernel SPH Particle Fluid (Gaussian SPH)
Gaussian kernel function for density and velocity estimation, a grid-based approximation of SPH.
```glsl
#define RADIUS 7  // search radius [3-10]

vec4 r = vec4(0);
for (vec2 i = vec2(-RADIUS); ++i.x < float(RADIUS);)
    for (i.y = -float(RADIUS); ++i.y < float(RADIUS);) {
        vec2 v = texelFetch(iChannel0, ivec2(i + fragCoord), 0).xy;
        float mass = texelFetch(iChannel0, ivec2(i + fragCoord), 0).z;
        float w = exp(-dot(v + i, v + i)) / 3.14;
        r += mass * w * vec4(mix(v + v + i, v, mass), 1, 1);
    }
r.xy /= r.z + 1e-6;
```

### Variant 5: Lagrangian Vortex Particle Method
Tracks discrete vortex particles, computing the velocity field using the Biot-Savart law.
```glsl
#define N 20              // N×N particles
#define STRENGTH 1e3*0.25 // vorticity strength scale

vec2 F = vec2(0);
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = vorticity(i, j);
        vec2 d = particle_pos(i, j) - my_pos;
        float l = dot(d, d);
        if (l > 1e-5)
            F += vec2(-d.y, d.x) * w / l;
    }
velocity = STRENGTH * F;
position += velocity * dt;
```

## Performance & Composition

**Performance tips**:
- 5-point cross stencil is fastest; 3x3 (9 samples) is the best accuracy/performance tradeoff
- SPH search radius >7 is extremely slow; use `texelFetch` instead of `texture` to skip filtering
- Merge multiple steps into a single Pass; inter-frame feedback forms implicit Jacobi iteration
- Multi-step advection (`ADVECTION_STEPS=3`) improves accuracy but 3x sampling cost
- `textureLod` provides O(1) multi-scale reads replacing large-radius sampling
- Add slight noise (`1e-6`) on initial frames to break symmetry lock
- `fract(uv + offset)` implements periodic boundaries without branching
- Multiply pressure field by `0.9999` decay to prevent drift

**Composition directions**:
- **+ Normal map lighting**: density field → height map → normals → Phong/GGX, liquid metal effects
- **+ Particle tracing**: passive particles update position following the flow field, visualizing streamlines/ink wash
- **+ Color advection**: extra channels store RGB, synchronous semi-Lagrangian advection, colorful blending
- **+ Audio response**: low freq → thrust, high freq → vortex perturbation, music-driven fluid
- **+ 3D volume rendering**: 2D slices packed as 3D voxels, ray marching to render clouds/explosions

## Further Reading

Full step-by-step tutorial, mathematical derivations, and advanced usage in [reference](../reference/fluid-simulation.md)
