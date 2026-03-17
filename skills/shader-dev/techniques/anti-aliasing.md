# Anti-Aliasing Techniques

## Use Cases
- Eliminating jagged edges (staircase artifacts) in ray-marched or SDF-rendered scenes
- Smooth 2D SDF shape rendering
- Post-process edge smoothing for any shader output
- Temporal smoothing for noise reduction

## Core Principles

Anti-aliasing in shaders differs from rasterization pipelines. Without hardware MSAA on procedural geometry, we rely on analytical or post-process approaches.

## Techniques

### 1. Supersampling (SSAA) for Ray Marching

Render multiple sub-pixel samples and average:
```glsl
#define AA 2  // 1=off, 2=4x, 3=9x
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 totalColor = vec3(0.0);
    for (int m = 0; m < AA; m++)
    for (int n = 0; n < AA; n++) {
        vec2 offset = vec2(float(m), float(n)) / float(AA) - 0.5;
        vec2 uv = (2.0 * (fragCoord + offset) - iResolution.xy) / iResolution.y;
        vec3 col = render(uv);
        totalColor += col;
    }
    fragColor = vec4(totalColor / float(AA * AA), 1.0);
}
```
Cost: AA^2 × full render. Use AA=2 for quality, AA=1 for development.

### 2. SDF Analytical Anti-Aliasing

For 2D SDF shapes, use pixel width to compute smooth edges:
```glsl
float d = sdShape(uv);
float fw = fwidth(d);  // screen-space derivative of SDF
float alpha = smoothstep(fw, -fw, d);  // smooth edge over exactly 1 pixel

// Alternative: manual pixel width for more control
float pixelWidth = 2.0 / iResolution.y;  // approximate pixel size in UV space
float alpha2 = smoothstep(pixelWidth, -pixelWidth, d);
```

For 3D SDF scenes, apply anti-aliasing at the edge of geometry:
```glsl
// After ray marching, at the surface:
float edgeFade = 1.0 - smoothstep(0.0, 0.01 * t, lastSdfValue);
// t = ray distance — scales threshold with distance for consistent edge width
```

### 3. Temporal Anti-Aliasing (TAA) Basics

Blend current frame with previous frame using a multipass buffer:
```glsl
// Buffer A: render with sub-pixel jitter
vec2 jitter = (hash22(vec2(iFrame)) - 0.5) / iResolution.xy;
vec2 uv = (fragCoord + jitter) / iResolution.xy;
vec3 currentColor = render(uv);

// Buffer A output: store current render
fragColor = vec4(currentColor, 1.0);

// Image shader: blend with history
vec3 current = texture(iChannel0, fragCoord / iResolution.xy).rgb;  // this frame
vec3 history = texture(iChannel1, fragCoord / iResolution.xy).rgb;  // previous frame
float blend = 0.9;  // higher = smoother but more ghosting
fragColor = vec4(mix(current, history, blend), 1.0);
```
Note: Full TAA also needs motion vectors and neighborhood clamping to avoid ghosting.

### 4. FXAA (Fast Approximate Anti-Aliasing)

Simplified post-process edge detection and smoothing:
```glsl
vec3 fxaa(sampler2D tex, vec2 uv, vec2 texelSize) {
    // Sample center and 4 neighbors
    vec3 rgbM = texture(tex, uv).rgb;
    vec3 rgbN = texture(tex, uv + vec2(0.0, texelSize.y)).rgb;
    vec3 rgbS = texture(tex, uv - vec2(0.0, texelSize.y)).rgb;
    vec3 rgbE = texture(tex, uv + vec2(texelSize.x, 0.0)).rgb;
    vec3 rgbW = texture(tex, uv - vec2(texelSize.x, 0.0)).rgb;

    // Luma for edge detection
    vec3 lumaCoeff = vec3(0.299, 0.587, 0.114);
    float lumaN = dot(rgbN, lumaCoeff);
    float lumaS = dot(rgbS, lumaCoeff);
    float lumaE = dot(rgbE, lumaCoeff);
    float lumaW = dot(rgbW, lumaCoeff);
    float lumaM = dot(rgbM, lumaCoeff);

    float lumaMin = min(lumaM, min(min(lumaN, lumaS), min(lumaE, lumaW)));
    float lumaMax = max(lumaM, max(max(lumaN, lumaS), max(lumaE, lumaW)));
    float lumaRange = lumaMax - lumaMin;

    // Skip if edge contrast is low
    if (lumaRange < max(0.0312, lumaMax * 0.125)) return rgbM;

    // Blend along edge direction
    vec2 dir;
    dir.x = -((lumaN + lumaS) - 2.0 * lumaM);
    dir.y = ((lumaE + lumaW) - 2.0 * lumaM);
    float dirReduce = max(lumaRange * 0.25, 1.0 / 128.0);
    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = clamp(dir * rcpDirMin, -8.0, 8.0) * texelSize;

    vec3 rgbA = 0.5 * (texture(tex, uv + dir * (1.0/3.0 - 0.5)).rgb +
                        texture(tex, uv + dir * (2.0/3.0 - 0.5)).rgb);
    return rgbA;
}
```

## Choosing the Right Approach

| Method | Cost | Quality | Best For |
|--------|------|---------|----------|
| SSAA 2x2 | 4× render | Excellent | Final quality renders |
| SDF analytical | Minimal | Great for SDF | 2D shapes, UI elements |
| TAA | 1× + blend | Good + temporal | Animated scenes with multipass |
| FXAA | 1 pass post | Good | Any scene, post-process only |

→ For deeper details, see [reference/anti-aliasing.md](../reference/anti-aliasing.md)
