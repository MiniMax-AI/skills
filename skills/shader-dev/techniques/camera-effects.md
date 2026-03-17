# Camera & Lens Effects

## Use Cases
- Adding cinematic depth of field (bokeh blur)
- Motion blur for dynamic scenes
- Lens distortion and chromatic aberration
- Film grain and photographic realism

## Techniques

### 1. Depth of Field (Thin Lens Model)

Simulate camera aperture by jittering ray origins on a virtual lens disk:
```glsl
// For each sample:
vec2 lens = randomDisk(seed) * apertureSize;  // random point on aperture
vec3 focalPoint = ro + rd * focalDistance;     // point on focal plane
vec3 newRo = ro + cameraRight * lens.x + cameraUp * lens.y;  // offset origin
vec3 newRd = normalize(focalPoint - newRo);   // new ray toward focal point

// Accumulate multiple samples (16-64) for smooth bokeh
// Use with AA loop or temporal accumulation

// Disk sampling helper:
vec2 randomDisk(float seed) {
    float angle = hash11(seed) * 6.2831853;
    float radius = sqrt(hash11(seed + 1.0));
    return vec2(cos(angle), sin(angle)) * radius;
}
```

Parameters:
- `apertureSize`: 0.0 = pinhole (sharp), 0.1-0.5 = visible bokeh
- `focalDistance`: distance to the in-focus plane

### 2. Post-Process Depth of Field (Single Pass)

Cheaper approximation using depth buffer blur:
```glsl
vec3 dofPostProcess(sampler2D colorTex, sampler2D depthTex, vec2 uv) {
    float depth = texture(depthTex, uv).r;
    float coc = abs(depth - focalDepth) * apertureSize;  // circle of confusion
    coc = clamp(coc, 0.0, maxBlur);

    vec3 color = vec3(0.0);
    float total = 0.0;
    // 16-tap Poisson disk sampling
    for (int i = 0; i < 16; i++) {
        vec2 offset = poissonDisk[i] * coc / iResolution.xy;
        color += texture(colorTex, uv + offset).rgb;
        total += 1.0;
    }
    return color / total;
}
```

### 3. Motion Blur (Velocity-Based)

```glsl
// Simple radial motion blur (camera rotation)
vec3 motionBlur(vec2 uv, float amount) {
    vec3 color = vec3(0.0);
    vec2 center = vec2(0.5);
    int samples = 8;
    for (int i = 0; i < samples; i++) {
        float t = float(i) / float(samples - 1) - 0.5;
        vec2 sampleUV = mix(uv, center, t * amount);
        color += texture(iChannel0, sampleUV).rgb;
    }
    return color / float(samples);
}

// Time-based motion blur for ray marching
// Sample multiple time offsets within the frame:
// float t_shutter = iTime + (hash11(seed) - 0.5) * shutterSpeed;
// Use t_shutter instead of iTime for scene animation
```

### 4. Lens Distortion

```glsl
// Barrel/pincushion distortion
vec2 lensDistortion(vec2 uv, float k1, float k2) {
    vec2 centered = uv - 0.5;
    float r2 = dot(centered, centered);
    float distortion = 1.0 + k1 * r2 + k2 * r2 * r2;
    return centered * distortion + 0.5;
    // k1 > 0: pincushion, k1 < 0: barrel
}
```

### 5. Film Grain

```glsl
vec3 filmGrain(vec3 color, vec2 uv, float time, float intensity) {
    float grain = hash12(uv * iResolution.xy + fract(time) * 1000.0) - 0.5;
    // Apply more grain in darker areas (realistic film response)
    float luminance = dot(color, vec3(0.299, 0.587, 0.114));
    float grainAmount = intensity * (1.0 - luminance * 0.5);
    return color + grain * grainAmount;
}
```

### 6. Vignette

```glsl
vec3 vignette(vec3 color, vec2 uv, float intensity, float smoothness) {
    vec2 centered = uv - 0.5;
    float dist = length(centered);
    float vig = smoothstep(0.5, 0.5 - smoothness, dist);
    return color * mix(1.0 - intensity, 1.0, vig);
}
```

→ For deeper details, see [reference/camera-effects.md](../reference/camera-effects.md)
