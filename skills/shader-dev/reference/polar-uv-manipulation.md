# Polar Coordinates & UV Manipulation — Detailed Reference

> This document is a detailed supplement to [SKILL.md](SKILL.md), covering prerequisites, step-by-step explanations, variant details, in-depth performance analysis, and complete combination code examples.

## Prerequisites

### GLSL Fundamentals
- **uniform / varying**: Global variable passing mechanisms
- **Built-in functions**: `sin`, `cos`, `atan`, `length`, `fract`, `mod`, `smoothstep`, `mix`, `clamp`, `pow`, `exp`, `log`, `abs`, `max`, `min`, `floor`, `ceil`, `dot`
- **Vector types**: `vec2`, `vec3`, `vec4`, with swizzle support (e.g., `.xy`, `.rgb`)
- **Matrix types**: `mat2` for 2D rotation

### Vector Math
- 2D vector operations: addition, subtraction, multiplication, division, length (`length`), normalization (`normalize`)
- Dot product (`dot`): projection and angle relationships
- 2D rotation matrix:
```glsl
mat2 rotate(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}
```

### Coordinate Systems
- Cartesian coordinates (x, y): standard rectangular coordinate system
- Screen coordinates: bottom-left (0,0), top-right (iResolution.x, iResolution.y)
- Normalized coordinates: typically mapped to [-1, 1] or [0, 1] range

### ShaderToy Framework
- `mainImage(out vec4 fragColor, in vec2 fragCoord)`: entry function
- `fragCoord`: current pixel's screen coordinates
- `iResolution`: viewport resolution (pixels)
- `iTime`: time since launch (seconds)
- `iMouse`: mouse position

## Implementation Steps

### Step 1: UV Normalization and Centering

**What**: Convert screen pixel coordinates to normalized coordinates centered at the screen center with uniform scaling.

**Why**: All subsequent polar coordinate operations depend on a correct center point and uniform scale. Without this step, effects would be offset or stretched.

**Three approaches compared**:

| Approach | Range | Use Case |
|----------|-------|----------|
| `/ min(iResolution.x, iResolution.y)` | [-1, 1] square region | Most universal, ensures circles stay circular |
| `/ iResolution.y` | [-aspect, aspect] × [-1, 1] | When full screen width is needed |
| Pixel quantization | Depends on PIXEL_FILTER | Pixelated/retro style |

```glsl
// Approach 1: range [-1, 1], most common
vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);

// Approach 2: range [-aspect, aspect] x [-1, 1]
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Approach 3: precise pixel size control (precise pixel size control)
float pixel_size = length(iResolution.xy) / PIXEL_FILTER; // PIXEL_FILTER adjustable: pixelation level
vec2 uv = (floor(fragCoord * (1.0/pixel_size)) * pixel_size - 0.5*iResolution.xy) / length(iResolution.xy);
```

### Step 2: Cartesian to Polar Coordinate Transform

**What**: Convert (x, y) coordinates to (r, θ) polar coordinates.

**Why**: This is the fundamental transform of the entire paradigm, mapping the linear xy space to a radial space centered at the origin. In polar coordinates:
- A circle is simply r = constant
- A ray is simply θ = constant
- This makes creating ring/spiral/radial effects very straightforward

**About the `atan` function**:
- `atan(y, x)` (two-argument version) is equivalent to atan2 in math, returning [-π, π]
- `atan(y/x)` (single-argument version) only returns [-π/2, π/2], losing quadrant information
- Always use the two-argument version

```glsl
// Basic transform
float r = length(uv);           // Radius
float theta = atan(uv.y, uv.x); // Angle, range [-PI, PI]

// Wrapped as reusable functionvec2 toPolar(vec2 p) {
    return vec2(length(p), atan(p.y, p.x));
}

// Normalize angle to [0, 1] rangevec2 polar = vec2(atan(uv.y, uv.x) / 6.283 + 0.5, length(uv));
// polar.x in [0,1], polar.y is radius
```

### Step 3: Operations in Polar Coordinate Space

**What**: Perform various transforms in (r, θ) space to create effects.

**Why**: The unique property of polar coordinate space is that rotation, spirals, radial repetition, and other effects that are extremely difficult in Cartesian coordinates become simple addition, subtraction, and multiplication operations here.

#### 3a. Radial Distortion (Swirl) — Angle Offset by Radius

**Principle**: `θ_new = θ - k × r` causes points farther from the center to rotate more, naturally forming a vortex. `k` controls how "tight" the vortex is.

```glsl
// Greater radius = more rotation → vortex effect
float spin_amount = 0.25; // Adjustable: vortex strength, 0=no rotation, 1=maximum rotation
float new_theta = theta - spin_amount * 20.0 * r;
```

#### 3b. Angular Twist — Angle Plus Time Offset

**Principle**: Adding functions of time and the angle itself to the angle produces distorted rings that change over time. The `sin(theta)` term makes the distortion non-uniform, creating an organic feel.

```glsl
// Angle varies with time and position → twisted ringsfloat twist_angle = theta + 2.0 * iTime + sin(theta) * sin(iTime) * 3.14159;
```

#### 3c. Archimedean Spiral — Radius Minus Angle

**Principle**: The Archimedean spiral r = a + bθ has the property of equal spacing. In UV space, `y -= x` (i.e., r -= θ) "unfolds" concentric rings into equally-spaced spiral bands.

```glsl
// Unfold into spiral bandsvec2 spiral_uv = vec2(theta_normalized, r);
spiral_uv.y -= spiral_uv.x; // Key: "unfold" radial space into spirals
```

#### 3d. Logarithmic Spiral — Angle Plus log(r) Shear

**Principle**: The logarithmic spiral (equiangular spiral) r = ae^(bθ) has the property of self-similarity — it looks exactly the same when magnified. The `log(r)` shear makes rotation amount grow logarithmically at different radii, commonly seen in nature (nautilus shells, galaxy arms).

```glsl
// Logarithmic spiral stretch
float shear = 2.0 * log(r); // Adjustable: coefficient controls spiral tightness
float c = cos(shear), s = sin(shear);
mat2 spiral_mat = mat2(c, -s, s, c); // Rotation matrix implements shear
```

#### 3e. Kaleidoscope — Angle Modulo and Mirroring

**Principle**: Divides the 2π angular range into N equal sectors, then maps all pixels to a single sector. Mirroring makes adjacent sectors symmetric, avoiding seams.

**Mathematical Derivation**:
1. `sector = 2π / N`: Angular width of each sector
2. `c_idx = floor((θ + sector/2) / sector)`: Current sector index
3. `θ' = mod(θ + sector/2, sector) - sector/2`: Fold to [-sector/2, sector/2]
4. `θ' *= (2 × (c_idx mod 2) - 1)`: Flip odd sectors

```glsl
// Angular subdivision + mirroring for kaleidoscopefloat rep = 12.0;          // Adjustable: number of symmetry axes
float sector = TAU / rep;  // Angle per sector
float a = polar.y;         // Angle component

// Modulo to single sector
float c_idx = floor((a + sector * 0.5) / sector);
a = mod(a + sector * 0.5, sector) - sector * 0.5;

// Mirror: flip adjacent sectors
a *= mod(c_idx, 2.0) * 2.0 - 1.0;
```

#### 3f. Spiral Arm Compression — Periodic Modulation in Angular Domain

**Principle**: Galaxy spiral arms are not simple lines but regions of higher matter density. `cos(N × (θ - shear))` creates periodic compression in the angular domain, causing matter (color/brightness) to accumulate along N arms. The `COMPR` parameter controls arm "sharpness".

**Density Compensation**: Compression changes local density (like an accordion effect); `arm_density` compensates for this non-uniformity, preventing the arms from being too bright or too dark.

```glsl
// Galaxy spiral arm effect
float NB_ARMS = 5.0;   // Adjustable: number of spiral arms
float COMPR = 0.1;      // Adjustable: intra-arm compression strength
float phase = NB_ARMS * (theta - shear);
theta = theta - COMPR * cos(phase); // Compress angular domain to form arm structures
float arm_density = 1.0 + NB_ARMS * COMPR * sin(phase); // Density compensation
```

### Step 4: Polar to Cartesian Reconstruction (Round Trip)

**What**: Convert modified polar coordinates back to Cartesian coordinates.

**Why**: Some effects need to transform in polar space and then return to xy space for further processing (e.g., overlaying texture noise, Truchet patterns, etc.). This forms the complete Cartesian→Polar→Cartesian "round trip".

**Notes**:
- After inverse transform, the coordinate origin may need adjustment (e.g., a `mid` offset to screen center)
- If you only need to color in polar space (e.g., ring gradients), no inverse transform is needed

```glsl
// Basic inverse transform
vec2 new_uv = vec2(r * cos(new_theta), r * sin(new_theta));

// Wrapped as reusable functionvec2 toRect(vec2 p) {
    return vec2(p.x * cos(p.y), p.x * sin(p.y));
}

// Complete round trip: offset to screen center after transform
vec2 mid = (iResolution.xy / length(iResolution.xy)) / 2.0;
vec2 warped_uv = vec2(
    r * cos(new_theta) + mid.x,
    r * sin(new_theta) + mid.y
) - mid;
```

### Step 5: Polar Coordinate Shape Definition (SDF)

**What**: Define signed distance fields of shapes via r(θ) functions in polar coordinates.

**Why**: Many classic curves (cardioid, rose curves, star shapes) have elegant analytical expressions in polar coordinates that would be extremely complex in Cartesian coordinates.

**Advantages of SDF**:
- Negative value = inside, positive value = outside, zero = boundary
- Convenient boolean operations (`max` = intersection, `min` = union)
- `smoothstep` directly produces anti-aliased edges
- `abs(d)` produces outlines, `1/abs(d)` produces glow

```glsl
// Cardioid
float a = atan(p.x, p.y) / 3.141593; // Note: atan(x,y) not atan(y,x), so heart points up
float h = abs(a);
float heart_r = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);
float dist = r - heart_r; // Negative = inside, positive = outside

// Rose curve / petals
float PETAL_FREQ = 3.0; // Adjustable: petal frequency (K.x/K.y controls integer/fractional petals)
float A_coeff = 0.2;    // Adjustable: petal amplitude
float rose_dist = abs(r - A_coeff * sin(PETAL_FREQ * theta) - 0.5); // Distance to curve

// Render SDF as visible shape
float shape = smoothstep(0.01, -0.01, dist); // Anti-aliased edge
```

### Step 6: Coloring and Anti-Aliasing

**What**: Color based on polar coordinate information and handle edge anti-aliasing.

**Why**: Polar coordinate coloring naturally produces radial gradients and ring patterns. Anti-aliasing is especially important in polar coordinates because pixel density varies significantly away from the center due to angular subdivision.

**Anti-aliasing method comparison**:

| Method | Pros | Cons |
|--------|------|------|
| `fwidth` | Adaptive, precise | Requires GPU derivative support |
| Fixed resolution width | Simple, reliable | Not adaptive to scaling |
| `smoothstep` + fixed offset | Simplest | Average results |

```glsl
// Adaptive anti-aliasing based on fwidthfloat aa = smoothstep(-1.0, 1.0, value / fwidth(value));

// Resolution-based anti-aliasingfloat aa_size = 2.0 / iResolution.y;
float edge = smoothstep(0.5 - aa_size, 0.5 + aa_size, value);

// General SDF anti-aliasing using smoothstep
float d = some_sdf_value;
float col = smoothstep(aa_size, -aa_size, d); // aa_size ≈ 1~3 pixels

// Radial gradient coloring
vec3 color = vec3(1.0, 0.4 * r, 0.3); // Color varies with radius
color *= 1.0 - 0.4 * r;               // Darken at edges

// Inter-spiral-band anti-aliasingfloat inter_spiral_aa = 1.0 - pow(abs(2.0 * fract(spiral_uv.y) - 1.0), 10.0);
```

## Variant Details

### Variant 1: Dynamic Vortex/Swirl Background

**Difference from basic version**: Complete Cartesian→Polar→Cartesian round trip + iterative domain warping to generate complex textures.

**Technical Points**:
1. First apply vortex distortion in polar coordinates
2. Convert back to Cartesian coordinates
3. Perform 5 iterations of domain warping in the transformed space, each iteration nonlinearly offsetting coordinates
4. The iterative sin/cos combination produces complex organic textures

**Parameter Descriptions**:
- `SPIN_AMOUNT`: Vortex strength, controls polar distortion magnitude
- `SPIN_EASE`: Vortex easing, makes rotation speed differ between center and edges
- `speed`: Animation speed, driven by `iTime`

```glsl
// Polar coordinate vortex transform
float new_angle = atan(uv.y, uv.x) + speed
    - SPIN_EASE * 20.0 * (SPIN_AMOUNT * uv_len + (1.0 - SPIN_AMOUNT));
vec2 mid = (screenSize.xy / length(screenSize.xy)) / 2.0;
uv = vec2(uv_len * cos(new_angle) + mid.x,
           uv_len * sin(new_angle) + mid.y) - mid;

// Iterative domain warping for organic textures
uv *= 30.0;
for (int i = 0; i < 5; i++) {
    uv2 += sin(max(uv.x, uv.y)) + uv;
    uv  += 0.5 * vec2(cos(5.1123 + 0.353*uv2.y + speed*0.131),
                       sin(uv2.x - 0.113*speed));
    uv  -= cos(uv.x + uv.y) - sin(uv.x*0.711 - uv.y);
}
```

### Variant 2: Polar Torus Twist

**Difference from basic version**: Renders geometry directly in polar coordinate space (without returning to Cartesian), simulating a 3D torus through angular slicing.

**Technical Points**:
1. Offset the r dimension to the ring's centerline (`r -= OUT_RADIUS`) to center the ring region
2. "Slice" along the ring in the angular dimension, with each slice being one edge of a regular polygon
3. The `twist` variable makes the polygon twist along the ring, producing a Möbius strip-like effect
4. The `sin(uvr.y)*sin(iTime)` term varies the twist speed with angle, creating organic squeezing/stretching

```glsl
// Geometric slicing in polar coordinates
vec2 uvr = vec2(length(uv), atan(uv.y, uv.x) + PI);
uvr.x -= OUT_RADIUS; // Offset to ring centerline

float twist = uvr.y + 2.0*iTime + sin(uvr.y)*sin(iTime)*PI;
for (int i = 0; i < NUM_FACES; i++) {
    float x0 = IN_RADIUS * sin(twist + TAU * float(i) / float(NUM_FACES));
    float x1 = IN_RADIUS * sin(twist + TAU * float(i+1) / float(NUM_FACES));
    // Define face start/end positions in the polar r direction
    vec4 face = slice(x0, x1, uvr);
    col = mix(col, face.rgb, face.a);
}
```

### Variant 3: Galaxy / Logarithmic Spiral (Galaxy Style)

**Difference from basic version**: Uses `log(r)` for equiangular spirals, combined with FBM noise and spiral arm compression.

**Technical Points**:
1. The `log(r)` shear is the core — it maps concentric circles to logarithmic spirals
2. Rotation matrix R rotates the noise sampling coordinates by the shear angle, aligning noise along the spiral arms
3. `NB_ARMS` and `COMPR` control the number and sharpness of arms
4. FBM noise is sampled in the rotated space, producing galactic dust texture

```glsl
float rho = length(uv);
float ang = atan(uv.y, uv.x);
float shear = 2.0 * log(rho);     // Logarithmic spiral core
mat2 R = mat2(cos(shear), -sin(shear), sin(shear), cos(shear));

// Spiral arms
float phase = NB_ARMS * (ang - shear);
ang = ang - COMPR * cos(phase) + SPEED * t; // Inter-arm compression
uv = rho * vec2(cos(ang), sin(ang));         // Reconstruct Cartesian
float gaz = fbm_noise(0.09 * R * uv);        // Sample noise in spiral space
```

### Variant 4: Archimedean Spiral Band + Vortices

**Difference from basic version**: Unfolds polar coordinates into spiral bands, creates independent vortex animations within bands, with arc-length parameterization.

**Technical Points**:
1. `U.y -= U.x` is the core of Archimedean unfolding — converts concentric rings to equally-spaced spiral bands
2. Arc-length parameterization `arc_length()` ensures uniform cell area within the spiral band
3. Each cell uses `dot` + `cos` to create a small vortex, strong at center, weak at edges
4. `cell_id.x` gives different cells different vortex phases, avoiding monotonous repetition

```glsl
vec2 U = vec2(atan(U.y, U.x)/TAU + 0.5, length(U));
U.y -= U.x;                                    // Archimedean unfolding
U.x = arc_length(ceil(U.y) + U.x) - iTime;     // Arc-length parameterization

// Vortex within each cell of the spiral band
vec2 cell_uv = fract(U) - 0.5;
float vortex = dot(cell_uv,
    cos(vec2(-33.0, 0.0)                       // Rotation matrix angle offset
        + 0.3 * (iTime + cell_id.x)            // Time + spatial rotation amount
        * max(0.0, 0.5 - length(cell_uv))));   // Strong at center, weak at edges
```

### Variant 5: Complex Number / Polar Duality (Jeweled Vortex Style)

**Difference from basic version**: Uses complex number operations (multiplication = rotation + scaling, power = spiral mapping) instead of explicit trigonometric functions to implement conformal mappings.

**Technical Points**:
1. Complex power `z^(1/e)` is equivalent to `(r^(1/e), θ/e)` in polar coordinates — simultaneously scaling radius and compressing angle
2. `exp(log(length(u)) / e)` implements `r^(1/e)` without explicitly computing the power
3. `ceil(r - a/TAU)` produces spiral contour lines — corresponding to different sheets of the Riemann surface in the complex plane
4. Multi-layered `sin`/`cos` combinations produce jewel-like interference colors

```glsl
float e = n * 2.0;  // Complex power exponent, controls spiral curvature
float a = atan(u.y, u.x) - PI/2.0;     // Angle
float r = exp(log(length(u)) / e);      // r^(1/e) — complex root
float sc = ceil(r - a/TAU);             // Spiral contour lines
float s = pow(sc + a/TAU, 2.0);         // Spiral gradient
// Multi-layer spiral compositing
col += sin(cr + s/n * TAU / 2.0);       // Spiral color layer 1
col *= cos(cr + s/n * TAU);             // Spiral color layer 2
col *= pow(abs(sin((r - a/TAU) * PI)), abs(e) + 5.0); // Smooth edges
```

## In-Depth Performance Analysis

### 1. Avoiding Numerical Issues at the Pole

`atan(0,0)` and `length(0)` may produce numerical instability near the origin. While GLSL's `atan` won't crash at the origin, the return value is undefined and may cause flickering.

```glsl
// Safe polar coordinate conversion
float r = max(length(uv), 1e-6); // Avoid division by zero
float theta = atan(uv.y, uv.x);  // atan2 is not well-defined at origin but won't crash
```

**When needed**: Protection is required when subsequent calculations include `1.0/r`, `log(r)`, or `normalize(uv)`. If only `r * something`, r=0 at the origin is naturally safe.

### 2. Trigonometric Function Optimization

Frequent sin/cos calls are the main cost of polar coordinate shaders. Although GPU sin/cos is hardware-accelerated, heavy use in loops can still become a bottleneck.

```glsl
// If both sin and cos are needed, replace with a single matrix multiplication
mat2 ROT(float a) { float c=cos(a), s=sin(a); return mat2(c,s,-s,c); }
vec2 rotated = ROT(angle) * uv; // Cleaner than computing sin, cos separately and manually constructing

// Use vector dot product instead of explicit trig
// Instead of U.y = cos(rot)*U.x + sin(rot)*U.y
// Use U.y = dot(U, cos(vec2(-33,0) + angle))
```

**Principle**: `cos(vec2(a, b))` in GLSL is a single SIMD instruction that computes two cos values simultaneously. Combined with `dot`, rotation can be achieved with only one `cos` call (leveraging the identity `cos(x - π/2) = sin(x)`).

### 3. Leveraging Kaleidoscope Symmetry

A kaleidoscope inherently reduces computation by a factor of N (N = number of symmetry segments), serving as a natural optimization. All expensive pattern calculations are done in just one sector:

```glsl
// Do kaleidoscope folding first, then expensive pattern computation
vec2 kp = kaleidoscope(polar, segments); // Cheap
vec2 rect = toRect(kp);
// All subsequent computation only applies to one sector
float expensive_pattern = some_costly_function(rect); // Same cost but N× visual complexity
```

**Note**: The cost of kaleidoscope folding itself (a few `floor`, `mod`, and multiplication operations) is far less than the visual complexity it "saves". A 12-segment kaleidoscope means you get 12x visual richness for 1/12 the pattern computation cost.

### 4. Loop Optimization in Spiral Bands

For effects like rose curves that require multi-loop computation, keep loop counts reasonable:

```glsl
// Rose curves only need ceil(K.y) loops
for (int i = 0; i < 7; i++) { // 7 loops are enough to cover most fractional frequencies
    v = max(v, ribbon_value);
    a += 6.28; // Next loop
}
// Don't use excessively large loop counts; 4~8 loops suffice for most cases
```

**Why 4~8 loops**: The rose curve r = cos(p/q × θ) has a period of q loops (when p/q is fractional). For most practical petal frequencies, 7 loops provide full coverage. Excessive loops not only waste computation but may also produce artifacts from floating-point accumulation errors.

### 5. Pixel Filter Downsampling

For stylized effects, downsampling can dramatically reduce computation:

```glsl
float pixel_size = length(iResolution.xy) / 745.0; // Adjustable: smaller = more pixelated
vec2 uv = floor(fragCoord / pixel_size) * pixel_size; // Quantize coordinates
// All subsequent computation uses quantized uv, adjacent pixels share results
```

**Performance benefit**: If pixel_size makes each "virtual pixel" cover 4×4 actual pixels, the GPU only needs to compute 1/16 of unique values (remaining adjacent pixels produce identical results and may benefit from cache optimization).

## Complete Combination Code Examples

### Polar Coordinates + FBM Noise

Sample FBM noise in polar coordinate space to produce organic spiral textures (galactic dust, flame vortices):

```glsl
vec2 polar_uv = rho * vec2(cos(modified_ang), sin(modified_ang));
float organic = fbm(polar_uv * frequency); // Sample in transformed space
```

### Polar Coordinates + Truchet Patterns

Lay Truchet tiles in kaleidoscope-folded space to produce kaleidoscopic geometric tunnel effects. The kaleidoscope provides symmetry; Truchet provides detail patterns.

```glsl
// Kaleidoscope folding
vec2 kp = kaleidoscope(polar, segments);
vec2 rect = toRect(kp);

// Truchet grid
rect *= 4.0;
vec2 cell_id = floor(rect + 0.5);
vec2 cell_uv = fract(rect + 0.5) - 0.5;
float cell_hash = fract(sin(dot(cell_id, vec2(127.1, 311.7))) * 43758.5453);

// Arc Truchet
float d = length(cell_uv);
float truchet = abs(d - 0.35);
if (cell_hash > 0.5) {
    truchet = min(truchet, abs(length(cell_uv - 0.5) - 0.5));
} else {
    truchet = min(truchet, abs(length(cell_uv + 0.5) - 0.5));
}
```

### Polar Coordinates + SDF Shapes

Define shape contours with polar equations r(θ), combined with SDF techniques for boolean operations, rounded corners, and glow:

```glsl
float heart_sdf = r - heart_r_theta;
float glow = 0.02 / abs(heart_sdf); // Glow effect
float solid = smoothstep(0.01, -0.01, heart_sdf); // Solid fill
```

### Polar Coordinates + Checkerboard/Grid

Lay a checkerboard pattern in polar coordinate space, naturally forming ring/spiral checkerboards:

```glsl
// Create checkerboard in polar UV
float checker = sign(sin(u * PI * 4.0) * cos(uvr.y * 16.0));
col *= checker * (1.0/16.0) + 0.7; // Low contrast checkerboard texture
```

### Polar Coordinates + Post-Processing

Polar coordinate effects combined with gamma correction, vignette, and color mapping can greatly enhance visual quality:

```glsl
col = pow(col, vec3(1.0/2.2));                                    // Gamma
col = col*0.6 + 0.4*col*col*(3.0-2.0*col);                      // Contrast enhancement
col *= 0.5 + 0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y), 0.7);  // Vignette
```
