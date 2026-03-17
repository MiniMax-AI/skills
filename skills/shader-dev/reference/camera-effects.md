# Camera Effects Detailed Reference

## Prerequisites
- Ray marching fundamentals (ray origin, ray direction)
- Multipass buffers (for accumulation-based DoF)
- Hash functions for stochastic sampling

## Thin Lens Model Derivation

A real camera lens focuses light from a focal plane onto the sensor. Points not on the focal plane project to a **circle of confusion (CoC)** on the sensor.

### Circle of Confusion Formula
```
CoC = |S2 - S1| × A × f / (S1 × (S2 - f))
```
Where:
- `S1` = focal distance (distance to in-focus plane)
- `S2` = object distance
- `A` = aperture diameter
- `f` = focal length

### Simplified for Shaders
```
CoC ≈ apertureSize × |depth - focalDistance| / depth
```

### Ray-Based Implementation
Instead of computing CoC per pixel, we model the physical process:
1. Choose a random point on the aperture disk → new ray origin
2. The focal point (where the original ray hits the focal plane) stays fixed
3. New ray direction = `normalize(focalPoint - newOrigin)`
4. Average many such samples → natural bokeh with correct occlusion

### Aperture Shape
- Circular: `vec2 p = sqrt(r) * vec2(cos(a), sin(a))` — uniform disk
- Polygonal: reject samples outside polygon for hexagonal/octagonal bokeh
- The `sqrt(r)` is critical for uniform distribution (area-preserving)

## Poisson Disk Sampling

Pre-computed 16-point Poisson disk for blur kernels:
```glsl
const vec2 poissonDisk[16] = vec2[](
    vec2(-0.94201624, -0.39906216), vec2(0.94558609, -0.76890725),
    vec2(-0.09418410, -0.92938870), vec2(0.34495938,  0.29387760),
    vec2(-0.91588581,  0.45771432), vec2(-0.81544232, -0.87912464),
    vec2(-0.38277543,  0.27676845), vec2(0.97484398,  0.75648379),
    vec2(0.44323325, -0.97511554),  vec2(0.53742981, -0.47373420),
    vec2(-0.26496911, -0.41893023), vec2(0.79197514,  0.19090188),
    vec2(-0.24188840,  0.99706507), vec2(-0.81409955,  0.91437590),
    vec2(0.19984126,  0.78641367),  vec2(0.14383161, -0.14100790)
);
```

Advantages over regular grid: no structured aliasing patterns, better coverage per sample count.

## Motion Blur Approaches

### Stochastic Time Sampling (Ray Marching)
For each pixel, pick a random time within the shutter interval:
```
t_sample = iTime + (rand - 0.5) * shutterDuration
```
Use `t_sample` for all scene animation. Accumulate multiple frames for convergence.

### Velocity Buffer (Post-Process)
1. Render scene + store per-pixel velocity vectors
2. For each pixel, sample along the velocity direction
3. Weight samples by distance from center (triangle filter)

### Hybrid
Use temporal accumulation (TAA-style) with per-frame time jitter — converges over frames with no per-frame cost increase.

## Film Grain Characteristics

Real film grain properties:
- **Luminance-dependent**: More visible in shadows, less in highlights
- **Temporally varying**: Different pattern each frame (use `fract(iTime)` in hash seed)
- **Spatially uncorrelated**: Use pixel coordinates in hash, not UV (grain should be screen-resolution)
- **Intensity**: 0.02-0.05 for subtle, 0.1+ for stylized/vintage look
