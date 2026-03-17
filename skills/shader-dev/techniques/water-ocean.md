# Water & Ocean Rendering Skill

## Use Cases
- Rendering water body surfaces such as oceans, lakes, and rivers
- Water surface reflection/refraction, Fresnel effects
- Underwater caustics lighting effects
- Waves, foam, and water flow animation

## Core Principles

Water rendering solves three problems: **water surface shape generation**, **light-water surface interaction**, and **water body color compositing**.

### Wave Generation: Exponential Sine Stacking + Derivative Domain Warping

`wave(x) = exp(sin(x) - 1)` — sharp wave crests (`exp(0)=1`), broad flat troughs (`exp(-2)≈0.135`), similar to a trochoidal profile but at much lower computational cost than Gerstner waves.

When stacking multiple waves, use **derivative domain warping (Drag)**:
```
position += direction * derivative * weight * DRAG_MULT
```
Small ripples cluster on the crests of large waves, simulating capillary waves riding on gravity waves.

### Lighting: Schlick Fresnel + Subsurface Scattering

- **Schlick Fresnel**: `F = F0 + (1-F0) * (1-dot(N,V))^5`, water F0 ≈ 0.04
- **SSS approximation**: thicker water layer at troughs → stronger blue-green scattering; thinner layer at crests → weaker scattering

### Water Surface Intersection: Bounded Height Field Marching

The water surface is constrained within a `[0, -WATER_DEPTH]` bounding box, with adaptive step size: `step = ray_y - wave_height`.

## Implementation Steps

### Step 1: Exponential Sine Wave Function
```glsl
// Single wave: exp(sin(x)-1) produces sharp peaks and broad troughs, returns (value, negative derivative)
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);
    float dx = wave * cos(x);
    return vec2(wave, -dx);
}
```

### Step 2: Multi-Octave Wave Stacking with Domain Warping
```glsl
#define DRAG_MULT 0.38  // Domain warp strength, 0=none, 0.5=strong clustering

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1;
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));  // Pseudo-random wave direction
        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * DRAG_MULT; // Derivative domain warp
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = mix(weight, 0.0, 0.2);      // Weight decay
        frequency *= 1.18;                     // Frequency growth rate
        timeMultiplier *= 1.07;                // Dispersion
        iter += 1232.399963;                   // Uniform direction distribution
    }
    return sumOfValues / sumOfWeights;
}
```

### Step 3: Bounded Bounding Box Ray Marching
```glsl
#define WATER_DEPTH 1.0

float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < 64; i++) {
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);      // Adaptive step size
    }
    return distance(start, camera);
}
```

### Step 4: Normal Calculation and Distance Smoothing
```glsl
#define ITERATIONS_RAYMARCH 12  // For marching (fewer = faster)
#define ITERATIONS_NORMAL 36    // For normals (more = finer detail)

vec3 calcNormal(vec2 pos, float e, float depth) {
    vec2 ex = vec2(e, 0);
    float H = getwaves(pos.xy, ITERATIONS_NORMAL) * depth;
    vec3 a = vec3(pos.x, H, pos.y);
    return normalize(
        cross(
            a - vec3(pos.x - e, getwaves(pos.xy - ex.xy, ITERATIONS_NORMAL) * depth, pos.y),
            a - vec3(pos.x, getwaves(pos.xy + ex.yx, ITERATIONS_NORMAL) * depth, pos.y + e)
        )
    );
}

// Distance smoothing: normals approach (0,1,0) at far distances
// N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```

### Step 5: Fresnel Reflection and Subsurface Scattering
```glsl
float fresnel = 0.04 + 0.96 * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

vec3 R = normalize(reflect(ray, N));
R.y = abs(R.y);  // Force upward to avoid self-intersection

vec3 reflection = getAtmosphere(R) + getSun(R);

vec3 scattering = vec3(0.0293, 0.0698, 0.1717) * 0.1
                * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

vec3 C = fresnel * reflection + scattering;
```

### Step 6: Atmosphere and Tone Mapping
```glsl
vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4),
                        special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002
                   * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0));
}

vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(
        0.59719, 0.07600, 0.02840,
        0.35458, 0.90834, 0.13383,
        0.04823, 0.01566, 0.83777);
    mat3 m2 = mat3(
        1.60475, -0.10208, -0.00327,
       -0.53108,  1.10813, -0.07276,
       -0.07367, -0.00605,  1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return pow(clamp(m2 * (a / b), 0.0, 1.0), vec3(1.0 / 2.2));
}
```

## Complete Code Template

Can be pasted directly into ShaderToy to run. Distilled from `afl_ext`'s "Very fast procedural ocean".

```glsl
// Water & Ocean Rendering — ShaderToy Template
// exp(sin) wave model + derivative domain warp + Schlick Fresnel + SSS

// ==================== Tunable Parameters ====================
#define DRAG_MULT 0.38
#define WATER_DEPTH 1.0
#define CAMERA_HEIGHT 1.5
#define ITERATIONS_RAYMARCH 12
#define ITERATIONS_NORMAL 36
#define RAYMARCH_STEPS 64
#define NORMAL_EPSILON 0.01
#define FRESNEL_F0 0.04
#define SSS_COLOR vec3(0.0293, 0.0698, 0.1717)
#define SSS_INTENSITY 0.1
#define SUN_POWER 720.0
#define SUN_BRIGHTNESS 210.0
#define EXPOSURE 2.0

// ==================== Wave Functions ====================
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);
    float dx = wave * cos(x);
    return vec2(wave, -dx);
}

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1;
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));
        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * DRAG_MULT;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = mix(weight, 0.0, 0.2);
        frequency *= 1.18;
        timeMultiplier *= 1.07;
        iter += 1232.399963;
    }
    return sumOfValues / sumOfWeights;
}

// ==================== Ray Marching ====================
float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < RAYMARCH_STEPS; i++) {
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);
    }
    return distance(start, camera);
}

// ==================== Normals ====================
vec3 calcNormal(vec2 pos, float e, float depth) {
    vec2 ex = vec2(e, 0);
    float H = getwaves(pos.xy, ITERATIONS_NORMAL) * depth;
    vec3 a = vec3(pos.x, H, pos.y);
    return normalize(
        cross(
            a - vec3(pos.x - e, getwaves(pos.xy - ex.xy, ITERATIONS_NORMAL) * depth, pos.y),
            a - vec3(pos.x, getwaves(pos.xy + ex.yx, ITERATIONS_NORMAL) * depth, pos.y + e)
        )
    );
}

// ==================== Camera ====================
#define NormalizedMouse (iMouse.xy / iResolution.xy)

mat3 createRotationMatrixAxisAngle(vec3 axis, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat3(
        oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s, oc * axis.z * axis.x + axis.y * s,
        oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,          oc * axis.y * axis.z - axis.x * s,
        oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s, oc * axis.z * axis.z + c
    );
}

vec3 getRay(vec2 fragCoord) {
    vec2 uv = ((fragCoord.xy / iResolution.xy) * 2.0 - 1.0) * vec2(iResolution.x / iResolution.y, 1.0);
    vec3 proj = normalize(vec3(uv.x, uv.y, 1.5));
    if (iResolution.x < 600.0) return proj;
    return createRotationMatrixAxisAngle(vec3(0.0, -1.0, 0.0), 3.0 * ((NormalizedMouse.x + 0.5) * 2.0 - 1.0))
         * createRotationMatrixAxisAngle(vec3(1.0, 0.0, 0.0), 0.5 + 1.5 * (((NormalizedMouse.y == 0.0 ? 0.27 : NormalizedMouse.y)) * 2.0 - 1.0))
         * proj;
}

// ==================== Atmosphere ====================
vec3 getSunDirection() {
    return normalize(vec3(-0.0773502691896258, 0.5 + sin(iTime * 0.2 + 2.6) * 0.45, 0.5773502691896258));
}

vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4), special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002 * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0));
}

vec3 getAtmosphere(vec3 dir) {
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;
}

float getSun(vec3 dir) {
    return pow(max(0.0, dot(dir, getSunDirection())), SUN_POWER) * SUN_BRIGHTNESS;
}

// ==================== Tone Mapping ====================
vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(
        0.59719, 0.07600, 0.02840,
        0.35458, 0.90834, 0.13383,
        0.04823, 0.01566, 0.83777);
    mat3 m2 = mat3(
        1.60475, -0.10208, -0.00327,
       -0.53108,  1.10813, -0.07276,
       -0.07367, -0.00605,  1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return pow(clamp(m2 * (a / b), 0.0, 1.0), vec3(1.0 / 2.2));
}

// ==================== Main Function ====================
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 ray = getRay(fragCoord);
    if (ray.y >= 0.0) {
        vec3 C = getAtmosphere(ray) + getSun(ray);
        fragColor = vec4(aces_tonemap(C * EXPOSURE), 1.0);
        return;
    }

    vec3 waterPlaneHigh = vec3(0.0, 0.0, 0.0);
    vec3 waterPlaneLow = vec3(0.0, -WATER_DEPTH, 0.0);
    vec3 origin = vec3(iTime * 0.2, CAMERA_HEIGHT, 1.0);

    float highPlaneHit = intersectPlane(origin, ray, waterPlaneHigh, vec3(0.0, 1.0, 0.0));
    float lowPlaneHit = intersectPlane(origin, ray, waterPlaneLow, vec3(0.0, 1.0, 0.0));
    vec3 highHitPos = origin + ray * highPlaneHit;
    vec3 lowHitPos = origin + ray * lowPlaneHit;

    float dist = raymarchwater(origin, highHitPos, lowHitPos, WATER_DEPTH);
    vec3 waterHitPos = origin + ray * dist;

    vec3 N = calcNormal(waterHitPos.xz, NORMAL_EPSILON, WATER_DEPTH);
    N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));

    float fresnel = FRESNEL_F0 + (1.0 - FRESNEL_F0) * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

    vec3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);
    vec3 reflection = getAtmosphere(R) + getSun(R);

    vec3 scattering = SSS_COLOR * SSS_INTENSITY
                    * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

    vec3 C = fresnel * reflection + scattering;
    fragColor = vec4(aces_tonemap(C * EXPOSURE), 1.0);
}
```

## Common Variants

### Variant 1: 2D Underwater Caustic Texture
```glsl
#define TAU 6.28318530718
#define MAX_ITER 5

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.5 + 23.0;
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec2 p = mod(uv * TAU, TAU) - 250.0;
    vec2 i = vec2(p);
    float c = 1.0;
    float inten = 0.005;

    for (int n = 0; n < MAX_ITER; n++) {
        float t = time * (1.0 - (3.5 / float(n + 1)));
        i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
        c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten), p.y / (cos(i.y + t) / inten)));
    }
    c /= float(MAX_ITER);
    c = 1.17 - pow(c, 1.4);
    vec3 colour = vec3(pow(abs(c), 8.0));
    colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0);
    fragColor = vec4(colour, 1.0);
}
```

### Variant 2: FBM Bump-Mapped Lake Surface
```glsl
float waterMap(vec2 pos) {
    mat2 m2 = mat2(0.60, -0.80, 0.80, 0.60);
    vec2 posm = pos * m2;
    return abs(fbm(vec3(8.0 * posm, iTime)) - 0.5) * 0.1;
}

// Analytic plane intersection instead of ray marching
float t = -ro.y / rd.y;
vec3 hitPos = ro + rd * t;

// Finite difference normals (central differencing)
float eps = 0.1;
vec3 normal = vec3(0.0, 1.0, 0.0);
normal.x = -bumpfactor * (waterMap(hitPos.xz + vec2(eps, 0.0)) - waterMap(hitPos.xz - vec2(eps, 0.0))) / (2.0 * eps);
normal.z = -bumpfactor * (waterMap(hitPos.xz + vec2(0.0, eps)) - waterMap(hitPos.xz - vec2(0.0, eps))) / (2.0 * eps);
normal = normalize(normal);

float bumpfactor = 0.1 * (1.0 - smoothstep(0.0, 60.0, distance(ro, hitPos)));
vec3 refracted = refract(rd, normal, 1.0 / 1.333);
```

### Variant 3: Ridge Noise Coastal Waves
```glsl
float sea(vec2 p) {
    float f = 1.0;
    float r = 0.0;
    float time = -iTime;
    for (int i = 0; i < 8; i++) {
        r += (1.0 - abs(noise(p * f + 0.9 * time))) / f;
        f *= 2.0;
        p -= vec2(-0.01, 0.04) * (r - 0.2 * time / (0.1 - f));
    }
    return r / 4.0 + 0.5;
}

// Shoreline foam
float dh = seaDist - rockDist;
float foam = 0.0;
if (dh < 0.0 && dh > -0.02) {
    foam = 0.5 * exp(20.0 * dh);
}
```

### Variant 4: Flow Map Water Animation
```glsl
vec3 FBM_DXY(vec2 p, vec2 flow, float persistence, float domainWarp) {
    vec3 f = vec3(0.0);
    float tot = 0.0;
    float a = 1.0;
    for (int i = 0; i < 4; i++) {
        p += flow;
        flow *= -0.75;
        vec3 v = SmoothNoise_DXY(p);
        f += v * a;
        p += v.xy * domainWarp;
        p *= 2.0;
        tot += a;
        a *= persistence;
    }
    return f / tot;
}

// Two-phase flow cycle (eliminates stretching)
float t0 = fract(time);
float t1 = fract(time + 0.5);
vec4 sample0 = SampleWaterNormal(uv + Hash2(floor(time)),     flowRate * (t0 - 0.5));
vec4 sample1 = SampleWaterNormal(uv + Hash2(floor(time+0.5)), flowRate * (t1 - 0.5));
float weight = abs(t0 - 0.5) * 2.0;
vec4 result = mix(sample0, sample1, weight);
```

### Variant 5: Beer's Law Water Absorption
```glsl
vec3 GetWaterExtinction(float dist) {
    float fOpticalDepth = dist * 6.0;
    vec3 vExtinctCol = vec3(0.5, 0.6, 0.9);
    return exp2(-fOpticalDepth * vExtinctCol);
}

vec3 vInscatter = vSurfaceDiffuse * (1.0 - exp(-refractDist * 0.1))
               * (1.0 + dot(sunDir, viewDir));

vec3 underwaterColor = terrainColor * GetWaterExtinction(waterDepth) + vInscatter;
vec3 finalColor = mix(underwaterColor, reflectionColor, fresnel);
```

## Performance & Composition

### Performance Tips
- **Dual iteration count strategy**: 12 iterations for marching, 36 for normals — halves render time with virtually no visual loss
- **Distance-adaptive normal smoothing**: `N = mix(N, up, 0.8 * min(1.0, sqrt(dist*0.01)*1.1))`, eliminates distant flickering
- **Bounding box clipping**: pre-compute upper/lower plane intersections, early-out for sky directions
- **Adaptive step size**: `pos += dir * (pos.y - height)`, 3-5x faster than fixed steps
- **Filter-width-aware decay**: `dFdx/dFdy` driven normal LOD
- **LOD conditional detail**: only compute high-frequency displacement at close range

### Composition Tips
- **Volumetric clouds**: ray march clouds along reflection direction `R`, blend into reflection term
- **Terrain coastline**: `dh = waterSDF - terrainSDF`, render foam when `dh ≈ 0`
- **Caustics overlay**: project Variant 1 onto underwater terrain, `caustic * exp(-depth * absorption)` depth attenuation
- **Fog/atmosphere**: independent extinction + in-scatter, per-channel RGB decay:
  ```glsl
  vec3 fogExtinction = exp2(fogExtCoeffs * -distance);
  vec3 fogInscatter = fogColor * (1.0 - exp2(fogInCoeffs * -distance));
  finalColor = finalColor * fogExtinction + fogInscatter;
  ```
- **Post-processing**: Bloom (Fibonacci spiral blur), ACES tone mapping, depth of field (DOF)

## Further Reading

For full step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/water-ocean.md)
