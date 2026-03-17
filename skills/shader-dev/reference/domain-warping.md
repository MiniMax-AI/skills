# Domain Warping — Detailed Reference

This document contains the complete step-by-step tutorial, mathematical derivations, and advanced usage for domain warping techniques. See [SKILL.md](SKILL.md) for the condensed version.

## Prerequisites

- **GLSL Basics**: uniform variables, built-in functions (`mix`, `smoothstep`, `fract`, `floor`, `sin`, `dot`)
- **Vector Math**: dot product, matrix multiplication, 2D rotation matrix
- **Noise Function Concepts**: understanding the basic principle of value noise (lattice interpolation)
- **fBM (Fractal Brownian Motion)**: superposition of multiple noise layers at different frequencies/amplitudes
- **ShaderToy Environment**: meaning of `iTime`, `iResolution`, `fragCoord`

## Implementation Steps in Detail

### Step 1: Hash Function

**What**: Implement a hash function that maps 2D integer coordinates to a pseudo-random float.

**Why**: This is the foundation of noise functions — producing deterministic "random" values at each lattice point. The `sin-dot` trick compresses 2D input to 1D then takes the fractional part, using sin's high-frequency oscillation to produce a chaotic distribution.

**Code**:
```glsl
float hash(vec2 p) {
    p = fract(p * 0.6180339887); // Golden ratio pre-perturbation
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}
```

> Note: The classic `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)` version can also be used, but the sin-free version above is more stable in precision on some GPUs.

### Step 2: Value Noise

**What**: Implement 2D value noise — take hash values at integer lattice points and interpolate between them with Hermite smoothing.

**Why**: Value noise is the simplest continuous noise, producing smooth, jump-free output suitable as the foundation for fBM. Hermite interpolation `f*f*(3.0-2.0*f)` ensures the derivative is zero at lattice points, avoiding the angular appearance of linear interpolation.

**Code**:
```glsl
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // Hermite smooth interpolation

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}
```

### Step 3: fBM (Fractal Brownian Motion)

**What**: Superpose multiple noise layers at different frequencies/amplitudes to create fractal noise with self-similar properties.

**Why**: A single noise layer is too uniform. fBM superimposes multiple "octaves" to simulate nature's fractal structures. Each layer doubles in frequency (lacunarity ~ 2.0), halves in amplitude (persistence = 0.5), and uses a rotation matrix to break lattice alignment.

**Code**:
```glsl
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80); // Rotation ~36.87°, for decorrelation

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875; // Normalize: sum of all amplitudes
}
```

> Using lacunarity values of 2.01~2.04 rather than exact 2.0 is to **avoid visual artifacts caused by lattice regularity**. This is a widely adopted trick in classic implementations.

### Step 4: Domain Warping (Core)

**What**: Use fBM output as a coordinate offset, recursively nesting to form multi-level warping.

**Why**: This is the core of the entire technique. `fbm(p)` generates a scalar field; adding it to the coordinate `p` is equivalent to "pulling and stretching space according to the noise field's shape." Multi-level nesting makes the deformation more complex and organic — each warping level operates in space already deformed by the previous level.

**Code**:
```glsl
float pattern(vec2 p) {
    return fbm(p + fbm(p + fbm(p)));
}
```

This single line is the classic three-level domain warping. It can be decomposed for understanding:

```glsl
float pattern(vec2 p) {
    float warp1 = fbm(p);           // Level 1: noise in original space
    float warp2 = fbm(p + warp1);   // Level 2: noise in first-level warped space
    float result = fbm(p + warp2);  // Level 3: final value in second-level warped space
    return result;
}
```

### Step 5: Time Animation

**What**: Inject `iTime` into specific fBM octaves so the warp field evolves over time.

**Why**: Directly offsetting all octaves causes uniform translation, lacking organic feel. The classic approach is to inject time only in the lowest frequency (first layer) and highest frequency (last layer) — low frequency drives overall flow, high frequency adds detail variation.

**Code**:
```glsl
float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p + iTime);  // Lowest frequency with time: slow overall flow
    p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p + sin(iTime)); // Highest frequency with time: subtle detail motion
    return f / 0.96875;
}
```

### Step 6: Coloring

**What**: Map the scalar output of the warp field to colors.

**Why**: Domain warping outputs a scalar field (0~1 range) that needs to be mapped to visually meaningful colors. The classic method uses a `mix` chain — interpolating between multiple preset colors using the warp value.

**Code**:
```glsl
vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);                              // Deep purple base
    col = mix(col, vec3(0.3, 0.05, 0.05), t);                    // Dark red
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);                  // White at high values
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t));// Blue highlights
    return col * t * 2.0;                                         // Overall brightness modulation
}
```

## Common Variants in Detail

### Variant 1: Multi-Resolution Layered Warping

**Difference from the basic version**: Uses different octave counts for different warping layers — coarse layers use 4 octaves (fast, low frequency), detail layers use 6 octaves (fine, high frequency). Outputs `vec2` for two-dimensional displacement rather than scalar offset. Intermediate variables participate in coloring, producing richer color gradients.

**Key modified code**:
```glsl
// 4-octave fBM (coarse layer)
float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;
}

// 6-octave fBM (fine layer)
float fbm6(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875;
}

// vec2 output version (independent displacement per axis)
vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));
}
vec2 fbm6_2(vec2 p) {
    return vec2(fbm6(p + vec2(9.2)), fbm6(p + vec2(5.7)));
}

// Layered warping chain
float func(vec2 q, out vec2 o, out vec2 n) {
    q += 0.05 * sin(vec2(0.11, 0.13) * iTime + length(q) * 4.0);
    o = 0.5 + 0.5 * fbm4_2(q);           // Level 1: coarse displacement
    o += 0.02 * sin(vec2(0.13, 0.11) * iTime * length(o));
    n = fbm6_2(4.0 * o);                  // Level 2: fine displacement
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p); // Level 3: final scalar field
    f = mix(f, f * f * f * 3.5, f * abs(n.x)); // Contrast enhancement
    return f;
}

// Coloring uses intermediate variables o, n
vec3 col = vec3(0.2, 0.1, 0.4);
col = mix(col, vec3(0.3, 0.05, 0.05), f);
col = mix(col, vec3(0.9, 0.9, 0.9), dot(n, n));         // n magnitude drives white
col = mix(col, vec3(0.5, 0.2, 0.2), 0.5 * o.y * o.y);   // o.y drives brown
col = mix(col, vec3(0.0, 0.2, 0.4), 0.5 * smoothstep(1.2, 1.3, abs(n.y) + abs(n.x)));
col *= f * 2.0;
```

### Variant 2: Turbulence / Ridge Warping (Electric Arc / Plasma Effect)

**Difference from the basic version**: Takes the absolute value of noise `abs(noise - 0.5)` inside fBM, producing sharp ridge textures instead of smooth waves. Dual-axis independent fBM displacement (separate x/y offsets) combined with reverse time drift creates turbulence.

**Key modified code**:
```glsl
// Turbulence / ridged fBM
float fbm_ridged(vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        rz += abs((noise(p) - 0.5) * 2.0) / z; // abs() produces ridge folding
        z *= 2.0;
        p *= 2.0;
    }
    return rz;
}

// Dual-axis independent displacement
float dualfbm(vec2 p) {
    vec2 p2 = p * 0.7;
    // Opposite time drift in two directions creates turbulence
    vec2 basis = vec2(
        fbm_ridged(p2 - iTime * 0.24),  // x axis drifts left
        fbm_ridged(p2 + iTime * 0.26)   // y axis drifts right
    );
    basis = (basis - 0.5) * 0.2;         // Scale to small displacement
    p += basis;
    return fbm_ridged(p * makem2(iTime * 0.03)); // Slow overall rotation
}

// Electric arc coloring (division creates high-contrast light/dark)
vec3 col = vec3(0.2, 0.1, 0.4) / rz;
```

### Variant 3: Domain Warping with Pseudo-3D Lighting

**Difference from the basic version**: Estimates screen-space normals from the warp field using finite differences, then applies directional lighting, giving the 2D warp field a 3D relief appearance. Combined with color inversion and square compression to produce a characteristic dark tone.

**Key modified code**:
```glsl
// Screen-space normal estimation (finite differences)
float e = 2.0 / iResolution.y; // Sample spacing = 1 pixel
vec3 nor = normalize(vec3(
    pattern(p + vec2(e, 0.0)) - shade,  // df/dx
    2.0 * e,                             // Constant y (controls normal tilt)
    pattern(p + vec2(0.0, e)) - shade    // df/dy
));

// Dual-component lighting
vec3 lig = normalize(vec3(0.9, 0.2, -0.4));
float dif = clamp(0.3 + 0.7 * dot(nor, lig), 0.0, 1.0);
vec3 lin = vec3(0.70, 0.90, 0.95) * (nor.y * 0.5 + 0.5);  // Hemisphere ambient light
lin += vec3(0.15, 0.10, 0.05) * dif;                         // Warm diffuse

col *= 1.2 * lin;
col = 1.0 - col;       // Color inversion
col = 1.1 * col * col;  // Square compression, increases dark contrast
```

### Variant 4: Flow Field Iterative Warping (Gas Giant Planet Effect)

**Difference from the basic version**: Instead of directly nesting fBM, computes the fBM gradient field and iteratively advances coordinates via Euler integration. Simulates fluid advection, producing vortex-like planetary atmospheric banding.

**Key modified code**:
```glsl
#define ADVECT_ITERATIONS 5 // Adjustable: iteration count, more = more pronounced vortices

// Compute fBM gradient (finite differences)
vec2 field(vec2 p) {
    float t = 0.2 * iTime;
    p.x += t;
    float n = fbm(p, t);
    float e = 0.25;
    float nx = fbm(p + vec2(e, 0.0), t);
    float ny = fbm(p + vec2(0.0, e), t);
    return vec2(n - ny, nx - n) / e; // 90° rotated gradient = streamline direction
}

// Iterative flow field advection
vec3 distort(vec2 p) {
    for (float i = 0.0; i < float(ADVECT_ITERATIONS); i++) {
        p += field(p) / float(ADVECT_ITERATIONS);
    }
    return vec3(fbm(p, 0.0)); // Sample at the advected coordinates
}
```

### Variant 5: 3D Volumetric Domain Warping (Explosion / Fireball Effect)

**Difference from the basic version**: Extends domain warping from 2D to 3D, using 3D fBM to displace a sphere's distance field, then rendering via sphere tracing or volumetric ray marching. Produces volcanic eruptions, solar surface, and other volumetric effects.

**Key modified code**:
```glsl
#define NOISE_FREQ 4.0     // Adjustable: noise frequency
#define NOISE_AMP -0.5     // Adjustable: displacement amplitude (negative = inward bulging feel)

// 3D rotation matrix (for decorrelation)
mat3 m3 = mat3(0.00, 0.80, 0.60,
              -0.80, 0.36,-0.48,
              -0.60,-0.48, 0.64);

// 3D value noise
float noise3D(vec3 p) {
    vec3 fl = floor(p);
    vec3 fr = fract(p);
    fr = fr * fr * (3.0 - 2.0 * fr);
    float n = fl.x + fl.y * 157.0 + 113.0 * fl.z;
    return mix(mix(mix(hash(n+0.0),   hash(n+1.0),   fr.x),
                   mix(hash(n+157.0), hash(n+158.0), fr.x), fr.y),
               mix(mix(hash(n+113.0), hash(n+114.0), fr.x),
                   mix(hash(n+270.0), hash(n+271.0), fr.x), fr.y), fr.z);
}

// 3D fBM
float fbm3D(vec3 p) {
    float f = 0.0;
    f += 0.5000 * noise3D(p); p = m3 * p * 2.02;
    f += 0.2500 * noise3D(p); p = m3 * p * 2.03;
    f += 0.1250 * noise3D(p); p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p); p = m3 * p * 2.02;
    f += 0.03125 * abs(noise3D(p)); // Last layer uses abs for added detail
    return f / 0.9375;
}

// Sphere distance field + domain warping displacement
float distanceFunc(vec3 p, out float displace) {
    float d = length(p) - 0.5; // Sphere SDF
    displace = fbm3D(p * NOISE_FREQ + vec3(0, -1, 0) * iTime);
    d += displace * NOISE_AMP;  // fBM displaces the surface
    return d;
}
```

## Performance Optimization Deep Dive

### Bottleneck Analysis

The main performance bottleneck of domain warping is **repeated noise sampling**. Three warping levels times 6 octaves = 18 noise samples per pixel, plus finite differences for lighting (2 additional full warping computations), totaling up to **54 noise samples/pixel**.

### Optimization Techniques

1. **Reduce octave count**: Using 4 octaves instead of 6 shows little visual difference but improves performance by ~33%
   ```glsl
   // Use 4 octaves for coarse layers, only 6 octaves for fine layers
   ```

2. **Reduce warping depth**: Two-level warping `fbm(p + fbm(p))` already produces organic results, saving ~33% performance over three levels

3. **Use sin-product noise instead of value noise**: `sin(p.x)*sin(p.y)` is completely branch-free with no memory access, suitable for mobile
   ```glsl
   float noise(vec2 p) {
       return sin(p.x) * sin(p.y); // Minimal version, no hash needed
   }
   ```

4. **GPU built-in derivatives instead of finite differences**: Saves 2 extra full warping computations
   ```glsl
   // Use dFdx/dFdy instead of manual finite differences (slightly lower quality but 3x faster)
   vec3 nor = normalize(vec3(dFdx(shade) * iResolution.x, 6.0, dFdy(shade) * iResolution.y));
   ```

5. **Texture noise**: Pre-bake noise textures and use `texture()` instead of procedural noise, converting computation to memory reads
   ```glsl
   float noise(vec2 x) {
       return texture(iChannel0, x * 0.01).x;
   }
   ```

6. **LOD adaptation**: Reduce octave count for distant pixels
   ```glsl
   int octaves = int(mix(float(NUM_OCTAVES), 2.0, length(uv) / 5.0));
   ```

7. **Supersampling strategy**: Only use 2x2 supersampling when anti-aliasing is needed (4x performance cost)
   ```glsl
   #if HW_PERFORMANCE == 0
   #define AA 1
   #else
   #define AA 2
   #endif
   ```

## Combination Suggestions with Complete Code Examples

### Combining with Ray Marching
The scalar field generated by domain warping can serve directly as an SDF displacement function, deforming smooth geometry into organic forms. Used for flames, explosions, alien creatures, etc.
```glsl
float sdf(vec3 p) {
    return length(p) - 1.0 + fbm3D(p * 4.0) * 0.3;
}
```

### Combining with Polar Coordinate Transform
Perform domain warping in polar coordinate space to produce vortices, nebulae, spirals, and other effects.
```glsl
vec2 polar = vec2(length(uv), atan(uv.y, uv.x));
float shade = pattern(polar);
```

### Combining with Cosine Color Palette
The cosine palette `a + b*cos(2*pi*(c*t+d))` is more flexible than a fixed mix chain. By adjusting four vec3 parameters, you can quickly switch color schemes.
```glsl
vec3 palette(float t) {
    vec3 a = vec3(0.5); vec3 b = vec3(0.5);
    vec3 c = vec3(1.0); vec3 d = vec3(0.0, 0.33, 0.67);
    return a + b * cos(6.28318 * (c * t + d));
}
```

### Combining with Post-Processing Effects
- **Bloom/Glow**: Blur and overlay high-brightness areas to enhance glow effects
- **Tone Mapping**: `col = col / (1.0 + col)` to compress HDR range
- **Chromatic Aberration**: Sample the warp field at offset positions for R/G/B channels separately
```glsl
float r = pattern(uv + vec2(0.003, 0.0));
float g = pattern(uv);
float b = pattern(uv - vec2(0.003, 0.0));
```

### Combining with Particle Systems / Geometry
The domain warping scalar field can drive particle velocity fields, mesh vertex displacement, or UV animation deformation — not limited to pure fragment shader usage.
