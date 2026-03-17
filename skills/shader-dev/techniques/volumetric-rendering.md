# Volumetric Rendering Skill

## Use Cases
- Rendering participating media: clouds, fog, smoke, fire, explosions, atmospheric scattering
- Visual effects of light passing through and scattering/absorbing within semi-transparent volumes
- Suitable for ShaderToy real-time fragment shaders, also portable to game engines

## Core Principles

Advance along each view ray at fixed or adaptive step sizes (Ray Marching), querying medium density at each sample point, accumulating color and opacity.

### Key Formulas

**Beer-Lambert transmittance**: `T = exp(-σe × d)`, where `σe = σs + σa`

**Front-to-back alpha compositing (premultiplied form)**:
```glsl
col.rgb *= col.a;
sum += col * (1.0 - sum.a);
```

**Henyey-Greenstein phase function**: `HG(cosθ, g) = (1 - g²) / (1 + g² - 2g·cosθ)^(3/2)`
- `g > 0` forward scattering, `g < 0` back scattering, `g = 0` isotropic

**Frostbite improved integration**: `Sint = (S - S × exp(-σe × dt)) / σe`

## Implementation Steps

### Step 1: Camera and Ray Construction
```glsl
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
vec3 ro = vec3(0.0, 1.0, -5.0);  // Camera position
vec3 ta = vec3(0.0, 0.0, 0.0);   // Look-at target
vec3 ww = normalize(ta - ro);
vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
vec3 vv = cross(uu, ww);
float fl = 1.5; // Focal length
vec3 rd = normalize(uv.x * uu + uv.y * vv + fl * ww);
```

### Step 2: Volume Bounds Intersection
```glsl
// Method A: Horizontal plane bounds (cloud layers)
float tmin = (yBottom - ro.y) / rd.y;
float tmax = (yTop    - ro.y) / rd.y;
if (tmin > tmax) { float tmp = tmin; tmin = tmax; tmax = tmp; }

// Method B: Sphere bounds (explosions, atmosphere)
vec2 intersectSphere(vec3 ro, vec3 rd, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5);
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```

### Step 3: Density Field Definition
```glsl
// 3D Value Noise (texture-based)
float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    vec2 uv = (p.xy + vec2(37.0, 239.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

// fBM
float fbm(vec3 p) {
    float f = 0.0;
    f += 0.50000 * noise(p); p *= 2.02;
    f += 0.25000 * noise(p); p *= 2.03;
    f += 0.12500 * noise(p); p *= 2.01;
    f += 0.06250 * noise(p); p *= 2.02;
    f += 0.03125 * noise(p);
    return f;
}

// Cloud density
float cloudDensity(vec3 p) {
    vec3 q = p - vec3(0.0, 0.1, 1.0) * iTime;
    float f = fbm(q);
    return clamp(1.5 - p.y - 2.0 + 1.75 * f, 0.0, 1.0);
}
```

### Step 4: Ray Marching Main Loop
```glsl
#define NUM_STEPS 64
#define STEP_SIZE 0.05

vec4 raymarch(vec3 ro, vec3 rd, float tmin, float tmax, vec3 bgCol) {
    vec4 sum = vec4(0.0);
    // Dither start position to eliminate banding artifacts
    float t = tmin + STEP_SIZE * fract(sin(dot(fragCoord, vec2(12.9898, 78.233))) * 43758.5453);

    for (int i = 0; i < NUM_STEPS; i++) {
        if (t > tmax || sum.a > 0.99) break;
        vec3 pos = ro + t * rd;
        float den = cloudDensity(pos);
        if (den > 0.01) {
            vec4 col = vec4(1.0, 0.95, 0.8, den);
            col.a *= 0.4;
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);
        }
        t += STEP_SIZE;
    }
    return clamp(sum, 0.0, 1.0);
}
```

### Step 5: Lighting Calculation
```glsl
// Method A: Directional derivative lighting (1 extra sample)
vec3 sundir = normalize(vec3(1.0, 0.0, -1.0));
float dif = clamp((den - cloudDensity(pos + 0.3 * sundir)) / 0.6, 0.0, 1.0);
vec3 lin = vec3(1.0, 0.6, 0.3) * dif + vec3(0.91, 0.98, 1.05);

// Method B: Volumetric shadow (secondary ray march)
float volumetricShadow(vec3 from, vec3 lightDir) {
    float shadow = 1.0, dt = 0.5, d = dt * 0.5;
    for (int s = 0; s < 6; s++) {
        shadow *= exp(-cloudDensity(from + lightDir * d) * dt);
        dt *= 1.3; d += dt;
    }
    return shadow;
}

// Method C: HG phase function mixed scattering
float HenyeyGreenstein(float cosTheta, float g) {
    float gg = g * g;
    return (1.0 - gg) / pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
}
float scattering = mix(
    HenyeyGreenstein(dot(rd, -sundir), 0.8),
    HenyeyGreenstein(dot(rd, -sundir), -0.2),
    0.5
);
```

### Step 6: Color Mapping
```glsl
// Method A: Density-interpolated coloring (clouds)
vec3 cloudColor = mix(vec3(1.0, 0.95, 0.8), vec3(0.25, 0.3, 0.35), den);

// Method B: Radial gradient coloring (explosions, fire)
vec3 computeColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8), vec3(0.4, 0.15, 0.1), density);
    result *= mix(7.0 * vec3(0.8, 1.0, 1.0), 1.5 * vec3(0.48, 0.53, 0.5), min(radius / 0.9, 1.15));
    return result;
}

// Method C: Height-based ambient light gradient
vec3 ambientLight = mix(
    vec3(39., 67., 87.) * (1.5 / 255.),
    vec3(149., 167., 200.) * (1.5 / 255.),
    normalizedHeight
);
```

### Step 7: Final Compositing and Post-Processing
```glsl
// Sky background
vec3 bgCol = vec3(0.6, 0.71, 0.75) - rd.y * 0.2 * vec3(1.0, 0.5, 1.0);
float sun = clamp(dot(sundir, rd), 0.0, 1.0);
bgCol += 0.2 * vec3(1.0, 0.6, 0.1) * pow(sun, 8.0);

// Compositing
vec4 vol = raymarch(ro, rd, tmin, tmax, bgCol);
vec3 col = bgCol * (1.0 - vol.a) + vol.rgb;
col += vec3(0.2, 0.08, 0.04) * pow(sun, 3.0); // Sun glare
col = smoothstep(0.15, 1.1, col);               // Tone mapping
```

## Complete Code Template

Runnable volumetric cloud renderer for ShaderToy (iChannel0 = Gray Noise Small 256x256):

```glsl
// Volumetric Cloud Renderer — ShaderToy Template

#define NUM_STEPS 80
#define SUN_DIR normalize(vec3(-0.7, 0.0, -0.7))
#define CLOUD_BOTTOM -1.0
#define CLOUD_TOP     2.0
#define WIND_SPEED 0.1
#define DENSITY_SCALE 1.75
#define DENSITY_THRESHOLD 0.01

float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    vec2 uv = (p.xy + vec2(37.0, 239.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z) * 2.0 - 1.0;
}

float map(vec3 p, int lod) {
    vec3 q = p - vec3(0.0, WIND_SPEED, 1.0) * iTime;
    float f;
    f  = 0.50000 * noise(q); q *= 2.02;
    if (lod >= 2)
    f += 0.25000 * noise(q); q *= 2.03;
    if (lod >= 3)
    f += 0.12500 * noise(q); q *= 2.01;
    if (lod >= 4)
    f += 0.06250 * noise(q); q *= 2.02;
    if (lod >= 5)
    f += 0.03125 * noise(q);
    return clamp(1.5 - p.y - 2.0 + DENSITY_SCALE * f, 0.0, 1.0);
}

vec3 lightSample(vec3 pos, float den, int lod) {
    float dif = clamp((den - map(pos + 0.3 * SUN_DIR, lod)) / 0.6, 0.0, 1.0);
    vec3 lin = vec3(1.0, 0.6, 0.3) * dif + vec3(0.91, 0.98, 1.05);
    vec3 col = mix(vec3(1.0, 0.95, 0.8), vec3(0.25, 0.3, 0.35), den);
    return col * lin;
}

vec4 raymarch(vec3 ro, vec3 rd, vec3 bgcol, ivec2 px) {
    float tmin = (CLOUD_BOTTOM - ro.y) / rd.y;
    float tmax = (CLOUD_TOP - ro.y) / rd.y;
    if (tmin > tmax) { float tmp = tmin; tmin = tmax; tmax = tmp; }
    if (tmax < 0.0) return vec4(0.0);
    tmin = max(tmin, 0.0);
    tmax = min(tmax, 60.0);

    float t = tmin + 0.1 * fract(sin(float(px.x * 73 + px.y * 311)) * 43758.5453);
    vec4 sum = vec4(0.0);

    for (int i = 0; i < NUM_STEPS; i++) {
        float dt = max(0.05, 0.02 * t);
        int lod = 5 - int(log2(1.0 + t * 0.5));
        vec3 pos = ro + t * rd;
        float den = map(pos, lod);

        if (den > DENSITY_THRESHOLD) {
            vec3 litCol = lightSample(pos, den, lod);
            litCol = mix(litCol, bgcol, 1.0 - exp(-0.003 * t * t));
            vec4 col = vec4(litCol, den);
            col.a *= 0.4;
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);
        }

        t += dt;
        if (t > tmax || sum.a > 0.99) break;
    }
    return clamp(sum, 0.0, 1.0);
}

mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = normalize(cross(cu, cw));
    return mat3(cu, cv, cw);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    vec2 m = iMouse.xy / iResolution.xy;

    vec3 ro = 4.0 * normalize(vec3(sin(3.0 * m.x), 0.8 * m.y, cos(3.0 * m.x)));
    ro.y += 0.5;
    vec3 ta = vec3(0.0, -1.0, 0.0);
    mat3 ca = setCamera(ro, ta, 0.07 * cos(0.25 * iTime));
    vec3 rd = ca * normalize(vec3(p, 1.5));

    float sun = clamp(dot(SUN_DIR, rd), 0.0, 1.0);
    vec3 bgcol = vec3(0.6, 0.71, 0.75) - rd.y * 0.2 * vec3(1.0, 0.5, 1.0) + 0.075;
    bgcol += 0.2 * vec3(1.0, 0.6, 0.1) * pow(sun, 8.0);

    vec4 res = raymarch(ro, rd, bgcol, ivec2(fragCoord - 0.5));
    vec3 col = bgcol * (1.0 - res.a) + res.rgb;
    col += vec3(0.2, 0.08, 0.04) * pow(sun, 3.0);
    col = smoothstep(0.15, 1.1, col);

    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Self-Emissive Volume (Fire/Explosions)
```glsl
vec3 emissionColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8), vec3(0.4, 0.15, 0.1), density);
    vec3 colCenter = 7.0 * vec3(0.8, 1.0, 1.0);
    vec3 colEdge = 1.5 * vec3(0.48, 0.53, 0.5);
    result *= mix(colCenter, colEdge, min(radius / 0.9, 1.15));
    return result;
}
// Bloom effect
sum.rgb += lightColor / exp(lDist * lDist * lDist * 0.08) / 30.0;
```

### Variant 2: Physical Scattering Atmosphere (Rayleigh + Mie)
```glsl
float density(vec3 p, float scaleHeight) {
    return exp(-max(length(p) - R_INNER, 0.0) / scaleHeight);
}
float opticDepth(vec3 from, vec3 to, float scaleHeight) {
    vec3 s = (to - from) / float(NUM_STEPS_LIGHT);
    vec3 v = from + s * 0.5;
    float sum = 0.0;
    for (int i = 0; i < NUM_STEPS_LIGHT; i++) { sum += density(v, scaleHeight); v += s; }
    return sum * length(s);
}
float phaseRayleigh(float cc) { return (3.0 / 16.0 / PI) * (1.0 + cc); }
vec3 scatter = sumRay * kRay * phaseRayleigh(cc) + sumMie * kMie * phaseMie(-0.78, c, cc);
```

### Variant 3: Frostbite Energy-Conserving Integration
```glsl
vec3 S = evaluateLight(p) * sigmaS * phaseFunction() * volumetricShadow(p, lightPos);
vec3 Sint = (S - S * exp(-sigmaE * dt)) / sigmaE;
scatteredLight += transmittance * Sint;
transmittance *= exp(-sigmaE * dt);
```

### Variant 4: Production-Grade Clouds (Horizon Zero Dawn Style)
```glsl
float m = cloudMapBase(pos, norY);
m *= cloudGradient(norY);
m -= cloudMapDetail(pos) * dstrength * 0.225;
m = smoothstep(0.0, 0.1, m + (COVERAGE - 1.0));
float scattering = mix(HenyeyGreenstein(sundotrd, 0.8), HenyeyGreenstein(sundotrd, -0.2), 0.5);
// Temporal reprojection
vec2 spos = reprojectPos(ro + rd * dist, iResolution.xy, iChannel1);
col = mix(texture(iChannel1, spos, 0.0), col, 0.05);
```

### Variant 5: Gradient Normal Surface Lighting (Fur Ball / Volume Surface)
```glsl
vec3 furNormal(vec3 pos, float density) {
    float eps = 0.01;
    vec3 n;
    n.x = sampleDensity(pos + vec3(eps, 0, 0)) - density;
    n.y = sampleDensity(pos + vec3(0, eps, 0)) - density;
    n.z = sampleDensity(pos + vec3(0, 0, eps)) - density;
    return normalize(n);
}
vec3 N = -furNormal(pos, density);
float diff = max(0.0, dot(N, L) * 0.5 + 0.5);  // Half-Lambert
float spec = pow(max(0.0, dot(N, H)), 50.0);     // Blinn-Phong
```

## Performance & Composition

### Performance Tips
- **Early exit**: break out of loop when `sum.a > 0.99`
- **LOD noise**: `int lod = 5 - int(log2(1.0 + t * 0.5));` reduce fBM octaves at distance
- **Adaptive step size**: `float dt = max(0.05, 0.02 * t);` fine near, coarse far
- **Dithering**: add pixel-dependent random offset to start position, eliminates banding artifacts
- **Bounds clipping**: only march within the ray-volume intersection interval
- **Density threshold skip**: only compute lighting when `den > 0.01`
- **Minimal shadow steps**: 6-16 steps with increasing step size
- **Temporal reprojection**: blend history frames (e.g., 5% new frame + 95% history frame)

### Composition Tips
- **SDF terrain + volumetric clouds**: mutual depth occlusion (Himalayas style)
- **Volumetric fog + scene lighting**: `color = color * transmittance + scatteredLight`
- **Multi-layer volumes**: different density functions at different heights, march independently then composite
- **Post-process light shafts (God Rays)**: radial blur or screen-space ray marching
- **Procedural sky + volumetric clouds**: distance fogging for natural transitions

## Further Reading

For full step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/volumetric-rendering.md)
