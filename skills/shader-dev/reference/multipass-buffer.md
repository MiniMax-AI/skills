# Multi-Pass Buffer Techniques — Detailed Reference

This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, in-depth explanations of each step, complete variant descriptions, performance optimization analysis, and full combination code examples.

## Prerequisites

### GLSL Fundamentals

- GLSL basic syntax: `uniform`, `varying`, `sampler2D`
- ShaderToy execution model: `iChannel0-3` texture inputs, `iResolution`, `iTime`, `iFrame`, `iMouse`
- Difference between `texture()` and `texelFetch()`:
  - `texture()` performs interpolated sampling (bilinear filtering), suitable for continuous field sampling
  - `texelFetch()` reads a specific texel exactly, without interpolation, suitable for data storage reads
- `textureLod()` is used for explicit MIP level sampling, avoiding the blur caused by automatic MIP selection
- Buffer A/B/C/D concept in ShaderToy: each buffer is an independent render pass that outputs to a corresponding texture, which can be read by other passes or itself via iChannel

### Basic Math

- Basic vector math and matrix transforms
- Finite difference method: using neighboring pixels to approximate gradients and the Laplacian operator
- Iterative mapping: the concept of `x(n+1) = f(x(n))`, the mathematical basis for self-feedback

## Implementation Steps

### Step 1: Establish a Minimal Self-Feedback Loop

**What**: Create a Buffer that reads its own previous frame output, adds new content, and outputs the result. The Image pass simply displays the Buffer result.

**Why**: This is the cornerstone of all multi-pass techniques. Once you understand self-feedback loops, fluid simulation, temporal accumulation, etc. are all extensions of this foundation. An initialization guard (`iFrame == 0` or `iFrame < N`) prevents reading uninitialized data.

**iChannel Binding**: Buffer A's iChannel0 → Buffer A (self-feedback); Image's iChannel0 → Buffer A

**Key Points**:
- `exp(-33.0 / iResolution.y)` controls the decay rate; higher values produce faster decay
- The `fragCoord + vec2(1.0, sin(iTime))` offset creates motion effects
- The `iFrame < 4` guard ensures stable initial values for the first few frames

### Step 2: Implement Self-Advection

**What**: Building on self-feedback, interpret the buffer values as a velocity field and implement self-advection — each pixel offsets its sampling position based on the local velocity.

**Why**: Self-advection is the core of all Eulerian grid fluid simulations. By accumulating rotational information across multiple scales through rotational sampling, rich vortex structures can be produced without a complete Navier-Stokes solver.

**Parameter Tuning**:
- `ROT_NUM` (rotation sample count): Affects the sampling accuracy of the rotation field; 5 is a good balance
- `SCALE_NUM` (number of scale levels): Affects the detail level of vortices; 20 levels produce rich multi-scale structures
- `bbMax = 0.7 * iResolution.y`: Adaptive loop termination threshold

**Mathematical Principles**:
- The `getRot` function samples the velocity field at ROT_NUM equally spaced angular directions around a given position
- Computes the rotational component via `dot(velocity - 0.5, perpendicular)`
- The multi-scale loop `b *= 2.0` progressively enlarges the sampling radius, capturing vortices at different scales

### Step 3: Navier-Stokes Fluid Solver

**What**: Implement velocity field solving based on the paper "Simple and fast fluids" (Guay, Colin, Egli, 2011), including advection, viscous forces, and vorticity confinement.

**Why**: More physically accurate than pure rotational self-advection, supporting low-viscosity fluid simulation (e.g., smoke, fire). Vorticity is stored in the alpha channel to avoid extra buffer overhead.

**Complete `solveFluid` Function Breakdown**:

```glsl
vec4 solveFluid(sampler2D smp, vec2 uv, vec2 w, float time, vec3 mouse, vec3 lastMouse) {
    const float K = 0.2;   // Pressure coefficient: controls the strength of the incompressibility constraint
    const float v = 0.55;  // Viscosity coefficient: high value = viscous fluid, low value = thin fluid

    // Read four neighboring pixels (basis for central differencing)
    vec4 data = textureLod(smp, uv, 0.0);
    vec4 tr = textureLod(smp, uv + vec2(w.x, 0), 0.0);
    vec4 tl = textureLod(smp, uv - vec2(w.x, 0), 0.0);
    vec4 tu = textureLod(smp, uv + vec2(0, w.y), 0.0);
    vec4 td = textureLod(smp, uv - vec2(0, w.y), 0.0);

    // Density and velocity gradients (central differencing)
    vec3 dx = (tr.xyz - tl.xyz) * 0.5;  // x-direction gradient
    vec3 dy = (tu.xyz - td.xyz) * 0.5;  // y-direction gradient
    vec2 densDif = vec2(dx.z, dy.z);     // Density gradient

    // Density update: continuity equation ∂ρ/∂t + ∇·(ρv) = 0
    data.z -= DT * dot(vec3(densDif, dx.x + dy.y), data.xyz);

    // Viscous force (Laplacian operator): μ∇²v
    // Discrete Laplacian = up + down + left + right - 4*center
    vec2 laplacian = tu.xy + td.xy + tr.xy + tl.xy - 4.0 * data.xy;
    vec2 viscForce = vec2(v) * laplacian;

    // Advection: Semi-Lagrangian backtrace method
    // Trace backward from the current position along the reverse velocity direction, sample previous step's value
    data.xyw = textureLod(smp, uv - DT * data.xy * w, 0.0).xyw;

    // External forces (mouse interaction)
    vec2 newForce = vec2(0);
    if (mouse.z > 1.0 && lastMouse.z > 1.0) {
        // Mouse movement velocity as force direction
        vec2 vv = clamp((mouse.xy * w - lastMouse.xy * w) * 400.0, -6.0, 6.0);
        // Force magnitude inversely proportional to distance from mouse (similar to a point charge field)
        newForce += 0.001 / (dot(uv - mouse.xy * w, uv - mouse.xy * w) + 0.001) * vv;
    }

    // Velocity update: v += dt * (viscous force - pressure gradient + external forces)
    data.xy += DT * (viscForce - K / DT * densDif + newForce);
    // Linear decay: simulates energy dissipation
    data.xy = max(vec2(0), abs(data.xy) - 1e-4) * sign(data.xy);

    // Vorticity Confinement
    // Compute curl = ∂vy/∂x - ∂vx/∂y
    data.w = (tr.y - tl.y - tu.x + td.x);
    // Vorticity gradient direction
    vec2 vort = vec2(abs(tu.w) - abs(td.w), abs(tl.w) - abs(tr.w));
    // Normalize then multiply by vorticity value to produce a force that enhances vortices
    vort *= VORTICITY_AMOUNT / length(vort + 1e-9) * data.w;
    data.xy += vort;

    // Top/bottom boundaries: soft decay to avoid hard edges
    data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    // Numerical stability: clamp extreme values
    data = clamp(data, vec4(vec2(-10), 0.5, -10.0), vec4(vec2(10), 3.0, 10.0));

    return data;
}
```

**RGBA Channel Packing Strategy**:
- `xy` = velocity components (vx, vy)
- `z` = density
- `w` = vorticity (curl)

A single vec4 carries the complete fluid state without needing extra buffers.

### Step 4: Chained Buffers for Accelerated Simulation

**What**: Execute the same simulation code in a chain through Buffer A → B → C, completing multiple simulation sub-steps per frame.

**Why**: Each ShaderToy buffer executes only once per frame. By chaining identical code (A reads itself → B reads A → C reads B), three iterations are completed in a single frame, significantly increasing simulation speed without adding buffer count. Use the Common tab to avoid code duplication.

**iChannel Binding**:
- Buffer A: iChannel0 → Buffer C (reads previous frame's final result)
- Buffer B: iChannel0 → Buffer A (reads current frame's first step result)
- Buffer C: iChannel0 → Buffer B (reads current frame's second step result)

**Mouse State Inter-Frame Transfer**:
- `if (fragCoord.y < 1.0) data = iMouse;` writes the current frame's mouse state into the first row of pixels
- `texelFetch(iChannel0, ivec2(0, 0), 0)` reads the previous frame's mouse state in the next frame
- The delta between two frames' mouse positions gives mouse velocity, used to calculate the direction and magnitude of applied forces

### Step 5: Separable Gaussian Blur Pipeline

**What**: Use two Buffers to implement horizontal and vertical separable Gaussian blur.

**Why**: A 2D Gaussian kernel can be separated into the product of two 1D kernels. An NxN kernel drops from N² samples to 2N. This is the standard implementation for Bloom, the diffusion term in reaction-diffusion, and various post-processing blurs.

**iChannel Binding**: Buffer B: iChannel0 → Buffer A (source); Buffer C: iChannel0 → Buffer B (horizontal blur result)

**Vertical blur complete code** (horizontal version in SKILL.md; vertical version symmetrically replaces the y-axis):
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pixelSize = 1.0 / iResolution.xy;
    vec2 uv = fragCoord * pixelSize;

    float v = pixelSize.y;
    vec4 sum = vec4(0.0);
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 4.0*v))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 3.0*v))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 2.0*v))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 1.0*v))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y         ))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 1.0*v))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 2.0*v))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 3.0*v))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 4.0*v))) * 0.05;

    fragColor = vec4(sum.xyz / 0.98, 1.0);
}
```

**9-tap Weight Explanation**:
- Weights [0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05] approximate a Gaussian distribution with sigma≈2.0
- Total sum is 0.98, divided by 0.98 for normalization
- `fract()` implements wrap addressing

### Step 6: Structured State Storage (Texel-Addressed Registers)

**What**: Use specific pixels in a Buffer as named registers to store non-image data (positions, velocities, scores, etc.).

**Why**: GPUs have no global variables. By assigning semantic meaning to specific texel positions, arbitrary structured state can be persisted in a buffer. This enables complete game logic, particle system state, etc. to be implemented in shaders.

**Design Pattern Details**:

1. **Address Constants**: Use `const ivec2` to define the texel address for each state variable
2. **Load Function**: `texelFetch(iChannel0, addr, 0)` for exact reads (no interpolation)
3. **Store Function**: Use conditional assignment `fragColor = (px == addr) ? val : fragColor`, ensuring each pixel only writes data belonging to its own address
4. **Region Storage**: `ivec4 rect` defines rectangular regions for grid-like data (e.g., brick matrices)
5. **Discard outside data region**: `if (fragCoord.x > 14.0 || fragCoord.y > 14.0) discard;` skips unnecessary computation

**Notes**:
- `ivec2(fragCoord - 0.5)` ensures correct integer texel coordinates (fragCoord's center offset)
- Initialization must set all state values when `iFrame == 0`
- Default behavior `fragColor = loadValue(px)` keeps unmodified state unchanged

### Step 7: Inter-Frame Mouse State Tracking

**What**: Store the mouse position in specific pixels of a Buffer, and compute mouse movement delta by reading the previous frame's value.

**Why**: ShaderToy does not directly provide mouse velocity. Storing the current frame's `iMouse` in a fixed pixel allows calculating the delta in the next frame. This is critical for fluid interaction — mouse velocity is needed to apply forces.

**Comparison of Two Methods**:

| Feature | Method 1 (First Row Pixel) | Method 2 (Fixed UV Region) |
|---------|---------------------------|---------------------------|
| Source | Chimera's Breath | Reaction-Diffusion |
| Storage Location | `fragCoord.y < 1.0` | Fixed UV coordinate |
| Read Method | `texelFetch(ch, ivec2(0,0), 0)` | `texture(ch, vec2(7.5/8, 2.5/8))` |
| Advantage | Simple, suitable for fluids | Resolution-independent |
| Disadvantage | Occupies the first row of pixels | Requires extra buffer channel |

## Variant Details

### Variant 1: Temporal Accumulation Anti-Aliasing (TAA)

**Difference from basic version**: The Buffer does not perform physics simulation, but instead renders a jittered image and blends it with history frames to achieve supersampling. Uses YCoCg color space neighborhood clamping to prevent ghosting.

**How It Works**:
1. Buffer A renders the scene with sub-pixel level random jitter
2. New frames are blended with history frames at a 10:90 ratio, accumulating supersampling over time
3. The TAA buffer performs YCoCg neighborhood clamping: constraining the history frame color to the statistical range of the current frame's 3x3 neighborhood
4. A 0.75 sigma clamping range balances ghost removal and detail preservation

**Complete TAA Flow**:
```
Buffer A (render+jitter) → Buffer B (motion vectors, optional) → Buffer C (TAA blend) → Image
```

### Variant 2: Deferred Rendering G-Buffer Pipeline

**Difference from basic version**: Buffers do not use self-feedback, but instead process in stages within a single frame: geometry → edge detection → post-processing.

**G-Buffer Encoding Scheme**:
- `col.xy`: View-space normal xy components (multiplied by camMat to convert to screen space)
- `col.z`: Linear depth (normalized to [0,1])
- `col.w`: Diffuse lighting + shadow information

**Edge Detection Principle**:
- The `checkSame` function compares normal and depth differences between adjacent pixels
- `Sensitivity.x` controls normal edge sensitivity
- `Sensitivity.y` controls depth edge sensitivity
- Threshold 0.1 determines the edge detection criterion

### Variant 3: HDR Bloom Post-Processing Pipeline

**Difference from basic version**: Uses Buffers to build a MIP pyramid, achieving wide-range glow through multiple levels of downsampling and blur.

**MIP Pyramid Packing Strategy**:
- All MIP levels are packed into a single texture
- `CalcOffset` computes the offset position of each level within the texture
- Each level is half the size, with padding to prevent inter-level leakage

**Complete Bloom Pipeline**:
```
Buffer A (scene render) → Buffer B (MIP pyramid) → Buffer C (horizontal blur) → Buffer D (vertical blur) → Image (compositing)
```

**Tone Mapping**:
```glsl
// Reinhard tone mapping
color = pow(color, vec3(1.5));  // Gamma preprocessing
color = color / (1.0 + color);  // Reinhard compression
```

### Variant 4: Reaction-Diffusion System

**Difference from basic version**: Simulates chemical reaction-diffusion (e.g., Gray-Scott model). Diffusion is implemented via separable blur, and the reaction term is computed in the main buffer.

**Gray-Scott Equations**:
- `∂u/∂t = Du∇²u - uv² + F(1-u)` — Diffusion and reaction of chemical substance u
- `∂v/∂t = Dv∇²v + uv² - (F+k)v` — Diffusion and reaction of chemical substance v
- `Du`, `Dv` are diffusion coefficients, `F` is the feed rate, `k` is the kill rate

**Implementation Strategy**:
- The diffusion term is implemented via separable blur buffers (reusing the blur pipeline from Step 5)
- The reaction term is computed in the main buffer
- The offset of `uv_red` implements diffusion expansion
- Random noise decay prevents pattern stagnation

### Variant 5: Multi-Scale MIP Fluid

**Difference from basic version**: Uses `textureLod` to explicitly sample different MIP levels, achieving O(n) complexity multi-scale computation (turbulence, vorticity confinement, Poisson solving), with each physical quantity in its own buffer.

**Core Advantage**:
- Traditional multi-scale computation requires O(N²) samples (sampling N neighbors at each scale)
- MIP sampling leverages hardware automatic averaging; a single `textureLod` at high MIP levels is equivalent to a large-range mean
- Total complexity drops to O(NUM_SCALES × 9) (3x3 neighborhood per scale)

**Weight Function Choices**:
- `1.0/float(i+1)`: Logarithmic decay, reduces large-scale influence
- `1.0/float(1<<i)`: Exponential decay, rapidly suppresses large scales
- Constant: Equal weight for all scales

## In-Depth Performance Optimization

### 1. Reduce Texture Samples

**Separable Blur**:
- Principle: The 2D Gaussian function G(x,y) = G(x) × G(y) can be separated into two 1D convolutions
- An NxN kernel drops from N² to 2N samples
- 9-tap example: 81 → 18 samples

**Bilinear Tap Trick**:
```glsl
// Standard 9-tap: requires 9 samples
// Bilinear optimization: achieves equivalent results with 5 samples using hardware interpolation
// Key: place sample points between two texels, GPU hardware automatically computes weighted average
float offset1 = 1.0 + weight2 / (weight1 + weight2);  // Offset encodes weight ratio
vec4 s1 = texture(smp, uv + vec2(offset1, 0) * texelSize);
// s1 is automatically the weighted average of texel[1] and texel[2]
```

**MIP Sampling Replaces Large Kernels**:
- `textureLod(smp, uv, 3.0)` samples MIP level 3, equivalent to an 8×8 area mean
- A single sample replaces 64 samples
- Suitable for coarse-scale approximation in multi-scale computation

### 2. Limit Computation Region

**Data Region Discard**:
```glsl
// In a state storage shader, only the first 14×14 pixels store data
// Remaining pixels are discarded, GPU skips subsequent computation
if (fragCoord.x > 14.0 || fragCoord.y > 14.0) discard;
```

**Soft Boundaries**:
```glsl
// Use smoothstep instead of if-statements
// Avoids branch divergence (warp divergence), more efficient on GPU
data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
// Smoothly decays to 0 in the y=0.48~0.52 range
```

### 3. Reduce Buffer Count

**RGBA Channel Packing**:
| Channel | Fluid Simulation | G-Buffer | Particle System |
|---------|-----------------|----------|----------------|
| R | Velocity x | Normal x | Position x |
| G | Velocity y | Normal y | Position y |
| B | Density | Depth | Lifetime |
| A | Vorticity | Diffuse | Type ID |

**Chained Sub-Steps**:
- 3 buffers running identical code = 3 iterations per frame
- Equivalent to 3x time step, but more stable (each step is still a small step)
- Code is shared via the Common tab, zero maintenance cost

### 4. Reduce Iteration/Sample Count

**Adaptive Loop Termination**:
```glsl
// In multi-scale sampling, exit early when the sampling radius exceeds the effective range
float bbMax = 0.7 * iResolution.y;
bbMax *= bbMax;
for (int l = 0; l < SCALE_NUM; l++) {
    if (dot(b, b) > bbMax) break;  // Beyond screen range, no need to continue
    // ...
    b *= 2.0;
}
```

**MIP Level Count Adjustment**:
- `TURBULENCE_SCALES = 11`: Full multi-scale, highest quality
- `TURBULENCE_SCALES = 7`: Removes the largest scales, minimal quality loss
- `TURBULENCE_SCALES = 5`: Noticeable speedup, suitable for mobile

### 5. Initialization Strategy

**Progressive Initialization**:
```glsl
// Output stable initial values for the first 20 frames
if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
```
- Why not `iFrame == 0`? Because some buffers depend on the output of other buffers
- 20 frames ensures all buffers complete initialization propagation

**Tiny Noise Initialization**:
```glsl
if (iFrame == 0) fragColor = 1e-6 * noise;
```
- Avoids exact zero values causing `0/0` or `normalize(vec2(0))` problems
- Tiny noise breaks symmetry, allowing vortices to develop naturally

## Combination Examples with Complete Code

### 1. Fluid Simulation + Lighting

```glsl
// Image: Compute gradient from fluid buffer as normal, apply Phong lighting
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float delta = 1.0 / iResolution.y;

    // Compute fluid surface gradient
    float valC = getVal(uv);
    vec2 grad = vec2(
        getVal(uv + vec2(delta, 0)) - getVal(uv - vec2(delta, 0)),
        getVal(uv + vec2(0, delta)) - getVal(uv - vec2(0, delta))
    ) / delta;

    // Build normal (z=150 controls surface flatness)
    vec3 normal = normalize(vec3(grad, 150.0));

    // Lighting
    vec3 lightDir = normalize(vec3(-1.0, -1.0, 2.0));
    vec3 viewDir = vec3(0, 0, 1);

    float diff = clamp(dot(normal, lightDir), 0.5, 1.0);
    float spec = pow(clamp(dot(reflect(lightDir, normal), viewDir), 0.0, 1.0), 36.0);

    vec3 baseColor = vec3(0.2, 0.4, 0.8);  // Water surface color
    fragColor = vec4(baseColor * diff + vec3(1.0) * spec * 0.5, 1.0);
}
```

### 2. Fluid Simulation + Color Advection

```glsl
// Color Buffer: Track a color field, advected by the velocity field
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    float dt = 0.15;
    float scale = 3.0;

    // Read velocity field
    vec2 velocity = textureLod(iChannel0, uv, 0.0).xy;

    // Color advection: sample own previous frame in the reverse velocity direction
    vec4 col = textureLod(iChannel1, uv - dt * velocity * w * scale, 0.0);

    // Inject color at the emission point
    vec2 emitPos = vec2(0.5, 0.5);
    float dist = length(uv - emitPos);
    float emitterStrength = 0.0025;
    float epsilon = 0.0005;
    col += emitterStrength / (epsilon + pow(dist, 1.75)) * dt * 0.12 * palette(iTime * 0.05);

    // Color decay
    float decay = 0.004;
    col = max(col - (0.0001 + col * decay) * 0.5, 0.0);
    col = clamp(col, 0.0, 5.0);

    fragColor = col;
}
```

### 3. Scene Rendering + Bloom + TAA Post-Processing Chain

Four-Buffer pipeline:
- **Buffer A**: Scene rendering (with sub-pixel jitter for TAA)
- **Buffer B**: Brightness extraction + downsampling to build bloom pyramid
- **Buffer C/D**: Separable Gaussian blur
- **Image**: Bloom compositing + tone mapping + chromatic aberration + vignette

```glsl
// Image: Final compositing
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Original scene
    vec3 scene = texture(iChannel0, uv).rgb;

    // Multi-level bloom compositing
    vec3 bloom = vec3(0);
    bloom += Grab(uv, 1.0, CalcOffset(0.0)).rgb * 1.0;
    bloom += Grab(uv, 2.0, CalcOffset(1.0)).rgb * 1.5;
    bloom += Grab(uv, 4.0, CalcOffset(2.0)).rgb * 2.0;
    bloom += Grab(uv, 8.0, CalcOffset(3.0)).rgb * 3.0;

    // Compositing
    vec3 color = scene + bloom * 0.08;

    // Filmic tone mapping
    color = pow(color, vec3(1.5));
    color = color / (1.0 + color);

    // Chromatic Aberration
    float ca = 0.002;
    color.r = texture(iChannel0, uv + vec2(ca, 0)).r;
    color.b = texture(iChannel0, uv - vec2(ca, 0)).b;

    // Vignette
    float vignette = 1.0 - dot(uv - 0.5, uv - 0.5) * 0.5;
    color *= vignette;

    fragColor = vec4(color, 1.0);
}
```

### 4. G-Buffer + Screen-Space Effects

Two-Buffer pipeline, no temporal feedback:
- **Buffer A**: Output normals + depth + diffuse to G-Buffer
- **Buffer B**: Screen-space edge detection / SSAO / SSR
- **Image**: Stylized compositing (e.g., hand-drawn style, noise distortion)

```glsl
// Buffer B: Screen-space edge detection
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 offset = 1.0 / iResolution.xy;

    vec4 center = texture(iChannel0, uv);

    // Roberts Cross edge detection
    vec4 tl = texture(iChannel0, uv + vec2(-offset.x, offset.y));
    vec4 tr = texture(iChannel0, uv + vec2(offset.x, offset.y));
    vec4 bl = texture(iChannel0, uv + vec2(-offset.x, -offset.y));
    vec4 br = texture(iChannel0, uv + vec2(offset.x, -offset.y));

    float edge = checkSame(center, tl) * checkSame(center, tr) *
                 checkSame(center, bl) * checkSame(center, br);

    fragColor = vec4(edge, center.w, center.z, 1.0);
}
```

### 5. State Storage + Visualization Separation

Standard pattern for games/particle systems. Logic and rendering are fully separated:
- **Buffer A**: Pure logic computation, state stored in fixed texel positions
- **Image**: Pure rendering, reads state via `texelFetch`, draws visuals using distance fields/rasterization

```glsl
// Image: Read game state from Buffer A and render
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 aspect = vec2(iResolution.x / iResolution.y, 1.0);

    // Read ball state
    vec4 ballPV = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec2 ballPos = ballPV.xy;

    // Read paddle position
    float paddleX = texelFetch(iChannel0, ivec2(1, 0), 0).x;

    // Draw ball (distance field)
    float ballDist = length((uv - ballPos * 0.5 - 0.5) * aspect);
    vec3 ballColor = vec3(1.0, 0.8, 0.2) * smoothstep(0.02, 0.015, ballDist);

    // Draw paddle
    vec2 paddleCenter = vec2(paddleX * 0.5 + 0.5, 0.05);
    vec2 paddleSize = vec2(0.08, 0.01);
    vec2 d = abs((uv - paddleCenter) * aspect) - paddleSize;
    float paddleDist = length(max(d, 0.0));
    vec3 paddleColor = vec3(0.2, 0.6, 1.0) * smoothstep(0.005, 0.0, paddleDist);

    // Read and draw brick grid
    vec3 brickColor = vec3(0);
    for (int y = 1; y <= 12; y++) {
        for (int x = 0; x <= 13; x++) {
            float alive = texelFetch(iChannel0, ivec2(x, y), 0).x;
            if (alive > 0.5) {
                vec2 brickCenter = vec2(float(x) / 14.0 + 0.036, float(y) / 14.0 + 0.036);
                vec2 bd = abs((uv - brickCenter) * aspect) - vec2(0.03, 0.015);
                float brickDist = length(max(bd, 0.0));
                brickColor += vec3(0.8, 0.3, 0.5) * smoothstep(0.003, 0.0, brickDist);
            }
        }
    }

    fragColor = vec4(ballColor + paddleColor + brickColor, 1.0);
}
```
