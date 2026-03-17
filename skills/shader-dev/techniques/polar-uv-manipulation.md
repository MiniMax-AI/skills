## WebGL2 Adaptation Requirements

Code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt to WebGL2:

- Use `canvas.getContext("webgl2")`
- **IMPORTANT: Version directive must strictly be on the first line**: When injecting shader code into HTML, ensure nothing precedes `#version 300 es` — no newlines, spaces, comments, or other characters. Common pitfall: accidentally adding `\n` when concatenating template strings, causing the version directive to appear on line 2-3
- First line of shader: `#version 300 es`, add `precision highp float;` for fragment shaders
- Vertex shader: `attribute` → `in`, `varying` → `out`
- Fragment shader: `varying` → `in`, `gl_FragColor` → custom `out vec4 fragColor`, `texture2D()` → `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` must be adapted to standard `void main()` entry

**IMPORTANT: GLSL Type Strictness Warning**:
- `vec2 = float` is illegal: types must match exactly, e.g., `float r = length(uv)` not `vec2 r = length(uv)`
- Function return types must match: commonly used `fbm()` / `noise()` return `float`, cannot be assigned to `vec2`
- If you need a vec2 type, use `vec2(fbm(...), fbm(...))` or `vec2(value)` constructor

# Polar Coordinates & UV Manipulation

## Use Cases
- Radially symmetric effects: flowers, kaleidoscopes, gears, radial patterns
- Spiral patterns: galaxies, vortices, spiral staircases
- Ring/tunnel effects: tube flying, torus twisting, circular UI elements
- Polar coordinate shapes: cardioid, rose curves, stars, and other shapes defined by r(θ)
- Vortex animations: swirls, rotational warping, card game backgrounds (e.g., Balatro)
- Fractal/repetitive structures: recursive symmetric patterns based on angular subdivision

## Core Principles

Polar coordinates convert (x, y) to (r, θ):
- **r = length(p)** — distance to origin
- **θ = atan(y, x)** — angle from positive x-axis, range [-π, π]

Inverse transform: x = r·cos(θ), y = r·sin(θ)

Manipulation effects:
- Modifying θ → rotation, warping, kaleidoscope
- Modifying r → scaling, radial ripples
- θ += f(r) → spiral effect

| Spiral Type | Equation | Code |
|------------|----------|------|
| Archimedean spiral | r = a + bθ | `theta += radius` |
| Logarithmic spiral | r = ae^(bθ) | `theta += log(radius)` |
| Rose curve | r = cos(nθ) | `r - A*sin(n*theta)` |

## Implementation Steps

### Step 1: UV Normalization and Centering
```glsl
// Range [-1, 1], most commonly used
vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);

// Range [-aspect, aspect] x [-1, 1]
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Pixelated style (Balatro style)
float pixel_size = length(iResolution.xy) / PIXEL_FILTER;
vec2 uv = (floor(fragCoord * (1.0/pixel_size)) * pixel_size - 0.5*iResolution.xy) / length(iResolution.xy);
```

### Step 2: Cartesian → Polar Coordinates
```glsl
float r = length(uv);
float theta = atan(uv.y, uv.x); // [-PI, PI]

// Reusable function
vec2 toPolar(vec2 p) { return vec2(length(p), atan(p.y, p.x)); }

// Normalized angle to [0, 1]
vec2 polar = vec2(atan(uv.y, uv.x) / 6.283 + 0.5, length(uv));
```

### Step 3: Polar Space Operations

**3a. Radial Swirl**
```glsl
float spin_amount = 0.25;
float new_theta = theta - spin_amount * 20.0 * r;
```

**3b. Angular Twist**
```glsl
float twist_angle = theta + 2.0 * iTime + sin(theta) * sin(iTime) * 3.14159;
```

**3c. Archimedean Spiral**
```glsl
vec2 spiral_uv = vec2(theta_normalized, r);
spiral_uv.y -= spiral_uv.x; // Unwrap into spiral band
```

**3d. Logarithmic Spiral**
```glsl
float shear = 2.0 * log(r);
float c = cos(shear), s = sin(shear);
mat2 spiral_mat = mat2(c, -s, s, c);
```

**3e. Kaleidoscope**
```glsl
float rep = 12.0;          // Number of symmetry axes
float sector = TAU / rep;
float a = polar.y;
float c_idx = floor((a + sector * 0.5) / sector);
a = mod(a + sector * 0.5, sector) - sector * 0.5;
a *= mod(c_idx, 2.0) * 2.0 - 1.0; // Mirror
```

**3f. Spiral Arm Compression**
```glsl
float NB_ARMS = 5.0;
float COMPR = 0.1;
float phase = NB_ARMS * (theta - shear);
theta = theta - COMPR * cos(phase);
float arm_density = 1.0 + NB_ARMS * COMPR * sin(phase);
```

### Step 4: Polar → Cartesian Reconstruction
```glsl
vec2 new_uv = vec2(r * cos(new_theta), r * sin(new_theta));

vec2 toRect(vec2 p) { return vec2(p.x * cos(p.y), p.x * sin(p.y)); }

// Balatro-style round-trip (offset to screen center)
vec2 mid = (iResolution.xy / length(iResolution.xy)) / 2.0;
vec2 warped_uv = vec2(r * cos(new_theta) + mid.x, r * sin(new_theta) + mid.y) - mid;
```

### Step 5: Polar Coordinate Shape SDF
```glsl
// Cardioid
float a = atan(p.x, p.y) / 3.141593; // atan(x,y) makes the heart face upward
float h = abs(a);
float heart_r = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);
float dist = r - heart_r;

// Rose curve
float rose_dist = abs(r - A_coeff * sin(PETAL_FREQ * theta) - 0.5);

// Rendering
float shape = smoothstep(0.01, -0.01, dist);
```

### Step 6: Coloring and Anti-Aliasing
```glsl
// fwidth adaptive anti-aliasing
float aa = smoothstep(-1.0, 1.0, value / fwidth(value));

// Resolution-based anti-aliasing
float aa_size = 2.0 / iResolution.y;
float edge = smoothstep(0.5 - aa_size, 0.5 + aa_size, value);

// Radial gradient coloring
vec3 color = vec3(1.0, 0.4 * r, 0.3);
color *= 1.0 - 0.4 * r;

// Inter-spiral-band anti-aliasing
float inter_spiral_aa = 1.0 - pow(abs(2.0 * fract(spiral_uv.y) - 1.0), 10.0);
```

## Complete Code Template

```glsl
// === Polar Coordinates & UV Manipulation Complete Template ===
// Paste directly into ShaderToy to run

#define PI 3.14159265359
#define TAU 6.28318530718

// ===== Adjustable Parameters =====
#define MODE 0            // 0=swirl, 1=spiral, 2=kaleidoscope, 3=rose curve
#define SPIRAL_TYPE 0     // 0=Archimedean, 1=logarithmic (MODE=1)
#define NUM_ARMS 5.0      // Number of spiral arms (MODE=1)
#define KALEID_SEGMENTS 6.0 // Kaleidoscope segments (MODE=2)
#define PETAL_COUNT 5.0   // Number of petals (MODE=3)
#define SWIRL_STRENGTH 3.0 // Swirl intensity (MODE=0)
#define ANIM_SPEED 1.0    // Animation speed
#define COLOR_SCHEME 0    // 0=warm, 1=cool, 2=rainbow

vec2 toPolar(vec2 p) {
    return vec2(length(p), atan(p.y, p.x));
}

vec2 toRect(vec2 p) {
    return vec2(p.x * cos(p.y), p.x * sin(p.y));
}

vec2 kaleidoscope(vec2 polar, float segments) {
    float sector = TAU / segments;
    float a = polar.y;
    float c = floor((a + sector * 0.5) / sector);
    a = mod(a + sector * 0.5, sector) - sector * 0.5;
    a *= mod(c, 2.0) * 2.0 - 1.0;
    return vec2(polar.x, a);
}

vec3 getColor(float t, int scheme) {
    if (scheme == 1) return 0.5 + 0.5 * cos(TAU * (t + vec3(0.0, 0.33, 0.67)));
    if (scheme == 2) return 0.5 + 0.5 * cos(TAU * t + vec3(0.0, 2.1, 4.2));
    return vec3(1.0, 0.4 + 0.4 * cos(t * TAU), 0.3 + 0.2 * sin(t * TAU));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);
    vec2 polar = toPolar(uv);
    float r = polar.x;
    float theta = polar.y;
    float t = iTime * ANIM_SPEED;
    vec3 col = vec3(0.0);
    float aa = 2.0 / iResolution.y;

    #if MODE == 0
    // --- Swirl mode ---
    float swirl_theta = theta - SWIRL_STRENGTH * r + t;
    vec2 warped = toRect(vec2(r, swirl_theta));
    warped *= 10.0;
    float pattern = sin(warped.x) * cos(warped.y);
    pattern += 0.5 * sin(2.0 * warped.x + t) * cos(2.0 * warped.y - t);
    float val = smoothstep(-0.1, 0.1, pattern);
    col = mix(
        getColor(r * 0.5, COLOR_SCHEME),
        getColor(r * 0.5 + 0.5, COLOR_SCHEME),
        val
    );
    col *= exp(-r * 0.5);

    #elif MODE == 1
    // --- Spiral mode ---
    #if SPIRAL_TYPE == 0
        float spiral = theta / TAU + 0.5;
        float bands = spiral + r;
        bands -= t * 0.1;
        float arm = fract(bands * NUM_ARMS);
    #else
        float shear = 2.0 * log(max(r, 0.001));
        float phase = NUM_ARMS * (theta - shear);
        float arm = 0.5 + 0.5 * cos(phase);
        arm *= 1.0 + NUM_ARMS * 0.1 * sin(phase);
    #endif
    float brightness = smoothstep(0.0, 0.4, arm) * smoothstep(1.0, 0.6, arm);
    col = getColor(theta / TAU + t * 0.05, COLOR_SCHEME) * brightness;
    col *= exp(-r * r * 0.5);
    col += 0.15 * exp(-r * r * 8.0);

    #elif MODE == 2
    // --- Kaleidoscope mode ---
    vec2 kp = kaleidoscope(polar, KALEID_SEGMENTS);
    vec2 rect = toRect(kp);
    rect *= 4.0;
    rect += vec2(t * 0.3, 0.0);
    vec2 cell_id = floor(rect + 0.5);
    vec2 cell_uv = fract(rect + 0.5) - 0.5;
    float cell_hash = fract(sin(dot(cell_id, vec2(127.1, 311.7))) * 43758.5453);
    float d = length(cell_uv);
    float truchet = abs(d - 0.35);
    if (cell_hash > 0.5) {
        truchet = min(truchet, abs(length(cell_uv - 0.5) - 0.5));
    } else {
        truchet = min(truchet, abs(length(cell_uv + 0.5) - 0.5));
    }
    col = getColor(cell_hash + r * 0.2, COLOR_SCHEME);
    col *= smoothstep(0.05, 0.0, truchet - 0.03);
    col *= smoothstep(3.0, 0.0, r);

    #elif MODE == 3
    // --- Rose curve mode ---
    float rose_r = 0.6 * cos(PETAL_COUNT * theta + t);
    float dist = abs(r - abs(rose_r));
    float ribbon_width = 0.04;
    float rose_shape = smoothstep(ribbon_width + aa, ribbon_width - aa, dist);
    float depth = 0.5 + 0.5 * cos(PETAL_COUNT * theta + t);
    col = getColor(theta / TAU, COLOR_SCHEME) * depth;
    col *= rose_shape;
    float center = smoothstep(0.08 + aa, 0.08 - aa, r);
    col += getColor(0.5, COLOR_SCHEME) * center * 0.5;
    #endif

    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Dynamic Vortex Background (Balatro Style)
Cartesian→Polar→Cartesian round-trip + iterative domain warping
```glsl
float new_angle = atan(uv.y, uv.x) + speed
    - SPIN_EASE * 20.0 * (SPIN_AMOUNT * uv_len + (1.0 - SPIN_AMOUNT));
vec2 mid = (screenSize.xy / length(screenSize.xy)) / 2.0;
uv = vec2(uv_len * cos(new_angle) + mid.x,
           uv_len * sin(new_angle) + mid.y) - mid;
uv *= 30.0;
for (int i = 0; i < 5; i++) {
    uv2 += sin(max(uv.x, uv.y)) + uv;
    uv  += 0.5 * vec2(cos(5.1123 + 0.353*uv2.y + speed*0.131),
                       sin(uv2.x - 0.113*speed));
    uv  -= cos(uv.x + uv.y) - sin(uv.x*0.711 - uv.y);
}
```

### Variant 2: Polar Torus Twist (Ring Twister Style)
Direct rendering in polar space, angular slicing to simulate 3D torus
```glsl
vec2 uvr = vec2(length(uv), atan(uv.y, uv.x) + PI);
uvr.x -= OUT_RADIUS;
float twist = uvr.y + 2.0*iTime + sin(uvr.y)*sin(iTime)*PI;
for (int i = 0; i < NUM_FACES; i++) {
    float x0 = IN_RADIUS * sin(twist + TAU * float(i) / float(NUM_FACES));
    float x1 = IN_RADIUS * sin(twist + TAU * float(i+1) / float(NUM_FACES));
    vec4 face = slice(x0, x1, uvr);
    col = mix(col, face.rgb, face.a);
}
```

### Variant 3: Galaxy / Logarithmic Spiral (Galaxy Style)
`log(r)` equiangular spiral + FBM noise + spiral arm compression
```glsl
float rho = length(uv);
float ang = atan(uv.y, uv.x);
float shear = 2.0 * log(rho);
mat2 R = mat2(cos(shear), -sin(shear), sin(shear), cos(shear));
float phase = NB_ARMS * (ang - shear);
ang = ang - COMPR * cos(phase) + SPEED * t;
uv = rho * vec2(cos(ang), sin(ang));
float gaz = fbm_noise(0.09 * R * uv);
```

### Variant 4: Archimedean Spiral Band (Wave Greek Frieze Style)
Polar unwrap into spiral band, creating vortex animation within the band
```glsl
vec2 U = vec2(atan(U.y, U.x)/TAU + 0.5, length(U));
U.y -= U.x;                                    // Archimedean unwrap
U.x = arc_length(ceil(U.y) + U.x) - iTime;     // Arc length parameterization
vec2 cell_uv = fract(U) - 0.5;
float vortex = dot(cell_uv,
    cos(vec2(-33.0, 0.0)
        + 0.3 * (iTime + cell_id.x)
        * max(0.0, 0.5 - length(cell_uv))));
```

### Variant 5: Complex / Polar Duality (Jeweled Vortex Style)
Complex arithmetic replaces explicit trigonometric functions for conformal mapping
```glsl
float e = n * 2.0;
float a = atan(u.y, u.x) - PI/2.0;
float r = exp(log(length(u)) / e);      // r^(1/e)
float sc = ceil(r - a/TAU);
float s = pow(sc + a/TAU, 2.0);
col += sin(cr + s/n * TAU / 2.0);
col *= cos(cr + s/n * TAU);
col *= pow(abs(sin((r - a/TAU) * PI)), abs(e) + 5.0);
```

## Performance & Composition

### Performance Tips
- **Pole safety**: `float r = max(length(uv), 1e-6);` to avoid division by zero
- **Trigonometric optimization**: When both sin/cos are needed, use a rotation matrix `mat2 ROT(float a) { float c=cos(a),s=sin(a); return mat2(c,s,-s,c); }`
- **Kaleidoscope is naturally optimized**: All expensive computation happens in a single sector, visual complexity ×N
- **Loop control**: Rose curves and other multi-loop effects work well with 4-8 loops; don't go too high
- **Pixel downsampling**: `floor(fragCoord / pixel_size) * pixel_size` quantizes coordinates to reduce computation

### Composition Tips
- **Polar + FBM**: Sample noise in transformed space → organic spiral textures
- **Polar + Truchet**: Lay Truchet tiles after kaleidoscope folding → geometric tunnel effects
- **Polar + SDF**: `r(θ)` defines contour + SDF boolean operations / glow
- **Polar + Checkerboard**: `sign(sin(u*PI*4.0)*cos(uvr.y*16.0))` → circular checkerboard
- **Polar + Post-Processing**: Gamma + vignette + contrast enhancement for improved visual quality

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/polar-uv-manipulation.md)
