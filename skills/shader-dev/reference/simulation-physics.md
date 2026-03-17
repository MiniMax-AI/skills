# GPU Physics Simulation — Detailed Reference

This document is the complete reference material for [SKILL.md](SKILL.md), containing step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL Basics**: uniforms, texture sampling (`texture`/`texelFetch`), `fragCoord`/`iResolution` coordinate system
- **ShaderToy Multi-Pass Mechanism**: Buffer A/B/C/D read/write between each other, `iChannel0~3` binding, Common pass for shared code
- **Vector Calculus Basics**: gradient, divergence, curl, Laplacian
- **Numerical Integration**: Forward Euler, semi-implicit methods (Semi-implicit / Verlet)
- **Textures as Data Storage**: Encoding physical quantities such as position/velocity/density into RGBA channels of texture pixels

## Core Principles in Detail

The core paradigm of GPU physics simulation is **Buffer Feedback**: leveraging ShaderToy's multi-pass architecture to store physical state (position, velocity, density, pressure, etc.) in texture buffers. Each frame reads the previous frame's state, computes new state, and writes it back. Each pixel computes independently in parallel, achieving GPU-level massively parallel physics solving.

### Key Mathematical Tools in Detail

**1. Discrete Laplacian Operator** (used for wave equation, viscous force, diffusion):
```
∇²f ≈ f(x+1,y) + f(x-1,y) + f(x,y+1) + f(x,y-1) - 4·f(x,y)
```
The Laplacian measures the difference between a point's value and the average of its neighbors. In the wave equation, it drives wave propagation; in fluid simulation, it provides viscous force (velocity diffusion); in the heat equation, it drives temperature equalization.

**2. Semi-Lagrangian Advection** (used for fluid solving):
```
f_new(x) = f_old(x - v·dt)    // backward tracing along the velocity field
```
Advection is the most critical step in fluid simulation. The semi-Lagrangian method achieves unconditionally stable advection through "backward tracing" — starting from the target position, tracing backward along the velocity field to find the source position, then sampling the value at the source. This avoids the CFL condition limitation of forward Euler advection.

**3. Spring-Damper Force** (used for cloth, soft bodies):
```
F_spring = k · (|Δx| - L₀) · normalize(Δx)
F_damper = c · dot(normalize(Δx), Δv) · normalize(Δx)
```
Spring force pulls two mass points back to the rest length L₀; stiffness k determines the restoring force strength. Damper force attenuates relative velocity along the connection direction; coefficient c determines the energy dissipation rate. Combined, they produce stable elastic motion.

**4. Vorticity Confinement** (used for preserving fluid detail):
```
curl = ∂v_x/∂y - ∂v_y/∂x
vorticity_force = ε · (∇|curl| × curl) / |∇|curl||
```
Numerical viscosity over-smooths small-scale vortices. Vorticity confinement compensates for this artificial dissipation by applying an additional force in high-vorticity regions, pushing small vortices into more concentrated rotational structures and preserving the visual richness of the fluid.

## Implementation Steps in Detail

### Step 1: Ping-Pong Double Buffer Structure

**What**: Create two Buffers (A and B) that alternate read/write to achieve state persistence.

**Why**: GPU shaders cannot simultaneously read and write the same buffer. The ping-pong strategy reads from one buffer (previous frame's data) and writes to the other each frame, then swaps on the next frame.

**IMPORTANT: Key Difference Between ShaderToy and WebGL2**: In ShaderToy, Buffer A/B are two independent passes with separate write targets, so `iChannel0=self, iChannel1=other` doesn't conflict. However, in WebGL2 there's only one shader program doing ping-pong, and the write target texture cannot be simultaneously read. The solution is **dual-channel encoding** (R=current height, G=previous frame height).

**Code** (WebGL2-safe version, reads only from iChannel0, with RGBA8-compatible encoding):
```glsl
// IMPORTANT: Only use iChannel0 (read currentBuf), write to nextBuf (must be different!)
// IMPORTANT: encode/decode ensure signed values aren't clipped on RGBA8 (no float textures/SwiftShader)
uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }
float encode(float v) { return useFloatTex == 1 ? v : v * 0.5 + 0.5; }

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

    float laplacian = left + right + down + up - 4.0 * current;
    float next = 2.0 * current - previous + 0.25 * laplacian;

    next *= 0.995; // damping decay
    next *= min(1.0, float(iFrame)); // zero on frame 0

    fragColor = vec4(encode(next), encode(current), 0.0, 0.0);
}
```

### Step 2: Interaction-Driven (External Force Injection)

**What**: Inject energy into the simulation through mouse clicks or programmatic generation.

**Why**: Physics simulations need external excitation to start and sustain. Mouse interaction is the most intuitive driving method; programmatic methods can simulate raindrops, explosions, etc.

**Code** (insert before wave equation computation):
```glsl
float d = 0.0;

if (iMouse.z > 0.0)
{
    // Mouse click: create ripple at mouse position
    d = smoothstep(4.5, 0.5, length(iMouse.xy - fragCoord));
}
else
{
    // Programmatic raindrop: pseudo-random position + impulse
    float t = iTime * 2.0;
    vec2 pos = fract(floor(t) * vec2(0.456665, 0.708618)) * iResolution.xy;
    float amp = 1.0 - step(0.05, fract(t));
    d = -amp * smoothstep(2.5, 0.5, length(pos - fragCoord));
}
```

### Step 3: Rendering Layer (Height Field Visualization)

**What**: Read simulation results in the Image Pass, compute normals via gradient calculation, and render lighting effects.

**Why**: The simulation result is a height field texture that needs to be transformed into a visible surface effect. Computing gradients via finite differences as normals enables refraction, diffuse reflection, specular highlights, and other water surface effects.

**Code** (Image Pass):
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec3 e = vec3(vec2(1.0) / iResolution.xy, 0.0);

    // Read four-neighbor height values from Buffer A
    float left  = texture(iChannel0, uv - e.xz).x;
    float right = texture(iChannel0, uv + e.xz).x;
    float down  = texture(iChannel0, uv - e.zy).x;
    float up    = texture(iChannel0, uv + e.zy).x;

    // Construct normal from gradient
    vec3 normal = normalize(vec3(right - left, up - down, 1.0));

    // Lighting computation
    vec3 light = normalize(vec3(0.2, -0.5, 0.7));
    float diffuse = max(dot(normal, light), 0.0);
    float spec = pow(max(-reflect(light, normal).z, 0.0), 32.0);

    // Refraction-offset background texture sampling
    vec4 bg = texture(iChannel1, uv + normal.xy * 0.35);
    vec3 waterTint = vec3(0.7, 0.8, 1.0);

    fragColor = mix(bg, vec4(waterTint, 1.0), 0.25) * diffuse + spec;
}
```

### Step 4: Chained Multi-Buffer Iteration (Improving Accuracy)

**What**: Chain multiple Buffers together to execute the same solver multiple times per frame.

**Why**: Many physics solvers (fluid pressure projection, constraint solving) require multiple iterations to converge. In ShaderToy, you can chain Buffer A → B → C to execute the same code, equivalent to 3 iterations per frame. This is critical for Eulerian fluid (pressure-divergence elimination) and rigid bodies (impulse constraint solving).

**Full Euler fluid solver code** (Buffer A/B/C share Common pass):
```glsl
// === Common Pass ===
#define dt 0.15                        // adjustable: time step
#define viscosityThreshold 0.64        // adjustable: viscosity coefficient (larger = thinner)
#define vorticityThreshold 0.25        // adjustable: vorticity confinement strength

vec4 fluidSolver(sampler2D field, vec2 uv, vec2 step,
                 vec4 mouse, vec4 prevMouse)
{
    float k = 0.2, s = k / dt;

    // Sample center and four neighbors
    vec4 c  = textureLod(field, uv, 0.0);
    vec4 fr = textureLod(field, uv + vec2(step.x, 0.0), 0.0);
    vec4 fl = textureLod(field, uv - vec2(step.x, 0.0), 0.0);
    vec4 ft = textureLod(field, uv + vec2(0.0, step.y), 0.0);
    vec4 fd = textureLod(field, uv - vec2(0.0, step.y), 0.0);

    // Divergence and density gradient
    vec3 ddx = (fr - fl).xyz * 0.5;
    vec3 ddy = (ft - fd).xyz * 0.5;
    float divergence = ddx.x + ddy.y;
    vec2 densityDiff = vec2(ddx.z, ddy.z);

    // Density solve
    c.z -= dt * dot(vec3(densityDiff, divergence), c.xyz);

    // Viscous force (Laplacian)
    vec2 laplacian = fr.xy + fl.xy + ft.xy + fd.xy - 4.0 * c.xy;
    vec2 viscosity = viscosityThreshold * laplacian;

    // Semi-Lagrangian advection
    vec2 densityInv = s * densityDiff;
    vec2 uvHistory = uv - dt * c.xy * step;
    c.xyw = textureLod(field, uvHistory, 0.0).xyw;

    // Mouse external force
    vec2 extForce = vec2(0.0);
    if (mouse.z > 1.0 && prevMouse.z > 1.0)
    {
        vec2 drag = clamp((mouse.xy - prevMouse.xy) * step * 600.0,
                          -10.0, 10.0);
        vec2 p = uv - mouse.xy * step;
        extForce += 0.001 / dot(p, p) * drag;
    }

    c.xy += dt * (viscosity - densityInv + extForce);

    // Velocity decay
    c.xy = max(vec2(0.0), abs(c.xy) - 5e-6) * sign(c.xy);

    // Vorticity confinement
    c.w = (fd.x - ft.x + fr.y - fl.y); // curl
    vec2 vorticity = vec2(abs(ft.w) - abs(fd.w),
                          abs(fl.w) - abs(fr.w));
    vorticity *= vorticityThreshold / (length(vorticity) + 1e-5) * c.w;
    c.xy += vorticity;

    // Boundary conditions
    c.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    c.x *= smoothstep(0.5, 0.49, abs(uv.x - 0.5));

    // Stability clamping
    c = clamp(c, vec4(-24.0, -24.0, 0.5, -0.25),
                 vec4( 24.0,  24.0, 3.0,  0.25));

    return c;
}

// === Buffer A / B / C (identical code) ===
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 stepSize = 1.0 / iResolution.xy;
    vec4 prevMouse = textureLod(iChannel0, vec2(0.0), 0.0);
    fragColor = fluidSolver(iChannel0, uv, stepSize, iMouse, prevMouse);

    // Bottom row stores mouse state
    if (fragCoord.y < 1.0) fragColor = iMouse;
}
```

### Step 5: Texture Data Layout for Particle/Mass-Point Systems

**What**: Encode particle positions, velocities, and other attributes at specific pixel locations in a texture.

**Why**: In GPU physics simulation, each particle/mass point needs to store multiple attributes (position, velocity, force, etc.). By partitioning the texture into regions (e.g., left half for positions, right half for velocities), or encoding different attributes into different RGBA channels, a compact data layout is achieved.

**Code** (cloth simulation data layout example):
```glsl
#define SIZX 128.0  // adjustable: cloth width (particle count)
#define SIZY 64.0   // adjustable: cloth height (particle count)

// Left half [0, SIZX) stores positions, right half [SIZX, 2*SIZX) stores velocities
// IMPORTANT: In WebGL2, getpos/getvel both read from iChannel0 (currentBuf, read-only),
//    write target is nextBuf (separate buffer), avoiding read-write conflict
vec3 getpos(vec2 id)
{
    return texture(iChannel0, (id + 0.5) / iResolution.xy).xyz;
}

vec3 getvel(vec2 id)
{
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iResolution.xy).xyz;
}

// In mainImage, decide whether to output position or velocity based on fragCoord
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 fc = floor(fragCoord);
    vec2 c = fc;
    c.x = fract(c.x / SIZX) * SIZX; // mass point ID

    vec3 pos = getpos(c);
    vec3 vel = getvel(c);

    // ... physics computation ...

    // Output: left half stores position, right half stores velocity
    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```

### Step 6: Spring-Damper Constraint System

**What**: Implement spring forces and damping forces between mass points.

**Why**: Spring-dampers are the core of cloth and soft body simulation. Each mass point is connected to neighbors via springs — spring force maintains structural shape, damping force dissipates oscillation energy. Using near-neighbors (structural springs) + diagonals (shear springs) + skip-connections (bending springs) provides complete constraints.

**Full code**:
```glsl
const float SPRING_K = 0.15;  // adjustable: spring stiffness
const float DAMPER_C = 0.10;  // adjustable: damping coefficient
const float GRAVITY  = 0.0022; // adjustable: gravitational acceleration

vec3 pos, vel, ovel;
vec2 c; // current mass point ID

void edge(vec2 dif)
{
    // Boundary check
    if ((dif + c).x < 0.0 || (dif + c).x >= SIZX ||
        (dif + c).y < 0.0 || (dif + c).y >= SIZY) return;

    float restLen = length(dif); // rest length = initial distance
    vec3 posdif = getpos(dif + c) - pos;
    vec3 veldif = getvel(dif + c) - ovel;

    // IMPORTANT: Must check for zero length, otherwise normalize(vec3(0)) produces NaN
    float plen = length(posdif);
    if (plen < 0.0001) return;
    vec3 dir = posdif / plen;

    // Spring force: restore to rest length
    vel += dir
         * clamp(plen - restLen, -1.0, 1.0)
         * SPRING_K;

    // Damping force: attenuate relative velocity along connection direction
    vel += dir
         * dot(dir, veldif)
         * DAMPER_C;
}

// In mainImage, call 12 edges (near-neighbors + diagonals + skip-connections)
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // ... initialize pos, vel, c ...
    ovel = vel;

    // Structural springs (4 near-neighbors)
    edge(vec2( 0.0, 1.0));
    edge(vec2( 0.0,-1.0));
    edge(vec2( 1.0, 0.0));
    edge(vec2(-1.0, 0.0));

    // Shear/bending springs (diagonals + skip-connections)
    edge(vec2( 1.0, 1.0));
    edge(vec2(-1.0,-1.0));
    edge(vec2( 0.0, 2.0));
    edge(vec2( 0.0,-2.0));
    edge(vec2( 2.0, 0.0));
    edge(vec2(-2.0, 0.0));
    edge(vec2( 2.0,-2.0));
    edge(vec2(-2.0, 2.0));

    // Collision detection (sphere)
    // ... ballcollis() ...

    // Integration
    pos += vel;
    vel.y += GRAVITY;

    // Air resistance (normal wind force)
    vec3 norm = findnormal(c);
    vec3 windvel = vec3(0.01, 0.0, -0.005); // adjustable: wind direction and speed
    vel -= norm * (dot(norm, vel - windvel) * 0.05);

    // Fixed boundary (top row pinned as curtain rod)
    if (c.y == 0.0)
    {
        pos = vec3(fc.x * 0.85, fc.y, fc.y * 0.01);
        vel = vec3(0.0);
    }

    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```

### Step 7: N-Body Particle Interaction (Biot-Savart Vortex Method)

**What**: Implement all-pairs interaction forces between all particles.

**Why**: Certain physical systems (such as vortex dynamics, gravitational N-body problems) require each particle to interact with all other particles. The Biot-Savart law gives the velocity field generated by vorticity, which is the core of 2D vortex simulation. Uses semi-Newton (Verlet-type) two-step integration for improved accuracy.

**Full code**:
```glsl
#define N 20           // adjustable: N×N total particles
#define Nf float(N)
#define MARKERS 0.90   // adjustable: passive marker particle ratio

// STRENGTH automatically scales with particle count and marker ratio
float STRENGTH = 1e3 * 0.25 / (1.0 - MARKERS) * sqrt(30.0 / Nf);

#define tex(i,j) texture(iChannel1, (vec2(i,j) + 0.5) / iResolution.xy)
#define W(i,j)   tex(i, j + N).z  // vorticity stored in tile(0,1) z channel

void mainImage(out vec4 O, vec2 U)
{
    vec2 T = floor(U / Nf);   // tile index
    U = mod(U, Nf);            // particle ID

    // Pass 1 (Buffer A): half-step integration dt*0.5
    // Pass 2 (Buffer B): full-step integration using Pass 1 velocity

    vec2 F = vec2(0.0);

    // N×N all-pairs Biot-Savart summation
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
        {
            float w = W(i, j);
            vec2 d = tex(i, j).xy - O.xy;
            // Periodic boundary: take nearest image
            d = (fract(0.5 + d / iResolution.xy) - 0.5) * iResolution.xy;
            float l = dot(d, d);
            if (l > 1e-5)
                F += vec2(-d.y, d.x) * w / l; // Biot-Savart kernel
        }

    O.zw = STRENGTH * F;  // velocity
    O.xy += O.zw * dt;    // integrate position
    O.xy = mod(O.xy, iResolution.xy); // periodic boundary
}
```

### Step 8: State Storage in Specific Pixels (Global Variable Trick)

**What**: Store global state (current position, time, mouse history) at fixed pixel locations in the texture.

**Why**: GPU shaders have no global variables. By storing state at agreed-upon pixel coordinates (usually `(0,0)` or the bottom row), the next frame can read these "global variables". This is indispensable for ODE integration (e.g., Lorenz attractor) and interactions that need to track mouse history.

**Full code**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Pixel (0,0) stores global state (e.g., Lorenz attractor's current 3D position)
    if (floor(fragCoord) == vec2(0, 0))
    {
        if (iFrame == 0)
        {
            fragColor = vec4(0.1, 0.001, 0.0, 0.0); // initial conditions
        }
        else
        {
            vec3 state = texture(iChannel0, vec2(0.0)).xyz;
            // Execute multi-step ODE integration
            for (float i = 0.0; i < 96.0; i++)
            {
                // Lorenz system: dx/dt = σ(y-x), dy/dt = x(ρ-z)-y, dz/dt = xy-βz
                vec3 deriv;
                deriv.x = 10.0 * (state.y - state.x);        // σ = 10
                deriv.y = state.x * (28.0 - state.z) - state.y; // ρ = 28
                deriv.z = state.x * state.y - 8.0/3.0 * state.z; // β = 8/3
                state += deriv * 0.016 * 0.2;
            }
            fragColor = vec4(state, 0.0);
        }
        return;
    }

    // Other pixels: accumulate trajectory distance field
    vec3 last = texture(iChannel0, vec2(0.0)).xyz;
    float d = 1e6;
    for (float i = 0.0; i < 96.0; i++)
    {
        vec3 next = Integrate(last, 0.016 * 0.2);
        d = min(d, dfLine(last.xz * 0.015, next.xz * 0.015, uv));
        last = next;
    }

    float c = 0.5 * smoothstep(1.0 / iResolution.y, 0.0, d);
    vec3 prev = texture(iChannel0, fragCoord / iResolution.xy).rgb;
    fragColor = vec4(vec3(c) + prev * 0.99, 0.0); // decaying accumulation
}
```

## Common Variant Details

### Variant 1: Eulerian Fluid Simulation (Smoke / Ink)

**Difference from base version**: Extends from scalar wave equation to full 2D velocity field solving — including advection, viscosity, vorticity confinement, and density tracking. Requires 3+ chained buffer iterations for enhanced convergence.

**Key code**:
```glsl
// Buffer storage: xy = velocity, z = density, w = curl
// Key difference: semi-Lagrangian advection replaces simple neighborhood update
vec2 uvHistory = uv - dt * velocity.xy * stepSize;
vec4 advected = textureLod(field, uvHistory, 0.0);

// Vorticity confinement (preserve fluid detail)
float curl = (fd.x - ft.x + fr.y - fl.y);
vec2 vortGrad = vec2(abs(ft.w) - abs(fd.w), abs(fl.w) - abs(fr.w));
vec2 vortForce = vorticityThreshold / (length(vortGrad) + 1e-5) * curl * vortGrad;
velocity.xy += vortForce;
```

### Variant 2: Cloth Simulation (Mass-Spring-Damper)

**Difference from base version**: Changes from grid-based field equations to a discrete particle system. Each pixel represents a mass point storing 3D position and velocity. Connected to neighbors via spring-dampers, plus gravity, wind force, and collision. Multi-buffer chained iteration (4 passes) implements multiple sub-steps.

**Key code**:
```glsl
// Data layout: left half of texture = position, right half = velocity
// Spring force core
vec3 posdif = getpos(neighbor) - pos;
vec3 veldif = getvel(neighbor) - vel;
float restLen = length(neighborOffset);
force += normalize(posdif) * clamp(length(posdif) - restLen, -1.0, 1.0) * 0.15;
force += normalize(posdif) * dot(normalize(posdif), veldif) * 0.10;

// Sphere collision response
if (length(pos - ballPos) < ballRadius) {
    vel -= normalize(pos - ballPos) * dot(normalize(pos - ballPos), vel);
    pos = ballPos + normalize(pos - ballPos) * ballRadius;
}
```

> **IMPORTANT: Common Pitfalls**:
> - **Cloth Image Pass must project world coordinates to screen**: You cannot use `uv * vec2(SIZX, SIZY)` to map screen UV to grid ID, because particles have moved from their initial positions, producing scattered fragments. You must iterate over mesh faces, projecting vertex world coordinates to screen space for triangle rasterization
> - GLSL is strictly typed; you cannot write `float / vec2`. Wrong example: `length(dif) / vec2(SIZX, SIZY).x` will first execute float/vec2 causing a compile error; use `length(dif) / SIZX` instead
> - `normalize(vec3(0))` produces NaN; all `normalize()` calls must include a length check beforehand
> - In the Image Pass, `getpos`/`getvel` must use the simulation resolution (`iSimResolution`) for UV calculation, not the screen resolution `iResolution`
> - Texel center sampling should use `+0.5` offset (not `+0.01`)

### Variant 3: Rigid Body Physics Engine (Box2D-lite on GPU)

**Difference from base version**: The most complex variant. Uses structured pixel addressing (ECS data layout) to serialize rigid body attributes, joints, contact points, etc., into textures. Buffer A handles integration + collision detection, Buffer B/C/D handle impulse constraint iteration. Requires Common pass to encapsulate a complete physics library.

**Key code**:
```glsl
// Structured memory addressing: map structs to consecutive pixels
int bodyAddress(int b_id) {
    return pixel_count_of_Globals + pixel_count_of_Body * b_id;
}
Body loadBody(sampler2D buff, int b_id) {
    int addr = bodyAddress(b_id);
    vec4 d0 = texelFetch(buff, address2D(res, addr), 0);
    vec4 d1 = texelFetch(buff, address2D(res, addr+1), 0);
    b.pos = d0.xy; b.vel = d0.zw;
    b.ang = d1.x; b.ang_vel = d1.y; // ...
}

// Contact impulse solving
float v_n = dot(dv, contact.normal);
float dp_n = contact.mass_n * (-v_n + contact.bias);
dp_n = max(0.0, dp_n);
body.vel += body.inv_mass * dp_n * contact.normal;
```

### Variant 4: N-Body Vortex Particle Simulation

**Difference from base version**: Changes from field (Eulerian) method to particle (Lagrangian) method. Each particle carries vorticity, and the Biot-Savart law computes the full-field velocity. Uses semi-Newton two-step integration (Buffer A half-step → Buffer B full-step). O(N²) all-pairs interaction.

**Key code**:
```glsl
// Biot-Savart kernel: velocity induced by vorticity w at distance d
// v = w * (-dy, dx) / |d|²
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

**Difference from base version**: Extends to 3D. Uses Particle Cluster Grid (PCG) for spatial neighborhood management, custom bit packing (5-bit exponent + 9-bit component) to compress particle data into 4 floats. Buffer A handles advection + clustering, Buffer B computes density, Buffer C computes forces + integration, Buffer D computes shadows.

**Key code**:
```glsl
// Map 3D grid to 2D texture
vec2 dim2from3(vec3 p3d) {
    float ny = floor(p3d.z / SCALE.x);
    float nx = floor(p3d.z) - ny * SCALE.x;
    return vec2(nx, ny) * size3d.xy + p3d.xy;
}

// SPH pressure force
float pressure = max(rho / rest_density - 1.0, 0.0);
float SPH_F = force_coef_a * GD(d, 1.5) * pressure;
// Friction + surface tension
float Friction = 0.45 * dot(dir, dvel) * GD(d, 1.5);
float F = surface_tension * GD(d, surface_tension_rad);
p.force += force_k * dir * (F + SPH_F + Friction) * irho / rest_density;
```

## Performance Optimization Details

### 1. Neighborhood Sampling Optimization
- **Bottleneck**: Each pixel samples 4~12 neighbors; texture bandwidth is the main bottleneck
- **Optimization**: Use `texelFetch` instead of `texture` (skips filtering), pre-compute `1.0/iResolution.xy` to avoid repeated division

### 2. N-Body O(N²) Loop Optimization
- **Bottleneck**: All-pairs interaction has O(N²) complexity; N=20 means 400 iterations per frame, N=50 means 2500
- **Optimization**:
  - Limit N value (20~30 is enough for good visual results)
  - Use "cheap" periodic boundary mode (`fract` instead of 3×3 loop traversal)
  - Passive marker particles (90%) don't participate in force computation, only flow passively

### 3. Iteration Count vs. Accuracy Balance
- **Bottleneck**: Fluid/rigid body solvers need multiple iterations, but each buffer can only execute once
- **Optimization**:
  - Use 3 chained buffers (A→B→C) for 3 iterations/frame
  - 4 chained buffers for cloth (4 sub-steps/frame, time step = 1/4/60)
  - More buffers consume more GPU memory; balance accuracy against resources

### 4. Adaptive Precision
- **Optimization**: Use larger step sizes for screen edges or distant regions
```glsl
// Kelvin wave example: distant pixels use 8× step size
if (abs(U.y * R.y) > 100.0) dx *= 8.0 * abs(U.y);
```

### 5. Data Packing Compression
- **Optimization**: When each particle has more than 4 float attributes, use bit operations for packing
```glsl
// 3D SPH example: 3 floats compressed into 1 uint (5-bit exponent + 3×9-bit components)
uint packvec3(vec3 v) {
    int exp = clamp(int(ceil(log2(max(...)))), -15, 15);
    float scale = exp2(-float(exp));
    uvec3 sv = uvec3(round(clamp(v*scale, -1.0, 1.0) * 255.0) + 255.0);
    return uint(exp + 15) | (sv.x << 5) | (sv.y << 14) | (sv.z << 23);
}
```

### 6. Stability Safeguards
- Apply `clamp` to velocity/density to prevent numerical explosion
- Use `smoothstep` for soft boundary decay instead of hard cutoff
- Keep damping coefficients in the 0.95~0.999 range

## Combination Suggestions in Detail

### 1. Physics Simulation + Post-Processing Rendering
The most common combination. Buffer passes handle physics computation, Image pass handles visualization:
- **Waves + Refraction/Caustics**: Height field gradient drives refraction-offset sampling
- **Fluid + Ink Coloring**: Velocity field advects colored ink particles (Buffer D), with HSV random coloring
- **Cloth + Ray Tracing**: Voxelized spatial tree accelerates cloth surface ray intersection

### 2. Physics Simulation + SDF Rendering
Rigid body/particle position data is passed to the Image pass, rendered as geometry using SDF functions:
- `sdBox(p - bodyPos, bodySize)` renders rigid bodies
- `length(p - particlePos) - radius` renders particles
- Suitable for Box2D-lite rigid body engine visualization

### 3. Physics Simulation + Volume Rendering
3D simulations (e.g., SPH) require a volume rendering pipeline:
- Density field trilinear interpolation → ray marching → normal computation → lighting
- Shadows via a separate buffer accumulating optical density along light rays
- Environment map reflections + Fresnel blending

### 4. Multiple Physics System Coupling
- **Fluid + Rigid Bodies**: Fluid velocity field drives rigid body motion; rigid body occupancy modifies fluid boundaries
- **Cloth + Colliders**: Sphere/box shapes for collision detection, cloth elastic response
- **Particles + Fields**: Particles generate fields (density/vorticity), fields in turn drive particles (SPH / Biot-Savart)

### 5. Physics Simulation + Audio Visualization
- Bind audio texture via `iChannel`, mapping spectrum energy to external forces or parameters
- Low frequencies drive large-scale motion, high frequencies drive small-scale vortices/ripples
