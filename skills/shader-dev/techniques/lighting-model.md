# Lighting Models Skill

## Use Cases
- Adding realistic lighting to raymarched or rasterized scenes
- Simulating light interaction with various materials (metal, dielectric, water, skin, etc.)
- From simple diffuse/specular to full PBR
- Multi-light compositing (sun, sky, ambient)
- Adding material appearance to SDF scenes in ShaderToy

## Core Principles

Lighting = Diffuse + Specular Reflection:

- **Diffuse**: Lambert's law `I = max(0, N·L)`
- **Specular**: Empirical model uses Blinn-Phong `pow(max(0, N·H), shininess)`; physically-based model uses Cook-Torrance BRDF

### Key Formulas

```
Lambert:        L_diffuse  = albedo * lightColor * max(0, N·L)
Blinn-Phong:    H = normalize(V + L); L_specular = lightColor * pow(max(0, N·H), shininess)
Cook-Torrance:  f_specular = D(h) * F(v,h) * G(l,v,h) / (4 * (N·L) * (N·V))
Fresnel:        F = F0 + (1 - F0) * (1 - V·H)^5
```

- **D** = GGX/Trowbridge-Reitz normal distribution
- **F** = Schlick Fresnel approximation
- **G** = Smith geometric shadowing
- F0: dielectric ~0.04, metals use baseColor

## Implementation Steps

### Step 1: Scene Basics (Normal + Vector Setup)

```glsl
// SDF normal (finite difference method)
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

vec3 N = calcNormal(pos);           // surface normal
vec3 V = -rd;                        // view direction
vec3 L = normalize(lightPos - pos);  // light direction (point light)
// directional light: vec3 L = normalize(vec3(0.6, 0.8, -0.5));
```

### Step 2: Lambert Diffuse

```glsl
float NdotL = max(0.0, dot(N, L));
vec3 diffuse = albedo * lightColor * NdotL;

// energy-conserving version
vec3 diffuse_conserved = albedo / PI * lightColor * NdotL;

// Half-Lambert (reduces over-darkening on backlit faces, commonly used for SSS approximation)
float halfLambert = NdotL * 0.5 + 0.5;
vec3 diffuse_wrapped = albedo * lightColor * halfLambert;
```

### Step 3: Blinn-Phong Specular

```glsl
vec3 H = normalize(V + L);
float NdotH = max(0.0, dot(N, H));
float SHININESS = 32.0;  // 4.0 (rough) ~ 256.0 (smooth)

// with normalization factor for energy conservation
float normFactor = (SHININESS + 8.0) / (8.0 * PI);
float spec = normFactor * pow(NdotH, SHININESS);
vec3 specular = lightColor * spec;
```

### Step 4: Fresnel-Schlick

```glsl
vec3 fresnelSchlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// metallic workflow
vec3 F0 = mix(vec3(0.04), baseColor, metallic);

// computed with V·H (specular reflection BRDF)
float VdotH = max(0.0, dot(V, H));
vec3 F = fresnelSchlick(F0, VdotH);

// computed with N·V (environment reflection, rim light)
float NdotV = max(0.0, dot(N, V));
vec3 F_env = fresnelSchlick(F0, NdotV);
```

### Step 5: GGX Normal Distribution (D Term)

```glsl
float distributionGGX(float NdotH, float roughness) {
    float a = roughness * roughness;  // roughness must be squared first
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}
```

### Step 6: Geometric Shadowing (G Term)

```glsl
// Method 1: Schlick-GGX
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}
float geometrySmith(float NdotV, float NdotL, float roughness) {
    return geometrySchlickGGX(NdotV, roughness) * geometrySchlickGGX(NdotL, roughness);
}

// Method 2: Height-Correlated Smith (more accurate, directly returns the visibility term)
float visibilitySmith(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    float gv = NdotL * sqrt(NdotV * (NdotV - NdotV * a2) + a2);
    float gl = NdotV * sqrt(NdotL * (NdotL - NdotL * a2) + a2);
    return 0.5 / max(gv + gl, 0.00001);
}

// Method 3: Simplified approximation
float G1V(float dotNV, float k) {
    return 1.0 / (dotNV * (1.0 - k) + k);
}
// Usage: float vis = G1V(NdotL, k) * G1V(NdotV, k); where k = roughness/2
```

### Step 7: Assembling Cook-Torrance BRDF

```glsl
vec3 cookTorranceBRDF(vec3 N, vec3 V, vec3 L, float roughness, vec3 F0) {
    vec3 H = normalize(V + L);
    float NdotL = max(0.0, dot(N, L));
    float NdotV = max(0.0, dot(N, V));
    float NdotH = max(0.0, dot(N, H));
    float VdotH = max(0.0, dot(V, H));

    float D = distributionGGX(NdotH, roughness);
    vec3 F = fresnelSchlick(F0, VdotH);
    float Vis = visibilitySmith(NdotV, NdotL, roughness);

    // Vis version already includes the 4*NdotV*NdotL denominator
    vec3 specular = D * F * Vis;
    // Or with standard G term: specular = (D * F * G) / max(4.0 * NdotV * NdotL, 0.001);

    return specular * NdotL;
}
```

### Step 8: Multi-Light Accumulation and Compositing

```glsl
vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);  // metals have no diffuse
    vec3 color = vec3(0.0);

    // primary light (sun)
    vec3 sunDir = normalize(vec3(0.6, 0.8, -0.5));
    vec3 sunColor = vec3(1.0, 0.95, 0.85) * 2.0;
    vec3 H = normalize(V + sunDir);
    float NdotL = max(0.0, dot(N, sunDir));
    float NdotV = max(0.0, dot(N, V));
    float VdotH = max(0.0, dot(V, H));
    vec3 F = fresnelSchlick(F0, VdotH);
    vec3 kD = (1.0 - F) * (1.0 - metallic);  // energy conservation

    color += kD * diffuseColor / PI * sunColor * NdotL;
    color += cookTorranceBRDF(N, V, sunDir, roughness, F0) * sunColor;

    // sky light (hemisphere approximation)
    vec3 skyColor = vec3(0.2, 0.5, 1.0) * 0.3;
    float skyDiffuse = 0.5 + 0.5 * N.y;
    color += diffuseColor * skyColor * skyDiffuse;

    // back light / rim light
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float backDiffuse = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
    color += diffuseColor * vec3(0.25, 0.15, 0.1) * backDiffuse;

    return color;
}
```

### Step 9: Ambient Occlusion (AO)

```glsl
// Raymarching AO (using SDF queries)
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

float ao = calcAO(pos, N);
diffuseLight *= ao;
// specular AO (more subtle):
specularLight *= clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
```

### Outdoor Three-Light Model

The go-to lighting setup for outdoor SDF scenes. Uses three directional sources to approximate full global illumination with minimal cost:

```glsl
// === Outdoor Three-Light Lighting ===
// Compute material, occlusion, and shadow first
vec3 material = getMaterial(pos, nor);  // albedo, keep ≤ 0.2 for realism
float occ = calcAO(pos, nor);          // ambient occlusion
float sha = calcSoftShadow(pos, sunDir, 0.02, 8.0);

// Three light contributions
float sun = clamp(dot(nor, sunDir), 0.0, 1.0);        // direct sunlight
float sky = clamp(0.5 + 0.5 * nor.y, 0.0, 1.0);       // hemisphere sky light
float ind = clamp(dot(nor, normalize(sunDir * vec3(-1.0, 0.0, -1.0))), 0.0, 1.0); // indirect bounce

// Combine with colored shadows (key technique: shadow penumbra tints blue)
vec3 lin = vec3(0.0);
lin += sun * vec3(1.64, 1.27, 0.99) * pow(vec3(sha), vec3(1.0, 1.2, 1.5));  // warm sun, colored shadow
lin += sky * vec3(0.16, 0.20, 0.28) * occ;   // cool sky fill
lin += ind * vec3(0.40, 0.28, 0.20) * occ;   // warm ground bounce

vec3 color = material * lin;
```

Key principles:
- **Colored shadow penumbra**: `pow(vec3(sha), vec3(1.0, 1.2, 1.5))` makes shadow edges slightly blue/cool, mimicking real subsurface scattering in penumbra regions
- **Material albedo rule**: Keep diffuse albedo ≤ 0.2; adjust light intensities for brightness, not material values. Real-world surfaces rarely exceed 0.3 albedo
- **Linear workflow**: All computations in linear space, apply gamma `pow(color, vec3(1.0/2.2))` at the very end
- **Sky light approximation**: `0.5 + 0.5 * nor.y` is a cheap hemisphere integral — surfaces pointing up get full sky, pointing down get none
- Do NOT apply ambient occlusion to the sun/key light — shadows handle that

## Complete Code Template

```glsl
// Lighting Model Complete Template - Runs directly in ShaderToy
// Progressive implementation from Lambert to Cook-Torrance PBR

#define PI 3.14159265359

// ========== Adjustable Parameters ==========
#define ROUGHNESS 0.35
#define METALLIC 0.0
#define ALBEDO vec3(0.8, 0.2, 0.2)
#define SUN_DIR normalize(vec3(0.6, 0.8, -0.5))
#define SUN_COLOR vec3(1.0, 0.95, 0.85) * 2.0
#define SKY_COLOR vec3(0.2, 0.5, 1.0) * 0.4
#define BACKGROUND_TOP vec3(0.5, 0.7, 1.0)
#define BACKGROUND_BOT vec3(0.8, 0.85, 0.9)

// ========== SDF Scene ==========
float map(vec3 p) {
    float sphere = length(p - vec3(0.0, 0.0, 0.0)) - 1.0;
    float ground = p.y + 1.0;
    return min(sphere, ground);
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// ========== AO ==========
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

// ========== Soft Shadow ==========
float softShadow(vec3 ro, vec3 rd, float mint, float maxt) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 24; i++) {
        float h = map(ro + rd * t);
        res = min(res, 8.0 * h / t);
        t += clamp(h, 0.02, 0.2);
        if (res < 0.001 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

// ========== PBR BRDF Components ==========
float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float d = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}

vec3 F_Schlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

float V_SmithGGX(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    a2 *= a2;
    float gv = NdotL * sqrt(NdotV * NdotV * (1.0 - a2) + a2);
    float gl = NdotV * sqrt(NdotL * NdotL * (1.0 - a2) + a2);
    return 0.5 / max(gv + gl, 1e-5);
}

// ========== Complete Lighting ==========
vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);
    float NdotV = max(dot(N, V), 1e-4);
    float ao = calcAO(pos, N);
    vec3 color = vec3(0.0);

    // sunlight
    {
        vec3 L = SUN_DIR;
        vec3 H = normalize(V + L);
        float NdotL = max(dot(N, L), 0.0);
        float NdotH = max(dot(N, H), 0.0);
        float VdotH = max(dot(V, H), 0.0);
        float D = D_GGX(NdotH, roughness);
        vec3  F = F_Schlick(F0, VdotH);
        float Vis = V_SmithGGX(NdotV, NdotL, roughness);
        vec3 kD = (1.0 - F) * (1.0 - metallic);
        vec3 diffuse  = kD * diffuseColor / PI;
        vec3 specular = D * F * Vis;
        float shadow = softShadow(pos, L, 0.02, 5.0);
        color += (diffuse + specular) * SUN_COLOR * NdotL * shadow;
    }

    // sky light (hemisphere approximation)
    {
        float skyDiff = 0.5 + 0.5 * N.y;
        color += diffuseColor * SKY_COLOR * skyDiff * ao;
    }

    // back light / rim light
    {
        vec3 backDir = normalize(vec3(-SUN_DIR.x, 0.0, -SUN_DIR.z));
        float backDiff = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
        color += diffuseColor * vec3(0.15, 0.1, 0.08) * backDiff * ao;
    }

    // environment reflection (simplified)
    {
        vec3 R = reflect(-V, N);
        vec3 envColor = mix(BACKGROUND_BOT, BACKGROUND_TOP, clamp(R.y * 0.5 + 0.5, 0.0, 1.0));
        vec3 F_env = F_Schlick(F0, NdotV);
        float envOcc = clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
        color += F_env * envColor * envOcc * (1.0 - roughness * 0.7);
    }

    return color;
}

// ========== Raymarching ==========
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        float d = map(ro + rd * t);
        if (d < 0.001) return t;
        t += d;
        if (t > 50.0) break;
    }
    return -1.0;
}

// ========== Background ==========
vec3 background(vec3 rd) {
    vec3 col = mix(BACKGROUND_BOT, BACKGROUND_TOP, clamp(rd.y * 0.5 + 0.5, 0.0, 1.0));
    float sun = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    col += SUN_COLOR * 0.3 * pow(sun, 8.0);
    col += SUN_COLOR * 1.0 * pow(sun, 256.0);
    return col;
}

// ========== Main Function ==========
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    float angle = iTime * 0.3;
    vec3 ro = vec3(3.0 * cos(angle), 1.5, 3.0 * sin(angle));
    vec3 ta = vec3(0.0, 0.0, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.5 * ww);

    vec3 col = background(rd);
    float t = raymarch(ro, rd);

    if (t > 0.0) {
        vec3 pos = ro + t * rd;
        vec3 N = calcNormal(pos);
        vec3 V = -rd;
        vec3 albedo = ALBEDO;
        float roughness = ROUGHNESS;
        float metallic = METALLIC;

        if (pos.y < -0.99) {
            roughness = 0.8;
            metallic = 0.0;
            float checker = mod(floor(pos.x) + floor(pos.z), 2.0);
            albedo = mix(vec3(0.3), vec3(0.6), checker);
        }

        col = shade(pos, N, V, albedo, roughness, metallic);
    }

    col = col / (col + vec3(1.0));       // Tone mapping (Reinhard)
    col = pow(col, vec3(1.0 / 2.2));     // Gamma
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Classic Phong (Non-PBR)

```glsl
vec3 R = reflect(-L, N);
float spec = pow(max(0.0, dot(R, V)), 32.0);
vec3 color = albedo * lightColor * NdotL + lightColor * spec;
```

### Variant 2: Point Light Attenuation

```glsl
float dist = length(lightPos - pos);
float attenuation = 1.0 / (1.0 + dist * 0.1 + dist * dist * 0.01);
color *= attenuation;
```

### Variant 3: IBL (Image-Based Lighting)

```glsl
// diffuse IBL: spherical harmonics
vec3 diffuseIBL = diffuseColor * SHIrradiance(N);

// specular IBL: EnvBRDFApprox
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

```glsl
// SDF-based interior probing
float subsurface(vec3 pos, vec3 L) {
    float sss = 0.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.05 + float(i) * 0.1;
        float d = map(pos + L * h);
        sss += max(0.0, h - d);
    }
    return clamp(1.0 - sss * 4.0, 0.0, 1.0);
}

// Henyey-Greenstein phase function
float HenyeyGreenstein(float cosTheta, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5) * 4.0 * PI);
}
float sssAmount = HenyeyGreenstein(dot(V, L), 0.5);
color += sssColor * sssAmount * NdotL;
```

### Variant 5: Beer's Law Water Lighting

```glsl
vec3 waterExtinction(float depth) {
    float opticalDepth = depth * 6.0;
    vec3 extinctColor = 1.0 - vec3(0.5, 0.4, 0.1);
    return exp2(-opticalDepth * extinctColor);
}
vec3 underwaterColor = objectColor * waterExtinction(depth);
vec3 inscatter = waterDiffuse * (1.0 - exp(-depth * 0.1));
underwaterColor += inscatter;
```

## Performance & Composition

- **Fresnel optimization**: Use `x2*x2*x` instead of `pow(x, 5.0)`
- **Visibility term**: Use `V_SmithGGX` to directly return `G/(4*NdotV*NdotL)`, avoiding separate division
- **AO sampling**: 5 samples is sufficient; can reduce to 3 at far distances
- **Soft shadow**: `clamp(h, 0.02, 0.2)` limits step size; 14~24 steps usually sufficient; `8.0*h/t` controls softness
- **Simplified IBL**: Without cubemap, approximate with `mix(groundColor, skyColor, R.y*0.5+0.5)`
- **Branch culling**: Skip specular calculation when `NdotL <= 0`
- **Raymarching integration**: Use SDF finite differences for normals, query SDF directly for AO/shadows
- **Volume rendering integration**: Beer's Law attenuation + Henyey-Greenstein phase function; FBM noise procedural normals can be passed directly to lighting functions
- **Post-processing integration**: ACES `(col*(2.51*col+0.03))/(col*(2.43*col+0.59)+0.14)` / Reinhard `col/(col+1)` + Gamma
- **Reflection integration**: `reflect(rd, N)` to query scene again, blend result with Fresnel weighting

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/lighting-model.md)
