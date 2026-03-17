# Particle System

**IMPORTANT: GLSL ES 3.0 return values**: All code paths in non-void functions must return a value. Every branch of an if statement must have a return.

**IMPORTANT: Particle system time cycling**: Must use `mod(time - offset, period)` for cycle computation. **Never use `floor(time / period) * period`**! The latter causes all particles to have negative time initially, resulting in startup delay or blank rendering.

**IMPORTANT: Brightness budget (most common failure cause!)**: Each particle's `numerator / (dist² + epsilon)` peak = `numerator / epsilon`. **Total peak = N_particles x (numerator / epsilon) must be < 5.0** (single pass). Exceeding this budget causes washout even with Reinhard. See specific reference values in the comments of each template below. Multi-pass ping-pong systems have a stricter budget, see below.

**IMPORTANT: Particle color vs background contrast**: When particle color is close to the background (sand dust/snow/fog), visibility must be enhanced through at least one method: (1) brightness significantly higher than background (2) different hue (3) visible motion trail.

**IMPORTANT: Elongated glow (meteor/trail lines)**: Do not use `1/(distPerp² + tiny_epsilon)` for line glow — too-small epsilon makes the line center extremely bright. Correct approach: use `smoothstep` or `exp(-dist)` for lines, see meteor template below.

### Correct Pattern
```glsl
// Vertex shader
#version 300 es
in vec4 aPosition;
void main() {
    gl_Position = aPosition;
}

// Fragment shader
#version 300 es
precision highp float;
uniform vec2 iResolution;
uniform float iTime;
out vec4 fragColor;

float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;
    // ... particle system logic
    fragColor = vec4(col, 1.0);
}
```

### Complete Single-File Template (Fireworks Particle System)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Fireworks</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');

const vs = `#version 300 es
in vec4 aPosition;
void main() { gl_Position = aPosition; }`;

const fs = `#version 300 es
precision highp float;
uniform vec2 iResolution;
uniform float iTime;
out vec4 fragColor;

#define NUM_FIREWORKS 4
#define PARTICLES_PER_FIREWORK 40
#define PI 3.14159265

float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    vec3 col = vec3(0.01, 0.01, 0.03);
    float t = iTime;

    for (int fw = 0; fw < NUM_FIREWORKS; fw++) {
        float fwId = float(fw);
        float launchTime = 1.5 + fwId * 1.8 + hash11(fwId * 7.3) * 1.5;
        float cycleTime = 4.5;
        float fireworkTime = mod(t - launchTime, cycleTime);

        float launchDuration = 0.6;
        float launchPhase = clamp(fireworkTime / launchDuration, 0.0, 1.0);

        float launchX = (hash11(fwId * 13.7) - 0.5) * 1.2;
        float launchY = -0.8;
        float peakY = 0.2 + hash11(fwId * 17.3) * 0.4;

        float baseHue = hash11(fwId * 23.0);

        if (fireworkTime < launchDuration) {
            vec2 rocketPos = vec2(launchX, mix(launchY, peakY, launchPhase));
            vec2 rel = uv - rocketPos;
            float dist = length(rel);
            // Rocket head: peak = 0.008/0.002 = 4.0, only 1 point, OK
            float rocket = 0.008 / (dist * dist + 0.002);
            float tail = 0.004 / (length(vec2(rel.x * 4.0, max(rel.y, 0.0))) + 0.01);
            col += vec3(1.0, 0.8, 0.5) * rocket;
            col += vec3(1.0, 0.5, 0.2) * tail * (1.0 - launchPhase);
        } else {
            float burstTime = fireworkTime - launchDuration;
            float burstDuration = cycleTime - launchDuration;
            float burstPhase = burstTime / burstDuration;

            for (int p = 0; p < PARTICLES_PER_FIREWORK; p++) {
                float pId = float(p);
                float angle = hash11(fwId * 100.0 + pId * 7.3) * PI * 2.0;
                float speed = 0.3 + hash11(fwId * 100.0 + pId * 13.7) * 0.7;

                vec2 particleDir = vec2(cos(angle), sin(angle));

                float damping = exp(-burstPhase * 2.5);
                float travelDist = speed * (1.0 - damping) / 2.5;
                vec2 particlePos = vec2(launchX, peakY) + particleDir * travelDist;

                particlePos.y -= 0.5 * 1.2 * burstTime * burstTime;

                vec2 rel = uv - particlePos;
                float dist = length(rel);

                float fade = smoothstep(1.0, 0.0, burstPhase);
                fade *= fade;

                // IMPORTANT: Brightness budget: peak = 0.015/0.03 = 0.5, x 40 particles x fade ≈ total peak < 5.0
                float intensity = fade * 0.015 / (dist * dist + 0.03);

                float hueOffset = (hash11(pId * 3.7 + fwId * 11.0) - 0.5) * 0.15;
                vec3 particleColor = hsv2rgb(vec3(baseHue + hueOffset, 0.8, 1.0));

                col += particleColor * intensity;
            }
        }
    }

    col = col / (1.0 + col);
    col = pow(col, vec3(0.9));
    fragColor = vec4(col, 1.0);
}`;

function createShader(type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(s));
    }
    return s;
}

const program = gl.createProgram();
gl.attachShader(program, createShader(gl.VERTEX_SHADER, vs));
gl.attachShader(program, createShader(gl.FRAGMENT_SHADER, fs));
gl.linkProgram(program);
gl.useProgram(program);

const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
const aPos = gl.getAttribLocation(program, 'aPosition');
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

// Cache uniform locations (do NOT look up every frame - causes performance issues)
const iResolutionLoc = gl.getUniformLocation(program, 'iResolution');
const iTimeLoc = gl.getUniformLocation(program, 'iTime');

// Resize handler: only resize when window size actually changes
let lastWidth = 0, lastHeight = 0;
function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    if (w !== lastWidth || h !== lastHeight) {
        lastWidth = w; lastHeight = h;
        canvas.width = w; canvas.height = h;
        gl.viewport(0, 0, w, h);
    }
}

function render(t) {
    resize();
    gl.uniform2f(iResolutionLoc, canvas.width, canvas.height);
    gl.uniform1f(iTimeLoc, t * 0.001);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
</body>
</html>
```

### Stateful Particle System HTML Template (Multi-Pass Ping-Pong)

Stateful particles (Boids, cloth, fluid particles, etc.) need Buffers for inter-frame state storage. The following JS skeleton demonstrates the correct WebGL2 multi-pass ping-pong structure; shader code is in Steps 4-5 below:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Stateful Particles</title>
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

// fsBuffer: particle physics update (see Step 4)
// fsImage:  particle rendering (see Step 5)
const progBuf = createProgram(vsSource, fsBuffer);
const progImg = createProgram(vsSource, fsImage);

function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    const fmt = ext ? gl.RGBA16F : gl.RGBA8;
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
</body>
</html>
```

### Star Field Function Template (For Meteors, Fireworks, and Other Night Sky Scenes)

**IMPORTANT: Star visibility**: Stars must be clearly visible in screenshots as individual light points. Use `exp(-dist*dist*k)` for sharp Gaussian dots rather than `1/(dist²+eps)` broad glow. Each star's peak brightness should be at least 0.3 to be visible against a dark background.

```glsl
#define NUM_STARS 200

vec3 starField(vec2 uv) {
    vec3 col = vec3(0.0);
    for (int i = 0; i < NUM_STARS; i++) {
        float fi = float(i);
        vec2 starPos = vec2(hash11(fi * 13.7 + 1.3), hash11(fi * 7.3 + 91.1));
        starPos = starPos * 2.0 - 1.0;
        float brightness = 0.3 + 0.7 * pow(hash11(fi * 3.1 + 47.0), 2.0);
        float twinkle = 0.7 + 0.3 * sin(iTime * (1.0 + hash11(fi * 5.7) * 3.0) + fi * 6.28);
        brightness *= twinkle;
        float dist = length(uv - starPos);
        // Sharp Gaussian dot: peak = brightness (0.3~1.0), very small radius, no accumulation washout
        float glow = brightness * exp(-dist * dist * 8000.0);
        // Add soft halo to make stars more visible
        glow += brightness * 0.0008 / (dist * dist + 0.003);
        float temp = hash11(fi * 11.3 + 23.0);
        vec3 starCol = mix(vec3(0.6, 0.7, 1.0), vec3(1.0, 0.9, 0.7), temp);
        col += starCol * glow;
    }
    return col;
}
```

### Incorrect Pattern (Do Not Do This)
```glsl
// WRONG: cannot write this in standalone HTML
void mainImage(out vec4 fragColor, in vec2 fragCoord) { ... }
void main() {
    mainImage(fragColor, fragCoord);  // compilation error!
}
```

## ShaderToy vs Standalone HTML Code Templates

The following code examples fall into two categories; be sure to use the correct template:

### Standalone HTML Template (complete example provided above)

### ShaderToy Template (for the ShaderToy website)

## Use Cases
- **Stateless particle effects**: fireworks, starfields, campfire/flames (flying embers), orbiting light points, and other decorative effects that don't need inter-frame memory
- **Stateful physics particles**: flocking/boids, raindrops, cloth, fluids, and other simulations requiring persistent position and velocity
- **Motion blur and trails**: particle trajectories needing afterglow or halo effects
- **Large-scale particle management**: real-time rendering and interaction with hundreds to thousands of particles
- **Weather/atmospheric effects**: sandstorms, blizzards, volcanic ash, and other vortex-driven particle systems
- **Magic/geometric arrays**: magic dust, spiraling ascending light points, magic circle rings, iridescent shimmering particles

Core decision tree: Do particles need inter-frame memory?
- **No** → Single-pass stateless system (using loops + hash functions)
- **Yes** → Multi-pass stateful system (using Buffer for position/velocity storage)

## Core Principles

Particle systems manage collections of many independent entities, each with position, velocity, lifetime, and other attributes.

**Stateless paradigm**: All attributes are recomputed each frame from particle ID and time, no Buffer needed.
```
position_i = trajectory(id_i, time) + randomOffset(hash(id_i))
lifetime_i = fract((time - spawnTime_i) / lifeDuration_i)
```

**Stateful paradigm**: Particle state is stored in Buffer texture pixels, each frame reading → computing → writing back.
```
// Euler method
velocity += acceleration * dt
position += velocity * dt

// Verlet integration (no explicit velocity, more stable)
newPos = 2 * currentPos - previousPos + acceleration * dt²
```

**Rendering**: Distance-based falloff `intensity = brightness / (dist² + epsilon)`, with multi-particle superposition creating metaball fusion effects.

## Implementation Steps

### Step 1: Hash Random Functions
```glsl
// 1D -> 1D hash, returns [0, 1)
float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

// 1D -> 2D hash
vec2 hash12(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

// 3D -> 3D hash
vec3 hash33(vec3 p) {
    p = fract(p * vec3(443.897, 397.297, 491.187));
    p += dot(p.zxy, p.yxz + 19.19);
    return fract(vec3(p.x * p.y, p.z * p.x, p.y * p.z)) - 0.5;
}
```

### Step 2: Particle Lifecycle Management
```glsl
#define NUM_PARTICLES 100
#define LIFETIME_MIN 1.0
#define LIFETIME_MAX 3.0
#define START_TIME 2.0

// Returns: x = normalized age [0,1], y = life cycle number
vec2 particleAge(int id, float time) {
    float spawnTime = START_TIME * hash11(float(id) * 2.0);
    float lifetime = mix(LIFETIME_MIN, LIFETIME_MAX, hash11(float(id) * 3.0 - 35.0));
    float age = mod(time - spawnTime, lifetime);
    float run = floor((time - spawnTime) / lifetime);
    return vec2(age / lifetime, run);
}
```

### Step 3: Stateless Particle Position Computation
```glsl
#define GRAVITY vec2(0.0, -4.5)
#define DRIFT_MAX vec2(0.28, 0.28)

// Harmonic superposition for smooth main trajectory
float harmonics(vec3 freq, vec3 amp, vec3 phase, float t) {
    float val = 0.0;
    for (int h = 0; h < 3; h++)
        val += amp[h] * cos(t * freq[h] * 6.2832 + phase[h] / 360.0 * 6.2832);
    return (1.0 + val) / 2.0;
}

vec2 particlePosition(int id, float time) {
    vec2 ageInfo = particleAge(id, time);
    float age = ageInfo.x;
    float run = ageInfo.y;

    float slowTime = time * 0.1;
    vec2 mainPos = vec2(
        harmonics(vec3(0.4, 0.66, 0.78), vec3(0.8, 0.24, 0.18), vec3(0.0, 45.0, 55.0), slowTime),
        harmonics(vec3(0.415, 0.61, 0.82), vec3(0.72, 0.28, 0.15), vec3(90.0, 120.0, 10.0), slowTime)
    );

    vec2 drift = DRIFT_MAX * (vec2(hash11(float(id) * 3.0 + run * 4.0),
                                    hash11(float(id) * 7.0 - run * 2.5)) - 0.5) * age;
    vec2 grav = GRAVITY * age * age * 0.5;

    return mainPos + drift + grav;
}
```

### Step 4: Buffer-Stored Particle State (Stateful System)
```glsl
// === Buffer A: Particle Physics Update ===
// IMPORTANT: Multi-pass system warning: each fragment shader is compiled independently, helper functions must be redefined in each shader!
#define NUM_PARTICLES 40
#define MAX_VEL 0.5
#define MAX_ACC 3.0
#define RESIST 0.2
#define DT 0.03

// Helper functions that must be defined in the Buffer A shader
float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

vec2 hash12(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

vec4 loadParticle(float i) {
    return texelFetch(iChannel0, ivec2(i, 0), 0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    if (fragCoord.y > 0.5 || fragCoord.x > float(NUM_PARTICLES)) discard;

    float id = floor(fragCoord.x);
    vec2 res = iResolution.xy / iResolution.y;

    if (iFrame < 5) {
        vec2 rng = hash12(id);
        fragColor = vec4(0.1 + 0.8 * rng * res, 0.0, 0.0);
        return;
    }

    vec4 particle = loadParticle(id); // xy = pos, zw = vel
    vec2 pos = particle.xy;
    vec2 vel = particle.zw;

    vec2 force = vec2(0.0);
    force += 0.8 * (1.0 / abs(pos) - 1.0 / abs(res - pos)); // boundary repulsion
    for (float i = 0.0; i < float(NUM_PARTICLES); i++) {     // inter-particle interaction
        if (i == id) continue;
        vec4 other = loadParticle(i);
        vec2 w = pos - other.xy;
        float d = length(w);
        if (d > 0.0)
            force -= w * (6.3 + log(d * d * 0.02)) / exp(d * d * 2.4) / d;
    }
    force -= vel * RESIST / DT; // friction

    vec2 acc = force;
    float a = length(acc);
    acc *= a > MAX_ACC ? MAX_ACC / a : 1.0;
    vel += acc * DT;
    float v = length(vel);
    vel *= v > MAX_VEL ? MAX_VEL / v : 1.0;
    pos += vel * DT;

    fragColor = vec4(pos, vel);
}
```

### Step 5: Particle Rendering — Metaball Style
// IMPORTANT: Multi-pass system warning: Image shader must define all the following helper functions (compiled independently)!
```glsl
#define BRIGHTNESS 0.002
#define COLOR_START vec3(0.0, 0.64, 0.2)
#define COLOR_END vec3(0.06, 0.35, 0.85)

// Helper functions that must be defined in the Image shader
float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

vec2 hash12(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

vec4 loadParticle(float i) {
    return texelFetch(iChannel0, ivec2(i, 0), 0);
}

// HSV to RGB (correct implementation)
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec3 renderParticles(vec2 uv) {
    vec3 col = vec3(0.0);
    float totalWeight = 0.0;
    for (int i = 0; i < NUM_PARTICLES; i++) {
        vec4 particle = loadParticle(float(i));
        vec2 p = uv - particle.xy;
        float mb = BRIGHTNESS / dot(p, p);
        totalWeight += mb;
        float ratio = length(particle.zw) / MAX_VEL;
        vec3 pcol = mix(COLOR_START, COLOR_END, ratio);
        col = mix(col, pcol, mb / totalWeight);
    }
    totalWeight /= float(NUM_PARTICLES);
    col = normalize(col) * clamp(totalWeight, 0.0, 0.4);
    return col;
}
```

### Step 6: Frame Feedback Motion Blur
```glsl
// IMPORTANT: Ping-pong brightness budget (most common washout cause!):
// Steady-state brightness = singleFrameContribution / (1 - TRAIL_DECAY)
// decay=0.88 → 8.3x amplification, decay=0.95 → 20x amplification
// Budget formula: N_particles x (numerator/epsilon) x 1/(1-decay) < 10.0
//
// Safe parameter lookup table (decay=0.88, 8.3x amplification):
//   20 particles → single particle peak < 0.06  (numerator=0.002, epsilon=0.03)
//   50 particles → single particle peak < 0.024 (numerator=0.001, epsilon=0.04)
//  100 particles → single particle peak < 0.012 (numerator=0.0005, epsilon=0.04)
//
// Safe parameter lookup table (decay=0.92, 12.5x amplification):
//   20 particles → single particle peak < 0.04  (numerator=0.001, epsilon=0.03)
//   50 particles → single particle peak < 0.016 (numerator=0.0005, epsilon=0.03)
//  100 particles → single particle peak < 0.008 (numerator=0.0003, epsilon=0.04)
#define TRAIL_DECAY 0.88

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 prev = texture(iChannel0, uv).rgb * TRAIL_DECAY;
    vec3 current = renderParticles(fragCoord / iResolution.y);
    fragColor = vec4(prev + current, 1.0);
}
```

### Step 7: HSV Coloring & Star Glare Effect
```glsl
// HSV to RGB (correct implementation)
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Star glare: thin rays in horizontal/vertical/diagonal directions
float starGlare(vec2 relPos, float intensity) {
    vec2 stretch = vec2(9.0, 0.32);
    float dh = length(relPos * stretch);
    float dv = length(relPos * stretch.yx);
    vec2 diagPos = 0.707 * vec2(dot(relPos, vec2(1, 1)), dot(relPos, vec2(1, -1)));
    float dd1 = length(diagPos * vec2(13.0, 0.61));
    float dd2 = length(diagPos * vec2(0.61, 13.0));
    float glare = 0.25 / (dh * 3.0 + 0.01)
                + 0.25 / (dv * 3.0 + 0.01)
                + 0.19 / (dd1 * 3.0 + 0.01)
                + 0.19 / (dd2 * 3.0 + 0.01);
    return glare * intensity;
}
```

## Complete Code Template

Single-pass stateless particle system, runs directly in ShaderToy's Image tab:

```glsl
// === Particle System — Stateless Single-Pass Template ===

#define NUM_PARTICLES 80
#define LIFETIME_MIN 1.0
#define LIFETIME_MAX 3.5
#define START_TIME 2.5
#define BRIGHTNESS 0.00004
#define GRAVITY vec2(0.0, -2.0)
#define DRIFT_SPEED 0.2
#define HUE_SHIFT 0.035
#define TRAIL_DECAY 0.92
#define STAR_ENABLED 1

#define PI 3.14159265
#define TAU 6.28318530

float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float harmonics3(vec3 freq, vec3 amp, vec3 phase, float t) {
    float val = 0.0;
    for (int h = 0; h < 3; h++)
        val += amp[h] * cos(t * freq[h] * TAU + phase[h] / 360.0 * TAU);
    return (1.0 + val) * 0.5;
}

vec3 getLifecycle(int id, float time) {
    float spawn = START_TIME * hash11(float(id) * 2.0);
    float life = mix(LIFETIME_MIN, LIFETIME_MAX, hash11(float(id) * 3.0 - 35.0));
    float age = mod(time - spawn, life);
    float run = floor((time - spawn) / life);
    return vec3(age / life, run, spawn);
}

vec2 getPosition(int id, float time) {
    vec3 lc = getLifecycle(id, time);
    float age = lc.x;
    float run = lc.y;

    float tfact = mix(6.0, 20.0, hash11(float(id) * 2.0 + 94.0 + run * 1.5));
    float pt = (run * lc.x * mix(LIFETIME_MIN, LIFETIME_MAX, hash11(float(id)*3.0-35.0)) + lc.z) * (-1.0/tfact + 1.0) + time / tfact;

    vec2 mainPos = vec2(
        harmonics3(vec3(0.4, 0.66, 0.78), vec3(0.8, 0.24, 0.18), vec3(0.0, 45.0, 55.0), pt),
        harmonics3(vec3(0.415, 0.61, 0.82), vec3(0.72, 0.28, 0.15), vec3(90.0, 120.0, 10.0), pt)
    ) + vec2(0.35, 0.15);

    vec2 drift = DRIFT_SPEED * (vec2(
        hash11(float(id) * 3.0 - 23.0 + run * 4.0),
        hash11(float(id) * 7.0 + 632.0 - run * 2.5)
    ) - 0.5) * age;

    vec2 grav = GRAVITY * age * age * 0.004;

    return (mainPos + drift + grav) * vec2(0.6, 0.45);
}

float starGlare(vec2 rel) {
    #if STAR_ENABLED == 0
        return 0.0;
    #endif
    vec2 stretchHV = vec2(9.0, 0.32);
    float dh = length(rel * stretchHV);
    float dv = length(rel * stretchHV.yx);
    vec2 dRel = 0.707 * vec2(dot(rel, vec2(1, 1)), dot(rel, vec2(1, -1)));
    vec2 stretchDiag = vec2(13.0, 0.61);
    float dd1 = length(dRel * stretchDiag);
    float dd2 = length(dRel * stretchDiag.yx);
    return 0.25 / (dh * 3.0 + 0.01) + 0.25 / (dv * 3.0 + 0.01)
         + 0.19 / (dd1 * 3.0 + 0.01) + 0.19 / (dd2 * 3.0 + 0.01);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord.xy / iResolution.xx;
    float time = iTime * 0.75;

    vec3 col = vec3(0.0);

    for (int i = 1; i < NUM_PARTICLES; i++) {
        vec3 lc = getLifecycle(i, time);
        float age = lc.x;
        float run = lc.y;

        vec2 ppos = getPosition(i, time);
        vec2 rel = uv - ppos;
        float dist = length(rel);

        float baseInt = mix(0.1, 3.2, hash11(run * 4.0 + float(i) - 55.0));
        float glow = 1.0 / (dist * 3.0 + 0.015);

        float star = starGlare(rel);
        float intensity = baseInt * pow(glow + star, 2.3) / 40000.0;

        intensity *= (1.0 - age);
        intensity *= smoothstep(0.0, 0.15, age);
        float sparkFreq = mix(2.5, 6.0, hash11(float(i) * 5.0 + 72.0 - run * 1.8));
        intensity *= 0.5 * sin(sparkFreq * TAU * time) + 1.0;

        float hue = mix(-0.13, 0.13, hash11(float(i) + 124.0 + run * 1.5)) + HUE_SHIFT * time;
        float sat = mix(0.5, 0.9, hash11(float(i) * 6.0 + 44.0 + run * 3.3)) * 0.45 / max(intensity, 0.001);
        col += hsv2rgb(vec3(hue, clamp(sat, 0.0, 1.0), intensity));
    }

    col = pow(max(col, 0.0), vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Metaball Polar Coordinate Particles
```glsl
float d = fract(time * 0.51 + 48934.4238 * sin(float(i) * 692.7398));
float angle = TAU * float(i) / float(NUM_PARTICLES);
vec2 particlePos = d * vec2(cos(angle), sin(angle)) * 4.0;

vec2 p = uv - particlePos;
float mb = 0.84 / dot(p, p);
col = mix(col, mix(startColor, endColor, d), mb / totalSum);
```

### Variant 2: Buffer Storage + Boids Flocking Behavior
```glsl
vec2 sumForce = vec2(0.0);
for (float j = 0.0; j < NUM_PARTICLES; j++) {
    if (j == id) continue;
    vec4 other = texelFetch(iChannel0, ivec2(j, 0), 0);
    vec2 w = pos - other.xy;
    float d = length(w);
    sumForce -= w * (6.3 + log(d * d * 0.02)) / exp(d * d * 2.4) / d;
}
sumForce -= vel * 0.2 / dt;
```

### Variant 3: Verlet Integration Cloth Simulation
```glsl
vec2 newPos = 2.0 * particle.xy - particle.zw + vec2(0.0, -0.6) * dt * dt;
particle.zw = particle.xy;
particle.xy = newPos;

vec4 neighbor = texelFetch(iChannel0, neighborId, 0);
vec2 delta = neighbor.xy - particle.xy;
float dist = length(delta);
float restLength = 0.1;
particle.xy += 0.1 * (dist - restLength) * (delta / dist);
```

### Variant 4: 3D Particles + Ray Rendering
```glsl
vec3 ro = vec3(0.0, 0.0, 2.5);
vec3 rd = normalize(vec3(uv, -0.5));
for (int i = 0; i < numParticles; i++) {
    vec3 pos = texture(iChannel0, vec2(i, 100.0) * w).rgb;
    float d = dot(cross(pos - ro, rd), cross(pos - ro, rd));
    d *= 1000.0;
    float glow = 0.14 / (pow(d, 1.1) + 0.03);
    col += glow * particleColor;
}
```

### Variant 5: Raindrop Particles (3D Scene Integration)
```glsl
float speedScale = 0.0015 * (0.1 + 1.9 * sin(PI * 0.5 * pow(age / lifetime, 2.0)));
particle.x += (windShieldOffset.x + windIntensity * dot(rayRight, windDir)) * fallSpeed * speedScale * dt;
particle.y += (windShieldOffset.y + windIntensity * dot(rayUp, windDir)) * fallSpeed * speedScale * dt;
particle.xy += 0.001 * (randVec2(particle.xy + iTime) - 0.5) * jitterSpeed * dt;
if (particle.z > particle.a) {
    particle.xy = vec2(rand(seedX), rand(seedY)) * iResolution.xy;
    particle.a = lifetimeMin + rand(pid) * (lifetimeMax - lifetimeMin);
    particle.z = 0.0;
}
```

### Variant 6: Vortex/Storm Particle System (Sandstorm, Blizzard, Whirlwind, etc.)

Uses stateless single pass. Key: spiral trajectory + high-visibility particles + vortex eye dark zone + separated background fog layer.

```glsl
// IMPORTANT: Particle color must be 2-3x brighter than background to be visible (sand-colored particles on sand-colored background easily disappear)
// IMPORTANT: Brightness budget: 150 particles x peak(0.005/0.003=1.67) x fade(avg~0.3) ≈ 75, overexposed!
//    Must increase epsilon or decrease numerator. Safe values: numerator=0.002, epsilon=0.008 → peak=0.25, total=11 → OK after Reinhard
#define NUM_DUST 150
#define VORTEX_CENTER vec2(0.0)

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    float t = iTime;

    vec3 bg = mix(vec3(0.25, 0.18, 0.08), vec3(0.4, 0.28, 0.12), gl_FragCoord.y / iResolution.y);

    vec3 col = vec3(0.0);
    for (int i = 0; i < NUM_DUST; i++) {
        float fi = float(i);
        float life = mix(2.0, 5.0, hash11(fi * 3.7));
        float age = mod(t - hash11(fi * 2.0) * life, life);
        float norm = age / life;

        float initAngle = hash11(fi * 7.3) * 6.2832;
        float initR = 0.05 + hash11(fi * 11.0) * 0.5;
        float angularSpeed = 2.0 / (0.3 + initR);
        float angle = initAngle + norm * angularSpeed;
        float radius = initR + norm * 0.15;

        vec2 pos = VORTEX_CENTER + vec2(cos(angle), sin(angle)) * radius;

        vec2 rel = uv - pos;
        float dist = length(rel);

        float fade = smoothstep(0.0, 0.1, norm) * smoothstep(1.0, 0.5, norm);
        // Safe brightness: peak = 0.002/0.008 = 0.25, x 150 x avg_fade(0.3) ≈ 11 → Reinhard OK
        float glow = 0.002 / (dist * dist + 0.008) * fade;

        // Particles need to be noticeably brighter than background, use light sand + white blend
        vec3 dustColor = mix(vec3(1.0, 0.9, 0.6), vec3(1.0, 0.95, 0.85), hash11(fi * 5.0));
        col += dustColor * glow;
    }

    float eyeDist = length(uv - VORTEX_CENTER);
    float eye = smoothstep(0.06, 0.15, eyeDist);

    vec3 final = bg + col * eye;
    final = final / (1.0 + final);
    fragColor = vec4(final, 1.0);
}
```

### Variant 7: Meteor/Trail Line Rendering (Single-Pass Stateless)

Meteors, magic projectiles, etc. need elongated glow (stretched luminous lines). **Do not use `1/(distPerp² + tiny_epsilon)` for lines** — too-small epsilon makes line centers extremely bright and washed out. Use `exp(-dist)` or `smoothstep` for safe line glow.

**IMPORTANT: Common meteor failures**: (1) Star background too dark to see — must call `starField()` above and ensure stars use Gaussian dots `exp(-dist²*k)` for rendering (2) Meteor trail too faint — `core` multiplier should be at least 0.15, each step after dividing by `NUM_TRAIL_STEPS` still needs >= 0.005 contribution

```glsl
#define NUM_METEORS 6
#define NUM_TRAIL_STEPS 20

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    float t = iTime;

    // Deep blue night sky background + must call starField to draw stars
    vec3 col = vec3(0.005, 0.005, 0.02);
    col += starField(uv);

    for (int m = 0; m < NUM_METEORS; m++) {
        float fm = float(m);
        float cycleTime = mix(3.0, 7.0, hash11(fm * 17.3));
        float meteorTime = mod(t - hash11(fm * 23.7) * cycleTime, cycleTime);
        float travelDuration = mix(0.5, 1.2, hash11(fm * 31.1));

        if (meteorTime > travelDuration + 0.3) continue;

        float angle = mix(-0.4, -1.3, hash11(fm * 41.3));
        vec2 dir = normalize(vec2(cos(angle), sin(angle)));
        vec2 startPos = vec2(
            mix(-0.3, 0.8, hash11(fm * 53.7)),
            mix(0.2, 0.7, hash11(fm * 61.1))
        );
        float speed = mix(1.0, 2.0, hash11(fm * 71.3));
        float headT = clamp(meteorTime / travelDuration, 0.0, 1.0);
        vec2 headPos = startPos + dir * speed * headT;

        float headFade = smoothstep(0.0, 0.1, meteorTime)
                       * smoothstep(travelDuration + 0.3, travelDuration, meteorTime);

        float trailLen = mix(0.15, 0.35, hash11(fm * 83.7));

        for (int s = 0; s < NUM_TRAIL_STEPS; s++) {
            float sf = float(s) / float(NUM_TRAIL_STEPS);
            vec2 samplePos = headPos - dir * trailLen * sf;
            vec2 rel = uv - samplePos;

            float distPerp = abs(dot(rel, vec2(-dir.y, dir.x)));

            // Line width: narrow at head, wide at tail
            float width = mix(0.003, 0.015, sf);
            // core multiplier 0.15 ensures trail is visible even under SwiftShader
            float core = exp(-distPerp / width) * 0.15;

            float trailFade = (1.0 - sf) * (1.0 - sf);
            float intensity = core * trailFade * headFade / float(NUM_TRAIL_STEPS);

            float hue = mix(0.05, 0.12, sf);
            vec3 meteorCol = hsv2rgb(vec3(hue, mix(0.1, 0.4, sf), 1.0));
            col += meteorCol * intensity;
        }

        // Meteor head: bright point
        float headDist = length(uv - headPos);
        float headGlow = headFade * 0.005 / (headDist * headDist + 0.0008);
        col += vec3(1.0, 0.95, 0.85) * headGlow;
    }

    col = col / (1.0 + col);
    col = pow(col, vec3(0.95));
    fragColor = vec4(col, 1.0);
}
```

### Variant 8: Fountain/Upward Jet Particle System (Single-Pass Stateless)

Water/sparks jetting upward from a point, parabolic descent. Key: **Particles must be sharp, individually visible points** (small epsilon), not just a diffuse glow blob. Must include: (1) main water column particles (upward jet + parabola) (2) splash particles (spread sideways after hitting water) (3) water surface/pool visuals.

**IMPORTANT: Most common fountain failure**: Only produces blurry glow without visible individual water droplet trajectories! Must use small epsilon (<=0.002) so each particle is clearly visible as an individual light point. Numerator must also be proportionally reduced to control total brightness.

```glsl
#define NUM_WATER 60
#define NUM_SPLASH 40
#define FOUNTAIN_BASE vec2(0.0, -0.3)
#define WATER_LEVEL -0.3

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    float t = iTime;

    // Dark background
    vec3 col = vec3(0.01, 0.02, 0.06);

    // --- Water pool/surface ---
    float waterDist = abs(uv.y - WATER_LEVEL);
    float waterLine = smoothstep(0.01, 0.0, waterDist) * 0.3;
    float waterBody = smoothstep(WATER_LEVEL, WATER_LEVEL - 0.15, uv.y);
    col += vec3(0.02, 0.06, 0.12) * waterBody;
    col += vec3(0.3, 0.5, 0.7) * waterLine;

    // --- Main water column particles: upward jet + parabola ---
    for (int i = 0; i < NUM_WATER; i++) {
        float fi = float(i);
        float lifetime = mix(1.0, 2.0, hash11(fi * 3.7));
        float age = mod(t - hash11(fi * 2.3) * lifetime, lifetime);
        float norm = age / lifetime;

        float spreadAngle = (hash11(fi * 7.3) - 0.5) * 0.6;
        float speed = mix(0.9, 1.6, hash11(fi * 11.0));
        vec2 vel0 = vec2(sin(spreadAngle), cos(spreadAngle)) * speed;

        vec2 pos = FOUNTAIN_BASE + vel0 * age + vec2(0.0, -1.8) * age * age;

        if (pos.y < WATER_LEVEL - 0.02) continue;

        vec2 rel = uv - pos;
        float dist = length(rel);

        float fade = smoothstep(0.0, 0.05, norm) * smoothstep(1.0, 0.6, norm);
        // Sharp light point: small epsilon makes each particle clearly visible as an individual dot
        // peak = 0.004/0.0015 = 2.67, x 60 x avg_fade(0.25) ≈ 40 → Reinhard OK
        float glow = 0.004 / (dist * dist + 0.0015) * fade;

        vec3 waterCol = mix(vec3(0.5, 0.8, 1.0), vec3(0.9, 0.97, 1.0), hash11(fi * 5.0));
        col += waterCol * glow;
    }

    // --- Splash particles: spread sideways at water surface ---
    for (int i = 0; i < NUM_SPLASH; i++) {
        float fi = float(i) + 200.0;
        float lifetime = mix(0.3, 0.8, hash11(fi * 3.7));
        float age = mod(t - hash11(fi * 2.3) * lifetime, lifetime);
        float norm = age / lifetime;

        float xOffset = (hash11(fi * 7.3) - 0.5) * 0.5;
        vec2 splashBase = vec2(xOffset, WATER_LEVEL);
        float splashAngle = (hash11(fi * 11.0) - 0.5) * 2.5;
        float splashSpeed = mix(0.2, 0.5, hash11(fi * 13.0));
        vec2 splashVel = vec2(sin(splashAngle), abs(cos(splashAngle))) * splashSpeed;

        vec2 pos = splashBase + splashVel * age + vec2(0.0, -2.0) * age * age;
        if (pos.y < WATER_LEVEL - 0.01) continue;

        vec2 rel = uv - pos;
        float dist = length(rel);

        float fade = smoothstep(0.0, 0.05, norm) * smoothstep(1.0, 0.3, norm);
        float glow = 0.002 / (dist * dist + 0.001) * fade;

        col += vec3(0.7, 0.85, 1.0) * glow;
    }

    col = col / (1.0 + col);
    fragColor = vec4(col, 1.0);
}
```

### Variant 9: Campfire/Flame Particle System (Single-Pass Stateless)

Flame effects must include **two layers**: (1) smooth flame body at the base (noise-driven cone gradient) (2) many **discrete ember/spark particles** above, drifting upward and gradually extinguishing. Using only a smooth gradient will be judged as "no particle system."

**IMPORTANT: Most common flame failure**: Only draws a smooth gradient without discrete particles! Must have NUM_SPARKS individual point-like particles drifting out from the flame top.

```glsl
#define NUM_SPARKS 60
#define FIRE_BASE vec2(0.0, -0.35)

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash11(dot(i, vec2(127.1, 311.7)));
    float b = hash11(dot(i + vec2(1.0, 0.0), vec2(127.1, 311.7)));
    float c = hash11(dot(i + vec2(0.0, 1.0), vec2(127.1, 311.7)));
    float d = hash11(dot(i + vec2(1.0, 1.0), vec2(127.1, 311.7)));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    float t = iTime;
    vec3 col = vec3(0.02, 0.01, 0.01);

    // --- Layer 1: flame body (smooth noise cone) ---
    vec2 fireUV = uv - FIRE_BASE;
    float fireH = clamp(fireUV.y / 0.5, 0.0, 1.0);
    float width = mix(0.15, 0.01, fireH);
    float n = noise(vec2(fireUV.x * 6.0, fireUV.y * 4.0 - t * 3.0));
    float flameShape = smoothstep(width, 0.0, abs(fireUV.x + (n - 0.5) * 0.08))
                     * smoothstep(-0.02, 0.05, fireUV.y)
                     * smoothstep(0.55, 0.0, fireUV.y);
    vec3 innerCol = vec3(1.0, 0.95, 0.7);
    vec3 outerCol = vec3(1.0, 0.35, 0.05);
    vec3 flameCol = mix(outerCol, innerCol, smoothstep(0.3, 0.8, flameShape));
    col += flameCol * flameShape * 1.5;

    // --- Layer 2: discrete ember particles (required!) ---
    for (int i = 0; i < NUM_SPARKS; i++) {
        float fi = float(i);
        float lifetime = mix(0.8, 2.0, hash11(fi * 3.7));
        float age = mod(t - hash11(fi * 2.3) * lifetime, lifetime);
        float norm = age / lifetime;

        float xSpread = (hash11(fi * 7.3) - 0.5) * 0.2;
        float riseSpeed = mix(0.3, 0.7, hash11(fi * 11.0));
        float wobble = sin(t * 3.0 + fi * 2.7) * 0.03 * norm;
        vec2 sparkPos = FIRE_BASE + vec2(0.0, 0.25)
                      + vec2(xSpread + wobble, riseSpeed * age);

        vec2 rel = uv - sparkPos;
        float dist = length(rel);

        float fade = smoothstep(0.0, 0.1, norm) * smoothstep(1.0, 0.3, norm);
        // peak = 0.003/0.0008 = 3.75, x 60 x avg_fade(0.2) ≈ 45 → Reinhard OK
        float glow = 0.003 / (dist * dist + 0.0008) * fade;

        float hue = mix(0.03, 0.12, norm);
        vec3 sparkCol = hsv2rgb(vec3(hue, mix(0.9, 0.3, norm), 1.0));
        col += sparkCol * glow;
    }

    col = col / (1.0 + col);
    col = pow(col, vec3(0.95));
    fragColor = vec4(col, 1.0);
}
```

### Variant 10: Spiral Array/Magic Particle System (Single-Pass Stateless)

Magic effects, spiral ascent, magic circles, etc. require particles arranged in **geometric arrays** with **iridescent shimmer**. Key: particles must be individually visible glowing points (not a blurry glow blob), and the spiral structure must be clearly discernible.

**IMPORTANT: Most common magic failure**: Only produces a blob of blurry light (diffuse glow blob) without visible individual particles or geometric structure! Ensure each particle is an independently visible small light point, and the overall arrangement forms spiral/ring/other geometric shapes. Reduce epsilon to make each particle sharper (small light dot) rather than a large blurry halo.

```glsl
#define NUM_SPIRAL 80
#define NUM_RING 40
#define WAND_TIP vec2(0.0, -0.15)

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;
    float t = iTime;
    vec3 col = vec3(0.01, 0.005, 0.02);

    // --- Layer 1: spiral ascending particles (emanating from emission point) ---
    for (int i = 0; i < NUM_SPIRAL; i++) {
        float fi = float(i);
        float lifetime = mix(2.0, 4.0, hash11(fi * 3.7));
        float age = mod(t - hash11(fi * 2.3) * lifetime, lifetime);
        float norm = age / lifetime;

        // Spiral trajectory: angle increases with time and height
        float baseAngle = fi / float(NUM_SPIRAL) * 6.2832 * 3.0;
        float spiralAngle = baseAngle + norm * 8.0 + t * 1.5;
        float radius = 0.05 + norm * 0.25;
        float height = norm * 0.7;

        vec2 pos = WAND_TIP + vec2(cos(spiralAngle) * radius, height);

        vec2 rel = uv - pos;
        float dist = length(rel);

        float fade = smoothstep(0.0, 0.08, norm) * smoothstep(1.0, 0.4, norm);
        // Sharp small light point: small epsilon makes particles clearly visible as individual dots
        // peak = 0.004/0.0006 = 6.67, x 80 x avg_fade(0.25) ≈ 133 → Reinhard OK
        float glow = 0.004 / (dist * dist + 0.0006) * fade;

        // Iridescent effect: hue varies with particle ID + time, producing rainbow shimmer
        float hue = fract(fi / float(NUM_SPIRAL) + t * 0.3 + norm * 0.5);
        float shimmer = 0.7 + 0.3 * sin(t * 8.0 + fi * 3.7);
        vec3 pCol = hsv2rgb(vec3(hue, 0.7, 1.0)) * shimmer;
        col += pCol * glow;
    }

    // --- Layer 2: magic circle ring (horizontally rotating light point ring) ---
    float ringY = WAND_TIP.y + 0.45;
    float ringRadius = 0.2 + 0.03 * sin(t * 2.0);
    for (int i = 0; i < NUM_RING; i++) {
        float fi = float(i);
        float angle = fi / float(NUM_RING) * 6.2832 + t * 2.0;
        // Simulated perspective: ellipse (cos full width, sin compressed)
        vec2 ringPos = vec2(cos(angle) * ringRadius, ringY + sin(angle) * ringRadius * 0.3);

        vec2 rel = uv - ringPos;
        float dist = length(rel);

        float pulse = 0.6 + 0.4 * sin(t * 5.0 + fi * 1.5);
        // peak = 0.003/0.0004 = 7.5, x 40 x avg_pulse(0.6) ≈ 180 → Reinhard OK
        float glow = 0.003 / (dist * dist + 0.0004) * pulse;

        float hue = fract(fi / float(NUM_RING) + t * 0.5);
        vec3 rCol = hsv2rgb(vec3(hue, 0.6, 1.0));
        col += rCol * glow;
    }

    col = col / (1.0 + col);
    col = pow(col, vec3(0.9));
    fragColor = vec4(col, 1.0);
}
```

## Performance & Composition

**Performance**:
- Particle count is the biggest performance lever; use early exit `if (dist > threshold) continue;` for optimization
- Frame feedback trails (`prev * 0.95 + current`) can achieve high visual density with fewer particles
- N-body O(N²) interaction: reduce to O(1) neighbor queries using spatial grid partitioning or Voronoi tracking
- High-speed particles use sub-frame stepping to eliminate trajectory gaps
- Velocity/acceleration need clamp to prevent numerical explosion; Verlet is more stable than Euler
-

**Composition**:
- **Raymarching**: sample particle density during march steps, or particles in separate Buffer then composited
- **Noise / Flow Field**: use noise gradients to drive particle velocity, producing organic flow effects
- **Post-Processing**: Bloom (Gaussian blur overlay), chromatic aberration, Reinhard tone mapping
- **SDF shapes**: rotate local coordinates based on velocity direction to render fish/droplet specific shapes
- **Voronoi acceleration**: large-scale particles use Voronoi tracking, reducing rendering and physics queries from O(N) to O(1)

## Further Reading

Full step-by-step tutorial, mathematical derivations, and advanced usage in [reference](../reference/particle-system.md)
