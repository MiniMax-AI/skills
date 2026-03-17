# 2D Procedural Patterns — Detailed Reference

This document is a complete supplement to [SKILL.md](SKILL.md), containing prerequisites, detailed explanations for each step, variant descriptions, in-depth performance analysis, and combination example code.

---

## Prerequisites

- **GLSL Basic Syntax**: uniform, varying, built-in functions
- **Vector Math**: `dot`, `length`, `normalize`, `atan`
- **Coordinate Space Concepts**: UV normalization, aspect ratio correction
- **Basic Math Functions**: `sin`/`cos`, `fract`/`floor`/`mod`, `smoothstep`, `pow`
- **Polar Coordinates**: `atan(y,x)` returns angle, `length` returns radial distance

---

## Core Principles in Detail

The essence of 2D procedural patterns is the combination of **domain transforms + distance fields + color mapping**:

1. **Domain Repetition**: use `fract()`/`mod()` to fold an infinite plane into finite cells, each cell independently rendering the same (or variant) pattern
2. **Cell Identification**: use `floor()` to extract the integer coordinates of the current cell as a hash seed to generate pseudo-random numbers, driving independent variations per cell
3. **Distance Fields (SDF)**: use mathematical functions to compute the distance from a pixel to geometric shapes (circles, hexagons, line segments, arcs), converting to crisp or soft edges via `smoothstep`
4. **Color Mapping**: Cosine palette `a + b*cos(2pi(c*t+d))` or HSV mapping, converting scalar values to rich colors
5. **Layered Compositing**: results from multiple loops or multi-layer passes are combined through addition, multiplication, or `mix` to build visual complexity

---

## Implementation Steps in Detail

### Step 1: UV Coordinate Normalization and Aspect Ratio Correction

**What**: Convert pixel coordinates to normalized coordinates centered on the screen with Y-axis range [-1, 1]

**Why**: A unified coordinate system ensures patterns don't distort with resolution changes; using Y-axis as reference maintains square pixels

```glsl
vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
```

### Step 2: Domain Repetition — Dividing Space into Repeating Cells

**What**: Scale UV coordinates and take the fractional part to generate repeating local coordinates; simultaneously extract cell IDs using `floor`

**Why**: `fract()` folds an infinite plane into a repeating [0,1) space, `floor()` provides a unique cell identifier for subsequent randomization. Subtracting 0.5 centers the origin

```glsl
#define SCALE 4.0 // Tunable: repetition density, higher = more cells
vec2 cell_uv = fract(uv * SCALE) - 0.5;
vec2 cell_id = floor(uv * SCALE);
```

For hexagonal grids, domain repetition requires special handling (two offset rectangular grids, taking the nearest):

```glsl
const vec2 s = vec2(1, 1.7320508); // 1 and sqrt(3)
vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
// Take the nearest hexagonal center
vec4 hex_data = dot(h.xy, h.xy) < dot(h.zw, h.zw)
    ? vec4(h.xy, hC.xy)
    : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
```

### Step 3: Cell Randomization

**What**: Use cell IDs to generate pseudo-random numbers, giving each cell different attributes (size, position, color offset)

**Why**: Pure repetition looks mechanical; randomization gives patterns a "procedural yet lively" quality

```glsl
float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(141.173, 289.927))) * 43758.5453);
}

float rnd = hash21(cell_id);
float radius = 0.15 + 0.1 * rnd; // Tunable: base radius and random range
```

### Step 4: Distance Field Shape Rendering

**What**: Compute the distance from the pixel to the target shape, then convert to visualization using `smoothstep`

**Why**: SDF is the cornerstone of procedural graphics — a single scalar value simultaneously encodes shape, edges, and glow effects

```glsl
// Circle SDF
float d = length(cell_uv) - radius;

// Hexagon SDF
float hex_sdf(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

// Line segment SDF (for networks/grid lines)
float line_sdf(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Anti-aliased rendering with smoothstep
float shape = 1.0 - smoothstep(radius - 0.008, radius + 0.008, length(cell_uv));
```

### Step 5: Polar Coordinate Conversion and Ring/Arc Patterns

**What**: Convert Cartesian coordinates to polar coordinates, using radial distance to draw concentric rings and angle to draw sectors/arc segments

**Why**: Polar coordinates are naturally suited for radar sweeps, concentric circles, spirals, and other radially symmetric patterns

```glsl
vec2 polar = vec2(length(uv), atan(uv.y, uv.x));
float ring_id = floor(polar.x * NUM_RINGS + 0.5) / NUM_RINGS; // Tunable: NUM_RINGS ring count

// Concentric rings
float ring = 1.0 - pow(abs(sin(polar.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);

// Arc segment clipping
float arc_end = polar.y + sin(iTime + ring_id * 5.5) * 1.52 - 1.5;
ring *= smoothstep(0.0, 0.05, arc_end);
```

### Step 6: Cosine Palette

**What**: Generate a continuous rainbow color mapping function using four vec3 parameters

**Why**: A single line of code generates infinite smooth color schemes, more flexible and GPU-friendly than lookup tables

```glsl
vec3 palette(float t) {
    // Tunable: modify a/b/c/d to change color scheme
    vec3 a = vec3(0.5, 0.5, 0.5);       // Brightness offset
    vec3 b = vec3(0.5, 0.5, 0.5);       // Amplitude
    vec3 c = vec3(1.0, 1.0, 1.0);       // Frequency
    vec3 d = vec3(0.263, 0.416, 0.557);  // Phase offset
    return a + b * cos(6.28318 * (c * t + d));
}
```

### Step 7: Iterative Stacking and Glow Effects

**What**: Repeatedly perform domain repetition + distance field calculation in a loop, accumulating color; use `pow(1/d)` to produce glow

**Why**: A single layer pattern is too simple; multi-layer iterative stacking produces fractal-like visual complexity with minimal code. Exponentially decaying glow gives patterns a neon light feel

```glsl
#define NUM_LAYERS 4.0 // Tunable: number of iteration layers, more = more complex
vec3 finalColor = vec3(0.0);
vec2 uv0 = uv; // Preserve original UV for global coloring

for (float i = 0.0; i < NUM_LAYERS; i++) {
    uv = fract(uv * 1.5) - 0.5;    // Tunable: 1.5 is the scale factor
    float d = length(uv) * exp(-length(uv0));
    vec3 col = palette(length(uv0) + i * 0.4 + iTime * 0.4);
    d = sin(d * 8.0 + iTime) / 8.0; // Tunable: 8.0 is the ripple frequency
    d = abs(d);
    d = pow(0.01 / d, 1.2);         // Tunable: 0.01 is glow width, 1.2 is decay exponent
    finalColor += col * d;
}
```

### Step 8: Trigonometric Interference Patterns

**What**: Use `sin`/`cos` to mutually perturb coordinates in iterations, generating water caustic-like interference patterns

**Why**: Superposition of trigonometric functions produces complex Moire-like interference patterns; a few iterations yield highly organic visual effects

```glsl
#define MAX_ITER 5 // Tunable: iteration count, more = richer detail
vec2 p = mod(uv * TAU, TAU) - 250.0; // TAU period ensures tileability
vec2 i = p;
float c = 1.0;
float inten = 0.005; // Tunable: intensity coefficient

for (int n = 0; n < MAX_ITER; n++) {
    float t = iTime * (1.0 - 3.5 / float(n + 1));
    i = p + vec2(cos(t - i.x) + sin(t + i.y),
                 sin(t - i.y) + cos(t + i.x));
    c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten),
                            p.y / (cos(i.y + t) / inten)));
}
c /= float(MAX_ITER);
c = 1.17 - pow(c, 1.4); // Tunable: 1.4 is the contrast exponent
vec3 colour = vec3(pow(abs(c), 8.0));
```

### Step 9: Multi-Layer Depth Compositing

**What**: Render the same pattern at different zoom levels, using depth fade-in/out to simulate parallax

**Why**: Multi-scale stacking breaks the mechanical feel of a single scale, producing a pseudo-3D depth effect

```glsl
#define NUM_DEPTH_LAYERS 4.0 // Tunable: number of depth layers
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);    // Dense far away, sparse up close
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z); // Fade at both ends
    m += fade * patternLayer(uv * size, i, iTime);
}
```

### Step 10: Post-Processing Pipeline

**What**: Apply gamma correction, contrast enhancement, saturation adjustment, and vignette in sequence

**Why**: Post-processing transforms "technically correct" output into "visually pleasing" final results

```glsl
// Gamma correction
col = pow(clamp(col, 0.0, 1.0), vec3(1.0 / 2.2));
// Contrast enhancement (S-curve)
col = col * 0.6 + 0.4 * col * col * (3.0 - 2.0 * col);
// Saturation adjustment
col = mix(col, vec3(dot(col, vec3(0.33))), -0.4); // Tunable: -0.4 increases saturation, positive reduces it
// Vignette
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.7);
```

---

## Common Variants in Detail

### Variant 1: Hexagonal Grid + Truchet Arcs

**Difference from base version**: Replaces the square grid with a hexagonal grid coordinate system, drawing three randomly oriented arcs within each hexagonal cell; arcs form maze-like continuous paths between cells

**Key modified code**:
```glsl
// Hexagon distance field
float hex(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

// Hexagonal grid coordinates (returns xy=cell-local coords, zw=cell ID)
const vec2 s = vec2(1.0, 1.7320508);
vec4 getHex(vec2 p) {
    vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
    vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
    return dot(h.xy, h.xy) < dot(h.zw, h.zw)
        ? vec4(h.xy, hC.xy)
        : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
}

// Truchet three-arc: one arc for each of three directions
float r = 1.0;
vec2 q1 = p - vec2(0.0, r) / s;
vec2 q2 = rot2(6.28318 / 3.0) * p - vec2(0.0, r) / s;
vec2 q3 = rot2(6.28318 * 2.0 / 3.0) * p - vec2(0.0, r) / s;
// Take nearest arc
float d = min(min(length(q1), length(q2)), length(q3));
d = abs(d - 0.288675) - 0.1; // 0.288675 = sqrt(3)/6, arc radius
```

### Variant 2: Water Caustic Interference Pattern

**Difference from base version**: Does not use domain repetition grids; instead generates full-screen interference textures through trigonometric iteration, seamlessly tileable

**Key modified code**:
```glsl
#define TAU 6.28318530718
#define MAX_ITER 5 // Tunable: iteration count

vec2 p = mod(uv * TAU, TAU) - 250.0;
vec2 i = p;
float c = 1.0;
float inten = 0.005;
for (int n = 0; n < MAX_ITER; n++) {
    float t = iTime * (1.0 - 3.5 / float(n + 1));
    i = p + vec2(cos(t - i.x) + sin(t + i.y),
                 sin(t - i.y) + cos(t + i.x));
    c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten),
                            p.y / (cos(i.y + t) / inten)));
}
c /= float(MAX_ITER);
c = 1.17 - pow(c, 1.4);
vec3 colour = vec3(pow(abs(c), 8.0));
colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0); // Aquatic color shift
```

### Variant 3: Polar Concentric Rings + Animated Arc Segments

**Difference from base version**: Uses polar coordinates instead of Cartesian grids, drawing concentric ring arc segments with independent animation, suitable for radar/HUD style

**Key modified code**:
```glsl
#define NUM_RINGS 20.0 // Tunable: ring count
#define PALETTE vec3(0.0, 1.4, 2.0) + 1.5

vec2 plr = vec2(length(p), atan(p.y, p.x));
float id = floor(plr.x * NUM_RINGS + 0.5) / NUM_RINGS;

// Each ring rotates independently
p *= rot2(id * 11.0);
p.y = abs(p.y); // Mirror symmetry

// Concentric ring SDF
float rz = 1.0 - pow(abs(sin(plr.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);

// Arc segment animation
float arc = plr.y + sin(iTime + id * 5.5) * 1.52 - 1.5;
rz *= smoothstep(0.0, 0.05, arc);

// Per-ring coloring
vec3 col = (sin(PALETTE + id * 5.0 + iTime) * 0.5 + 0.5) * rz;
```

### Variant 4: Multi-Layer Depth Parallax Network

**Difference from base version**: Renders grid nodes and connections at multiple zoom levels, using depth fade-in/out to produce a pseudo-3D effect

**Key modified code**:
```glsl
#define NUM_DEPTH_LAYERS 4.0 // Tunable: number of depth layers

// Random vertex position within each cell
vec2 GetPos(vec2 id, vec2 offs, float t) {
    float n = hash21(id + offs);
    return offs + vec2(sin(t + n * 6.28), cos(t + fract(n * 100.0) * 6.28)) * 0.4;
}

// Line segment SDF
float df_line(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Multi-layer compositing
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z);
    m += fade * NetLayer(uv * size, i, iTime);
}
```

### Variant 5: Fractal Apollian Pattern

**Difference from base version**: Uses iterative fold-and-invert transforms to generate infinitely detailed aperiodic fractal patterns, combined with HSV coloring

**Key modified code**:
```glsl
float apollian(vec4 p, float s) {
    float scale = 1.0;
    for (int i = 0; i < 7; ++i) {     // Tunable: iteration count (5~12)
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // Space folding
        float r2 = dot(p, p);
        float k = s / r2;              // Tunable: s is scaling factor (1.0~1.5)
        p *= k;                        // Inversion mapping
        scale *= k;
    }
    return abs(p.y) / scale;
}

// 4D slice animation for smooth morphing
vec4 pp = vec4(p.x, p.y, 0.0, 0.0) + offset;
pp.w = 0.125 * (1.0 - tanh(length(pp.xyz)));
float d = apollian(pp / 4.0, 1.2) * 4.0;

// HSV coloring
float hue = fract(0.75 * length(p) - 0.3 * iTime) + 0.3;
float sat = 0.75 * tanh(2.0 * length(p));
vec3 col = hsv2rgb(vec3(hue, sat, 1.0));
```

---

## In-Depth Performance Optimization

### 1. Control Iteration Count
The iteration loop is the biggest performance bottleneck. Increasing `NUM_LAYERS` from 4 to 8 halves performance. On mobile, keep it at 3 or fewer layers.

### 2. Avoid Branching
Replace `if/else` with branchless `step()`/`smoothstep()`/`mix()` alternatives:
```glsl
// Bad: if(rnd > 0.5) p.y = -p.y;
// Good: p.y *= sign(rnd - 0.5);  // or use mix
```

### 3. Merge Distance Field Calculations
Combine multiple shape SDFs using `min()`/`max()` and apply a single `smoothstep`, rather than rendering each shape separately.

### 4. Precompute Constants
Compute `sin`/`cos` pairs (e.g., rotation matrices) once outside the loop; write irrational numbers like `1.7320508` (sqrt(3)) as direct constants.

### 5. Minimize `atan` Calls
`atan` is an expensive function. If you only need periodic angular variation, consider approximating with `dot`.

### 6. LOD Strategy
Reduce iteration count at distance/when zoomed out:
```glsl
int iters = int(mix(3.0, float(MAX_ITER), smoothstep(0.0, 1.0, 1.0 / scale)));
```

### 7. Use `smoothstep` Instead of `pow`
`pow(x, n)` is slower than `smoothstep` on some GPUs, and `smoothstep` naturally clamps to [0,1].

---

## Complete Combination Suggestion Examples

### 1. + Noise Texture
Overlay Perlin/Simplex noise perturbation on distance fields to give geometric patterns an organic/eroded feel. Triangle noise (as used in "Overly Satisfying") is an efficient low-cost alternative:
```glsl
d += triangleNoise(uv * 10.0) * 0.05; // Noise perturbation amount is tunable
```

### 2. + Post-Processing Cross-Hatch
Overlay cross-hatching effects on patterns to simulate hand-drawn/printmaking style (as used in "Hexagonal Maze Flow"):
```glsl
float gr = dot(col, vec3(0.299, 0.587, 0.114)); // Grayscale
float hatch = (gr < 0.45) ? clamp(sin((uv.x - uv.y) * 125.6) * 2.0 + 1.5, 0.0, 1.0) : 1.0;
col *= hatch * 0.5 + 0.5;
```

### 3. + SDF Boolean Operations
Combine multiple base patterns through `min` (union), `max` (intersection), and subtraction into complex geometry:
```glsl
float d = max(hexSDF, -circleSDF); // Hexagon minus circle = hexagonal ring
```

### 4. + Domain Warping
Apply sin/cos distortion to UVs before domain repetition, producing flowing/swirling effects:
```glsl
uv += 0.05 * vec2(sin(uv.y * 5.0 + iTime), sin(uv.x * 3.0 + iTime));
```

### 5. + Radial Blur / Motion Blur
Average multiple samples in the polar coordinate direction on the final color, producing rotational motion blur to enhance dynamism.

### 6. + Pseudo-3D Lighting
Use SDF gradients as normals and add simple diffuse/specular lighting to give 2D patterns a relief/embossed appearance (as in "Apollian with a twist" shadow casting method).
