# Cellular Automata & Reaction-Diffusion — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), containing prerequisites, step-by-step explanations, variant details, performance analysis, and complete code examples for combination suggestions.

---

## Prerequisites

### GLSL Basics
- **Uniform variables**: `iResolution` (viewport resolution), `iFrame` (current frame number), `iTime` (elapsed time), `iMouse` (mouse position)
- **Texture sampling**: `texture(iChannel0, uv)` samples using UV coordinates (with filtering), `texelFetch(iChannel0, ivec2(px), 0)` samples at exact integer pixel coordinates
- **Multi-buffer feedback architecture**: ShaderToy supports Buffer A~D, each buffer can bind itself or other buffers as iChannel input

### ShaderToy Multi-Pass Mechanism
Data written by Buffer A → next frame Buffer A reads via iChannel0 self-feedback. This is the core mechanism for inter-frame state persistence. The Image pass handles final visual output.

### 2D Grid Sampling
- Pixel coordinates `fragCoord` are floating point, range `[0.5, resolution - 0.5]`
- UV coordinates = `fragCoord / iResolution.xy`, range `[0, 1]`
- `texelFetch(iChannel0, ivec2(px), 0)` reads the specified pixel exactly (no filtering), suitable for discrete CA
- `texture(iChannel0, uv)` uses hardware bilinear interpolation, suitable for continuous RD

### Basic Vector Math
- `normalize(v)`: normalize a vector
- `dot(a, b)`: dot product
- `cross(a, b)`: cross product
- `length(v)`: vector length

### Convolution Kernel Concepts
A 3x3 stencil performs a weighted sum of the center pixel and its 8 neighbors. Different weights produce different effects:
- **Laplacian kernel**: Detects deviation of the current value from the neighborhood mean (diffusion)
- **Gaussian kernel**: Blur/smoothing
- **Sobel kernel**: Edge detection/gradient computation

---

## Implementation Steps in Detail

### Step 1: Grid State Storage and Self-Feedback

**What**: Use ShaderToy's Buffer self-read mechanism to persistently store simulation state in a buffer texture. Each frame reads the previous frame's state, computes new state, and writes it back.

**Why**: GPU shaders are inherently stateless; buffer inter-frame feedback is required for time-step iteration. State is stored in RGBA channels — CA can use a single channel for alive/dead, while RD uses two channels for u and v respectively.

**Code**:
```glsl
// Buffer A: read previous frame's own state
// iChannel0 is bound to Buffer A itself (self-feedback)
vec4 prevState = texelFetch(iChannel0, ivec2(fragCoord), 0);

// Can also sample with UV coordinates (supports texture filtering)
vec2 uv = fragCoord / iResolution.xy;
vec4 prevSmooth = texture(iChannel0, uv);
```

**Key points**:
- `texelFetch` performs no filtering, reads a single pixel exactly, suitable for discrete CA
- `texture` uses hardware bilinear interpolation, blending adjacent pixel values near pixel boundaries, suitable for continuous RD
- The four RGBA channels can store different state variables (e.g., u, v, velocity field components, etc.)

### Step 2: Initialization (Noise Seeding)

**What**: Initialize the grid with pseudo-random noise on the first frame (or first few frames) to provide seeds for the simulation.

**Why**: Both CA and RD need initial perturbation to start evolution. Different initial conditions produce different final patterns. In practice, seeding is often repeated for the first 2~10 frames, since ShaderToy occasionally skips the first frame.

**Code**:
```glsl
// Simple hash noise function
float hash1(float n) {
    return fract(sin(n) * 138.5453123);
}

vec3 hash33(in vec2 p) {
    float n = sin(dot(p, vec2(41, 289)));
    return fract(vec3(2097152, 262144, 32768) * n);
}

// Initialization branch in mainImage
if (iFrame < 2) {
    // CA: random binary initialization
    float f = step(0.9, hash1(fragCoord.x * 13.0 + hash1(fragCoord.y * 71.1)));
    fragColor = vec4(f, 0.0, 0.0, 0.0);
} else if (iFrame < 10) {
    // RD: random continuous value initialization
    vec3 noise = hash33(fragCoord / iResolution.xy + vec2(53, 43) * float(iFrame));
    fragColor = vec4(noise, 1.0);
}
```

**Key points**:
- `hash1` is a simple pseudo-random number generator based on `sin`, producing values in [0, 1)
- `hash33` generates a 3D random vector from 2D coordinates, used for multi-channel RD initialization
- CA initialization uses `step(0.9, ...)` to produce approximately 10% density of living cells
- RD initialization uses continuous random values, with `iFrame` added so each frame seeds differently
- Multi-frame seeding (`iFrame < 10`) ensures sufficiently rich initial perturbation

### Step 3: Neighbor Sampling and Laplacian Computation

**What**: Perform weighted sampling of the current pixel's 8 (or 4) neighbors, computing the Laplacian or neighbor count.

**Why**: This is the core of CA/RD — local rules drive state updates through neighbor information. The Laplacian describes how much a point's value deviates from the surrounding average, physically corresponding to diffusion. The nine-point stencil is more accurate and isotropic than a simple cross stencil.

**Three Sampling Methods Compared**:

| Method | Use Case | Advantages | Disadvantages |
|------|----------|------|------|
| Method A: Discrete neighbor counting | CA | Exact integer coordinates, no filtering error | Can only handle discrete states |
| Method B: Nine-point Laplacian | RD | Good isotropy, high accuracy | 9 texture samples |
| Method C: 3x3 Gaussian blur | Simplified RD | Good smoothing effect | Not a true Laplacian |

**Method A Code Details**:
```glsl
// Discrete CA neighbor counting using texelFetch for exact reads
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;  // Wrap-around boundary (toroidal topology), left overflow appears on right
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}

ivec2 px = ivec2(fragCoord);
// Moore neighborhood: sum of 8 neighbors
int k = cell(px + ivec2(-1,-1)) + cell(px + ivec2(0,-1)) + cell(px + ivec2(1,-1))
      + cell(px + ivec2(-1, 0))                          + cell(px + ivec2(1, 0))
      + cell(px + ivec2(-1, 1)) + cell(px + ivec2(0, 1)) + cell(px + ivec2(1, 1));
```

**Method B Code Details**:
```glsl
// Nine-point Laplacian stencil (for RD)
// Weights: diagonal 0.5, cross 1.0, center -6.0 (sum = 0, ensuring Laplacian of a constant field is zero)
vec2 laplacian(vec2 uv) {
    vec2 px = 1.0 / iResolution.xy;
    vec4 P = vec4(px, 0.0, -px.x);
    return
        0.5 * texture(iChannel0, uv - P.xy).xy   // bottom-left
      +       texture(iChannel0, uv - P.zy).xy   // bottom
      + 0.5 * texture(iChannel0, uv - P.wy).xy   // bottom-right
      +       texture(iChannel0, uv - P.xz).xy   // left
      - 6.0 * texture(iChannel0, uv).xy           // center
      +       texture(iChannel0, uv + P.xz).xy   // right
      + 0.5 * texture(iChannel0, uv + P.wy).xy   // top-left
      +       texture(iChannel0, uv + P.zy).xy   // top
      + 0.5 * texture(iChannel0, uv + P.xy).xy;  // top-right
}
```

**Method C Code Details**:
```glsl
// 3x3 weighted blur (Gaussian approximation)
// Weights: diagonal 1, cross 2, center 4, total 16
// Uses vec3 swizzle to cleverly encode 9 offset directions
float blur3x3(vec2 uv) {
    vec3 e = vec3(1, 0, -1);  // e.x=1, e.y=0, e.z=-1
    vec2 px = 1.0 / iResolution.xy;
    float res = 0.0;
    // e.xx=(1,1), e.xz=(1,-1), e.zx=(-1,1), e.zz=(-1,-1) → four diagonals
    res += texture(iChannel0, uv + e.xx * px).x + texture(iChannel0, uv + e.xz * px).x
         + texture(iChannel0, uv + e.zx * px).x + texture(iChannel0, uv + e.zz * px).x;       // ×1
    // e.xy=(1,0), e.yx=(0,1), e.yz=(0,-1), e.zy=(-1,0) → four edges
    res += (texture(iChannel0, uv + e.xy * px).x + texture(iChannel0, uv + e.yx * px).x
          + texture(iChannel0, uv + e.yz * px).x + texture(iChannel0, uv + e.zy * px).x) * 2.; // ×2
    // e.yy=(0,0) → center
    res += texture(iChannel0, uv + e.yy * px).x * 4.;                                          // ×4
    return res / 16.0;
}
```

### Step 4: State Update Rules

**What**: Apply CA rules or RD differential equations based on neighbor information to compute new state values.

**Why**: This is the core simulation logic. CA uses discrete decisions (birth/survival/death), RD uses continuous differential equations with Euler integration.

**CA Rule Details**:

Conway's Game of Life B3/S23 means:
- B3 = Birth when 3 neighbors
- S23 = Survive when 2 or 3 neighbors

```glsl
int e = cell(px);  // current state (0 or 1)
// Equivalent to: if (k==3) born/survive; else if (k==2 && alive) survive; else die
float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;
```

**Generic Bitmask Rules**: Bitmasks can encode arbitrary CA rule sets without modifying logic code. For example:
- B3/S23 → bornset=8 (binary 1000, bit 3), stayset=12 (binary 1100, bits 2,3)
- B36/S23 → bornset=40 (bits 3,5), stayset=12

```glsl
// stayset/bornset are bitmasks; bit n=1 means triggered when neighbor count is n
float ff = 0.0;
if (currentAlive) {
    ff = ((stayset & (1 << (k - 1))) > 0) ? float(k) : 0.0;  // survive
} else {
    ff = ((bornset & (1 << (k - 1))) > 0) ? 1.0 : 0.0;       // birth
}
```

**RD Gray-Scott Update Details**:

Physical meaning of the Gray-Scott equations:
- `Du·∇²u`: diffusion of u (spatial smoothing)
- `-u·v²`: reaction consumption (u decreases when u and v meet)
- `F·(1-u)`: replenishment of u (feed, pulling u back toward 1.0)
- `Dv·∇²v`: diffusion of v
- `+u·v²`: reaction production (v increases when u and v meet)
- `-(F+k)·v`: removal of v (combined decay from kill + feed)

```glsl
float u = prevState.x;
float v = prevState.y;
vec2 Duv = laplacian(uv) * DIFFUSION;  // DIFFUSION = vec2(Du, Dv)
float du = Duv.x - u * v * v + F * (1.0 - u);
float dv = Duv.y + u * v * v - (F + k) * v;
// Forward Euler integration, clamp to prevent numerical instability
fragColor.xy = clamp(vec2(u + du * DT, v + dv * DT), 0.0, 1.0);
```

**Simplified RD Details**:
This approach doesn't use the standard Gray-Scott equations, but instead uses gradient-driven displacement and random decay to approximate reaction-diffusion behavior. The results are more organic but less controllable.

```glsl
float avgRD = blur3x3(uv);
vec2 pwr = (1.0 / iResolution.xy) * 1.5;
// Compute gradient (similar to Sobel)
vec2 lap = vec2(
    texture(iChannel0, uv + vec2(pwr.x, 0)).y - texture(iChannel0, uv - vec2(pwr.x, 0)).y,
    texture(iChannel0, uv + vec2(0, pwr.y)).y - texture(iChannel0, uv - vec2(0, pwr.y)).y
);
uv = uv + lap * (1.0 / iResolution.xy) * 3.0;  // Displace sampling point along gradient (diffusion)
float newRD = texture(iChannel0, uv).x + (noise.z - 0.5) * 0.0025 - 0.002;  // Random decay
newRD += dot(texture(iChannel0, uv + (noise.xy - 0.5) / iResolution.xy).xy, vec2(1, -1)) * 0.145;  // Reaction term
```

### Step 5: Visualization and Coloring

**What**: Map simulation buffer data to visual effects — color mapping, gradient lighting, bump mapping, etc.

**Why**: Raw simulation data consists of scalar/vector values in 0~1 range, requiring artistic processing to produce appealing visuals. The most common technique is computing the gradient of buffer values to obtain normal information for bump lighting.

**Color mapping techniques**:
```glsl
// Basic: nonlinear color separation
// c is a [0,1] value; different pow exponents make RGB channels respond at different rates
float c = 1.0 - texture(iChannel0, uv).y;
vec3 col = pow(vec3(1.5, 1, 1) * c, vec3(1, 4, 12));
// R channel responds linearly, G channel with 4th power (rapid decay in dark areas), B channel with 12th power (blue only at brightest spots)
```

**Gradient normal computation**:
```glsl
// Compute surface normals from scalar field (for bump map lighting)
vec3 normal(vec2 uv) {
    vec3 delta = vec3(1.0 / iResolution.xy, 0.0);
    // Central difference for x and y gradients
    float du = texture(iChannel0, uv + delta.xz).x - texture(iChannel0, uv - delta.xz).x;
    float dv = texture(iChannel0, uv + delta.zy).x - texture(iChannel0, uv - delta.zy).x;
    // z component controls bump intensity (smaller = stronger bumps)
    return normalize(vec3(du, dv, 1.0));
}
```

**Specular highlight effect**:
```glsl
// Produce specular edges via sampling offset
float c2 = 1.0 - texture(iChannel0, uv + 0.5 / iResolution.xy).y;
// c2*c2 - c*c is positive at gradient changes, producing edge highlights
col += vec3(0.36, 0.73, 1.0) * max(c2 * c2 - c * c, 0.0) * 12.0;
```

**Vignette + gamma correction**:
```glsl
// Vignette: darken edges
col *= pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.125) * 1.15;
// Fade-in effect
col *= smoothstep(0.0, 1.0, iTime / 2.0);
// Gamma correction (approximately 2.0)
fragColor = vec4(sqrt(min(col, 1.0)), 1.0);
```

---

## Variant Details

### Variant 1: Conway's Game of Life (Discrete CA)

**Difference from base version**: Uses discrete binary state and neighbor counting rules instead of continuous RD equations. This is the most classic cellular automaton, with simple rules that can give rise to extremely complex behavior (gliders, oscillators, still lifes, etc.).

**Complete Buffer A code**:
```glsl
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;  // wrap-around boundary
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 px = ivec2(fragCoord);

    // Moore neighborhood counting
    int k = cell(px+ivec2(-1,-1)) + cell(px+ivec2(0,-1)) + cell(px+ivec2(1,-1))
          + cell(px+ivec2(-1, 0))                        + cell(px+ivec2(1, 0))
          + cell(px+ivec2(-1, 1)) + cell(px+ivec2(0, 1)) + cell(px+ivec2(1, 1));
    int e = cell(px);

    // B3/S23 rule
    float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;

    // Initialization: approximately 10% random living cells
    if (iFrame < 2) {
        f = step(0.9, fract(sin(fragCoord.x * 13.0 + sin(fragCoord.y * 71.1)) * 138.5));
    }

    fragColor = vec4(f, 0.0, 0.0, 1.0);
}
```

**Adjustment directions**:
- Modifying B/S rule numbers can produce completely different behavior
- Increasing initial density (changing the 0.9 in `step(0.9, ...)`) alters the evolution result
- The .y channel can store "age" for color mapping during visualization

### Variant 2: Configurable Rule Set CA (Birth/Survival Bitmask)

**Difference from base version**: Uses bitmasks to encode arbitrary CA rules, supporting Moore/von Neumann/extended neighborhoods, capable of producing worms, sponges, explosions, and other patterns.

**Bitmask encoding explanation**:
- `BORN_SET = 8` is binary `0b1000`, meaning bit 3 is set → B3 (birth when 3 neighbors)
- `STAY_SET = 12` is binary `0b1100`, meaning bits 2,3 are set → S23 (survive when 2 or 3 neighbors)
- `LIVEVAL` controls the living cell's state value; when greater than 1, combined with `DECIMATE` it can produce gradient decay effects
- `DECIMATE` is the per-frame decay amount, producing a "trailing" effect

**Key code**:
```glsl
#define BORN_SET  8        // birth bitmask, 8 = B3 (bit 3 set)
#define STAY_SET  12       // survival bitmask, 12 = S23 (bits 2,3 set)
#define LIVEVAL   2.0      // living cell state value
#define DECIMATE  1.0      // decay value (0=no decay)

// Rule evaluation
float ff = 0.0;
float ev = texelFetch(iChannel0, px, 0).w;
if (ev > 0.5) {
    // Living cell: decay first, then check if survival rule is met
    if (DECIMATE > 0.0) ff = ev - DECIMATE;
    if ((STAY_SET & (1 << (k - 1))) > 0) ff = LIVEVAL;
} else {
    // Dead cell: check if birth rule is met
    ff = ((BORN_SET & (1 << (k - 1))) > 0) ? LIVEVAL : 0.0;
}
```

**Notable rule sets**:
- B3/S23 (Conway Life): BORN=8, STAY=12
- B36/S23 (HighLife): BORN=40, STAY=12 — has self-replicators
- B1/S1 (Gnarl): BORN=2, STAY=2 — fractal growth
- B3/S012345678 (Life without death): BORN=8, STAY=511 — only grows, never dies

### Variant 3: Separable Gaussian Blur RD (Multi-Buffer Architecture)

**Difference from base version**: Replaces the single 3x3 Laplacian with separable horizontal/vertical Gaussian blur for the diffusion step, achieving a larger effective diffusion radius with smoother patterns.

**Architecture**:
- Buffer A: Reaction step (reads Buffer C's blur result as diffusion term)
- Buffer B: Horizontal Gaussian blur (reads Buffer A)
- Buffer C: Vertical Gaussian blur (reads Buffer B)

**Why separate**:
- A direct NxN kernel requires N² samples
- Separating into horizontal + vertical passes requires N samples each, 2N total
- A 9-tap separable blur = 18 samples ≈ equivalent to an 81-point 9x9 kernel

**Buffer B complete code (horizontal blur)**:
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float h = 1.0 / iResolution.x;
    vec4 sum = vec4(0.0);
    // 9-tap Gaussian weights (approximate normal distribution)
    sum += texture(iChannel0, fract(vec2(uv.x - 4.0*h, uv.y))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x - 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x - 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x - 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x,         uv.y))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x + 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x + 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x + 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x + 4.0*h, uv.y))) * 0.05;
    fragColor = vec4(sum.xyz / 0.98, 1.0);  // 0.98 = weight sum, normalized
}
```

Buffer C has identical structure but blurs along the y-axis (replace `uv.x ± n*h` with `uv.y ± n*v`, where `v = 1.0/iResolution.y`).

### Variant 4: Continuous Differential Operator CA (Vein/Fluid Style)

**Difference from base version**: Computes curl, divergence, and Laplacian on the grid, combined with multi-step advection loops, producing vein/fluid-like organic patterns that sit between CA and PDE fluid simulation.

**Core concepts**:
- **Curl**: Describes the rotational tendency of a field, used to produce vortex effects
- **Divergence**: Describes the spreading/converging tendency of a field
- **Advection**: Propagates field values along the velocity field direction

**Parameter tuning guide**:
- `STEPS (10~60)`: Advection steps; more = smoother but slower
- `ts (0.1~0.5)`: Advection rotation strength, controls vortex intensity
- `cs (-3~-1)`: Curl scaling; negative values produce counter-clockwise rotation
- `ls (0.01~0.1)`: Laplacian scaling, controls diffusion strength
- `amp (0.5~2.0)`: Self-amplification coefficient
- `upd (0.2~0.6)`: Update smoothing coefficient, controls old/new state blend ratio

**Key code**:
```glsl
#define STEPS 40
#define ts    0.2
#define cs   -2.0
#define ls    0.05
#define amp   1.0
#define upd   0.4

// Discrete curl and divergence on a 3x3 stencil
// Standard weights: _K0=-20/6 (center), _K1=4/6 (edge), _K2=1/6 (corner)
curl = uv_n.x - uv_s.x - uv_e.y + uv_w.y
     + _D * (uv_nw.x + uv_nw.y + uv_ne.x - uv_ne.y
           + uv_sw.y - uv_sw.x - uv_se.y - uv_se.x);
div  = uv_s.y - uv_n.y - uv_e.x + uv_w.x
     + _D * (uv_nw.x - uv_nw.y - uv_ne.x - uv_ne.y
           + uv_sw.x + uv_sw.y + uv_se.y - uv_se.x);

// Multi-step advection loop
for (int i = 0; i < STEPS; i++) {
    advect(off, vUv, texel, curl, div, lapl, blur);
    offd = rot(offd, ts * curl);  // rotate offset direction
    off += offd;                   // accumulate offset
    ab += blur / float(STEPS);    // accumulate blurred value
}
```

### Variant 5: RD-Driven 3D Surface (Raymarched RD)

**Difference from base version**: 2D RD results serve as a texture mapped onto a 3D sphere, driving surface displacement and color; the Image pass becomes a full raymarcher.

**Implementation points**:
1. Buffer A maintains the standard RD simulation unchanged
2. Image pass becomes a raymarching renderer
3. The SDF function maps 3D points to spherical UV, then samples the RD buffer
4. RD values drive surface displacement

**Key code**:
```glsl
// Image pass: use RD texture for displacement in the SDF
vec2 map(in vec3 pos) {
    vec3 p = normalize(pos);
    vec2 uv;
    // Spherical parameterization: 3D point → 2D UV
    uv.x = 0.5 + atan(p.z, p.x) / (2.0 * 3.14159);  // longitude [0, 1]
    uv.y = 0.5 - asin(p.y) / 3.14159;                 // latitude [0, 1]

    float y = texture(iChannel0, uv).y;     // read v component from RD buffer
    float displacement = 0.1 * y;            // displacement amount (adjustable scale factor)
    float sd = length(pos) - (2.0 + displacement);  // base sphere SDF + displacement
    return vec2(sd, y);  // return distance and material parameter
}
```

**Extension directions**:
- Replace the sphere with a torus, plane, or other base shapes
- Use the two RD channels to separately drive displacement and color
- Add normal perturbation for finer surface detail
- Combine with environment maps for reflection/refraction

---

## Performance Optimization In-Depth Analysis

### 1. texelFetch vs texture

**Discrete CA** should use `texelFetch(iChannel0, ivec2(px), 0)` instead of `texture()`:
- Avoids unnecessary texture filtering overhead
- Guarantees pixel-precise reads without floating-point precision causing sampling of adjacent pixels
- For binary states (0/1), any interpolation introduces errors

**Continuous RD** can use `texture()` with linear filtering:
- Hardware automatically performs bilinear interpolation
- The interpolation effect is equivalent to additional smoothing/diffusion, which can be advantageous in some cases
- Hardware-accelerated, faster than manual interpolation

### 2. Separable Blur Instead of Large-Kernel Laplacian

If a large diffusion radius is needed:
- **Don't** use a larger NxN Laplacian kernel → O(N²) samples
- **Do** use separable two-pass Gaussian blur (horizontal + vertical) → O(2N) samples
- Implemented through additional buffer passes

**Numerical comparison**:
| Method | Equivalent Kernel Size | Sample Count |
|------|-----------|---------|
| 3x3 Laplacian | 3×3 | 9 |
| 5x5 Laplacian | 5×5 | 25 |
| 9x9 Laplacian | 9×9 | 81 |
| Separable 9-tap Gaussian | ≈9×9 | 18 |
| Separable 13-tap Gaussian | ≈13×13 | 26 |

### 3. Multi-Step Sub-Iteration

For RD, you can loop multiple sub-iterations within a single frame using smaller DT, improving convergence speed while maintaining stability:

```glsl
#define SUBSTEPS 4     // sub-iteration count
#define SUB_DT 0.25    // = DT / SUBSTEPS
for (int i = 0; i < SUBSTEPS; i++) {
    vec2 lap = laplacian9(uv);
    float uvv = u * v * v;
    u += (DU * lap.x - uvv + F * (1.0 - u)) * SUB_DT;
    v += (DV * lap.y + uvv - (F + K) * v) * SUB_DT;
}
```

**Note**: In sub-iterations, the Laplacian is only correct when read from the texture on the first step; subsequent steps should recompute the Laplacian based on updated values. However, in practice, the approximation of single-read multi-step integration is often good enough.

### 4. Reduced-Resolution Simulation

If the target display resolution is high but the pattern's spatial frequency doesn't require 1:1 pixel precision:
- Run the simulation at lower resolution in the buffer (not directly configurable in ShaderToy, but possible in custom engines)
- Use bilinear interpolation upsampling in the Image pass
- Can save 4x~16x computation

### 5. Avoiding Branches and Conditionals

Use `step()`, `mix()`, `clamp()` instead of `if/else` for CA rule evaluation to reduce GPU warp divergence:

```glsl
// Original if/else version:
// if (k==3) f=1.0; else if (k==2 && e==1) f=1.0; else f=0.0;

// Branch-free version:
float f = max(step(abs(float(k) - 3.0), 0.5),
              step(abs(float(k) - 2.0), 0.5) * step(0.5, float(e)));
```

**Explanation**:
- `step(abs(float(k) - 3.0), 0.5)` is 1.0 when k=3, otherwise 0.0
- `step(abs(float(k) - 2.0), 0.5) * step(0.5, float(e))` is 1.0 when k=2 and e=1
- `max()` combines the two conditions

---

## Combination Suggestions — Full Details

### 1. RD + Raymarching (3D Displacement/Shaping)

Map RD results as a heightmap onto 3D surfaces (sphere, plane, torus) and create organic bumpy surfaces through SDF displacement. Suitable for biological organisms, alien terrain, and similar effects.

**Complete Image pass example** (sphere + RD displacement):
```glsl
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

// Use map() in the raymarch loop
// Normals computed via central difference of map()
// Material color based on y value returned by map() for color mapping
```

### 2. CA/RD + Particle Systems

Use CA/RD fields as velocity fields or spawn probability fields for particles:
- Particles flow along RD gradients
- New particles spawn at living CA cells
- Produces "living" particle effects

**Implementation approach**:
- Buffer A: RD/CA simulation
- Buffer B: Particle position storage (each pixel stores one particle's position)
- Image: Visualize particles and/or fields

### 3. RD + Post-Processing Lighting

In the Image pass, compute normals from RD values → bump mapping → lighting/reflection/refraction. Combined with environment maps (cubemaps), this can produce etched metal surfaces, liquid ripples, and similar effects.

**Key techniques**:
- Compute gradients from RD scalar field to get normals
- Use Phong/Blinn-Phong lighting model
- Normals used to sample cubemaps for environment reflections
- Multiple color mapping schemes increase visual richness

### 4. CA + Color Decay Trails

Living cells use high values; after death, values decay each frame (instead of immediately dropping to zero), with different decay rates in RGB channels producing colorful trailing effects. This is the core technique of the Automata X Showcase.

**Implementation code example**:
```glsl
// Add decay logic after CA update
vec4 prev = texelFetch(iChannel0, px, 0);
if (f > 0.5) {
    // Living cell: set to high value
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
} else {
    // Dead cell: different decay rates per channel
    fragColor = vec4(
        prev.x * 0.99,   // R decays slowly → longest red trail
        prev.y * 0.95,   // G decays moderately
        prev.z * 0.90,   // B decays fast → shortest blue trail
        1.0
    );
}
```

### 5. RD + Domain Warping

Apply vortex warp or spiral zoom domain transforms to the RD sampling UV before computing, causing the diffusion field itself to be distorted, producing spiral and vortex-like organic patterns. Flexi's Expansive RD uses this technique.

**Implementation code example**:
```glsl
// Apply domain transform to UV before RD update
vec2 warpedUV = uv;
// Vortex warp
float angle = length(uv - 0.5) * 3.14159 * 2.0;
float s = sin(angle * 0.1);
float c = cos(angle * 0.1);
warpedUV = (warpedUV - 0.5) * mat2(c, -s, s, c) + 0.5;

// Sample state using transformed UV
vec2 state = texture(iChannel0, warpedUV).xy;
// Then proceed with normal RD computation...
```
