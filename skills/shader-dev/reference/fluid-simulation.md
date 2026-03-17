# Fluid Simulation — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing prerequisite knowledge, step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

### GLSL Basics
- `texture`/`texelFetch` sampling, `iChannel0` buffer feedback, multi-pass rendering
- ShaderToy multi-buffer architecture: data flow between Buffer A/B/C/D

### Vector Calculus Basics
- Gradient: the spatial rate of change of a scalar field, pointing in the direction of greatest increase
- Divergence: the "source/sink" strength of a vector field
- Curl: the local rotational strength of a vector field
- Laplacian: the second derivative of a scalar field, measuring deviation from the neighborhood mean

### Data Encoding Paradigm
Understanding the paradigm of "encoding physical quantities into texture RGBA channels":
- `.xy` = velocity
- `.z` = pressure / density
- `.w` = passive scalar, e.g., ink concentration

## Implementation Steps in Detail

### Step 1: Data Encoding and Buffer Layout

**What**: Encode fluid physical quantities into the RGBA channels of a texture.

**Why**: GPU textures serve as the storage medium for fluid state. Each pixel is a grid cell, with channels storing different physical quantities, enabling full fluid state persistence.

**Code**:
```glsl
// Data layout convention:
// .xy = velocity field
// .z  = pressure / density
// .w  = passive scalar, e.g., ink concentration

// Sampling macro — simplify neighborhood access
#define T(p) texture(iChannel0, (p) / iResolution.xy)

// Get current pixel and its four neighbors
vec4 c = T(p);                    // center
vec4 n = T(p + vec2(0, 1));       // north
vec4 e = T(p + vec2(1, 0));       // east
vec4 s = T(p - vec2(0, 1));       // south
vec4 w = T(p - vec2(1, 0));       // west
```

### Step 2: Discrete Differential Operators

**What**: Compute gradient, Laplacian, divergence, and curl over a 3x3 pixel neighborhood.

**Why**: These operators are the foundation for discretizing the Navier-Stokes equations. A 3x3 stencil is more isotropic than a simple cross stencil, reducing grid-direction artifacts.

**Code**:
```glsl
// ===== Laplacian =====
// Weighted 3x3 stencil: center weight _K0, edge weight _K1, corner weight _K2
const float _K0 = -20.0 / 6.0;  // adjustable: center weight
const float _K1 =   4.0 / 6.0;  // adjustable: edge weight
const float _K2 =   1.0 / 6.0;  // adjustable: corner weight

vec4 laplacian = _K0 * c
    + _K1 * (n + e + s + w)
    + _K2 * (T(p+vec2(1,1)) + T(p+vec2(-1,1)) + T(p+vec2(1,-1)) + T(p+vec2(-1,-1)));

// ===== Gradient =====
// Central difference with diagonal correction
vec4 dx = (e - w) / 2.0;
vec4 dy = (n - s) / 2.0;

// ===== Divergence =====
float div = dx.x + dy.y;  // ∂vx/∂x + ∂vy/∂y

// ===== Curl / Vorticity =====
float curl = dx.y - dy.x;  // ∂vy/∂x - ∂vx/∂y
```

### Step 3: Initial Frame and Noise

**What**: Initialize the fluid state and inject a small amount of noise to avoid symmetry lock.

**Why**: If the initial state is entirely zero (zero velocity), the fluid equations will maintain this symmetric state and never move. Adding a small amount of random noise breaks the symmetry, allowing turbulence to develop naturally.

**Code**:
```glsl
if (iFrame < 10) {
    vec2 uv = p / iResolution.xy;
    // Position-based pseudo-random noise
    float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    // velocity.xy = small noise, pressure.z = 1.0, ink.w = small amount
    fragColor = vec4(noise * 1e-4, noise * 1e-4, 1.0, noise * 0.1);
    return;
}
```

### Step 4: Semi-Lagrangian Advection

**What**: Trace backward along the velocity field and sample from the upstream position to update the current pixel.

**Why**: This is the standard method for handling the `-(v·∇)v` advection term. Direct forward advection on an Eulerian grid leads to instability, while the semi-Lagrangian method is unconditionally stable — it won't blow up regardless of time step size.

**Code**:
```glsl
#define DT 0.15  // adjustable: time step, larger = faster fluid motion but may reduce accuracy

// Core: backward tracing — find the "upstream" position by tracing backward along velocity
// Then sample from the upstream position, effectively "transporting" the upstream state here
vec4 advected = T(p - DT * c.xy);

// Only advect velocity and passive scalar (ink), preserve local pressure
c.xyw = advected.xyw;
```

### Step 5: Viscous Diffusion

**What**: Apply Laplacian diffusion to the velocity field to simulate viscosity.

**Why**: Corresponds to the `ν∇²v` term. Viscosity smooths the velocity field, dissipating small-scale vortices. The parameter `ν` controls whether the fluid behaves like "water" (low viscosity) or "honey" (high viscosity).

**Code**:
```glsl
#define NU 0.5     // adjustable: kinematic viscosity coefficient. 0.01=water, 1.0=syrup
#define KAPPA 0.1  // adjustable: passive scalar (ink) diffusion coefficient

c.xy  += DT * NU * laplacian.xy;     // velocity diffusion
c.w   += DT * KAPPA * laplacian.w;   // ink diffusion
```

### Step 6: Pressure Projection

**What**: Compute the gradient of the pressure field and subtract it from the velocity field to enforce the incompressibility constraint.

**Why**: This is the core of Helmholtz-Hodge decomposition — decomposing the velocity field into a divergence-free part (what we want) and a curl-free part. By projecting out the divergence component via `v = v - K·∇p`, we ensure `∇·v ≈ 0`. In ShaderToy, the per-frame buffer feedback itself constitutes an implicit Jacobi iteration.

**Code**:
```glsl
#define K 0.2  // adjustable: pressure correction strength. Too large causes oscillation, too small yields poor incompressibility

// Pressure is stored in the .z channel
// Use pressure gradient to correct velocity, eliminating divergence
c.xy -= K * vec2(dx.z, dy.z);

// Mass conservation: update density/pressure based on divergence (Euler method)
c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
```

### Step 7: External Forces and Mouse Interaction

**What**: Inject velocity and ink into the fluid based on mouse input.

**Why**: The external force term `f` is the entry point for user interaction. The typical approach is to apply a Gaussian-decaying velocity impulse and ink injection near the mouse position.

**Code**:
```glsl
// Mouse interaction — drag to inject velocity and ink
if (iMouse.z > 0.0) {
    vec2 mousePos = iMouse.xy;
    vec2 mouseDelta = iMouse.xy - iMouse.zw;  // drag direction

    float dist = length(p - mousePos);
    float influence = exp(-dist * dist / 50.0);  // adjustable: 50.0 controls influence radius

    c.xy += DT * influence * mouseDelta;  // inject velocity
    c.w  += DT * influence;                // inject ink
}
```

### Step 8: Boundary Conditions and Numerical Stability

**What**: Handle boundary pixels, clamp numerical ranges, and apply dissipation.

**Why**: Without boundary conditions, the fluid "leaks" off-screen; without dissipation, fluid energy accumulates indefinitely, causing numerical explosion.

**Code**:
```glsl
// Boundary condition: zero velocity at edge pixels (no-slip)
if (p.x < 1.0 || p.y < 1.0 ||
    iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
    c.xyw *= 0.0;
}

// IMPORTANT: Ink decay: must use multiplicative decay; subtractive decay causes saturation in high-concentration areas and overly fast decay in low-concentration areas
c.w *= 0.995;  // 0.5% decay per frame, adjustable [0.99=fast dissipation, 0.999=persistent]

// Numerical clamping (prevent explosion)
c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));
```

### Step 9: Visualization Rendering (Image Pass)

**What**: Map physical quantities from the buffer to visible colors.

**Why**: Raw physical data (velocity, pressure) needs artistic color mapping to produce visual effects. Common techniques include: mapping velocity direction to hue, pressure to brightness, and overlaying ink concentration.

**Code**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces bright colors in [0,1] range
    // Never use extremely dark base colors like vec3(0.02, 0.01, 0.08) — multiplied by ink, they become invisible
    vec3 col = 0.5 + 0.5 * cos(atan(c.y, c.x) + vec3(0.0, 2.1, 4.2));
    // IMPORTANT: Use smoothstep instead of linear division to preserve gradient variation
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // IMPORTANT: Background color must be visible to the eye (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```

## Variant Details

### Variant 1: Rotational Self-Advection

**Difference from base version**: Instead of pressure projection, uses multi-scale rotational sampling to achieve natural divergence-free advection. Simpler computation, suitable for purely decorative fluid effects.

**Core idea**: Compute local rotation (curl) at different scales, then use rotationally offset sampling positions for advection.

**Key code**:
```glsl
#define RotNum 3           // adjustable: rotational sample count [3-7], more = more precise
#define angRnd 1.0         // adjustable: rotational randomness [0-1]

const float ang = 2.0 * 3.14159 / float(RotNum);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

// Compute rotation amount at a given scale
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

// Main loop: multi-scale advection accumulation
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
    sc *= 2.0;  // next scale
}
fragColor = texture(iChannel0, fract(uv + v * 3.0 / iResolution.x));
```

### Variant 2: Vorticity Confinement

**Difference from base version**: Adds vorticity confinement force on top of the base solver to prevent small vortices from dissipating too quickly due to numerical diffusion. Suitable for smoke, fire, and other scenes that need rich detail.

**Core idea**: Compute the gradient direction of the vorticity field (the direction where vorticity concentrates), then apply a restoring force along that direction.

**Key code**:
```glsl
#define VORT_STRENGTH 0.01  // adjustable: vorticity confinement strength [0.001 - 0.1]

// Compute gradient of vorticity magnitude (points toward increasing vorticity)
float curl_c = curl_at(uv);                    // current vorticity
float curl_n = abs(curl_at(uv + vec2(0, texel.y)));
float curl_s = abs(curl_at(uv - vec2(0, texel.y)));
float curl_e = abs(curl_at(uv + vec2(texel.x, 0)));
float curl_w = abs(curl_at(uv - vec2(texel.x, 0)));

vec2 eta = normalize(vec2(curl_e - curl_w, curl_n - curl_s) + 1e-5);

// Vorticity confinement force = ε * (η × ω)
vec2 conf = VORT_STRENGTH * vec2(eta.y, -eta.x) * curl_c;
c.xy += DT * conf;
```

### Variant 3: Viscous Fingering / Reaction-Diffusion Style

**Difference from base version**: No advection; instead uses rotation-driven self-amplification and Laplacian diffusion to produce organic patterns resembling reaction-diffusion. Suitable for abstract art generation.

**Core idea**: Compute a rotation angle from curl, apply 2D rotation to velocity components, and combine with Laplacian diffusion and divergence feedback.

**Key code**:
```glsl
const float cs = 0.25;   // adjustable: curl → rotation angle scaling
const float ls = 0.24;   // adjustable: Laplacian diffusion strength
const float ps = -0.06;  // adjustable: divergence-pressure feedback strength
const float amp = 1.0;   // adjustable: self-amplification coefficient (>1 enhances patterns)
const float pwr = 0.2;   // adjustable: curl exponent (controls rotation sensitivity)

// Compute rotation angle from curl
float sc = cs * sign(curl) * pow(abs(curl), pwr);

// Temporary velocity (with diffusion and divergence feedback)
float ta = amp * uv.x + ls * lapl.x + norm.x * sp + uv.x * sd;
float tb = amp * uv.y + ls * lapl.y + norm.y * sp + uv.y * sd;

// Rotate velocity components
float a = ta * cos(sc) - tb * sin(sc);
float b = ta * sin(sc) + tb * cos(sc);

fragColor = clamp(vec4(a, b, div, 1), -1.0, 1.0);
```

### Variant 4: Gaussian Kernel SPH Particle Fluid

**Difference from base version**: Completely abandons grid advection, instead using Gaussian kernel functions to estimate density and velocity at each grid point. Minimal (about 20 lines of core code), suitable for rapid prototyping and teaching.

**Core idea**: For all pixels in the neighborhood, perform mass-weighted velocity blending using Gaussian weights based on velocity + displacement. This is essentially a grid-based approximation of SPH.

**Key code**:
```glsl
#define RADIUS 7    // adjustable: search radius [3-10], larger = slower but smoother

vec4 r = vec4(0);
for (vec2 i = vec2(-RADIUS); ++i.x < float(RADIUS);)
    for (i.y = -float(RADIUS); ++i.y < float(RADIUS);) {
        vec2 v = texelFetch(iChannel0, ivec2(i + fragCoord), 0).xy;  // neighbor velocity
        float mass = texelFetch(iChannel0, ivec2(i + fragCoord), 0).z; // neighbor mass
        float w = exp(-dot(v + i, v + i)) / 3.14;  // Gaussian kernel weight
        r += mass * w * vec4(mix(v + v + i, v, mass), 1, 1);
    }
r.xy /= r.z + 1e-6;  // mass-weighted average velocity
```

### Variant 5: Lagrangian Vortex Particle Method

**Difference from base version**: Instead of solving on a grid, tracks discrete vortex particles with their positions and vorticities. Uses the Biot-Savart law to compute the velocity field directly from the vorticity distribution. Suitable for precise simulation of a small number of vortices.

**Core idea**: Each particle carries a position and vorticity. Induced velocity is computed through N-body summation. Uses Heun (semi-implicit) time integration for improved accuracy.

**Key code**:
```glsl
#define N 20                     // adjustable: N×N particles
#define STRENGTH 1e3 * 0.25      // adjustable: vorticity strength scaling

// Biot-Savart velocity computation (similar to 2D vortex 1/r decay)
vec2 F = vec2(0);
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = vorticity(i, j);          // particle vorticity
        vec2 d = particle_pos(i, j) - my_pos;
        float l = dot(d, d);
        if (l > 1e-5)
            F += vec2(-d.y, d.x) * w / l;  // Biot-Savart: v = ω × r / |r|²
    }
velocity = STRENGTH * F;
position += velocity * dt;
```

## Performance Optimization Details

### Bottleneck 1: Neighborhood Sample Count
- The basic 5-point stencil (cross) is fastest but has poor isotropy
- A 3x3 stencil (9 samples) is the best balance between accuracy and performance
- The `N×N` search radius in the SPH variant is extremely expensive; anything above 7 becomes slow
- **Optimization**: Use `texelFetch` instead of `texture` (skips filtering), or use `textureLod` to lock the mip level

### Bottleneck 2: Multi-Pass Overhead
- Classic solvers need 2-4 buffer passes (velocity, pressure, vorticity, visualization)
- **Optimization**: Merge multiple steps into a single pass. Pressure projection can leverage inter-frame feedback as implicit Jacobi iteration, eliminating the need for dedicated iteration passes
- For decorative effects that don't require strict incompressibility, rotational self-advection (Variant 1) can completely eliminate pressure projection

### Bottleneck 3: Advection Accuracy vs. Performance
- Single-step advection loses detail in high-velocity regions
- **Optimization**: Multi-step advection (`ADVECTION_STEPS = 3`) uses 3 small steps instead of 1 large step, at the cost of 3x the sampling
- Compromise: pre-compute offsets then uniformly subdivide sampling (avoid recalculating offsets at each step)

### Bottleneck 4: Mipmap as Alternative to Multi-Scale Traversal
- Multi-scale fluid requires computation at different spatial scales. The brute-force approach is multiple large-radius samples
- **Optimization**: Leverage GPU-generated mipmaps for O(1) multi-scale reads, using `textureLod(channel, uv, mip)` to directly read at different scales

### General Tips
- Add tiny noise on the initial frame (`1e-6 * noise`) to avoid symmetry lock caused by numerical precision issues
- Use `fract(uv + offset)` for periodic boundaries (torus topology), eliminating boundary check branches
- Multiply the pressure field by a near-1 decay factor (e.g., `0.9999`) to prevent pressure drift

## Combination Suggestions

### 1. Fluid + Normal Map Lighting
Treat the fluid velocity/density field as a height map, compute normals, and apply Phong/GGX lighting to produce a liquid metal visual effect.
```glsl
// Compute normals from the density field
vec2 dxy = vec2(
    texture(buf, uv + vec2(tx, 0)).z - texture(buf, uv - vec2(tx, 0)).z,
    texture(buf, uv + vec2(0, ty)).z - texture(buf, uv - vec2(0, ty)).z
);
vec3 normal = normalize(vec3(-BUMP * dxy, 1.0));
// Then plug into Phong/GGX lighting calculation
```

### 2. Fluid + Particle Tracing
Scatter passive particles in the fluid velocity field, updating particle positions each frame according to the flow velocity. Suitable for visualizing streamlines and creating ink diffusion effects.
```glsl
// Particle position update (in a separate buffer)
vec2 pos = texture(particleBuf, id).xy;
vec2 vel = texture(fluidBuf, pos / iResolution.xy).xy;
pos += vel * dt;
pos = mod(pos, iResolution.xy);  // periodic boundary
```

### 3. Fluid + Color Advection
Store RGB colors in extra channels or buffers and perform semi-Lagrangian advection synchronized with the velocity field, producing colorful ink mixing effects.

### 4. Fluid + Audio Response
Map audio spectrum low-frequency energy to force intensity and high frequencies to vorticity injection, creating music-driven fluid visualization.
```glsl
float bass = texture(iChannel1, vec2(0.05, 0.0)).x;   // low frequency
float treble = texture(iChannel1, vec2(0.8, 0.0)).x;   // high frequency
// Low frequency → thrust, high frequency → vortex disturbance
c.xy += bass * radialForce + treble * randomVortex;
```

### 5. Fluid + 3D Volume Rendering
Extend 2D fluid to 3D (using 2D texture slice packing to store 3D voxels) and render semi-transparent volumes via ray marching. Suitable for clouds and explosion effects.
