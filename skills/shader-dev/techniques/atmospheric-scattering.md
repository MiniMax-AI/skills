# Atmospheric & Subsurface Scattering

## Use Cases
- Sky rendering (sunrise/sunset/noon/night)
- Aerial perspective
- Sun halo (Mie scattering haze)
- Planetary atmosphere rim glow
- Translucent material SSS (candles, skin, jelly)
- Volumetric light (God rays)

## Core Principles

Three physical mechanisms:

**Rayleigh scattering** — molecular-scale particles, β_R(λ) ∝ 1/λ⁴, shorter wavelengths scatter more strongly (blue sky / red sunset).
Sea-level values: `vec3(5.5e-6, 13.0e-6, 22.4e-6)` m⁻¹.
Phase function: `P_R(θ) = 3/(16π) × (1 + cos²θ)`, symmetric forward-backward.

**Mie scattering** — aerosol particles, wavelength-independent, strong forward scattering (sun halo).
Sea-level value: `vec3(21e-6)` m⁻¹.
Phase function: Henyey-Greenstein, `g ≈ 0.76~0.88`.

**Beer-Lambert attenuation** — `T(A→B) = exp(-∫ σ_e(s) ds)`, exponential decay of light through a medium.

**Algorithm flow**: ray march along the view ray; at each sample point: compute density → compute optical depth toward the sun → Beer-Lambert attenuation → phase function weighting → accumulate.

## Implementation Steps

### Step 1: Ray-Sphere Intersection

```glsl
// Returns (t_near, t_far); no intersection when t_near > t_far
vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5);
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```

### Step 2: Atmospheric Physical Constants

```glsl
#define PLANET_RADIUS 6371e3
#define ATMOS_RADIUS  6471e3
#define PLANET_CENTER vec3(0.0)

#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6)  // Rayleigh scattering coefficients
#define BETA_MIE vec3(21e-6)                        // Mie scattering coefficients
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6) // Ozone absorption

#define MIE_G 0.76          // Anisotropy parameter 0.76~0.88
#define MIE_EXTINCTION 1.1  // Extinction/scattering ratio

#define H_RAY 8000.0        // Rayleigh scale height
#define H_MIE 1200.0        // Mie scale height
#define H_OZONE 30e3        // Ozone peak altitude
#define OZONE_FALLOFF 4e3   // Ozone decay width

#define PRIMARY_STEPS 32    // Primary ray steps 8(mobile)~64(high quality)
#define LIGHT_STEPS 8       // Light direction steps 4~16
```

### Step 3: Phase Functions

```glsl
float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * 3.14159265) * (1.0 + cosTheta * cosTheta);
}

// Henyey-Greenstein phase function
float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * 3.14159265) * num / denom;
}
```

### Step 4: Atmospheric Density Sampling

```glsl
// Returns vec3(rayleigh, mie, ozone) density
vec3 atmosphereDensity(vec3 pos, float planetRadius) {
    float height = length(pos) - planetRadius;
    float densityRay = exp(-height / H_RAY);
    float densityMie = exp(-height / H_MIE);
    float denom = (H_OZONE - height) / OZONE_FALLOFF;
    float densityOzone = (1.0 / (denom * denom + 1.0)) * densityRay;
    return vec3(densityRay, densityMie, densityOzone);
}
```

### Step 5: Light Direction Optical Depth

```glsl
vec3 lightOpticalDepth(vec3 pos, vec3 sunDir) {
    float atmoDist = raySphereIntersect(pos - PLANET_CENTER, sunDir, ATMOS_RADIUS).y;
    float stepSize = atmoDist / float(LIGHT_STEPS);
    float rayPos = stepSize * 0.5;
    vec3 optDepth = vec3(0.0);
    for (int i = 0; i < LIGHT_STEPS; i++) {
        vec3 samplePos = pos + sunDir * rayPos;
        float height = length(samplePos - PLANET_CENTER) - PLANET_RADIUS;
        if (height < 0.0) return vec3(1e10); // Occluded by planet
        optDepth += atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        rayPos += stepSize;
    }
    return optDepth;
}
```

### Step 6: Primary Scattering Integration

```glsl
vec3 calculateScattering(
    vec3 rayOrigin, vec3 rayDir, float maxDist,
    vec3 sunDir, vec3 sunIntensity
) {
    vec2 atmoHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, ATMOS_RADIUS);
    if (atmoHit.x > atmoHit.y) return vec3(0.0);

    vec2 planetHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, PLANET_RADIUS);

    float tStart = max(atmoHit.x, 0.0);
    float tEnd = atmoHit.y;
    if (planetHit.x > 0.0) tEnd = min(tEnd, planetHit.x);
    tEnd = min(tEnd, maxDist);

    float stepSize = (tEnd - tStart) / float(PRIMARY_STEPS);
    float cosTheta = dot(rayDir, sunDir);
    float phaseR = phaseRayleigh(cosTheta);
    float phaseM = phaseMie(cosTheta, MIE_G);

    vec3 totalRay = vec3(0.0), totalMie = vec3(0.0), optDepthI = vec3(0.0);
    float rayPos = tStart + stepSize * 0.5;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 samplePos = rayOrigin + rayDir * rayPos;
        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        optDepthI += density;

        vec3 optDepthL = lightOpticalDepth(samplePos, sunDir);
        vec3 tau = BETA_RAY * (optDepthI.x + optDepthL.x)
                 + BETA_MIE * 1.1 * (optDepthI.y + optDepthL.y)
                 + BETA_OZONE * (optDepthI.z + optDepthL.z);
        vec3 attenuation = exp(-tau);

        totalRay += density.x * attenuation;
        totalMie += density.y * attenuation;
        rayPos += stepSize;
    }

    return sunIntensity * (totalRay * BETA_RAY * phaseR + totalMie * BETA_MIE * phaseM);
}
```

### Step 7: Tone Mapping

```glsl
vec3 tonemapExposure(vec3 color) { return 1.0 - exp(-color); }

vec3 tonemapReinhard(vec3 color) {
    float l = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 tc = color / (color + 1.0);
    return mix(color / (l + 1.0), tc, tc);
}

vec3 gammaCorrect(vec3 color) { return pow(color, vec3(1.0 / 2.2)); }
```

## Complete Code Template

Fully runnable Rayleigh + Mie atmospheric scattering for ShaderToy:

```glsl
#define PI 3.14159265359

#define PLANET_RADIUS 6371e3
#define ATMOS_RADIUS  6471e3
#define PLANET_CENTER vec3(0.0)

#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6)
#define BETA_MIE vec3(21e-6)
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6)

#define MIE_G 0.76
#define MIE_EXTINCTION 1.1

#define H_RAY 8e3
#define H_MIE 1.2e3
#define H_OZONE 30e3
#define OZONE_FALLOFF 4e3

#define PRIMARY_STEPS 32
#define LIGHT_STEPS 8

#define SUN_INTENSITY vec3(40.0)

vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5);
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}

float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * PI) * (1.0 + cosTheta * cosTheta);
}

float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * PI) * num / denom;
}

vec3 atmosphereDensity(vec3 pos) {
    float height = length(pos - PLANET_CENTER) - PLANET_RADIUS;
    float dRay = exp(-height / H_RAY);
    float dMie = exp(-height / H_MIE);
    float dOzone = (1.0 / (pow((H_OZONE - height) / OZONE_FALLOFF, 2.0) + 1.0)) * dRay;
    return vec3(dRay, dMie, dOzone);
}

vec3 calculateScattering(
    vec3 start, vec3 dir, float maxDist,
    vec3 sceneColor, vec3 sunDir, vec3 sunIntensity
) {
    start -= PLANET_CENTER;

    float a = dot(dir, dir);
    float b = 2.0 * dot(dir, start);
    float c = dot(start, start) - ATMOS_RADIUS * ATMOS_RADIUS;
    float d = b * b - 4.0 * a * c;
    if (d < 0.0) return sceneColor;

    vec2 rayLen = vec2(
        max((-b - sqrt(d)) / (2.0 * a), 0.0),
        min((-b + sqrt(d)) / (2.0 * a), maxDist)
    );
    if (rayLen.x > rayLen.y) return sceneColor;

    bool allowMie = maxDist > rayLen.y;
    rayLen.y = min(rayLen.y, maxDist);
    rayLen.x = max(rayLen.x, 0.0);

    float stepSize = (rayLen.y - rayLen.x) / float(PRIMARY_STEPS);
    float rayPos = rayLen.x + stepSize * 0.5;

    vec3 totalRay = vec3(0.0);
    vec3 totalMie = vec3(0.0);
    vec3 optI = vec3(0.0);

    float mu = dot(dir, sunDir);
    float phaseR = phaseRayleigh(mu);
    float phaseM = allowMie ? phaseMie(mu, MIE_G) : 0.0;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 pos = start + dir * rayPos;
        float height = length(pos) - PLANET_RADIUS;

        vec3 density = vec3(exp(-height / H_RAY), exp(-height / H_MIE), 0.0);
        float dOzone = (H_OZONE - height) / OZONE_FALLOFF;
        density.z = (1.0 / (dOzone * dOzone + 1.0)) * density.x;
        density *= stepSize;
        optI += density;

        float la = dot(sunDir, sunDir);
        float lb = 2.0 * dot(sunDir, pos);
        float lc = dot(pos, pos) - ATMOS_RADIUS * ATMOS_RADIUS;
        float ld = lb * lb - 4.0 * la * lc;
        float lightStepSize = (-lb + sqrt(ld)) / (2.0 * la * float(LIGHT_STEPS));
        float lightPos = lightStepSize * 0.5;
        vec3 optL = vec3(0.0);

        for (int j = 0; j < LIGHT_STEPS; j++) {
            vec3 posL = pos + sunDir * lightPos;
            float heightL = length(posL) - PLANET_RADIUS;
            vec3 densityL = vec3(exp(-heightL / H_RAY), exp(-heightL / H_MIE), 0.0);
            float dOzoneL = (H_OZONE - heightL) / OZONE_FALLOFF;
            densityL.z = (1.0 / (dOzoneL * dOzoneL + 1.0)) * densityL.x;
            densityL *= lightStepSize;
            optL += densityL;
            lightPos += lightStepSize;
        }

        vec3 attn = exp(
            -BETA_RAY * (optI.x + optL.x)
            - BETA_MIE * MIE_EXTINCTION * (optI.y + optL.y)
            - BETA_OZONE * (optI.z + optL.z)
        );

        totalRay += density.x * attn;
        totalMie += density.y * attn;

        rayPos += stepSize;
    }

    vec3 opacity = exp(-(BETA_MIE * optI.y + BETA_RAY * optI.x + BETA_OZONE * optI.z));

    return (
        phaseR * BETA_RAY * totalRay +
        phaseM * BETA_MIE * totalMie
    ) * sunIntensity + sceneColor * opacity;
}

vec3 getCameraVector(vec3 resolution, vec2 coord) {
    vec2 uv = coord.xy / resolution.xy - vec2(0.5);
    uv.x *= resolution.x / resolution.y;
    return normalize(vec3(uv.x, uv.y, -1.0));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 rayDir = getCameraVector(iResolution, fragCoord);
    vec3 cameraPos = vec3(0.0, PLANET_RADIUS + 100.0, 0.0);
    vec3 sunDir = normalize(vec3(0.0, cos(-iTime / 8.0), sin(-iTime / 8.0)));

    vec4 scene = vec4(0.0, 0.0, 0.0, 1e12);
    vec3 sunDisk = vec3(dot(rayDir, sunDir) > 0.9998 ? 3.0 : 0.0);
    scene.xyz = sunDisk;

    vec2 groundHit = raySphereIntersect(cameraPos - PLANET_CENTER, rayDir, PLANET_RADIUS);
    if (groundHit.x > 0.0) {
        scene.w = groundHit.x;
        vec3 hitPos = cameraPos + rayDir * groundHit.x - PLANET_CENTER;
        vec3 normal = normalize(hitPos);
        float shadow = max(0.0, dot(normal, sunDir));
        scene.xyz = vec3(0.1, 0.15, 0.08) * shadow;
    }

    vec3 col = calculateScattering(
        cameraPos, rayDir, scene.w,
        scene.xyz, sunDir, SUN_INTENSITY
    );

    col = 1.0 - exp(-col);
    col = pow(col, vec3(1.0 / 2.2));

    fragColor = vec4(col, 1.0);
}
```

## Advanced Fog Models

Three progressive fog techniques, from simple to physically motivated. These can be used standalone or combined with the full atmospheric scattering above.

### Level 1: Basic Exponential Fog
```glsl
vec3 applyFog(vec3 col, float t) {
    float fogAmount = 1.0 - exp(-t * density);
    vec3 fogColor = vec3(0.5, 0.6, 0.7);
    return mix(col, fogColor, fogAmount);
}
```

### Level 2: Sun-Aware Fog (Scattering Tint)
Fog color shifts warm when looking toward the sun — creates a very natural light dispersion effect:
```glsl
vec3 applyFogSun(vec3 col, float t, vec3 rd, vec3 sunDir) {
    float fogAmount = 1.0 - exp(-t * density);
    float sunAmount = max(dot(rd, sunDir), 0.0);
    vec3 fogColor = mix(
        vec3(0.5, 0.6, 0.7),          // base fog (blue-grey)
        vec3(1.0, 0.9, 0.7),          // sun-facing fog (warm gold)
        pow(sunAmount, 8.0)
    );
    return mix(col, fogColor, fogAmount);
}
```

### Level 3: Height-Based Fog (Analytical Integration)
Density decreases exponentially with altitude: `d(y) = a * exp(-b * y)`. The formula is an exact analytical integral along the ray, not an approximation — fog pools in valleys and clears at altitude:
```glsl
vec3 applyFogHeight(vec3 col, float t, vec3 ro, vec3 rd) {
    float a = 0.5;    // density multiplier
    float b = 0.3;    // density falloff with height
    float fogAmount = (a / b) * exp(-ro.y * b) * (1.0 - exp(-t * rd.y * b)) / rd.y;
    fogAmount = clamp(fogAmount, 0.0, 1.0);
    vec3 fogColor = vec3(0.5, 0.6, 0.7);
    return mix(col, fogColor, fogAmount);
}
```

### Level 4: Extinction + Inscattering Separation
Independent RGB coefficients for absorption and scattering — allows chromatic fog effects where different wavelengths scatter differently:
```glsl
vec3 applyFogPhysical(vec3 col, float t, vec3 fogCol) {
    vec3 be = vec3(0.02, 0.025, 0.03);   // extinction coefficients (RGB)
    vec3 bi = vec3(0.015, 0.02, 0.025);  // inscattering coefficients (RGB)
    vec3 extinction = exp(-t * be);
    vec3 inscatter = (1.0 - exp(-t * bi));
    return col * extinction + fogCol * inscatter;
}
```

## Common Variants

### Variant 1: Non-Physical Analytic Approximation (No Ray March)

Extremely low-cost analytic sky, suitable for mobile / backgrounds.

```glsl
#define zenithDensity(x) 0.7 / pow(max(x - 0.1, 0.0035), 0.75)

vec3 getSkyAbsorption(vec3 skyColor, float zenith) {
    return exp2(skyColor * -zenith) * 2.0;
}

float getMie(vec2 p, vec2 lp) {
    float disk = clamp(1.0 - pow(distance(p, lp), 0.1), 0.0, 1.0);
    return disk * disk * (3.0 - 2.0 * disk) * 2.0 * 3.14159;
}

vec3 getAtmosphericScattering(vec2 screenPos, vec2 lightPos) {
    vec3 skyColor = vec3(0.39, 0.57, 1.0);
    float zenith = zenithDensity(screenPos.y);
    float rayleighMult = 1.0 + pow(1.0 - clamp(distance(screenPos, lightPos), 0.0, 1.0), 2.0) * 1.57;
    vec3 absorption = getSkyAbsorption(skyColor, zenith);
    vec3 sunAbsorption = getSkyAbsorption(skyColor, zenithDensity(lightPos.y + 0.1));
    vec3 sky = skyColor * zenith * rayleighMult;
    vec3 mie = getMie(screenPos, lightPos) * sunAbsorption;
    float sunDist = clamp(length(max(lightPos.y + 0.1, 0.0)), 0.0, 1.0);
    vec3 totalSky = mix(sky * absorption, sky / (sky + 0.5), sunDist);
    totalSky += mie;
    totalSky *= sunAbsorption * 0.5 + 0.5 * length(sunAbsorption);
    return totalSky;
}
```

### Variant 2: Ozone Absorption Layer

Already integrated in the complete template. Set `BETA_OZONE` to a non-zero value to enable, producing a deeper blue zenith and purple tones at sunset.

### Variant 3: Subsurface Scattering (SSS)

For translucent materials (candles/skin/jelly), using SDF-estimated thickness to control light transmission.

```glsl
float subsurface(vec3 p, vec3 viewDir, vec3 normal) {
    vec3 scatterDir = refract(viewDir, normal, 1.0 / 1.5); // IOR 1.3~2.0
    vec3 samplePos = p;
    float accumThickness = 0.0;
    float MAX_SCATTER = 2.5;
    for (float i = 0.1; i < MAX_SCATTER; i += 0.2) {
        samplePos += scatterDir * i;
        accumThickness += map(samplePos); // SDF function
    }
    float thickness = max(0.0, -accumThickness);
    float SCATTER_STRENGTH = 16.0;
    return SCATTER_STRENGTH * pow(MAX_SCATTER * 0.5, 3.0) / thickness;
}
// Usage: float ss = max(0.0, subsurface(hitPos, viewDir, normal));
// vec3 sssColor = albedo * smoothstep(0.0, 2.0, pow(ss, 0.6));
// finalColor = mix(lambertian, sssColor, 0.7) + specular;
```

### Variant 4: LUT Precomputation Pipeline (Production Grade)

Precompute Transmittance/Multiple Scattering/Sky-View into LUTs, only table lookups at runtime.

```glsl
// Transmittance LUT query (Hillaire 2020)
vec3 getValFromTLUT(sampler2D tex, vec2 bufferRes, vec3 pos, vec3 sunDir) {
    float height = length(pos);
    vec3 up = pos / height;
    float sunCosZenithAngle = dot(sunDir, up);
    vec2 uv = vec2(
        256.0 * clamp(0.5 + 0.5 * sunCosZenithAngle, 0.0, 1.0),
        64.0 * max(0.0, min(1.0, (height - groundRadiusMM) / (atmosphereRadiusMM - groundRadiusMM)))
    );
    uv /= bufferRes;
    return texture(tex, uv).rgb;
}
```

### Variant 5: Analytic Fast Atmosphere (with Aerial Perspective)

Analytic exponential approximation replacing ray march, with distance attenuation support.

```glsl
void getRayleighMie(float opticalDepth, float densityR, float densityM, out vec3 R, out vec3 M) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    R = (1.0 - exp(-opticalDepth * densityR * C_RAYLEIGH / 2.5)) * 2.5;
    M = (1.0 - exp(-opticalDepth * densityM * C_MIE / 0.5)) * 0.5;
}

vec3 getLightTransmittance(vec3 lightDir) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    vec3 C_OZONE = vec3(0.650, 1.881, 0.085) * 1e-6;
    float extinction = exp(-clamp(lightDir.y + 0.05, 0.0, 1.0) * 40.0)
                     + exp(-clamp(lightDir.y + 0.5, 0.0, 1.0) * 5.0) * 0.4
                     + pow(clamp(1.0 - lightDir.y, 0.0, 1.0), 2.0) * 0.02
                     + 0.002;
    return exp(-(C_RAYLEIGH + C_MIE + C_OZONE) * extinction * 1e6);
}
```

## Performance & Composition

### Performance Tips
- **Nested ray march (O(N*M))**: reduce step counts (mobile: PRIMARY=12, LIGHT=4), use analytic approximation instead of light march, precompute Transmittance LUT
- **Dense exp()/pow()**: Schlick approximation replacing HG phase function — `k = 1.55*g - 0.55*g³; phase = (1-k²) / (4π*(1+k*cosθ)²)`
- **Full-screen per-pixel**: Sky-View LUT (200x200) table lookup, half-resolution rendering + bilinear upsampling
- **Banding dithering**: non-uniform step offset of 0.3, temporal blue noise dithering

### Composition Tips
- **+ Volumetric clouds**: atmospheric transmittance determines sun color reaching the cloud layer, set `maxDist` to cloud distance
- **+ SDF scene**: SDF hit distance → `maxDist`, scene color → `sceneColor`, automatic aerial perspective
- **+ God Rays**: add occlusion to scattering integration (shadow map or additional ray march)
- **+ Terrain**: `finalColor = terrainColor * transmittance + inscattering`
- **+ PBR/SSS**: `diffuse = mix(lambert, sss, 0.7); final = ambient + albedo*diffuse + specular + fresnel*env`

## Further Reading

For full step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/atmospheric-scattering.md)
