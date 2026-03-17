# 2D SDF Rendering Skill

## Use Cases

- 2D shape rendering: circles, rectangles, triangles, ellipses, line segments, Bezier curves, etc.
- UI elements and icons: drawn with math functions, naturally resolution-independent
- Anti-aliased graphics, shape boolean operations, outlines and glow
- Motion graphics and animation, 2D soft shadows and lighting

## Core Principles

For each pixel, compute the signed distance `d` to the shape boundary: `d < 0` inside, `d = 0` boundary, `d > 0` outside.

Map to color via `smoothstep`/`clamp`:
- **Fill**: color when `d < 0`
- **Anti-aliasing**: `smoothstep(-aa, aa, d)`
- **Stroke**: apply smoothstep to `abs(d) - strokeWidth`
- **Boolean operations**: `min(d1, d2)` union, `max(d1, d2)` intersection, `max(-d1, d2)` subtraction

Key formulas:
```
Circle:       d = length(p - center) - radius
Rectangle:    d = length(max(abs(p) - halfSize, 0.0)) + min(max(abs(p).x - halfSize.x, abs(p).y - halfSize.y), 0.0)
Line segment: d = length(p - a - clamp(dot(p-a, b-a)/dot(b-a, b-a), 0, 1) * (b-a)) - width/2
Smooth union: d = mix(d2, d1, h) - k*h*(1-h),  h = clamp(0.5 + 0.5*(d2-d1)/k, 0, 1)
```

## Implementation Steps

### Step 1: Coordinate Normalization

```glsl
// Origin at center, y range [-1, 1] (standard approach)
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Pixel space (suitable for fixed pixel-size UI)
vec2 p = fragCoord.xy;
vec2 center = iResolution.xy * 0.5;

// [0, 1] range (requires manual aspect ratio handling)
vec2 uv = fragCoord.xy / iResolution.xy;
```

### Step 2: SDF Primitive Functions

```glsl
float sdCircle(vec2 p, float radius) {
    return length(p) - radius;
}

// halfSize is half-width/half-height, radius is corner rounding
float sdBox(vec2 p, vec2 halfSize, float radius) {
    halfSize -= vec2(radius);
    vec2 d = abs(p) - halfSize;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - radius;
}

float sdLine(vec2 p, vec2 start, vec2 end, float width) {
    vec2 dir = end - start;
    float h = clamp(dot(p - start, dir) / dot(dir, dir), 0.0, 1.0);
    return length(p - start - dir * h) - width * 0.5;
}

// Exact signed distance, requires only one sqrt
float sdTriangle(vec2 p, vec2 p0, vec2 p1, vec2 p2) {
    vec2 e0 = p1 - p0, v0 = p - p0;
    vec2 e1 = p2 - p1, v1 = p - p1;
    vec2 e2 = p0 - p2, v2 = p - p2;
    float d0 = dot(v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0),
                   v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0));
    float d1 = dot(v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0),
                   v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0));
    float d2 = dot(v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0),
                   v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0));
    float o = e0.x * e2.y - e0.y * e2.x;
    vec2 d = min(min(vec2(d0, o * (v0.x * e0.y - v0.y * e0.x)),
                     vec2(d1, o * (v1.x * e1.y - v1.y * e1.x))),
                     vec2(d2, o * (v2.x * e2.y - v2.y * e2.x)));
    return -sqrt(d.x) * sign(d.y);
}

// Approximate ellipse SDF
float sdEllipse(vec2 p, vec2 center, float a, float b) {
    float a2 = a * a, b2 = b * b;
    vec2 d = p - center;
    return (b2 * d.x * d.x + a2 * d.y * d.y - a2 * b2) / (a2 * b2);
}
```

### Step 3: CSG Boolean Operations

```glsl
float opUnion(float d1, float d2) { return min(d1, d2); }
float opIntersect(float d1, float d2) { return max(d1, d2); }
float opSubtract(float d1, float d2) { return max(-d1, d2); }
float opXor(float d1, float d2) { return min(max(-d1, d2), max(-d2, d1)); }

// k controls transition width
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}
```

### Step 4: Coordinate Transforms

```glsl
vec2 translate(vec2 p, vec2 t) { return p - t; }

vec2 rotateCCW(vec2 p, float angle) {
    mat2 m = mat2(cos(angle), sin(angle), -sin(angle), cos(angle));
    return p * m;
}

// Usage: translate first, then rotate
float d = sdBox(rotateCCW(translate(p, vec2(0.5, 0.3)), iTime), vec2(0.2), 0.05);
```

### Step 5: Rendering and Anti-Aliasing

```glsl
// smoothstep anti-aliasing (recommended)
float px = 2.0 / iResolution.y;
float mask = smoothstep(px, -px, d);  // 1.0 inside, 0.0 outside
vec3 col = mix(backgroundColor, shapeColor, mask);

// fwidth adaptive anti-aliasing (suitable for scaled scenes)
float anti = fwidth(d) * 1.0;
float mask = 1.0 - smoothstep(-anti, anti, d);

// Classic distance field debug visualization
vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3) : vec3(0.65, 0.85, 1.0);
col *= 1.0 - exp(-12.0 * abs(d));
col *= 0.8 + 0.2 * cos(120.0 * d);
col = mix(col, vec3(1.0), smoothstep(1.5*px, 0.0, abs(d) - 0.002));
```

### Step 6: Stroke and Border

```glsl
// Fill + stroke rendering (fwidth adaptive)
vec4 renderShape(float d, vec3 color, float stroke) {
    float anti = fwidth(d) * 1.0;
    vec4 strokeLayer = vec4(vec3(0.05), 1.0 - smoothstep(-anti, anti, d - stroke));
    vec4 colorLayer  = vec4(color,      1.0 - smoothstep(-anti, anti, d));
    if (stroke < 0.0001) return colorLayer;
    return vec4(mix(strokeLayer.rgb, colorLayer.rgb, colorLayer.a), strokeLayer.a);
}

float fillMask(float d) { return clamp(-d, 0.0, 1.0); }
float innerBorderMask(float d, float width) {
    return clamp(d + width, 0.0, 1.0) - clamp(d, 0.0, 1.0);
}
float outerBorderMask(float d, float width) {
    return clamp(d, 0.0, 1.0) - clamp(d - width, 0.0, 1.0);
}
```

### Step 7: Multi-Layer Compositing

```glsl
vec3 bgColor = vec3(1.0, 0.8, 0.7 - 0.07 * p.y) * (1.0 - 0.25 * length(p));

float d1 = sdCircle(translate(p, pos1), 0.3);
vec4 layer1 = renderShape(d1, vec3(0.9, 0.3, 0.2), 0.02);

float d2 = sdBox(translate(p, pos2), vec2(0.2), 0.05);
vec4 layer2 = renderShape(d2, vec3(0.2, 0.5, 0.8), 0.0);

// Composite back to front
vec3 col = bgColor;
col = mix(col, layer1.rgb, layer1.a);
col = mix(col, layer2.rgb, layer2.a);
fragColor = vec4(col, 1.0);
```

## Full Code Template

```glsl
// ===== 2D SDF Full Template (runs directly in ShaderToy) =====

#define AA_WIDTH 1.0           // Anti-aliasing width factor
#define STROKE_WIDTH 0.015     // Stroke width
#define SMOOTH_K 0.05          // Smooth union transition width
#define CONTOUR_FREQ 80.0      // Contour line frequency (for debugging)
#define ANIM_SPEED 1.0         // Animation speed multiplier

// --- SDF Primitives ---
float sdCircle(vec2 p, float r) { return length(p) - r; }

float sdBox(vec2 p, vec2 b, float r) {
    b -= vec2(r);
    vec2 d = abs(p) - b;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - r;
}

float sdLine(vec2 p, vec2 a, vec2 b, float w) {
    vec2 d = b - a;
    float h = clamp(dot(p - a, d) / dot(d, d), 0.0, 1.0);
    return length(p - a - d * h) - w * 0.5;
}

float sdTriangle(vec2 p, vec2 p0, vec2 p1, vec2 p2) {
    vec2 e0 = p1 - p0, v0 = p - p0;
    vec2 e1 = p2 - p1, v1 = p - p1;
    vec2 e2 = p0 - p2, v2 = p - p2;
    float d0 = dot(v0 - e0 * clamp(dot(v0,e0)/dot(e0,e0),0.0,1.0),
                   v0 - e0 * clamp(dot(v0,e0)/dot(e0,e0),0.0,1.0));
    float d1 = dot(v1 - e1 * clamp(dot(v1,e1)/dot(e1,e1),0.0,1.0),
                   v1 - e1 * clamp(dot(v1,e1)/dot(e1,e1),0.0,1.0));
    float d2 = dot(v2 - e2 * clamp(dot(v2,e2)/dot(e2,e2),0.0,1.0),
                   v2 - e2 * clamp(dot(v2,e2)/dot(e2,e2),0.0,1.0));
    float o = e0.x*e2.y - e0.y*e2.x;
    vec2 dd = min(min(vec2(d0, o*(v0.x*e0.y-v0.y*e0.x)),
                      vec2(d1, o*(v1.x*e1.y-v1.y*e1.x))),
                      vec2(d2, o*(v2.x*e2.y-v2.y*e2.x)));
    return -sqrt(dd.x) * sign(dd.y);
}

// --- CSG ---
float opUnion(float a, float b) { return min(a, b); }
float opSubtract(float a, float b) { return max(-a, b); }
float opIntersect(float a, float b) { return max(a, b); }
float opSmoothUnion(float a, float b, float k) {
    float h = clamp(0.5 + 0.5*(b - a)/k, 0.0, 1.0);
    return mix(b, a, h) - k*h*(1.0-h);
}
float opXor(float a, float b) { return min(max(-a, b), max(-b, a)); }

// --- Coordinate Transforms ---
vec2 translate(vec2 p, vec2 t) { return p - t; }
vec2 rotateCCW(vec2 p, float a) {
    return mat2(cos(a), sin(a), -sin(a), cos(a)) * p;
}

// --- Rendering Utilities ---
vec4 render(float d, vec3 color, float stroke) {
    float anti = fwidth(d) * AA_WIDTH;
    vec4 strokeLayer = vec4(vec3(0.05), 1.0 - smoothstep(-anti, anti, d - stroke));
    vec4 colorLayer  = vec4(color,      1.0 - smoothstep(-anti, anti, d));
    if (stroke < 0.0001) return colorLayer;
    return vec4(mix(strokeLayer.rgb, colorLayer.rgb, colorLayer.a), strokeLayer.a);
}

float fillAA(float d, float px) { return smoothstep(px, -px, d); }

// --- Scene ---
float sceneDist(vec2 p) {
    float t = iTime * ANIM_SPEED;
    float c = sdCircle(translate(p, vec2(-0.6, 0.3)), 0.25);
    float b = sdBox(translate(p, vec2(0.0, 0.3)), vec2(0.25, 0.18), 0.05);
    vec2 tp = rotateCCW(translate(p, vec2(0.6, 0.3)), t * 0.5);
    float tr = sdTriangle(tp, vec2(0.0, 0.25), vec2(-0.22, -0.12), vec2(0.22, -0.12));
    float row1 = opUnion(c, opUnion(b, tr));

    float c2 = sdCircle(translate(p, vec2(-0.5, -0.35)), 0.2);
    float b2 = sdBox(translate(p, vec2(-0.3, -0.35)), vec2(0.15, 0.15), 0.0);
    float smooth_demo = opSmoothUnion(c2, b2, SMOOTH_K);

    float c3 = sdCircle(translate(p, vec2(0.15, -0.35)), 0.22);
    float b3 = sdBox(translate(p, vec2(0.15, -0.35 + sin(t) * 0.15)), vec2(0.3, 0.08), 0.0);
    float sub_demo = opSubtract(b3, c3);

    float c4 = sdCircle(translate(p, vec2(0.65, -0.35)), 0.2);
    float b4 = sdBox(translate(p, vec2(0.65, -0.35 + sin(t + 1.0) * 0.15)), vec2(0.3, 0.08), 0.0);
    float xor_demo = opXor(b4, c4);

    float row2 = opUnion(smooth_demo, opUnion(sub_demo, xor_demo));
    return opUnion(row1, row2);
}

// --- Main Function ---
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    float px = 2.0 / iResolution.y;
    float d = sceneDist(p);

    vec3 bgCol = vec3(0.15, 0.15, 0.18) + 0.05 * p.y;
    bgCol *= 1.0 - 0.3 * length(p);

    vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3) : vec3(0.4, 0.7, 1.0);
    col *= 1.0 - exp(-10.0 * abs(d));
    col *= 0.8 + 0.2 * cos(CONTOUR_FREQ * d);
    col = mix(col, vec3(1.0), smoothstep(1.5 * px, 0.0, abs(d) - 0.002));
    col = mix(bgCol, col, 0.85);

    // Uncomment to switch to solid rendering mode:
    // vec3 shapeCol = vec3(0.2, 0.8, 0.6);
    // float mask = fillAA(d, px);
    // col = mix(bgCol, shapeCol, mask);

    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Solid Fill + Stroke Mode

```glsl
vec3 shapeColor = vec3(0.32, 0.56, 0.53);
float strokeW = 0.015;
vec4 shape = render(d, shapeColor, strokeW);
vec3 col = bgCol;
col = mix(col, shape.rgb, shape.a);
```

### Variant 2: Multi-Layer CSG Illustration

```glsl
float a = sdEllipse(p, vec2(0.0, 0.16), 0.25, 0.25);
float b = sdEllipse(p, vec2(0.0, -0.03), 0.8, 0.35);
float body = opIntersect(a, b);
vec4 layer1 = render(body, vec3(0.32, 0.56, 0.53), fwidth(body) * 2.0);

float handle = sdLine(p, vec2(0.0, 0.05), vec2(0.0, -0.42), 0.01);
float arc = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.04);
float arcInner = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.03);
handle = opUnion(handle, opSubtract(arcInner, arc));
vec4 layer0 = render(handle, vec3(0.4, 0.3, 0.28), STROKE_WIDTH);

vec3 col = bgCol;
col = mix(col, layer0.rgb, layer0.a);
col = mix(col, layer1.rgb, layer1.a);
```

### Variant 3: Hexagonal Grid Tiling

```glsl
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

#define HEX_SCALE 8.0
vec4 h = hexagon(HEX_SCALE * p + 0.5 * iTime);
vec3 col = 0.15 + 0.15 * hash1(h.xy + 1.2);
col *= smoothstep(0.10, 0.11, h.z);
col *= smoothstep(0.10, 0.11, h.w);
```

### Variant 4: Organic Shapes (Polar SDF)

```glsl
// Heart SDF
p.y -= 0.25;
float a = atan(p.x, p.y) / 3.141593;
float r = length(p);
float h = abs(a);
float d = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);

// Pulse animation
float tt = mod(iTime, 1.5) / 1.5;
float ss = pow(tt, 0.2) * 0.5 + 0.5;
ss = 1.0 + ss * 0.5 * sin(tt * 6.2831 * 3.0) * exp(-tt * 4.0);
vec3 col = mix(bgCol, heartCol, smoothstep(-0.01, 0.01, d - r));
```

### Variant 5: Bezier Curve SDF

```glsl
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

float sdBezier(vec2 A, vec2 B, vec2 C, vec2 p) {
    B = mix(B + vec2(1e-4), B, step(1e-6, abs(B*2.0-A-C)));
    vec2 a = B-A, b = A-B*2.0+C, c = a*2.0, d = A-p;
    vec3 k = vec3(3.*dot(a,b), 2.*dot(a,a)+dot(d,b), dot(d,a)) / dot(b,b);
    vec3 t = clamp(solveCubic(k.x, k.y, k.z), 0.0, 1.0);
    vec2 pos = A+(c+b*t.x)*t.x; float dis = length(pos-p);
    pos = A+(c+b*t.y)*t.y; dis = min(dis, length(pos-p));
    pos = A+(c+b*t.z)*t.z; dis = min(dis, length(pos-p));
    return dis * signBezier(A, B, C, p);
}
```

## Extended 2D SDF Library

```glsl
// === Extended 2D SDF Library ===

// Rounded Box with independent corner radii (vec4 r = top-right, bottom-right, top-left, bottom-left)
float sdRoundedBox(vec2 p, vec2 b, vec4 r) {
    r.xy = (p.x > 0.0) ? r.xy : r.zw;
    r.x  = (p.y > 0.0) ? r.x  : r.y;
    vec2 q = abs(p) - b + r.x;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r.x;
}

// Oriented Box (from point a to point b with thickness th)
float sdOrientedBox(vec2 p, vec2 a, vec2 b, float th) {
    float l = length(b - a);
    vec2 d = (b - a) / l;
    vec2 q = (p - (a + b) * 0.5);
    q = mat2(d.x, -d.y, d.y, d.x) * q;
    q = abs(q) - vec2(l, th) * 0.5;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
}

// Arc (sc = vec2(sin,cos) of aperture angle, ra = radius, rb = thickness)
float sdArc(vec2 p, vec2 sc, float ra, float rb) {
    p.x = abs(p.x);
    return ((sc.y * p.x > sc.x * p.y) ? length(p - sc * ra) : abs(length(p) - ra)) - rb;
}

// Pie / Sector (c = vec2(sin,cos) of aperture angle)
float sdPie(vec2 p, vec2 c, float r) {
    p.x = abs(p.x);
    float l = length(p) - r;
    float m = length(p - c * clamp(dot(p, c), 0.0, r));
    return max(l, m * sign(c.y * p.x - c.x * p.y));
}

// Ring (n = vec2(sin,cos) of aperture, r = radius, th = thickness)
float sdRing(vec2 p, vec2 n, float r, float th) {
    p.x = abs(p.x);
    float d = length(p);
    // If within aperture angle
    if (n.y * p.x > n.x * p.y) {
        return abs(d - r) - th;
    }
    // Cap endpoints
    return min(length(p - n * r), length(p + n * r)) - th;
}

// Moon shape
float sdMoon(vec2 p, float d, float ra, float rb) {
    p.y = abs(p.y);
    float a = (ra * ra - rb * rb + d * d) / (2.0 * d);
    float b2 = ra * ra - a * a;
    if (d * (p.x * rb * rb - p.y * a * rb * rb - a * b2) > 0.0)
        return length(p - vec2(a, sqrt(max(b2, 0.0))));
    return max(length(p) - ra, -(length(p - vec2(d, 0.0)) - rb));
}

// Heart (approximate)
float sdHeart(vec2 p) {
    p.x = abs(p.x);
    if (p.y + p.x > 1.0)
        return sqrt(dot(p - vec2(0.25, 0.75), p - vec2(0.25, 0.75))) - sqrt(2.0) / 4.0;
    return sqrt(min(dot(p - vec2(0.0, 1.0), p - vec2(0.0, 1.0)),
                    dot(p - 0.5 * max(p.x + p.y, 0.0), p - 0.5 * max(p.x + p.y, 0.0)))) *
           sign(p.x - p.y);
}

// Vesica (lens shape)
float sdVesica(vec2 p, float w, float h) {
    p = abs(p);
    float b = sqrt(h * h + w * w * 0.25) / w;
    return ((p.y - h) * b * w > p.x * b * h)
        ? length(p - vec2(0.0, h))
        : length(p - vec2(-w * 0.5, 0.0)) - b;
}

// Egg shape
float sdEgg(vec2 p, float he, float ra, float rb) {
    p.x = abs(p.x);
    float r = (p.y < 0.0) ? ra : rb;
    return length(vec2(p.x, p.y - clamp(p.y, -he, he))) - r;
}

// Equilateral Triangle
float sdEquilateralTriangle(vec2 p, float r) {
    const float k = sqrt(3.0);
    p.x = abs(p.x) - r;
    p.y = p.y + r / k;
    if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
    p.x -= clamp(p.x, -2.0 * r, 0.0);
    return -length(p) * sign(p.y);
}

// Pentagon
float sdPentagon(vec2 p, float r) {
    const vec3 k = vec3(0.809016994, 0.587785252, 0.726542528);
    p.x = abs(p.x);
    p -= 2.0 * min(dot(vec2(-k.x, k.y), p), 0.0) * vec2(-k.x, k.y);
    p -= 2.0 * min(dot(vec2(k.x, k.y), p), 0.0) * vec2(k.x, k.y);
    p -= vec2(clamp(p.x, -r * k.z, r * k.z), r);
    return length(p) * sign(p.y);
}

// Hexagon
float sdHexagon(vec2 p, float r) {
    const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
    p = abs(p);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

// Octagon
float sdOctagon(vec2 p, float r) {
    const vec3 k = vec3(-0.9238795325, 0.3826834323, 0.4142135623);
    p = abs(p);
    p -= 2.0 * min(dot(vec2(k.x, k.y), p), 0.0) * vec2(k.x, k.y);
    p -= 2.0 * min(dot(vec2(-k.x, k.y), p), 0.0) * vec2(-k.x, k.y);
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

// Star (n-pointed, m = inner radius ratio)
float sdStar(vec2 p, float r, int n, float m) {
    float an = 3.141593 / float(n);
    float en = 3.141593 / m;
    vec2 acs = vec2(cos(an), sin(an));
    vec2 ecs = vec2(cos(en), sin(en));
    float bn = mod(atan(p.x, p.y), 2.0 * an) - an;
    p = length(p) * vec2(cos(bn), abs(sin(bn)));
    p -= r * acs;
    p += ecs * clamp(-dot(p, ecs), 0.0, r * acs.y / ecs.y);
    return length(p) * sign(p.x);
}

// Quadratic Bezier curve SDF
float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C) {
    vec2 a = B - A;
    vec2 b = A - 2.0 * B + C;
    vec2 c = a * 2.0;
    vec2 d = A - pos;
    float kk = 1.0 / dot(b, b);
    float kx = kk * dot(a, b);
    float ky = kk * (2.0 * dot(a, a) + dot(d, b)) / 3.0;
    float kz = kk * dot(d, a);
    float res = 0.0;
    float p2 = ky - kx * kx;
    float q = kx * (2.0 * kx * kx - 3.0 * ky) + kz;
    float h = q * q + 4.0 * p2 * p2 * p2;
    if (h >= 0.0) {
        h = sqrt(h);
        vec2 x = (vec2(h, -h) - q) / 2.0;
        vec2 uv2 = sign(x) * pow(abs(x), vec2(1.0 / 3.0));
        float t = clamp(uv2.x + uv2.y - kx, 0.0, 1.0);
        res = dot(d + (c + b * t) * t, d + (c + b * t) * t);
    } else {
        float z = sqrt(-p2);
        float v = acos(q / (p2 * z * 2.0)) / 3.0;
        float m2 = cos(v);
        float n2 = sin(v) * 1.732050808;
        vec3 t = clamp(vec3(m2 + m2, -n2 - m2, n2 - m2) * z - kx, 0.0, 1.0);
        res = min(dot(d + (c + b * t.x) * t.x, d + (c + b * t.x) * t.x),
                  dot(d + (c + b * t.y) * t.y, d + (c + b * t.y) * t.y));
    }
    return sqrt(res);
}

// Parabola
float sdParabola(vec2 pos, float k) {
    pos.x = abs(pos.x);
    float ik = 1.0 / k;
    float p2 = ik * (pos.y - 0.5 * ik) / 3.0;
    float q = 0.25 * ik * ik * pos.x;
    float h = q * q - p2 * p2 * p2;
    float r = sqrt(abs(h));
    float x = (h > 0.0) ?
        pow(q + r, 1.0 / 3.0) + pow(abs(q - r), 1.0 / 3.0) * sign(p2) :
        2.0 * cos(atan(r, q) / 3.0) * sqrt(p2);
    return length(pos - vec2(x, k * x * x)) * sign(pos.x - x);
}

// Cross shape
float sdCross(vec2 p, vec2 b, float r) {
    p = abs(p); p = (p.y > p.x) ? p.yx : p.xy;
    vec2 q = p - b;
    float k = max(q.y, q.x);
    vec2 w = (k > 0.0) ? q : vec2(b.y - p.x, -k);
    return sign(k) * length(max(w, 0.0)) + r;
}
```

## 2D SDF Modifiers

```glsl
// === 2D SDF Modifiers ===

// Round any 2D SDF
float opRound2D(float d, float r) { return d - r; }

// Create annular (ring) version of any 2D SDF
float opAnnular2D(float d, float r) { return abs(d) - r; }

// Repeat a 2D SDF in a grid
vec2 opRepeat2D(vec2 p, float s) { return mod(p + s * 0.5, s) - s * 0.5; }

// Mirror across arbitrary 2D direction
vec2 opMirror2D(vec2 p, vec2 dir) {
    return p - 2.0 * dir * max(dot(p, dir), 0.0);
}
```

## Performance & Composition Tips

**Performance:**
- In polygon SDFs, compare squared distances first; use a single `sqrt` at the end
- For simple scenes, use fixed `px = 2.0/iResolution.y` instead of `fwidth(d)`; use `fwidth` when coordinate scaling is involved
- For many primitives, spatially partition and skip distant ones early
- Supersampling (2x2/3x3) only for offline rendering; for real-time, single-pixel AA with `smoothstep`/`fwidth` is sufficient
- For 2D soft shadow marching, use adaptive step size `dt += max(1.0, abs(sd))`

**Composition:**
- **SDF + Noise**: `d += noise(p * 10.0 + iTime) * 0.05` to create organic edges
- **SDF + 2D Lighting**: cone marching for soft shadows, query occlusion via `sceneDist()`
- **SDF + Normal Mapping**: finite differences for normals + Blinn-Phong lighting to simulate bump effects
- **SDF + Domain Repetition**: `fract`/`mod` for infinite repetition, `floor` for cell ID
- **SDF + Animation**: parameters driven by `sin/cos` periodic motion, `exp` decay, `mod` looping

## Further Reading

Full step-by-step tutorials, mathematical derivations, and advanced usage in [reference](../reference/sdf-2d.md)
