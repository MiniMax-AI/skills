# Anti-Aliasing Detailed Reference

## Prerequisites
- Understanding of screen-space derivatives (`dFdx`, `dFdy`, `fwidth`)
- Multipass buffer setup (for TAA)
- Basic signal processing concepts

## Sampling Theory (Nyquist)

The **Nyquist-Shannon theorem** states: to accurately represent a signal, sampling rate must be ≥ 2× the highest frequency present. In shader terms:
- Pixel grid = sampling rate
- Procedural detail / edge sharpness = signal frequency
- When detail frequency > pixel frequency → aliasing (moiré, crawling edges)

**Solutions**: either increase sampling rate (SSAA) or reduce signal frequency (analytical AA, filtering).

## SSAA Implementation Details

### Jitter Patterns
- **Grid**: `offset = vec2(m, n) / AA - 0.5` — simple, uniform coverage
- **Rotated grid (RGSS)**: 4 samples at rotated positions — better edge coverage for near-horizontal/vertical lines
- **Halton sequence**: quasi-random low-discrepancy — best coverage for high sample counts

### Performance
AA=2 (4 samples) is the practical limit for real-time SDF scenes. AA=3 (9 samples) for offline/screenshot quality only.

## SDF Analytical AA Deep Dive

### Why `fwidth` Works

`fwidth(d) = abs(dFdx(d)) + abs(dFdy(d))` approximates how much the SDF value changes across one pixel. Using this as the smoothstep width:
- Edge transition spans exactly ~1 pixel regardless of zoom level
- No texture sampling needed — purely analytical
- Works for any SDF shape

### Signed Distance to Coverage

For a 2D SDF with value `d` at a pixel center:
```
coverage ≈ clamp(0.5 - d / fwidth(d), 0.0, 1.0)
```
This maps the signed distance to an approximate pixel coverage, equivalent to a box filter over the pixel footprint.

## TAA with Neighborhood Clamping

Full TAA pipeline:
1. **Jitter**: offset pixel center by Halton(2,3) sequence each frame
2. **Render**: full scene at jittered position → Buffer A
3. **Reproject**: use motion vectors to find previous frame's pixel for current position
4. **Clamp**: restrict history color to the min/max of current frame's 3×3 neighborhood (prevents ghosting)
5. **Blend**: `output = mix(current, clampedHistory, 0.9)`

### Neighborhood Clamping
```glsl
vec3 minCol = vec3(1e10), maxCol = vec3(-1e10);
for (int x = -1; x <= 1; x++)
for (int y = -1; y <= 1; y++) {
    vec3 s = texelFetch(currentBuffer, ivec2(fragCoord) + ivec2(x,y), 0).rgb;
    minCol = min(minCol, s);
    maxCol = max(maxCol, s);
}
vec3 clampedHistory = clamp(history, minCol, maxCol);
```

## FXAA Algorithm Walkthrough

1. **Luma computation**: Convert 5 samples (center + NSEW) to luminance
2. **Edge detection**: `lumaRange = lumaMax - lumaMin` — skip if below threshold
3. **Edge orientation**: Compare horizontal vs vertical luma gradients to determine edge direction
4. **Sub-pixel blending**: Sample along the edge direction at 1/3 and 2/3 offsets
5. **Quality**: The simplified version uses 2 taps; full FXAA 3.11 uses up to 12 taps along the edge for better endpoint detection
