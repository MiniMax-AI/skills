# Lighting Models Detailed Reference

This document is a detailed supplementary reference to [SKILL.md](SKILL.md), covering prerequisite knowledge, in-depth explanations for each step, complete descriptions of variants, performance optimization analysis, and full code examples for combination suggestions.

---

## Prerequisites

### Vector Math Fundamentals
- **Dot product**: `dot(A, B) = |A||B|cos(θ)`, used to compute the angular relationship between two vectors. Lighting models heavily use dot products such as N·L, N·V, N·H, V·H
- **Cross product**: `cross(A, B)` returns a vector perpendicular to both A and B, used to build camera coordinate systems and tangent spaces
- **normalize**: Scales a vector to unit length; lighting calculations require all direction vectors to be normalized
- **reflect**: `reflect(I, N) = I - 2.0 * dot(N, I) * N`, computes the reflection of incident vector I about normal N

### GLSL Fundamentals
- **uniform / varying**: uniforms are global constants (e.g., iTime, iResolution); varyings are interpolated from vertex to fragment
- **Key built-in functions**:
  - `clamp(x, min, max)` — clamp to range
  - `mix(a, b, t)` — linear interpolation `a*(1-t) + b*t`
  - `pow(base, exp)` — exponentiation, used for specular falloff
  - `exp(x)` / `exp2(x)` — exponential functions, used for attenuation and Beer's Law
  - `smoothstep(edge0, edge1, x)` — Hermite smooth interpolation

### Basic Computer Graphics Concepts
- **Normal (N)**: Unit vector pointing outward from the surface, determines lighting intensity
- **View Direction (V)**: Unit vector from the surface point toward the camera
- **Light Direction (L)**: Unit vector from the surface point toward the light source
- **Half Vector (H)**: `normalize(V + L)`, the core of the Blinn-Phong model
- **Reflect Vector (R)**: `reflect(-L, N)`, used in the classic Phong model

### Raymarching Basics (Recommended)
- **SDF (Signed Distance Function)**: Returns the signed distance from a point to the nearest surface
- **Normal computation (finite differences)**: Approximates the gradient (i.e., normal direction) by computing small-offset differences of the SDF along the x, y, and z axes
- **March**: Advances along the ray direction by the distance returned by the SDF until hitting a surface or exceeding the range

---

## Implementation Steps in Detail

### Step 1: Scene Foundation (UV, Camera, Raymarching)

**What**: Establish the standard ShaderToy framework — UV coordinates, camera ray, SDF scene, normal computation.

**Why**: Lighting calculations require normal N, view direction V, and light direction L as inputs, all of which depend on scene geometry. Without correct normals and direction vectors, no lighting model can work.

**Details**:
- UV coordinates are typically normalized as `(2.0 * fragCoord - iResolution.xy) / iResolution.y` to ensure correct aspect ratio
- The camera uses a look-at matrix: forward direction `ww`, right direction `uu`, up direction `vv`
- SDF normals use six-point central difference, which is more accurate than forward difference
- The epsilon value in `e = vec2(0.001, 0.0)` affects normal accuracy: too large blurs details, too small introduces noise

**Code**:
```glsl
// Compute normal from SDF scene (finite differences) — standard technique
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Prepare basic vectors needed for lighting
vec3 N = calcNormal(pos);           // Surface normal
vec3 V = -rd;                        // View direction (reverse of ray)
vec3 L = normalize(lightPos - pos);  // Light direction (point light)
// Or directional light: vec3 L = normalize(vec3(0.6, 0.8, -0.5));
```

### Step 2: Lambert Diffuse

**What**: Compute basic diffuse lighting — the foundation of all lighting models.

**Why**: Lambert's law describes the ideal diffuse behavior of rough surfaces — brightness is proportional to cos(angle of incidence). This is the most fundamental physically-based lighting model, assuming light enters the surface and is scattered uniformly.

**Details**:
- `max(0.0, dot(N, L))` uses `max(0,...)` to avoid negative values (backface lighting)
- Energy-conserving Lambertian diffuse requires dividing by PI, since Lambert BRDF = albedo/PI and the integrated irradiance = PI * L_incoming
- Half-Lambert (`NdotL * 0.5 + 0.5`) is a technique invented by Valve that maps [-1,1] to [0,1], giving backlit areas some brightness; commonly used for character rendering and SSS approximation
- Many ocean shaders use a similar wrapped diffuse pattern

**Code**:
```glsl
// Basic Lambert diffuse
float NdotL = max(0.0, dot(N, L));
vec3 diffuse = albedo * lightColor * NdotL;

// Energy-conserving version (albedo/PI)
vec3 diffuse_conserved = albedo / PI * lightColor * NdotL;

// Half-Lambert variant (wrapped dot product)
// Reduces over-darkening on backlit faces, commonly used for SSS approximation
float halfLambert = NdotL * 0.5 + 0.5;
vec3 diffuse_wrapped = albedo * lightColor * halfLambert;
```

### Step 3: Blinn-Phong Specular

**What**: Add specular highlights based on the half vector.

**Why**: Blinn-Phong is more computationally efficient and physically plausible than classic Phong. The half vector H is the average direction of V and L; the highlight is brightest when H aligns with N. Blinn-Phong also behaves more realistically at grazing angles compared to Phong.

**Details**:
- Half vector H = normalize(V + L), which avoids the reflect computation needed by Phong's reflect(-L, N)
- Shininess controls highlight concentration: 4.0 gives a very rough surface feel, 256.0 approaches a mirror
- The normalization factor `(shininess + 8.0) / (8.0 * PI)` ensures total reflected energy remains constant when changing shininess (energy conservation)
- Based on the standard half vector method used in many raymarching shaders

**Code**:
```glsl
// Blinn-Phong specular (standard half vector method)
vec3 H = normalize(V + L);
float NdotH = max(0.0, dot(N, H));

// Empirical model: directly use shininess exponent
float SHININESS = 32.0;  // Adjustable: 4.0 (rough) ~ 256.0 (mirror-like)
float spec = pow(NdotH, SHININESS);

// With energy-conserving normalization factor
// Normalization factor (s+8)/(8*PI) ensures total energy is preserved when changing shininess
float normFactor = (SHININESS + 8.0) / (8.0 * PI);
float spec_normalized = normFactor * pow(NdotH, SHININESS);

vec3 specular = lightColor * spec_normalized;
```

### Step 4: Fresnel-Schlick Approximation

**What**: Compute reflectance based on viewing angle — reflectance increases at grazing angles ("edge brightening" effect).

**Why**: All real materials approach 100% reflectance at grazing angles. This is a fundamental physical phenomenon (Fresnel effect). The Schlick approximation uses a fifth-power curve to simulate this, and is a core component of all PBR pipelines. This is a ubiquitous formula in real-time rendering.

**Details**:
- F0 is the reflectance at normal incidence (looking straight at the surface)
- Dielectrics (plastic, water, etc.): F0 is approximately 0.02~0.04; most light is scattered (diffuse)
- Metals: F0 uses the material's baseColor, since metals have virtually no diffuse reflection
- `mix(vec3(0.04), baseColor, metallic)` is the unified metallic workflow, interpolating between dielectrics and metals
- Using V·H for the Cook-Torrance BRDF specular term
- Using N·V for environment reflections, rim lighting, etc.
- A widely used approximation in both real-time and offline rendering pipelines.

**Code**:
```glsl
// Fresnel-Schlick approximation (standard formulation)
vec3 fresnelSchlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// Dielectrics (plastic, water, etc.): F0 approximately 0.02~0.04
vec3 F0_dielectric = vec3(0.04);

// Metals: F0 uses the material's baseColor
vec3 F0_metal = baseColor;

// Unified metallic workflow
vec3 F0 = mix(vec3(0.04), baseColor, metallic);

// Compute Fresnel using V·H (for specular BRDF)
float VdotH = max(0.0, dot(V, H));
vec3 F = fresnelSchlick(F0, VdotH);

// Alternatively, compute Fresnel using N·V (for environment reflections, rim light)
// Optional: pow(fGloss, 20.0) factor for gloss adjustment
float NdotV = max(0.0, dot(N, V));
vec3 F_env = F0 + (1.0 - F0) * pow(1.0 - NdotV, 5.0);
```

### Step 5: GGX Normal Distribution Function (D Term)

**What**: Compute the probability distribution of microfacet normals aligning with the half vector.

**Why**: The GGX (Trowbridge-Reitz) distribution has a wider "long tail" highlight, closer to real materials than the Beckmann distribution. This is the core term in PBR pipelines that determines highlight shape and size. This is the standard GGX formula used across PBR implementations.

**Details**:
- Roughness must be squared first (`a = roughness * roughness`); this is Disney's mapping from perceptual roughness to alpha
- `a2 = a * a` is the alpha^2 term in the GGX formula
- When roughness = 0.0, D approaches a delta function (perfect mirror); when roughness = 1.0, it approaches a uniform distribution
- The denominator `PI * denom * denom` ensures the distribution function integrates to 1 over the hemisphere
- The standard GGX formula used across PBR implementations

**Code**:
```glsl
// GGX/Trowbridge-Reitz normal distribution function (standard formulation)
float distributionGGX(float NdotH, float roughness) {
    float a = roughness * roughness;  // Note: roughness must be squared first!
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// Roughness parameter guide:
// roughness = 0.0 → perfect mirror (D approaches delta function)
// roughness = 0.5 → medium roughness
// roughness = 1.0 → fully rough (D approaches uniform distribution)
```

### Step 6: Geometric Occlusion Function (G Term)

**What**: Compute the mutual shadowing and masking between microfacets.

**Why**: Not all correctly-oriented microfacets can be "seen" by both the light and the view simultaneously — the G term corrects for this occlusion loss. The microfacet model assumes the surface is composed of countless tiny flat surfaces that can occlude each other (shadowing and masking).

**Details**:
- The Smith method decomposes G into two independent terms for the light direction (G1_L) and view direction (G1_V)
- **Schlick-GGX**: `k = (roughness+1)^2 / 8` for direct lighting, `k = roughness^2 / 2` for IBL
- **Height-Correlated Smith**: More physically accurate, accounts for height correlation of microfacets; directly returns the visibility term `G/(4*NdotV*NdotL)`
- **Simplified approximation** (G1V): Most compact implementation, suitable for code golf or extremely performance-constrained scenarios
- Three common implementations with different accuracy/performance tradeoffs

**Code**:
```glsl
// Smith method: decompose G into two independent G1 terms for light and view directions

// Method 1: Schlick-GGX (separated implementation)
// The clearest pedagogical implementation
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;  // For direct lighting: k = (r+1)^2/8
    return NdotV / (NdotV * (1.0 - k) + k);
}

float geometrySmith(float NdotV, float NdotL, float roughness) {
    float ggx1 = geometrySchlickGGX(NdotV, roughness);
    float ggx2 = geometrySchlickGGX(NdotL, roughness);
    return ggx1 * ggx2;
}

// Method 2: Height-Correlated Smith (visibility term form)
// More physically accurate, directly returns G/(4*NdotV*NdotL), i.e., the "visibility term"
float visibilitySmith(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    float gv = NdotL * sqrt(NdotV * (NdotV - NdotV * a2) + a2);
    float gl = NdotV * sqrt(NdotL * (NdotL - NdotL * a2) + a2);
    return 0.5 / max(gv + gl, 0.00001);
}

// Method 3: Simplified approximation (compact G1V helper)
// Most compact implementation
float G1V(float dotNV, float k) {
    return 1.0 / (dotNV * (1.0 - k) + k);
}
// Usage: float vis = G1V(NdotL, k) * G1V(NdotV, k); where k = roughness/2
```

### Step 7: Assembling the Cook-Torrance BRDF

**What**: Combine the D, F, and G terms into a complete specular reflection BRDF.

**Why**: The Cook-Torrance microfacet model is currently the most widely used physically-based specular reflection model in real-time rendering. It is based on microfacet theory, modeling the surface as countless tiny perfect mirrors.

**Details**:
- Full formula: `f_specular = D * F * G / (4 * NdotV * NdotL)`
- When using `visibilitySmith` (which returns `G/(4*NdotV*NdotL)`), there is no need to manually divide by the denominator
- When using the standard `geometrySmith` (which returns G), you must explicitly divide by `4 * NdotV * NdotL`
- `max(4.0 * NdotV * NdotL, 0.001)` prevents division by zero
- Based on the standard Cook-Torrance BRDF formulation

**Code**:
```glsl
// Complete Cook-Torrance BRDF assembly
// Standard Cook-Torrance BRDF assembly
vec3 cookTorranceBRDF(vec3 N, vec3 V, vec3 L, float roughness, vec3 F0) {
    vec3 H = normalize(V + L);

    float NdotL = max(0.0, dot(N, L));
    float NdotV = max(0.0, dot(N, V));
    float NdotH = max(0.0, dot(N, H));
    float VdotH = max(0.0, dot(V, H));

    // D: Normal distribution
    float D = distributionGGX(NdotH, roughness);

    // F: Fresnel
    vec3 F = fresnelSchlick(F0, VdotH);

    // G: Geometric occlusion (using visibility term form, which includes the 4*NdotV*NdotL denominator)
    float Vis = visibilitySmith(NdotV, NdotL, roughness);

    // Assembly (Vis version already divides by 4*NdotV*NdotL)
    vec3 specular = D * F * Vis;

    // Or using the standard G term form:
    // float G = geometrySmith(NdotV, NdotL, roughness);
    // vec3 specular = (D * F * G) / max(4.0 * NdotV * NdotL, 0.001);

    return specular * NdotL;
}
```

### Step 8: Multi-Light Accumulation and Final Compositing

**What**: Blend diffuse and specular reflections with energy conservation, and accumulate contributions from multiple lights.

**Why**: Real scenes contain multiple light sources (sun, sky, ground bounce, etc.). Energy conservation must be maintained between diffuse and specular: energy that has been reflected (F) should not participate in diffuse reflection.

**Details**:
- `kD = (1.0 - F) * (1.0 - metallic)` implements energy conservation:
  - `(1.0 - F)` ensures already-reflected light does not participate in diffuse
  - `(1.0 - metallic)` ensures metals have no diffuse (metals' free electrons absorb all refracted light)
- Sky light uses `0.5 + 0.5 * N.y` to approximate hemisphere integration — the more upward the normal, the brighter
- Back/rim light uses wrapped diffuse from the opposite direction of the sun to provide fill lighting
- Based on multi-light architecture patterns common in PBR raymarching shaders

**Code**:
```glsl
// Complete multi-light PBR lighting accumulation
// Multi-light PBR architecture

vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);  // Metals have no diffuse
    vec3 color = vec3(0.0);

    // --- Main light (sun) ---
    vec3 sunDir = normalize(vec3(0.6, 0.8, -0.5));
    vec3 sunColor = vec3(1.0, 0.95, 0.85) * 2.0;

    vec3 H = normalize(V + sunDir);
    float NdotL = max(0.0, dot(N, sunDir));
    float NdotV = max(0.0, dot(N, V));
    float VdotH = max(0.0, dot(V, H));

    vec3 F = fresnelSchlick(F0, VdotH);
    vec3 kD = (1.0 - F) * (1.0 - metallic);  // Energy conservation

    // Diffuse contribution
    color += kD * diffuseColor / PI * sunColor * NdotL;
    // Specular contribution
    color += cookTorranceBRDF(N, V, sunDir, roughness, F0) * sunColor;

    // --- Sky light (hemisphere light approximation) ---
    // Sky light (hemisphere light approximation)
    vec3 skyColor = vec3(0.2, 0.5, 1.0) * 0.3;
    float skyDiffuse = 0.5 + 0.5 * N.y;  // Simple hemisphere integration approximation
    color += diffuseColor * skyColor * skyDiffuse;

    // --- Back light / rim light ---
    // Back-light / fill light term
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float backDiffuse = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
    color += diffuseColor * vec3(0.25, 0.15, 0.1) * backDiffuse;

    return color;
}
```

### Step 9: Ambient Occlusion (AO)

**What**: Approximate the reduction of indirect lighting in surface crevices due to geometric occlusion.

**Why**: Scenes without AO appear overly "flat" and lack spatial depth. In raymarching scenes, the SDF can be used to efficiently compute AO — sample several points along the normal direction and compare the SDF distance with the ideal distance.

**Details**:
- Principle: Step gradually away from the surface along the normal, querying the SDF value at each sample point. If the SDF value is less than the sample distance h, nearby occluding geometry is present
- `sca *= 0.95` gradually decreases the weight of farther sample points
- The multiplier in `3.0 * occ` controls AO intensity (adjustable)
- AO affects both diffuse and specular, but in different ways:
  - Diffuse: multiply directly by the AO value
  - Specular: use `pow(NdotV + ao, roughness^2) - 1 + ao` for more subtle attenuation
- Based on the standard SDF ambient occlusion technique

**Code**:
```glsl
// AO computation for raymarching scenes (standard SDF-based technique)
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0;
        float d = map(pos + h * nor);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// Using AO (AO affects both diffuse and specular)
float ao = calcAO(pos, N);
diffuseLight *= ao;
// More subtle specular AO:
specularLight *= clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
```

---

## Variant Details

### Variant 1: Classic Phong (Non-PBR)

**Difference from base version**: Uses the reflection vector `R = reflect(-L, N)` instead of the half vector; no D/F/G decomposition.

**Use cases**: Quick prototyping, retro-style rendering, performance-constrained scenarios. The Phong model has the lowest computational cost but does not satisfy energy conservation, and highlights disappear at grazing angles (the opposite of real materials).

**Key code**:
```glsl
// Classic Phong reflection model
vec3 R = reflect(-L, N);
float spec = pow(max(0.0, dot(R, V)), 32.0);
vec3 color = albedo * lightColor * NdotL    // diffuse
           + lightColor * spec;              // specular
```

### Variant 2: Point Light Attenuation

**Difference from base version**: Adds distance attenuation, suitable for point light / spotlight scenarios. The base version assumes directional light (sun), while point light intensity decreases with distance.

**Use cases**: Indoor scenes, multiple point lights, close-range light effects.

**Details**:
- Physically correct attenuation should be `1/distance²`, but in practice `1/(1 + k1*d + k2*d²)` avoids infinite brightness at close range
- k1 (linear attenuation): 0.01~0.5, k2 (quadratic attenuation): 0.001~0.1
- Alternatively, use physical attenuation with a maximum intensity cap: `min(1.0/(d*d), maxIntensity)`

**Key code**:
```glsl
// Point light attenuation (standard pattern)
float dist = length(lightPos - pos);
float attenuation = 1.0 / (1.0 + dist * 0.1 + dist * dist * 0.01);
// k1: linear attenuation coefficient (adjustable 0.01~0.5)
// k2: quadratic attenuation coefficient (adjustable 0.001~0.1)
color *= attenuation;
```

### Variant 3: IBL (Image-Based Lighting)

**Difference from base version**: Uses environment maps instead of analytic light sources, split into diffuse SH (spherical harmonics) and specular split-sum parts.

**Use cases**: Scenes requiring realistic environmental lighting reflections. IBL can capture complex lighting environments (e.g., HDRI panoramas), producing very natural lighting effects.

**Details**:
- Diffuse IBL uses spherical harmonics (SH) to precompute the low-frequency component of environmental lighting
- Specular IBL uses Epic Games' split-sum approximation: splits the BRDF integral into environment map LOD lookup + precomputed BRDF integration lookup table
- `EnvBRDFApprox` is Unreal Engine 4's approximation, avoiding the need for a precomputed LUT texture
- `textureLod(envMap, R, roughness * 7.0)` uses mipmap levels to simulate blurred reflections on rough surfaces
- Based on the SH + EnvBRDFApprox method common in PBR pipelines

**Key code**:
```glsl
// IBL approximation (SH + EnvBRDFApprox method)
// Diffuse IBL: spherical harmonics
vec3 diffuseIBL = diffuseColor * SHIrradiance(N);

// Specular IBL: Unreal's EnvBRDFApprox approximation
vec3 EnvBRDFApprox(vec3 specColor, float roughness, float NdotV) {
    vec4 c0 = vec4(-1, -0.0275, -0.572, 0.022);
    vec4 c1 = vec4(1, 0.0425, 1.04, -0.04);
    vec4 r = roughness * c0 + c1;
    float a004 = min(r.x * r.x, exp2(-9.28 * NdotV)) * r.x + r.y;
    vec2 AB = vec2(-1.04, 1.04) * a004 + r.zw;
    return specColor * AB.x + AB.y;
}
vec3 R = reflect(-V, N);
vec3 envColor = textureLod(envMap, R, roughness * 7.0).rgb;
vec3 specularIBL = EnvBRDFApprox(F0, roughness, NdotV) * envColor;
```

### Variant 4: Subsurface Scattering Approximation (SSS)

**Difference from base version**: Simulates light passing through translucent materials (e.g., skin, wax, water surfaces).

**Use cases**: Water surfaces, skin, candles, leaves, and other translucent materials. SSS makes thin parts appear brighter and more translucent.

**Details**:
- **Method 1 (SDF probing)**: Probes the SDF value along the light direction into the material interior. If the SDF value is much smaller than the probe distance, the material is thicker at that point and transmits less light; otherwise it transmits more
- **Method 2 (Henyey-Greenstein phase function)**: Describes the directional distribution of light scattering in a medium. Parameter g controls forward/backward scattering: g > 0 for forward scattering (e.g., skin), g < 0 for backward scattering
- Combines SDF-based interior probing with Henyey-Greenstein phase function

**Key code**:
```glsl
// SSS approximation (SDF-based interior probing)
// Method 1: SDF-based interior probing
float subsurface(vec3 pos, vec3 L) {
    float sss = 0.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.05 + float(i) * 0.1;
        float d = map(pos + L * h);  // Probe along light direction into interior
        sss += max(0.0, h - d);      // Thinner areas transmit more light
    }
    return clamp(1.0 - sss * 4.0, 0.0, 1.0);
}

// Method 2: Henyey-Greenstein phase function
float HenyeyGreenstein(float cosTheta, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5) * 4.0 * PI);
}
float sssAmount = HenyeyGreenstein(dot(V, L), 0.5);
color += sssColor * sssAmount * NdotL;
```

### Variant 5: Beer's Law Water Lighting

**Difference from base version**: Simulates the exponential attenuation of light in water/transparent media.

**Use cases**: Water surfaces, underwater scenes, glass, juice, and other transparent/translucent media. The Beer-Lambert law describes the exponential decay of light intensity as it travels through a medium.

**Details**:
- `exp2(-opticalDepth * extinctColor)` implements wavelength-dependent exponential attenuation
- Different color channels have different attenuation coefficients, producing the characteristic color of water (blue/green transmits the most)
- In `extinctColor = 1.0 - vec3(0.5, 0.4, 0.1)`, the vec3 controls the absorption rate per channel
- Inscattering simulates multiple scattering of light inside the water body, giving deep water its inherent color
- `1.0 - exp(-depth * 0.1)` is a simplified inscattering model
- Based on the Beer-Lambert law for wavelength-dependent attenuation

**Key code**:
```glsl
// Beer's Law light attenuation
vec3 waterExtinction(float depth) {
    float opticalDepth = depth * 6.0;  // Adjustable: controls attenuation rate
    vec3 extinctColor = 1.0 - vec3(0.5, 0.4, 0.1);  // Adjustable: water absorption color
    return exp2(-opticalDepth * extinctColor);
}

// Usage: underwater object color multiplied by attenuation
vec3 underwaterColor = objectColor * waterExtinction(depth);
// Add water inscattering
vec3 inscatter = waterDiffuse * (1.0 - exp(-depth * 0.1));
underwaterColor += inscatter;
```

---

## Performance Optimization In-Depth Analysis

### 1. Avoiding the Cost of pow(x, 5.0)

The `pow` function on some GPUs is implemented as `exp2(5.0 * log2(x))`, involving two transcendental functions. Manually unrolling into a multiplication chain is more efficient:

```glsl
// Efficient implementation of Schlick Fresnel
float x = 1.0 - cosTheta;
float x2 = x * x;
float x5 = x2 * x2 * x;  // Faster than pow(x, 5.0)
vec3 F = F0 + (1.0 - F0) * x5;
```

### 2. Merging G and the Denominator (Visibility Term)

Using `V_SmithGGX` to directly return `G / (4 * NdotV * NdotL)` avoids computing G separately and then dividing. This not only eliminates one division but also avoids numerical instability when `4 * NdotV * NdotL` is near zero. The Height-Correlated Smith version is also more physically accurate.

### 3. AO Sample Count

- 5 samples are sufficient for most scenes
- Distant objects can use as few as 3 (since details are not visible)
- The upper bound of sample step h (`0.12 * i / 4.0`) controls the AO influence range: increasing it detects larger-scale occlusion but requires more samples
- The decay rate `sca *= 0.95` is also adjustable: smaller values make AO more concentrated near the surface

### 4. Soft Shadow Optimization

- Using `clamp(h, 0.02, 0.2)` to limit step size: minimum step 0.02 prevents getting stuck near the surface, maximum step 0.2 prevents skipping thin geometry
- Shadow ray maxSteps can be lower than the primary ray (14~24 steps is usually enough), since shadows don't need precise hit points
- The 8.0 in `8.0 * h / t` controls shadow softness: higher values produce harder shadows, lower values softer ones. This is an intuitive penumbra size control

### 5. Simplified IBL

- Without a cubemap, use a simple sky color gradient as a substitute for environment mapping
- `mix(groundColor, skyColor, R.y * 0.5 + 0.5)` is the cheapest "environment reflection"
- A `pow(max(0, dot(R, sunDir)), 64.0)` in the sun direction can be added to simulate the sun's specular reflection

### 6. Branch Culling

When NdotL <= 0, the surface faces away from the light source, and all specular calculations (D, F, G) can be skipped:

```glsl
// Skip entire specular computation when NdotL <= 0
if (NdotL > 0.0) {
    // ... D, F, G computation ...
}
```

Note: Branch efficiency on GPUs depends on the coherence of pixels within the same warp/wavefront. If large areas face away from the light, this branch is effective; if the branch condition switches frequently between adjacent pixels, it may actually be slower.

---

## Combination Suggestions in Detail

### Lighting + Raymarching

Raymarching scenes are the most common host for lighting models. Normals are obtained via SDF finite differences, and AO and shadows directly leverage SDF queries.

Key integration points:
- `calcNormal` provides normal N
- `calcAO` leverages SDF for ambient occlusion
- `softShadow` leverages SDF for soft shadows
- Material IDs can be passed through the return value of the `map` function

### Lighting + Volumetric Rendering

Volumetric effects like clouds, smoke, and fog require Beer's Law attenuation and phase functions (e.g., Henyey-Greenstein). PBR surface lighting integrates naturally with volumetric cloud lighting.

Key integration points:
- Volumetric rendering uses ray marching to step through the volume
- Each step accumulates density and applies Beer's Law attenuation
- Lighting uses the Henyey-Greenstein phase function instead of a BRDF
- The final result is alpha-blended with the surface rendering output

### Lighting + Normal Maps / Procedural Normals

Normals don't have to come from the SDF. Procedural normals generated by FBM noise (e.g., ocean wave normals, water surface normals) can be passed directly to lighting functions, producing rich surface detail.

Key integration points:
- Procedural normals work by perturbing the base normal: `N = normalize(N + perturbation)`
- FBM noise frequency and amplitude control the coarseness and strength of detail
- SDF normals and procedural normals can be combined for macro shape + micro detail

### Lighting + Post-Processing

Tone mapping and gamma correction are essential parts of a PBR pipeline. HDR lighting values must be mapped to the [0,1] LDR range for correct display:

```glsl
// ACES — currently the most popular tone mapping
col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);

// Reinhard — simplest tone mapping
col = col / (col + 1.0);

// Gamma correction — convert from linear space to sRGB
col = pow(col, vec3(1.0 / 2.2));
```

Note: All lighting calculations must be performed in linear space; gamma correction is only applied at final output.

### Lighting + Reflections

Multi-layer reflections or environment reflections query the scene again in the `reflect(rd, N)` direction, blending the reflected color into the final result weighted by Fresnel.

```glsl
// Basic reflection pattern
vec3 R = reflect(rd, N);
vec3 reflColor = traceScene(pos + N * 0.01, R);  // Offset to avoid self-intersection
vec3 F = fresnelSchlick(F0, NdotV);
color = mix(color, reflColor, F);
```

A common water surface rendering approach combines refraction + reflection + Fresnel blending:
- Reflection direction `reflect(rd, N)` queries the sky/scene
- Refraction direction `refract(rd, N, 1.0/1.33)` queries the underwater scene
- Fresnel coefficient blends between reflection and refraction
