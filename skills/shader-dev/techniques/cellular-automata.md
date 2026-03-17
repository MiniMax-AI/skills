# Cellular Automata & Reaction-Diffusion

## Use Cases
- GPU grid evolution simulation (cellular automata, reaction-diffusion)
- Organic texture generation: spots, stripes, mazes, coral, vein patterns
- Conway's Game of Life and variants (custom B/S rule sets)
- Gray-Scott reaction-diffusion real-time visualization
- Using simulation results to drive 3D surface displacement, lighting, or coloring

## Core Principles

### Cellular Automata (CA)
Each cell on a discrete grid updates based on **its own state** and **neighbor states** according to fixed rules. Conway B3/S23 rules:
- Dead cell with exactly 3 live neighbors → birth
- Live cell with 2 or 3 live neighbors → survival
- Otherwise → death

Neighbor computation (Moore neighborhood, 8 neighbors): `k = Σ cell(px + offset)`

### Reaction-Diffusion (RD)
Gray-Scott model — two substances u (activator) and v (inhibitor) diffuse and react:
```
∂u/∂t = Du·∇²u - u·v² + F·(1-u)
∂v/∂t = Dv·∇²v + u·v² - (F+k)·v
```
- `Du, Dv`: diffusion coefficients (Du > Dv produces patterns)
- `F`: feed rate, `k`: kill rate
- `∇²`: Laplacian, discretized using a nine-point stencil

Key parameters `(F, k)` determine the pattern:
| F | k | Pattern |
|---|---|---------|
| 0.035 | 0.065 | spots |
| 0.040 | 0.060 | stripes |
| 0.025 | 0.055 | labyrinthine |
| 0.050 | 0.065 | solitons |

## Implementation Steps

### Step 1: Grid State Storage & Self-Feedback
```glsl
// Buffer A: iChannel0 bound to Buffer A itself (self-feedback)
vec4 prevState = texelFetch(iChannel0, ivec2(fragCoord), 0);
// UV sampling (supports texture filtering)
vec2 uv = fragCoord / iResolution.xy;
vec4 prevSmooth = texture(iChannel0, uv);
```

### Step 2: Initialization (Noise Seeding)
```glsl
float hash1(float n) {
    return fract(sin(n) * 138.5453123);
}
vec3 hash33(in vec2 p) {
    float n = sin(dot(p, vec2(41, 289)));
    return fract(vec3(2097152, 262144, 32768) * n);
}

if (iFrame < 2) {
    // CA: random binary
    float f = step(0.9, hash1(fragCoord.x * 13.0 + hash1(fragCoord.y * 71.1)));
    fragColor = vec4(f, 0.0, 0.0, 0.0);
} else if (iFrame < 10) {
    // RD: random continuous values
    vec3 noise = hash33(fragCoord / iResolution.xy + vec2(53, 43) * float(iFrame));
    fragColor = vec4(noise, 1.0);
}
```

### Step 3: Neighbor Sampling & Laplacian
```glsl
// --- Method A: Discrete CA neighbor counting ---
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;  // wrap-around boundary
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}
ivec2 px = ivec2(fragCoord);
int k = cell(px+ivec2(-1,-1)) + cell(px+ivec2(0,-1)) + cell(px+ivec2(1,-1))
      + cell(px+ivec2(-1, 0))                        + cell(px+ivec2(1, 0))
      + cell(px+ivec2(-1, 1)) + cell(px+ivec2(0, 1)) + cell(px+ivec2(1, 1));

// --- Method B: Nine-point Laplacian (for RD) ---
// Weights: diagonal 0.5, cross 1.0, center -6.0
vec2 laplacian(vec2 uv) {
    vec2 px = 1.0 / iResolution.xy;
    vec4 P = vec4(px, 0.0, -px.x);
    return
        0.5 * texture(iChannel0, uv - P.xy).xy
      +       texture(iChannel0, uv - P.zy).xy
      + 0.5 * texture(iChannel0, uv - P.wy).xy
      +       texture(iChannel0, uv - P.xz).xy
      - 6.0 * texture(iChannel0, uv).xy
      +       texture(iChannel0, uv + P.xz).xy
      + 0.5 * texture(iChannel0, uv + P.wy).xy
      +       texture(iChannel0, uv + P.zy).xy
      + 0.5 * texture(iChannel0, uv + P.xy).xy;
}

// --- Method C: 3x3 weighted blur (Gaussian approximation) ---
// Weights: corner 1, edge 2, center 4, total 16
float blur3x3(vec2 uv) {
    vec3 e = vec3(1, 0, -1);
    vec2 px = 1.0 / iResolution.xy;
    float res = 0.0;
    res += texture(iChannel0, uv + e.xx*px).x + texture(iChannel0, uv + e.xz*px).x
         + texture(iChannel0, uv + e.zx*px).x + texture(iChannel0, uv + e.zz*px).x;
    res += (texture(iChannel0, uv + e.xy*px).x + texture(iChannel0, uv + e.yx*px).x
          + texture(iChannel0, uv + e.yz*px).x + texture(iChannel0, uv + e.zy*px).x) * 2.;
    res += texture(iChannel0, uv + e.yy*px).x * 4.;
    return res / 16.0;
}
```

### Step 4: State Update Rules
```glsl
// --- CA: Conway B3/S23 ---
int e = cell(px);
float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;

// --- CA: Generic Birth/Survival bitmask ---
float ff = 0.0;
if (currentAlive) {
    ff = ((stayset & (1 << (k - 1))) > 0) ? float(k) : 0.0;
} else {
    ff = ((bornset & (1 << (k - 1))) > 0) ? 1.0 : 0.0;
}

// --- RD: Gray-Scott update ---
float u = prevState.x;
float v = prevState.y;
vec2 Duv = laplacian(uv) * DIFFUSION;
float du = Duv.x - u * v * v + F * (1.0 - u);
float dv = Duv.y + u * v * v - (F + k) * v;
fragColor.xy = clamp(vec2(u + du * DT, v + dv * DT), 0.0, 1.0);

// --- RD: Simplified version (gradient + random decay) ---
float avgRD = blur3x3(uv);
vec2 pwr = (1.0 / iResolution.xy) * 1.5;
vec2 lap = vec2(
    texture(iChannel0, uv + vec2(pwr.x, 0)).y - texture(iChannel0, uv - vec2(pwr.x, 0)).y,
    texture(iChannel0, uv + vec2(0, pwr.y)).y - texture(iChannel0, uv - vec2(0, pwr.y)).y
);
uv = uv + lap * (1.0 / iResolution.xy) * 3.0;
float newRD = texture(iChannel0, uv).x + (noise.z - 0.5) * 0.0025 - 0.002;
newRD += dot(texture(iChannel0, uv + (noise.xy - 0.5) / iResolution.xy).xy, vec2(1, -1)) * 0.145;
```

### Step 5: Visualization & Coloring
```glsl
// Color mapping
float c = 1.0 - texture(iChannel0, uv).y;
vec3 col = pow(vec3(1.5, 1, 1) * c, vec3(1, 4, 12));

// Gradient normals + bump lighting
vec3 normal(vec2 uv) {
    vec3 delta = vec3(1.0 / iResolution.xy, 0.0);
    float du = texture(iChannel0, uv + delta.xz).x - texture(iChannel0, uv - delta.xz).x;
    float dv = texture(iChannel0, uv + delta.zy).x - texture(iChannel0, uv - delta.zy).x;
    return normalize(vec3(du, dv, 1.0));
}

// Specular highlight
float c2 = 1.0 - texture(iChannel0, uv + 0.5 / iResolution.xy).y;
col += vec3(0.36, 0.73, 1.0) * max(c2 * c2 - c * c, 0.0) * 12.0;

// Vignette + gamma
col *= pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.125) * 1.15;
col *= smoothstep(0.0, 1.0, iTime / 2.0);
fragColor = vec4(sqrt(min(col, 1.0)), 1.0);
```

## Complete Code Template

ShaderToy setup: Buffer A's iChannel0 = Buffer A (self-feedback, linear filtering). Image's iChannel0 = Buffer A.

### Standalone HTML JS Skeleton (Ping-Pong Render Pipeline)

CA/RD requires framebuffer self-feedback. The following JS skeleton demonstrates the correct WebGL2 multi-pass ping-pong structure:

```javascript
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

// fsBuffer / fsImage: adapt from the Buffer A / Image templates below (uniform declarations + void main entry point)

const progBuf = createProgram(vsSource, fsBuffer);
const progImg = createProgram(vsSource, fsImage);

function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    const fmt = ext ? gl.RGBA16F : gl.RGBA;
    const typ = ext ? gl.FLOAT : gl.UNSIGNED_BYTE;
    gl.texImage2D(gl.TEXTURE_2D, 0, fmt, w, h, 0, gl.RGBA, typ, null);
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

    // Buffer pass: read bufA → write bufB
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
    gl.bindVertexArray(vao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufA, bufB] = [bufB, bufA];

    // Image pass: read bufA → screen
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
```

### Buffer A (Simulation Computation)
```glsl
// Gray-Scott Reaction-Diffusion — Buffer A (Simulation)
// iChannel0 = Buffer A (self-feedback, linear filtering)

#define DU 0.210          // u diffusion coefficient (0.1~0.3)
#define DV 0.105          // v diffusion coefficient (0.05~0.15)
#define F  0.040          // feed rate (0.01~0.08)
#define K  0.060          // kill rate (0.04~0.07)
#define DT 1.0            // time step (0.5~2.0)
#define INIT_FRAMES 10

float hash1(float n) {
    return fract(sin(n) * 138.5453123);
}
vec3 hash33(vec2 p) {
    float n = sin(dot(p, vec2(41.0, 289.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

// Nine-point Laplacian: diagonal 0.05, cross 0.2, center -1.0
vec2 laplacian9(vec2 uv) {
    vec2 px = 1.0 / iResolution.xy;
    vec2 c  = texture(iChannel0, uv).xy;
    vec2 n  = texture(iChannel0, uv + vec2( 0, px.y)).xy;
    vec2 s  = texture(iChannel0, uv + vec2( 0,-px.y)).xy;
    vec2 e  = texture(iChannel0, uv + vec2( px.x, 0)).xy;
    vec2 w  = texture(iChannel0, uv + vec2(-px.x, 0)).xy;
    vec2 ne = texture(iChannel0, uv + vec2( px.x, px.y)).xy;
    vec2 nw = texture(iChannel0, uv + vec2(-px.x, px.y)).xy;
    vec2 se = texture(iChannel0, uv + vec2( px.x,-px.y)).xy;
    vec2 sw = texture(iChannel0, uv + vec2(-px.x,-px.y)).xy;
    return (n + s + e + w) * 0.2 + (ne + nw + se + sw) * 0.05 - c;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Initialization
    if (iFrame < INIT_FRAMES) {
        float rnd = hash1(fragCoord.x * 13.0 + hash1(fragCoord.y * 71.1 + float(iFrame)));
        float u = 1.0;
        float v = (rnd > 0.9) ? 1.0 : 0.0;
        vec2 center = iResolution.xy * 0.5;
        if (abs(fragCoord.x - center.x) < 20.0 && abs(fragCoord.y - center.y) < 20.0) {
            v = hash1(fragCoord.x * 7.0 + fragCoord.y * 13.0) > 0.5 ? 1.0 : 0.0;
        }
        fragColor = vec4(u, v, 0.0, 1.0);
        return;
    }

    // Read current state
    vec2 state = texture(iChannel0, uv).xy;
    float u = state.x;
    float v = state.y;

    // Gray-Scott equations
    vec2 lap = laplacian9(uv);
    float uvv = u * v * v;
    float du = DU * lap.x - uvv + F * (1.0 - u);
    float dv = DV * lap.y + uvv - (F + K) * v;

    u += du * DT;
    v += dv * DT;

    // Mouse interaction: click to add v
    if (iMouse.z > 0.0) {
        if (length(fragCoord - iMouse.xy) < 10.0) v = 1.0;
    }

    fragColor = vec4(clamp(u, 0.0, 1.0), clamp(v, 0.0, 1.0), 0.0, 1.0);
}
```

### Image (Visualization Output)
```glsl
// Gray-Scott Reaction-Diffusion — Image (Visualization)
// iChannel0 = Buffer A (linear filtering)

#define LIGHT_STRENGTH 12.0   // specular intensity (5~20)
#define COLOR_MODE 0          // 0=blue-gold, 1=flame, 2=monochrome
#define VIGNETTE 1            // 0=off, 1=vignette on

vec3 getNormal(vec2 uv) {
    vec2 d = 1.0 / iResolution.xy;
    float du = texture(iChannel0, uv + vec2(d.x, 0)).y - texture(iChannel0, uv - vec2(d.x, 0)).y;
    float dv = texture(iChannel0, uv + vec2(0, d.y)).y - texture(iChannel0, uv - vec2(0, d.y)).y;
    return normalize(vec3(du, dv, 0.05));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float val = texture(iChannel0, uv).y;
    float c = 1.0 - val;

    vec3 col;
    #if COLOR_MODE == 0
    float pattern = -cos(uv.x*0.75*3.14159-0.9)*cos(uv.y*1.5*3.14159-0.75)*0.5+0.5;
    col = pow(vec3(1.5, 1.0, 1.0) * c, vec3(1.0, 4.0, 12.0));
    col = mix(col, col.zyx, clamp(pattern - 0.2, 0.0, 1.0));
    #elif COLOR_MODE == 1
    col = vec3(c * 1.2, pow(c, 3.0), pow(c, 9.0));
    #else
    col = vec3(c);
    #endif

    float c2 = 1.0 - texture(iChannel0, uv + 0.5 / iResolution.xy).y;
    col += vec3(0.36, 0.73, 1.0) * max(c2*c2 - c*c, 0.0) * LIGHT_STRENGTH;

    #if VIGNETTE == 1
    col *= pow(16.0*uv.x*uv.y*(1.0-uv.x)*(1.0-uv.y), 0.125) * 1.15;
    #endif
    col *= smoothstep(0.0, 1.0, iTime / 2.0);
    fragColor = vec4(sqrt(clamp(col, 0.0, 1.0)), 1.0);
}
```

## Common Variants

### Variant 1: Conway's Game of Life (Discrete CA)
```glsl
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 px = ivec2(fragCoord);
    int k = cell(px+ivec2(-1,-1)) + cell(px+ivec2(0,-1)) + cell(px+ivec2(1,-1))
          + cell(px+ivec2(-1, 0))                        + cell(px+ivec2(1, 0))
          + cell(px+ivec2(-1, 1)) + cell(px+ivec2(0, 1)) + cell(px+ivec2(1, 1));
    int e = cell(px);
    float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;
    if (iFrame < 2)
        f = step(0.9, fract(sin(fragCoord.x*13.0 + sin(fragCoord.y*71.1)) * 138.5));
    fragColor = vec4(f, 0.0, 0.0, 1.0);
}
```

### Variant 2: Configurable Rule Set CA (B/S Bitmask)
```glsl
#define BORN_SET  8        // birth bitmask, 8 = B3
#define STAY_SET  12       // survival bitmask, 12 = S23
#define LIVEVAL   2.0
#define DECIMATE  1.0      // decay value

float ff = 0.0;
float ev = texelFetch(iChannel0, px, 0).w;
if (ev > 0.5) {
    if (DECIMATE > 0.0) ff = ev - DECIMATE;
    if ((STAY_SET & (1 << (k - 1))) > 0) ff = LIVEVAL;
} else {
    ff = ((BORN_SET & (1 << (k - 1))) > 0) ? LIVEVAL : 0.0;
}
```

### Variant 3: Separable Gaussian Blur RD (Multi-Buffer)
```glsl
// Buffer B: horizontal blur (reads Buffer A)
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float h = 1.0 / iResolution.x;
    vec4 sum = vec4(0.0);
    sum += texture(iChannel0, fract(vec2(uv.x - 4.0*h, uv.y))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x - 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x - 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x - 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x,         uv.y))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x + 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x + 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x + 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x + 4.0*h, uv.y))) * 0.05;
    fragColor = vec4(sum.xyz / 0.98, 1.0);
}
// Buffer C: vertical blur (reads Buffer B), same structure but along y-axis
// Buffer A: reaction step reads Buffer C as the diffusion term
```

### Variant 4: Continuous Differential Operator CA (Vein/Fluid Style)
```glsl
#define STEPS 40       // advection step count (10~60)
#define ts    0.2      // advection rotation strength
#define cs   -2.0      // curl scale
#define ls    0.05     // Laplacian scale
#define amp   1.0      // self-amplification coefficient
#define upd   0.4      // update smoothing coefficient

// 3x3 discrete curl and divergence
curl = uv_n.x - uv_s.x - uv_e.y + uv_w.y
     + _D * (uv_nw.x + uv_nw.y + uv_ne.x - uv_ne.y
           + uv_sw.y - uv_sw.x - uv_se.y - uv_se.x);
div  = uv_s.y - uv_n.y - uv_e.x + uv_w.x
     + _D * (uv_nw.x - uv_nw.y - uv_ne.x - uv_ne.y
           + uv_sw.x + uv_sw.y + uv_se.y - uv_se.x);

// Multi-step advection loop
for (int i = 0; i < STEPS; i++) {
    advect(off, vUv, texel, curl, div, lapl, blur);
    offd = rot(offd, ts * curl);
    off += offd;
    ab += blur / float(STEPS);
}
```

### Variant 5: RD-Driven 3D Surface (Raymarched RD)
```glsl
// Image pass: use RD texture for displacement in SDF
vec2 map(in vec3 pos) {
    vec3 p = normalize(pos);
    vec2 uv;
    uv.x = 0.5 + atan(p.z, p.x) / (2.0 * 3.14159);
    uv.y = 0.5 - asin(p.y) / 3.14159;
    float y = texture(iChannel0, uv).y;
    float displacement = 0.1 * y;
    float sd = length(pos) - (2.0 + displacement);
    return vec2(sd, y);
}
```

## Performance & Composition

### Performance Tips
- **texelFetch vs texture**: Use `texelFetch` for discrete CA (exact pixel reads), `texture` for continuous RD (bilinear interpolation)
- **Separable blur replaces large kernels**: For large diffusion radii, use two-pass separable Gaussian (O(2N)) instead of NxN Laplacian (O(N²))
- **Sub-iterations**: Multiple small DT steps within a single frame improves stability
- **Reduced resolution**: Low-resolution buffer simulation + Image pass upsampling
- **Avoid branching**: Use `step()/mix()/clamp()` instead of `if/else`

### Composition Directions
- **RD + Raymarching**: RD as heightmap mapped onto 3D surface for displacement modeling
- **CA/RD + Particle Systems**: Field used as velocity field or spawn probability field to drive particles
- **RD + Bump Lighting**: Compute normals from RD values, combine with environment maps for metallic etching/ripple effects
- **CA + Color Decay Trails**: After death, fade per-frame with different RGB decay rates producing colored trails
- **RD + Domain Transforms**: Apply vortex/spiral transforms before sampling, producing spiral swirl patterns

## Further Reading

Full step-by-step tutorial, mathematical derivations, and advanced usage in [reference](../reference/cellular-automata.md)
