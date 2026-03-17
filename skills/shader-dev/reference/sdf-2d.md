# 2D SDF Detailed Reference

This file contains the complete step-by-step tutorial, mathematical derivations, detailed explanations, and advanced usage for [SKILL.md](SKILL.md).

## Prerequisites

- **GLSL Basics**: uniforms, varyings, built-in functions (length, dot, clamp, mix, smoothstep, step, sign, abs, max, min)
- **Vector Math**: 2D vector operations, geometric meaning of dot and cross products
- **Coordinate Systems**: conversion from screen coordinates to normalized device coordinates (NDC), aspect ratio correction
- **Signed Distance Field Concept**: the function returns the signed distance to the shape boundary — negative inside, zero on the boundary, positive outside

## Core Principles in Detail

The core idea of 2D SDF: **for each pixel on screen, compute its shortest signed distance `d` to the target shape boundary**.

- `d < 0`: pixel is inside the shape
- `d = 0`: pixel is exactly on the boundary
- `d > 0`: pixel is outside the shape

Once you have the distance value `d`, use functions like `smoothstep` and `clamp` to map it to color/opacity, enabling:
- **Fill**: color when `d < 0`
- **Anti-aliased edges**: `smoothstep(-aa, aa, d)` for sub-pixel smoothing at the boundary
- **Stroke**: apply smoothstep again on `abs(d) - strokeWidth`
- **Boolean operations**: `min(d1, d2)` = union, `max(d1, d2)` = intersection, `max(-d1, d2)` = subtraction

Key mathematical formulas:
```
Circle:       d = length(p - center) - radius
Rectangle:    d = length(max(abs(p) - halfSize, 0.0)) + min(max(abs(p).x - halfSize.x, abs(p).y - halfSize.y), 0.0)
Line segment: d = length(p - a - clamp(dot(p-a, b-a)/dot(b-a, b-a), 0, 1) * (b-a)) - width/2
Union:        d = min(d1, d2)
Intersection: d = max(d1, d2)
Subtraction:  d = max(-d1, d2)
Smooth union: d = mix(d2, d1, h) - k*h*(1-h),  h = clamp(0.5 + 0.5*(d2-d1)/k, 0, 1)
```

## Implementation Steps in Detail

### Step 1: Coordinate Normalization and Aspect Ratio Correction

**What**: Convert screen pixel coordinates to normalized coordinates centered at the screen center, with the y range of [-1, 1].

**Why**: Pixel coordinates depend on resolution. After normalization, SDF parameters (such as radius) have resolution-independent physical meaning. Dividing by `iResolution.y` (not `.x`) ensures correct aspect ratio so circles don't become ellipses.

**Code**:
```glsl
// Method 1: Origin at center, y range [-1, 1] (most common, standard practice)
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Method 2: If you need to work in pixel space (suitable for fixed pixel-size UI)
vec2 p = fragCoord.xy;
vec2 center = iResolution.xy * 0.5;

// Method 3: [0, 1] range normalization (requires manual aspect ratio handling)
vec2 uv = fragCoord.xy / iResolution.xy;
```

### Step 2: Defining SDF Primitive Functions

**What**: Write basic primitive functions that return signed distances. Each function takes the current point `p` and shape parameters, and returns a `float` distance value.

**Why**: These are the atomic building blocks for all 2D SDF graphics. Encapsulating them as independent functions allows free combination, transformation, and reuse.

**Code**:
```glsl
// ---- Circle ----
// The most basic SDF: distance from point to center minus radius
float sdCircle(vec2 p, float radius) {
    return length(p) - radius;
}

// ---- Rectangle (optional rounded corners) ----
// halfSize is half-width and half-height, radius is the corner radius
float sdBox(vec2 p, vec2 halfSize, float radius) {
    halfSize -= vec2(radius);
    vec2 d = abs(p) - halfSize;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - radius;
}

// ---- Line Segment ----
// Line segment from start to end, with width
float sdLine(vec2 p, vec2 start, vec2 end, float width) {
    vec2 dir = end - start;
    float h = clamp(dot(p - start, dir) / dot(dir, dir), 0.0, 1.0);
    return length(p - start - dir * h) - width * 0.5;
}

// ---- Triangle (exact signed distance) ----
// Three vertices p0, p1, p2, only one sqrt needed
float sdTriangle(vec2 p, vec2 p0, vec2 p1, vec2 p2) {
    vec2 e0 = p1 - p0, v0 = p - p0;
    vec2 e1 = p2 - p1, v1 = p - p1;
    vec2 e2 = p0 - p2, v2 = p - p2;

    // Squared distance to each edge (projection + clamp)
    float d0 = dot(v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0),
                   v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0));
    float d1 = dot(v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0),
                   v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0));
    float d2 = dot(v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0),
                   v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0));

    // Determine inside/outside using cross product sign
    float o = e0.x * e2.y - e0.y * e2.x;
    vec2 d = min(min(vec2(d0, o * (v0.x * e0.y - v0.y * e0.x)),
                     vec2(d1, o * (v1.x * e1.y - v1.y * e1.x))),
                     vec2(d2, o * (v2.x * e2.y - v2.y * e2.x)));
    return -sqrt(d.x) * sign(d.y);
}

// ---- Ellipse (approximate) ----
// Simplified ellipse SDF based on scaled space
float sdEllipse(vec2 p, vec2 center, float a, float b) {
    float a2 = a * a, b2 = b * b;
    vec2 d = p - center;
    return (b2 * d.x * d.x + a2 * d.y * d.y - a2 * b2) / (a2 * b2);
}
```

### Step 3: CSG Boolean Operations

**What**: Combine two SDF distance values using min/max operations to achieve union, subtraction, and intersection of shapes.

**Why**: This is the most powerful capability of SDFs — building arbitrarily complex shapes from simple primitives. `min` takes the smaller of the two field values to produce a union (since smaller distance means "closer" to the shape interior); `max` takes the larger value for intersection; `max(a, -b)` inverts b's inside/outside and intersects for subtraction.

**Code**:
```glsl
// Union: take the nearest shape
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

// Intersection: overlapping region of both shapes
float opIntersect(float d1, float d2) {
    return max(d1, d2);
}

// Subtraction: carve d1 out of d2
float opSubtract(float d1, float d2) {
    return max(-d1, d2);
}

// Smooth union: produces a rounded transition at the junction, k controls transition width
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

// XOR: non-overlapping region of both shapes
float opXor(float d1, float d2) {
    return min(max(-d1, d2), max(-d2, d1));
}
```

### Step 4: Coordinate Transforms

**What**: Transform coordinates before computing the SDF so that shapes appear at desired positions and angles.

**Why**: SDF functions define shapes centered at the origin by default. By transforming the input coordinates (rather than the shape itself), you can freely place and rotate multiple primitives in the scene without affecting the mathematical properties of the distance field.

**Code**:
```glsl
// Translation: move the coordinate origin to position t
vec2 translate(vec2 p, vec2 t) {
    return p - t;
}

// Counter-clockwise rotation
vec2 rotateCCW(vec2 p, float angle) {
    mat2 m = mat2(cos(angle), sin(angle), -sin(angle), cos(angle));
    return p * m;
}

// Usage example: translate then rotate
float d = sdBox(rotateCCW(translate(p, vec2(0.5, 0.3)), iTime), vec2(0.2), 0.05);
```

### Step 5: Distance Field Visualization and Rendering

**What**: Convert the SDF distance value to final color output. Includes fill, anti-aliasing, stroke, contour lines, and other visualization methods.

**Why**: The distance value itself is just a scalar that needs a mapping strategy to become a visual effect. `smoothstep` creates sub-pixel smooth transitions at the boundary, avoiding aliasing from hard edges. The `fwidth` function uses screen-space derivatives to automatically calculate pixel width, achieving resolution-independent anti-aliasing.

**Code**:
```glsl
// ---- Method 1: clamp for simple alpha (most basic) ----
float t = clamp(d, 0.0, 1.0);
vec4 shapeColor = vec4(color, 1.0 - t);

// ---- Method 2: smoothstep anti-aliasing (recommended general approach) ----
// aa controls edge softness, typical value is pixel size px = 2.0/iResolution.y
float px = 2.0 / iResolution.y;                      // Adjustable: anti-aliasing width
float mask = smoothstep(px, -px, d);                  // 1.0 inside, 0.0 outside
vec3 col = mix(backgroundColor, shapeColor, mask);

// ---- Method 3: fwidth adaptive anti-aliasing (suitable for zooming scenes) ----
float anti = fwidth(d) * 1.0;                         // Adjustable: multiplier, larger = softer edges
float mask = 1.0 - smoothstep(-anti, anti, d);

// ---- Method 4: Classic distance field debug visualization ----
vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3)           // Outside: orange
                      : vec3(0.65, 0.85, 1.0);        // Inside: blue
col *= 1.0 - exp(-12.0 * abs(d));                     // Distance falloff
col *= 0.8 + 0.2 * cos(120.0 * d);                    // Contour lines, 120.0 adjustable: line density
col = mix(col, vec3(1.0), smoothstep(1.5*px, 0.0, abs(d) - 0.002)); // Zero contour highlight
```

### Step 6: Stroke and Border Rendering

**What**: Use the absolute value of the distance field to extract the shape's outline, or render inner/outer borders separately.

**Why**: Strokes are a natural byproduct of SDFs — `abs(d)` gives unsigned distance, and subtracting the stroke width yields the "stroke shape" SDF. Unlike rasterized strokes that require geometry expansion, SDF strokes need only one line of math.

**Code**:
```glsl
// ---- Fill mask ----
float fillMask(float d) {
    return clamp(-d, 0.0, 1.0);
}

// ---- Stroke rendering (fwidth adaptive) ----
// stroke is the stroke width (in distance field units)
vec4 renderShape(float d, vec3 color, float stroke) {
    float anti = fwidth(d) * 1.0;
    vec4 strokeLayer = vec4(vec3(0.05), 1.0 - smoothstep(-anti, anti, d - stroke));
    vec4 colorLayer  = vec4(color,      1.0 - smoothstep(-anti, anti, d));
    if (stroke < 0.0001) return colorLayer;
    return vec4(mix(strokeLayer.rgb, colorLayer.rgb, colorLayer.a), strokeLayer.a);
}

// ---- Inner border mask ----
float innerBorderMask(float d, float width) {
    return clamp(d + width, 0.0, 1.0) - clamp(d, 0.0, 1.0);
}

// ---- Outer border mask ----
float outerBorderMask(float d, float width) {
    return clamp(d, 0.0, 1.0) - clamp(d - width, 0.0, 1.0);
}
```

### Step 7: Multi-Layer Compositing

**What**: Render multiple SDF shapes as layers with alpha channels, then blend them back-to-front using `mix`.

**Why**: Complex 2D scenes typically contain backgrounds, multiple shapes, strokes, and other visual layers. Rendering each SDF as an independent RGBA layer and compositing them layer by layer with standard alpha blending (`mix(bottom, top, top.a)`) is both intuitive and gives precise control over stacking order.

**Code**:
```glsl
// Background layer
vec3 bgColor = vec3(1.0, 0.8, 0.7 - 0.07 * p.y) * (1.0 - 0.25 * length(p));

// Shape layer 1
float d1 = sdCircle(translate(p, pos1), 0.3);
vec4 layer1 = renderShape(d1, vec3(0.9, 0.3, 0.2), 0.02);

// Shape layer 2
float d2 = sdBox(translate(p, pos2), vec2(0.2), 0.05);
vec4 layer2 = renderShape(d2, vec3(0.2, 0.5, 0.8), 0.0);

// Composite back-to-front
vec3 col = bgColor;
col = mix(col, layer1.rgb, layer1.a);   // Overlay shape 1
col = mix(col, layer2.rgb, layer2.a);   // Overlay shape 2

fragColor = vec4(col, 1.0);
```

## Variant Detailed Descriptions

### Variant 1: Solid Fill + Stroke Mode

**Difference from the basic version**: Instead of showing distance field debug colors, renders solid shapes with clean strokes, suitable for UI and icons.

**Key modified code**:
```glsl
// Replace the distance field visualization section
vec3 shapeColor = vec3(0.32, 0.56, 0.53);
float strokeW = 0.015;   // Adjustable: stroke width
vec4 shape = render(d, shapeColor, strokeW);

vec3 col = bgCol;
col = mix(col, shape.rgb, shape.a);
```

### Variant 2: Multi-Layer CSG Illustration

**Difference from the basic version**: Combines multiple SDF primitives through boolean operations into complex patterns (e.g., an umbrella, a logo), with each layer independently colored and composited layer by layer. Suitable for 2D illustrations and icon construction.

**Key modified code**:
```glsl
// Build the body (ellipse intersection)
float a = sdEllipse(p, vec2(0.0, 0.16), 0.25, 0.25);
float b = sdEllipse(p, vec2(0.0, -0.03), 0.8, 0.35);
float body = opIntersect(a, b);
vec4 layer1 = render(body, vec3(0.32, 0.56, 0.53), fwidth(body) * 2.0);

// Build the handle (line segment + arc subtraction)
float handle = sdLine(p, vec2(0.0, 0.05), vec2(0.0, -0.42), 0.01);
float arc = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.04);
float arcInner = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.03);
handle = opUnion(handle, opSubtract(arcInner, arc));
vec4 layer0 = render(handle, vec3(0.4, 0.3, 0.28), STROKE_WIDTH);

// Composite
vec3 col = bgCol;
col = mix(col, layer0.rgb, layer0.a);
col = mix(col, layer1.rgb, layer1.a);
```

### Variant 3: Hexagonal Grid Tiling

**Difference from the basic version**: Uses non-orthogonal coordinate system domain repetition to tile SDFs across the screen, with each cell having an independent ID for differentiated coloring. Suitable for background textures and geometric patterns.

**Key modified code**:
```glsl
// Hexagonal grid function: returns (cellID.xy, edge distance, center distance)
vec4 hexagon(vec2 p) {
    vec2 q = vec2(p.x * 2.0 * 0.5773503, p.y + p.x * 0.5773503);
    vec2 pi = floor(q);
    vec2 pf = fract(q);
    float v = mod(pi.x + pi.y, 3.0);
    float ca = step(1.0, v);
    float cb = step(2.0, v);
    vec2 ma = step(pf.xy, pf.yx);
    float e = dot(ma, 1.0 - pf.yx + ca*(pf.x+pf.y-1.0) + cb*(pf.yx-2.0*pf.xy));
    p = vec2(q.x + floor(0.5 + p.y / 1.5), 4.0 * p.y / 3.0) * 0.5 + 0.5;
    float f = length((fract(p) - 0.5) * vec2(1.0, 0.85));
    return vec4(pi + ca - cb * ma, e, f);
}

// Usage
#define HEX_SCALE 8.0          // Adjustable: grid density
vec4 h = hexagon(HEX_SCALE * p + 0.5 * iTime);
vec3 col = 0.15 + 0.15 * hash1(h.xy + 1.2);          // Different gray per cell
col *= smoothstep(0.10, 0.11, h.z);                   // Edge lines
col *= smoothstep(0.10, 0.11, h.w);                   // Center falloff
```

### Variant 4: Organic Shapes (Polar Coordinate SDF)

**Difference from the basic version**: Uses polar coordinates `(atan, length)` to define shape boundary functions, enabling creation of hearts, petals, stars, and other non-polygonal organic shapes. Supports pulsing animations.

**Key modified code**:
```glsl
// Heart SDF (polar coordinate algebraic curve)
p.y -= 0.25;
float a = atan(p.x, p.y) / 3.141593;
float r = length(p);
float h = abs(a);
float d = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);

// Pulse animation
float tt = mod(iTime, 1.5) / 1.5;
float ss = pow(tt, 0.2) * 0.5 + 0.5;
ss = 1.0 + ss * 0.5 * sin(tt * 6.2831 * 3.0) * exp(-tt * 4.0);  // Adjustable: sin frequency controls pulse count

// Rendering
vec3 col = mix(bgCol, heartCol, smoothstep(-0.01, 0.01, d - r));
```

### Variant 5: Bezier Curve SDF

**Difference from the basic version**: Computes the exact signed distance from a point to a quadratic Bezier curve by solving a cubic equation (Cardano's formula). Suitable for curved text, path rendering, and similar scenarios.

**Key modified code**:
```glsl
// Cubic equation solver (Cardano's formula)
vec3 solveCubic(float a, float b, float c) {
    float p = b - a*a/3.0, p3 = p*p*p;
    float q = a*(2.0*a*a - 9.0*b)/27.0 + c;
    float d = q*q + 4.0*p3/27.0;
    float offset = -a/3.0;
    if (d >= 0.0) {
        float z = sqrt(d);
        vec2 x = (vec2(z,-z) - q) / 2.0;
        vec2 uv = sign(x) * pow(abs(x), vec2(1.0/3.0));
        return vec3(offset + uv.x + uv.y);
    }
    float v = acos(-sqrt(-27.0/p3)*q/2.0) / 3.0;
    float m = cos(v), n = sin(v) * 1.732050808;
    return vec3(m+m, -n-m, n-m) * sqrt(-p/3.0) + offset;
}

// Bezier SDF (three control points A, B, C)
float sdBezier(vec2 A, vec2 B, vec2 C, vec2 p) {
    B = mix(B + vec2(1e-4), B, step(1e-6, abs(B*2.0-A-C)));
    vec2 a = B-A, b = A-B*2.0+C, c = a*2.0, d = A-p;
    vec3 k = vec3(3.*dot(a,b), 2.*dot(a,a)+dot(d,b), dot(d,a)) / dot(b,b);
    vec3 t = clamp(solveCubic(k.x, k.y, k.z), 0.0, 1.0);
    vec2 pos = A+(c+b*t.x)*t.x; float dis = length(pos-p);
    pos = A+(c+b*t.y)*t.y; dis = min(dis, length(pos-p));
    pos = A+(c+b*t.z)*t.z; dis = min(dis, length(pos-p));
    return dis * signBezier(A, B, C, p);   // signBezier uses barycentric coordinates to determine sign
}
```

## Performance Optimization in Detail

### 1. Reducing sqrt Calls

In polygon SDFs (such as triangles), by comparing squared distance values first and only taking `sqrt` on the minimum distance at the end, multiple `sqrt` calls are reduced to one. This is the core optimization idea behind the triangle SDF implementation.

```glsl
// Bad: sqrt on every edge
float d0 = length(v0 - e0 * h0);
float d1 = length(v1 - e1 * h1);
// Good: compare dot(v,v) squares, one sqrt at the end
float d0 = dot(proj0, proj0);
float d1 = dot(proj1, proj1);
return -sqrt(min(d0, d1)) * sign(...);
```

### 2. fwidth vs Fixed Pixel Width

`fwidth(d)` invokes screen-space partial derivatives. In simple scenes, a fixed `px = 2.0/iResolution.y` can replace it to reduce GPU derivative computation overhead. However, in scenes with coordinate scaling/distortion (such as the hexagonal grid's `pos *= 1.2 + 0.15*length(pos)`), `fwidth` must be used to ensure correct anti-aliasing width.

### 3. Avoiding Excessive Boolean Operation Nesting

Large amounts of `min`/`max` nesting are correct but computing distances for all primitives per pixel per frame can be expensive. You can skip distant primitives by checking rough bounding boxes:

```glsl
// Only compute precisely when near the shape
if (length(p - shapeCenter) < shapeRadius + margin) {
    d = opUnion(d, sdComplexShape(p));
}
```

### 4. Supersampling AA Trade-off

Multiple samples (e.g., 2x2 supersampling) yield higher quality anti-aliasing but multiply the fragment shader computation by 4:

```glsl
#define AA 2  // Adjustable: 1 = no supersampling, 2 = 4x, 3 = 9x
for (int m = 0; m < AA; m++)
for (int n = 0; n < AA; n++) {
    vec2 off = vec2(m, n) / float(AA);
    // ... computation ...
    tot += col;
}
tot /= float(AA * AA);
```

For most real-time scenes, single-pixel AA with `smoothstep` or `fwidth` is sufficient. Supersampling is mainly for offline rendering or showcase scenes.

### 5. Step Size Optimization for 2D Soft Shadows

In cone marching 2D soft shadows, use `max(1.0, abs(sd))` instead of a fixed step size to take large leaps in open areas and small precise steps near shapes. Typically 64 steps can cover a large scene:

```glsl
dt += max(1.0, abs(sd));  // Adaptive step size
if (dt > dl) break;       // Early exit after reaching the light source
```

## Combination Suggestions in Detail

### 1. SDF + Noise Textures

Adding noise values to the distance field creates dissolve, erosion, and organic edge effects:

```glsl
float d = sdCircle(p, 0.4);
d += noise(p * 10.0 + iTime) * 0.05;  // Organic jittery edges
```

### 2. SDF + 2D Lighting and Shadows

Cone marching based on the distance field implements real-time soft shadows and multi-light lighting for 2D scenes. The distance field provides "scene query" capability, using `sceneDist()` during ray marching to check occlusion:

```glsl
// 2D soft shadow (see 4dfXDn for full implementation)
float shadow(vec2 p, vec2 lightPos, float radius) {
    vec2 dir = normalize(lightPos - p);
    float dl = length(p - lightPos);
    float lf = radius * dl;
    float dt = 0.01;
    for (int i = 0; i < 64; i++) {
        float sd = sceneDist(p + dir * dt);
        if (sd < -radius) return 0.0;
        lf = min(lf, sd / dt);
        dt += max(1.0, abs(sd));
        if (dt > dl) break;
    }
    lf = clamp((lf*dl + radius) / (2.0*radius), 0.0, 1.0);
    return smoothstep(0.0, 1.0, lf);
}
```

### 3. SDF + Normal Mapping / Bump Mapping

By computing normals via finite differences on the distance field, then applying standard lighting models, you can simulate 3D bump/highlight effects on 2D SDFs (as done in the DVD Bounce shader):

```glsl
vec2 e = vec2(0.8, 0.0) / iResolution.y;
float fx = sceneDist(p) - sceneDist(p + e);
float fy = sceneDist(p) - sceneDist(p + e.yx);
vec3 nor = normalize(vec3(fx, fy, e.x / 0.1));  // 0.1 = bump factor, adjustable
// Standard Blinn-Phong lighting
vec3 lig = normalize(vec3(1.0, 2.0, 2.0));
float dif = clamp(dot(lig, nor), 0.0, 1.0);
```

### 4. SDF + Domain Repetition (Spatial Tiling)

Use `fract` or `mod` on coordinates for infinite repetition; use `floor` to get cell IDs for differentiated coloring. Suitable for background patterns, particle arrays, etc.:

```glsl
vec2 cellSize = vec2(0.5);
vec2 cellID = floor(p / cellSize);
vec2 cellP = fract(p / cellSize) - 0.5;        // Local coordinate within cell
float d = sdCircle(cellP, 0.15 + 0.05 * sin(iTime + cellID.x * 3.0));
```

### 5. SDF + Animation

Distance field parameters (position, radius, rotation angle) naturally support continuous animation. Combine with `sin/cos` periodic motion, `exp` decay, `mod` looping, and other time functions:

```glsl
// Bouncing
float y = abs(sin(iTime * 3.0)) * 0.5;
float d = sdCircle(translate(p, vec2(0.0, y)), 0.2);

// Pulse scaling
float pulse = 1.0 + 0.1 * sin(iTime * 6.28 * 2.0) * exp(-mod(iTime, 1.0) * 4.0);
float d = sdCircle(p / pulse, 0.3) * pulse;

// Rotation
float d = sdBox(rotateCCW(p, iTime), vec2(0.2), 0.03);
```

## Extended 2D SDF Primitives Reference

### sdRoundedBox — Rounded Box with Independent Corner Radii

**Signature**: `float sdRoundedBox(vec2 p, vec2 b, vec4 r)`

- `p`: query point
- `b`: half-size of the box
- `r`: corner radii as `vec4(top-right, bottom-right, top-left, bottom-left)`

Selects the appropriate corner radius based on the quadrant of `p`, then computes a standard rounded box distance. Useful for UI elements where each corner needs a different rounding.

### sdOrientedBox — Oriented Box

**Signature**: `float sdOrientedBox(vec2 p, vec2 a, vec2 b, float th)`

- `p`: query point
- `a`, `b`: endpoints defining the box's center axis
- `th`: thickness (full width perpendicular to the axis)

Constructs a local coordinate frame aligned with segment `a`-to-`b`, then evaluates a standard box SDF. Useful for drawing thick line-like rectangles at arbitrary angles without manual rotation.

### sdArc — Arc

**Signature**: `float sdArc(vec2 p, vec2 sc, float ra, float rb)`

- `p`: query point
- `sc`: `vec2(sin, cos)` of the half-aperture angle
- `ra`: arc radius
- `rb`: arc thickness

Computes distance to an arc segment. The aperture is symmetric about the y-axis. Combines angular clamping with radial distance.

### sdPie — Pie / Sector

**Signature**: `float sdPie(vec2 p, vec2 c, float r)`

- `p`: query point
- `c`: `vec2(sin, cos)` of the half-aperture angle
- `r`: radius

Returns the signed distance to a filled pie-slice (sector) shape. The sector is symmetric about the y-axis.

### sdRing — Ring

**Signature**: `float sdRing(vec2 p, vec2 n, float r, float th)`

- `p`: query point
- `n`: `vec2(sin, cos)` of the half-aperture angle
- `r`: ring radius
- `th`: ring thickness

Similar to `sdArc` but with capped endpoints and full ring behavior within the aperture.

### sdMoon — Moon Shape

**Signature**: `float sdMoon(vec2 p, float d, float ra, float rb)`

- `p`: query point
- `d`: distance between circle centers
- `ra`: radius of outer circle
- `rb`: radius of inner (subtracted) circle

Creates a crescent/moon shape by subtracting one circle from another. The two circles are offset by distance `d` along the x-axis.

### sdHeart — Heart (Approximate)

**Signature**: `float sdHeart(vec2 p)`

- `p`: query point (centered at origin, roughly unit scale)

An approximate heart SDF composed of two geometric regions stitched together. The shape extends roughly from (0,0) to (0,1) vertically.

### sdVesica — Vesica / Lens Shape

**Signature**: `float sdVesica(vec2 p, float w, float h)`

- `p`: query point
- `w`: width of the vesica
- `h`: height of the vesica

A lens-shaped figure (vesica piscis) formed by the intersection of two circles. Symmetric about both axes.

### sdEgg — Egg Shape

**Signature**: `float sdEgg(vec2 p, float he, float ra, float rb)`

- `p`: query point
- `he`: half-height of the straight section
- `ra`: radius at bottom
- `rb`: radius at top

Produces an egg-like shape with different radii at top and bottom, connected by a straight vertical section.

### sdEquilateralTriangle — Equilateral Triangle

**Signature**: `float sdEquilateralTriangle(vec2 p, float r)`

- `p`: query point
- `r`: side length / scale

An exact SDF for an equilateral triangle centered at the origin using symmetry folding.

### sdPentagon — Pentagon

**Signature**: `float sdPentagon(vec2 p, float r)`

- `p`: query point
- `r`: circumscribed radius

Regular pentagon SDF using mirror-fold operations along pentagon edge normals. The constants encode cos/sin of 72-degree angles.

### sdHexagon — Hexagon

**Signature**: `float sdHexagon(vec2 p, float r)`

- `p`: query point
- `r`: circumscribed radius

Regular hexagon SDF. Constants encode cos(30), sin(30), and tan(30). Uses a single mirror fold.

### sdOctagon — Octagon

**Signature**: `float sdOctagon(vec2 p, float r)`

- `p`: query point
- `r`: circumscribed radius

Regular octagon SDF. Uses two mirror folds at 22.5-degree and 67.5-degree angles.

### sdStar — N-Pointed Star

**Signature**: `float sdStar(vec2 p, float r, int n, float m)`

- `p`: query point
- `r`: outer radius
- `n`: number of points
- `m`: inner radius ratio (controls pointiness; typical range 2.0-6.0)

A general n-pointed star using angular repetition (`mod(atan(...))`) and edge projection. Higher `m` values produce sharper, thinner points.

### sdBezier (Extended) — Quadratic Bezier Curve SDF

**Signature**: `float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C)`

- `pos`: query point
- `A`, `B`, `C`: control points of the quadratic Bezier

An alternative Bezier SDF formulation that solves for the closest point on the curve using the cubic formula. Returns unsigned distance (no sign). Note the different parameter order from the Variant 5 version.

### sdParabola — Parabola

**Signature**: `float sdParabola(vec2 pos, float k)`

- `pos`: query point
- `k`: curvature coefficient (y = k * x^2)

Signed distance to a parabola. Uses a cubic root solution to find the closest point on the curve.

### sdCross — Cross Shape

**Signature**: `float sdCross(vec2 p, vec2 b, float r)`

- `p`: query point
- `b`: half-extents of each arm (b.x = length, b.y = width)
- `r`: corner rounding offset

A plus/cross shape formed by the union of two perpendicular rectangles, with an optional rounding parameter.

## 2D SDF Modifiers Reference

### opRound2D — Rounding Modifier

**Signature**: `float opRound2D(float d, float r)`

Subtracts `r` from any SDF, effectively expanding the shape boundary outward by `r` and rounding all corners/edges. Apply to any existing SDF to add uniform rounding.

### opAnnular2D — Annular (Hollowing) Modifier

**Signature**: `float opAnnular2D(float d, float r)`

Takes the absolute value of the distance and subtracts thickness `r`, converting any filled shape into a ring/outline version with wall thickness `2*r`. Stackable: applying twice creates concentric rings.

### opRepeat2D — Grid Repetition

**Signature**: `vec2 opRepeat2D(vec2 p, float s)`

Applies `mod` to fold coordinates into a repeating grid cell of size `s`. Apply to `p` before passing to any SDF to create infinite tiling. Use `floor(p / s)` to obtain cell IDs for per-cell variation.

### opMirror2D — Arbitrary Mirror

**Signature**: `vec2 opMirror2D(vec2 p, vec2 dir)`

Mirrors coordinates across a line through the origin with direction `dir` (should be normalized). Any point on the negative side of the line is reflected to the positive side, effectively creating bilateral symmetry along any arbitrary axis.
