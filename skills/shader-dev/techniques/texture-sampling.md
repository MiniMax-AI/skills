**IMPORTANT - GLSL Type Strictness**:
- GLSL is a strongly-typed language and does not support the `string` type (you cannot define `string var`)
- `vec2`/`vec3`/`vec4` are vector types and cannot be directly assigned a float (e.g., `vec2 a = 1.0` must be `vec2 a = vec2(1.0)`)
- Array indices must be integer constants or uniform variables; runtime-computed floats cannot be used
- Avoid uninitialized variables — GLSL default values are undefined

# Texture Sampling

## Use Cases

- **Post-processing effects**: Blur, bloom, dispersion, chromatic aberration
- **Procedural noise**: FBM layering from noise textures to generate terrain, clouds, fire
- **PBR/IBL**: Cubemap environment lighting, BRDF LUT lookup
- **Simulation/feedback systems**: Reaction-diffusion, fluid simulation multi-buffer feedback
- **Data storage**: Textures used as structured data (game state, keyboard input)
- **Temporal accumulation**: TAA, motion blur, previous frame reading

## Core Principles

| Function | Coordinate Type | Filtering | Typical Use |
|----------|----------------|-----------|-------------|
| `texture(sampler, uv)` | Float UV `[0,1]` | Hardware bilinear | General texture reading |
| `textureLod(sampler, uv, lod)` | Float UV + LOD | Specified mip level | Control blur level / avoid auto mip |
| `texelFetch(sampler, ivec2, lod)` | Integer pixel coordinates | No filtering | Exact pixel data reading |

Key mathematics:
1. **Hardware bilinear interpolation**: `texture()` automatically linearly blends between 4 adjacent texels
2. **Quintic Hermite smoothing**: `u = f^3(6f^2 - 15f + 10)`, C2 continuous (eliminates hardware linear interpolation seams)
3. **LOD control**: `textureLod` third parameter selects mipmap level, `lod=0` is original resolution, each +1 halves resolution
4. **Coordinate wrapping**: `fract(uv)` implements torus boundary, equivalent to `GL_REPEAT`

## Implementation Steps

### Step 1: Basic Sampling and UV Normalization

```glsl
vec2 uv = fragCoord / iResolution.xy;
vec4 col = texture(iChannel0, uv);
```

### Step 2: textureLod for Mipmap Control

```glsl
// In ray marching: force LOD 0 to avoid artifacts
vec3 groundCol = textureLod(iChannel2, groundUv * 0.05, 0.0).rgb;

// Depth of field blur: LOD varies with distance
float focus = mix(maxBlur - coverage, minBlur, smoothstep(.1, .2, coverage));
vec3 col = textureLod(iChannel0, uv + normal, focus).rgb;

// Bloom: sample high mip levels
#define BLOOM_LOD_A 4.0  // adjustable: bloom first mip level
#define BLOOM_LOD_B 5.0
#define BLOOM_LOD_C 6.0
vec3 bloom = vec3(0.0);
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_A), BLOOM_LOD_A).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_B), BLOOM_LOD_B).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_C), BLOOM_LOD_C).rgb;
bloom /= 3.0;
```

### Step 3: texelFetch for Exact Pixel Reading

```glsl
// Data storage addresses
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);

vec4 loadValue(in ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

void storeValue(in ivec2 addr, in vec4 val, inout vec4 fragColor, in ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Keyboard input
float key = texelFetch(iChannel1, ivec2(KEY_SPACE, 0), 0).x;
```

### Step 4: Manual Bilinear + Quintic Hermite Smoothing

```glsl
float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0); // C2 continuous

    #define TEX_RES 1024.0  // adjustable: noise texture resolution
    float a = texture(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES).x;
    float b = texture(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES).x;
    float c = texture(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES).x;
    float d = texture(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES).x;

    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}
```

### Step 5: FBM Texture Noise

```glsl
#define FBM_OCTAVES 5       // adjustable: number of layers
#define FBM_PERSISTENCE 0.5 // adjustable: amplitude decay rate

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    float totalWeight = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        totalWeight += a;
        x *= 2.0;
        a *= FBM_PERSISTENCE;
    }
    return v / totalWeight;
}
```

### Step 6: Separable Gaussian Blur

```glsl
#define BLUR_RADIUS 4  // adjustable: blur radius

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 d = vec2(1.0 / iResolution.x, 0.0); // horizontal pass; for vertical pass change to vec2(0, 1/iResolution.y)
    float w[9] = float[9](0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05);

    vec4 col = vec4(0.0);
    for (int i = -4; i <= 4; i++) {
        col += w[i + 4] * texture(iChannel0, fract(uv + float(i) * d));
    }
    col /= 0.98;
    fragColor = col;
}
```

### Step 7: Dispersion Sampling

```glsl
#define DISP_SAMPLES 64  // adjustable: sample count

vec3 sampleWeights(float i) {
    return vec3(i * i, 46.6666 * pow((1.0 - i) * i, 3.0), (1.0 - i) * (1.0 - i));
}

vec3 sampleDisp(sampler2D tex, vec2 uv, vec2 disp) {
    vec3 col = vec3(0.0);
    vec3 totalWeight = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = sampleWeights(t);
        col += w * texture(tex, fract(uv + disp * t)).rgb;
        totalWeight += w;
    }
    return col / totalWeight;
}
```

### Step 8: IBL Environment Sampling

```glsl
#define MAX_LOD 7.0     // adjustable: cubemap max mip level
#define DIFFUSE_LOD 6.5 // adjustable: diffuse sampling LOD

vec3 getSpecularLightColor(vec3 N, float roughness) {
    vec3 raw = textureLod(iChannel0, N, roughness * MAX_LOD).rgb;
    return pow(raw, vec3(4.5)) * 6.5; // HDR approximation
}

vec3 getDiffuseLightColor(vec3 N) {
    return textureLod(iChannel0, N, DIFFUSE_LOD).rgb;
}

// BRDF LUT lookup
vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
vec3 specular = envColor * (F * brdf.x + brdf.y);
```

## Complete Code Template

iChannel0 bound to a noise texture (e.g., "Gray Noise Medium"), with mipmap enabled.

```glsl
// === Texture Sampling Comprehensive Demo ===
// iChannel0: noise texture (requires mipmap enabled)

#define TEX_RES 256.0
#define FBM_OCTAVES 6
#define FBM_PERSISTENCE 0.5
#define CLOUD_LAYERS 4
#define CLOUD_SPEED 0.02
#define DOF_MAX_BLUR 5.0
#define DOF_FOCUS_DIST 0.5
#define BLOOM_STRENGTH 0.3
#define BLOOM_LOD 4.0

float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);

    float a = textureLod(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES, 0.0).x;
    float b = textureLod(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES, 0.0).x;
    float c = textureLod(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES, 0.0).x;
    float d = textureLod(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES, 0.0).x;

    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    float w = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        w += a;
        x *= 2.0;
        a *= FBM_PERSISTENCE;
    }
    return v / w;
}

float cloudLayer(vec2 uv, float height, float time) {
    vec2 offset = vec2(time * CLOUD_SPEED * (1.0 + height), 0.0);
    float n = fbm((uv + offset) * (2.0 + height * 3.0));
    return smoothstep(0.4, 0.7, n);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float aspect = iResolution.x / iResolution.y;

    // 1. Procedural sky
    vec3 sky = mix(vec3(0.1, 0.15, 0.4), vec3(0.5, 0.7, 1.0), uv.y);

    // 2. FBM cloud layers
    vec3 col = sky;
    for (int i = 0; i < CLOUD_LAYERS; i++) {
        float h = float(i) / float(CLOUD_LAYERS);
        float density = cloudLayer(vec2(uv.x * aspect, uv.y), h, iTime);
        vec3 cloudCol = mix(vec3(0.8, 0.85, 0.9), vec3(1.0), h);
        col = mix(col, cloudCol, density * (0.3 + 0.7 * h));
    }

    // 3. textureLod depth of field blur
    float dist = abs(uv.y - DOF_FOCUS_DIST);
    float lod = dist * DOF_MAX_BLUR;
    vec3 blurred = textureLod(iChannel0, uv, lod).rgb;
    col = mix(col, blurred * 0.5 + col * 0.5, 0.3);

    // 4. Bloom
    vec3 bloom = textureLod(iChannel0, uv, BLOOM_LOD).rgb;
    bloom += textureLod(iChannel0, uv, BLOOM_LOD + 1.0).rgb;
    bloom += textureLod(iChannel0, uv, BLOOM_LOD + 2.0).rgb;
    bloom /= 3.0;
    col += bloom * BLOOM_STRENGTH;

    // 5. Post-processing
    col = (col * (6.2 * col + 0.5)) / (col * (6.2 * col + 1.7) + 0.06);
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.2);

    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Anisotropic Flow-Field Blur

```glsl
#define BLUR_ITERATIONS 32  // adjustable: number of samples along flow field
#define BLUR_STEP 0.008     // adjustable: UV offset per step

vec3 flowBlur(vec2 uv) {
    vec3 col = vec3(0.0);
    float acc = 0.0;
    for (int i = 0; i < BLUR_ITERATIONS; i++) {
        float h = float(i) / float(BLUR_ITERATIONS);
        float w = 4.0 * h * (1.0 - h);
        col += w * texture(iChannel0, uv).rgb;
        acc += w;
        vec2 dir = texture(iChannel1, uv).xy * 2.0 - 1.0;
        uv += BLUR_STEP * dir;
    }
    return col / acc;
}
```

### Variant 2: Buffer-as-Data Storage

```glsl
const ivec2 txPosition = ivec2(0, 0);
const ivec2 txVelocity = ivec2(1, 0);
const ivec2 txState    = ivec2(2, 0);

vec4 load(ivec2 addr) { return texelFetch(iChannel0, addr, 0); }

void store(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 p = ivec2(fragCoord);
    fragColor = texelFetch(iChannel0, p, 0);
    vec4 pos = load(txPosition);
    vec4 vel = load(txVelocity);
    // ... update logic ...
    store(txPosition, pos + vel * 0.016, fragColor, p);
    store(txVelocity, vel, fragColor, p);
}
```

### Variant 3: Dispersion Effect

```glsl
#define DISP_SAMPLES 64     // adjustable: sample count
#define DISP_STRENGTH 0.05  // adjustable: dispersion strength

vec3 dispersion(vec2 uv, vec2 displacement) {
    vec3 col = vec3(0.0);
    vec3 w_total = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = vec3(t * t, 46.666 * pow((1.0 - t) * t, 3.0), (1.0 - t) * (1.0 - t));
        col += w * texture(iChannel0, fract(uv + displacement * t * DISP_STRENGTH)).rgb;
        w_total += w;
    }
    return col / w_total;
}
```

### Variant 4: Triplanar Texture Mapping

```glsl
#define TRIPLANAR_SHARPNESS 2.0  // adjustable: blend sharpness

vec3 triplanarSample(sampler2D tex, vec3 pos, vec3 normal, float scale) {
    vec3 w = pow(abs(normal), vec3(TRIPLANAR_SHARPNESS));
    w /= (w.x + w.y + w.z);
    vec3 xSample = texture(tex, pos.yz * scale).rgb;
    vec3 ySample = texture(tex, pos.xz * scale).rgb;
    vec3 zSample = texture(tex, pos.xy * scale).rgb;
    return xSample * w.x + ySample * w.y + zSample * w.z;
}
```

### Variant 5: Temporal Reprojection (TAA)

```glsl
#define TAA_BLEND 0.9  // adjustable: history frame blend ratio

vec3 temporalBlend(vec2 currUv, vec2 prevUv, vec3 currColor) {
    vec3 history = textureLod(iChannel0, prevUv, 0.0).rgb;
    vec3 minCol = currColor - 0.1;
    vec3 maxCol = currColor + 0.1;
    history = clamp(history, minCol, maxCol);
    return mix(currColor, history, TAA_BLEND);
}
```

## Performance & Composition

**Performance Tips**:
- Heavy sampling (e.g., 64 dispersion samples) is a bandwidth bottleneck — reduce sample count + use smart weight compensation; use `textureLod` with high LOD to reduce cache misses
- 2D Gaussian blur uses separable two-pass (O(N^2) -> O(2N)), leveraging hardware bilinear for (N+1)/2 samples to achieve N-tap
- Must use `textureLod(..., 0.0)` inside ray marching — the GPU cannot correctly estimate screen-space derivatives
- Manual Hermite interpolation is ~4x slower than hardware — only use for the first two FBM octaves, fall back to `texture()` for higher frequencies
- Each multi-buffer feedback adds one frame of latency — merge operations into the same pass; use `texelFetch` to avoid filtering overhead

**Composition Tips**:
- **+ SDF Ray Marching**: Noise textures for displacement maps/materials; use `textureLod(..., 0.0)` inside ray marching
- **+ Procedural Noise**: Hermite + FBM driving domain warping to generate terrain/clouds/fire; texture noise is faster than pure mathematical noise
- **+ Post-Processing Pipeline**: Multi-LOD bloom → separable DOF → dispersion → tone mapping, chaining a complete post-processing pipeline
- **+ PBR/IBL**: `textureLod` samples cubemap by roughness + BRDF LUT lookup = split-sum IBL
- **+ Simulation/Feedback**: Multi-buffer reaction-diffusion/fluid; Buffer A state, B/C separable blur diffusion, Image visualization; `fract()` torus boundary

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/texture-sampling.md)
