# Path Tracing & Global Illumination - Detailed Reference

This document is a complete reference for [SKILL.md](SKILL.md), covering prerequisite knowledge, step-by-step detailed explanations, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL basic syntax**: ShaderToy multi-pass (Buffer A/B/Image) architecture
- **Vector math**: Dot product, cross product, reflection/refraction vector computation
- **Probability fundamentals**: PDF (probability density function), Monte Carlo integration, importance sampling
- **Rendering equation** basic form: $L_o = L_e + \int f_r \cdot L_i \cdot \cos\theta \, d\omega$
- **Ray-geometry intersection** methods (spheres, planes, SDF)

## Core Principles in Detail

Path tracing solves the rendering equation via Monte Carlo methods. For each pixel, a ray is emitted from the camera and bounces through the scene. At each bounce:

1. **Intersection**: Find the nearest intersection of the ray with the scene
2. **Shading**: Compute the lighting contribution at the current node based on material type (diffuse/specular/refractive)
3. **Sample next direction**: Generate the next bounce ray according to the BRDF/BSDF
4. **Accumulate**: Add the weighted lighting contributions from all nodes along the path

### Core Mathematics

- **Rendering equation**: $L_o(x, \omega_o) = L_e(x, \omega_o) + \int_\Omega f_r(x, \omega_i, \omega_o) L_i(x, \omega_i) (\omega_i \cdot n) d\omega_i$
- **Monte Carlo estimate**: $L \approx \frac{1}{N} \sum \frac{f_r \cdot L_i \cdot \cos\theta}{p(\omega)}$
- **Schlick Fresnel**: $F = F_0 + (1 - F_0)(1 - \cos\theta)^5$
- **Cosine-weighted sampling PDF**: $p(\omega) = \frac{\cos\theta}{\pi}$

### Key Design

An **iterative loop** replaces recursion, using two variables — `acc` (accumulated radiance) and `mask/throughput` (path attenuation) — to track path contributions. At each bounce, the material color is multiplied into the throughput, and self-emission and direct lighting are added to acc.

## Implementation Steps in Detail

### Step 1: Pseudorandom Number Generator

**What**: Provide a different random number sequence per pixel per frame, driving all Monte Carlo sampling.

**Why**: All random decisions in path tracing (direction sampling, Russian roulette, Fresnel selection) depend on random numbers. The seed must be sufficiently decorrelated between pixels and frames; otherwise structured noise will appear.

**Method 1: sin-hash (simple, good for getting started)**
```glsl
float seed;
float rand() { return fract(sin(seed++) * 43758.5453123); }
// Initialization: seed = iTime + iResolution.y * fragCoord.x / iResolution.x + fragCoord.y / iResolution.y;
```

**Method 2: Integer hash (better quality, recommended)**
```glsl
int iSeed;
int irand() { iSeed = iSeed * 0x343fd + 0x269ec3; return (iSeed >> 16) & 32767; }
float frand() { return float(irand()) / 32767.0; }
void srand(ivec2 p, int frame) {
    int n = frame;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.y;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.x;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    iSeed = n;
}
```

The sin-hash may produce periodic artifacts on some GPUs (due to inconsistent sin precision across hardware). The integer hash is more reliable and uniform. The Visual Studio LCG (`0x343fd`) is a commonly used linear congruential generator.

### Step 2: Ray-Scene Intersection

**What**: Given a ray origin and direction, find the nearest intersection along with normal and material information at the intersection point.

**Why**: This is the fundamental operation of path tracing. Either analytic geometry (spheres, planes) or SDF ray marching can be used.

**Analytic sphere intersection (classic smallpt approach)**
```glsl
struct Ray { vec3 o, d; };
struct Sphere { float r; vec3 p, e, c; int refl; };

float intersectSphere(Sphere s, Ray r) {
    vec3 op = s.p - r.o;
    float b = dot(op, r.d);
    float det = b * b - dot(op, op) + s.r * s.r;
    if (det < 0.) return 0.;
    det = sqrt(det);
    float t = b - det;
    if (t > 1e-3) return t;
    t = b + det;
    return t > 1e-3 ? t : 0.;
}
```

Derivation: Ray $r(t) = o + td$, sphere $|p - c|^2 = R^2$, substitution yields quadratic $t^2 - 2b \cdot t + c = 0$, where $b = (c - o) \cdot d$, discriminant $\Delta = b^2 - |c - o|^2 + R^2$. The epsilon of `1e-3` prevents self-intersection.

**SDF ray marching (for complex geometry)**
```glsl
float map(vec3 p) { /* returns distance to nearest surface */ }

float raymarch(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 256; i++) {
        float h = map(ro + rd * t);
        if (abs(h) < 0.0001 || t > tmax) break;
        t += h;
    }
    return t;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.0001, 0.);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)));
}
```

The principle of SDF marching: each step safely advances by the "distance to the nearest surface," ensuring no surface is crossed. The step count (128-256) and threshold (0.0001) represent a tradeoff between accuracy and performance.

### Step 3: Cosine-Weighted Hemisphere Sampling

**What**: Generate a random direction distributed according to cosine weighting on the hemisphere above the surface normal, used for diffuse bounces.

**Why**: Cosine-weighted sampling (Malley's method) matches the Lambertian BRDF distribution with PDF $\cos\theta / \pi$, simplifying BRDF/PDF to just the albedo and greatly reducing variance.

With uniform hemisphere sampling (PDF = $1/2\pi$), each bounce would need an extra multiplication by $\cos\theta \cdot 2$, and variance would be higher since many sample directions contribute very little to the integral.

**Method 1: fizzer method (most concise)**
```glsl
vec3 cosineDirection(vec3 nor) {
    float u = frand();
    float v = frand();
    float a = 6.2831853 * v;
    float b = 2.0 * u - 1.0;
    vec3 dir = vec3(sqrt(1.0 - b * b) * vec2(cos(a), sin(a)), b);
    return normalize(nor + dir); // fizzer method
}
```

Principle: Uniformly sampling a point on the unit sphere and adding the normal direction, then normalizing, naturally produces a cosine distribution. This works because uniform points on the unit sphere, projected onto the hemisphere above the normal, naturally form a cosine distribution.

**Method 2: Classic ONB construction (more intuitive)**
```glsl
vec3 cosineDirectionONB(vec3 n) {
    vec2 r = vec2(frand(), frand());
    vec3 u = normalize(cross(n, vec3(0., 1., 1.)));
    vec3 v = cross(u, n);
    float ra = sqrt(r.y);
    float rx = ra * cos(6.2831853 * r.x);
    float ry = ra * sin(6.2831853 * r.x);
    float rz = sqrt(1.0 - r.y);
    return normalize(rx * u + ry * v + rz * n);
}
```

Principle: First build an orthonormal basis (ONB) with n as the z-axis, then sample in local coordinates using Malley's method: map uniform random numbers onto the unit disk ($r = \sqrt{\xi_2}$, $\phi = 2\pi\xi_1$), with z-component $\sqrt{1 - r^2}$.

### Step 4: Material System and BRDF Evaluation

**What**: Based on the material type at the intersection (diffuse, specular, refractive), determine the ray's next direction and energy attenuation.

**Why**: Different materials respond to light completely differently. Diffuse scatters randomly, specular reflects perfectly, and refractive materials follow Snell's law. The Fresnel effect determines the reflection/refraction ratio.

```glsl
#define MAT_DIFFUSE  0
#define MAT_SPECULAR 1
#define MAT_DIELECTRIC 2
```

**Diffuse**:
- New direction = `cosineDirection(normal)`
- `throughput *= albedo`
- Because cosine-weighted sampling is used, BRDF($1/\pi$) * $\cos\theta$ / PDF($\cos\theta/\pi$) = 1, so throughput only needs to be multiplied by albedo

**Specular**:
- New direction = `reflect(rd, normal)`
- `throughput *= albedo`
- A perfect mirror's BRDF is a delta function; only one direction contributes

**Refractive (glass)**:
```glsl
void handleDielectric(inout Ray r, vec3 n, vec3 x, float ior,
                      vec3 albedo, inout vec3 mask) {
    float cosi = dot(n, r.d);
    float eta = cosi > 0. ? ior : 1.0 / ior;       // Entering/leaving medium
    vec3 nl = cosi > 0. ? -n : n;                    // Outward-facing normal
    cosi = abs(cosi);

    float cos2t = 1.0 - eta * eta * (1.0 - cosi * cosi);
    r = Ray(x, reflect(r.d, n));                      // Default to reflection

    if (cos2t > 0.) {
        vec3 tdir = normalize(r.d / eta + nl * (cosi / eta - sqrt(cos2t)));
        // Schlick Fresnel
        float R0 = ((ior - 1.) * (ior - 1.)) / ((ior + 1.) * (ior + 1.));
        float c = 1.0 - (cosi > 0. ? dot(tdir, n) : cosi);
        float Re = R0 + (1.0 - R0) * c * c * c * c * c;
        float P = 0.25 + 0.5 * Re;
        if (frand() < P) {
            mask *= Re / P;                            // Reflection
        } else {
            mask *= albedo * (1.0 - Re) / (1.0 - P);  // Refraction
            r = Ray(x, tdir);
        }
    }
}
```

Key points:
- **Snell's law**: $n_1 \sin\theta_1 = n_2 \sin\theta_2$; total internal reflection occurs when $\sin\theta_2 > 1$
- **Schlick approximation**: $R(\theta) = R_0 + (1-R_0)(1-\cos\theta)^5$, where $R_0 = ((n_1-n_2)/(n_1+n_2))^2$
- **Russian Roulette selection**: Instead of selecting directly by `Re`, an adjusted probability `P = 0.25 + 0.5 * Re` is used, then compensated through the mask. This avoids the problem of almost always choosing refraction when Re is low

### Step 5: Direct Light Sampling (Next Event Estimation)

**What**: At each diffuse intersection, directly cast a shadow ray toward the light source to compute direct lighting contribution.

**Why**: Purely random paths are unlikely to hit small-area light sources. Directly sampling light sources greatly reduces variance and accelerates convergence.

```glsl
// Solid angle sampling of spherical light source
vec3 directLighting(vec3 x, vec3 n, vec3 albedo,
                    vec3 lightPos, float lightRadius, vec3 lightEmission,
                    int selfId) {
    vec3 l0 = lightPos - x;
    float cos_a_max = sqrt(1.0 - clamp(lightRadius * lightRadius / dot(l0, l0), 0., 1.));
    float cosa = mix(cos_a_max, 1.0, frand());
    float sina = sqrt(1.0 - cosa * cosa);
    float phi = 6.2831853 * frand();

    // Sample within the cone toward the light source
    vec3 w = normalize(l0);
    vec3 u = normalize(cross(w.yzx, w));
    vec3 v = cross(w, u);
    vec3 l = (u * cos(phi) + v * sin(phi)) * sina + w * cosa;

    // Shadow test
    if (shadowTest(Ray(x, l), selfId, lightId)) {
        float omega = 6.2831853 * (1.0 - cos_a_max); // Solid angle
        return albedo * lightEmission * clamp(dot(l, n), 0., 1.) * omega / 3.14159265;
    }
    return vec3(0.);
}
```

Mathematical derivation:
- Solid angle subtended by spherical light at the shading point: $\omega = 2\pi(1 - \cos\alpha_{max})$, where $\cos\alpha_{max} = \sqrt{1 - R^2/d^2}$
- PDF for uniform sampling within the cone: $p = 1/\omega$
- Direct lighting contribution: $L_{direct} = \frac{f_r \cdot L_e \cdot \cos\theta_{light}}{p} = albedo \cdot L_e \cdot \cos\theta \cdot \omega / \pi$

Note: With NEE enabled, indirect bounces that hit the light source should **not** accumulate its emission again (to avoid double-counting). However, in smallpt-style implementations where the light source is large, this double-counting has negligible impact. The strict approach is to skip the indirect hit light emission when NEE is active.

### Step 6: Path Tracing Main Loop

**What**: Combine all the above modules into a complete path tracer.

**Why**: The iterative structure avoids GLSL's lack of recursion support, while the throughput/acc pattern is the standard path tracing implementation paradigm.

```glsl
#define MAX_BOUNCES 8       // Adjustable: max bounce count; more = more accurate indirect lighting
#define ENABLE_NEE true     // Adjustable: whether to enable direct light sampling

vec3 pathtrace(Ray r) {
    vec3 acc = vec3(0.);        // Accumulated radiance
    vec3 throughput = vec3(1.); // Path attenuation (throughput)

    for (int depth = 0; depth < MAX_BOUNCES; depth++) {
        // 1. Intersection
        float t;
        vec3 n, albedo, emission;
        int matType;
        if (!intersectScene(r, t, n, albedo, emission, matType))
            break; // Shot into the sky

        vec3 x = r.o + r.d * t;
        vec3 nl = dot(n, r.d) < 0. ? n : -n; // Outward-facing normal

        // 2. Accumulate emission
        acc += throughput * emission;

        // 3. Russian roulette (starting from bounce 3)
        if (depth > 2) {
            float p = max(throughput.r, max(throughput.g, throughput.b));
            if (frand() > p) break;
            throughput /= p;
        }

        // 4. Sample based on material
        if (matType == MAT_DIFFUSE) {
            // Direct light sampling (NEE)
            if (ENABLE_NEE)
                acc += throughput * directLighting(x, nl, albedo, ...);
            // Indirect bounce
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, cosineDirection(nl));

        } else if (matType == MAT_SPECULAR) {
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, reflect(r.d, n));

        } else if (matType == MAT_DIELECTRIC) {
            handleDielectric(r, n, x, 1.5, albedo, throughput);
        }
    }
    return acc;
}
```

Key design points:
- `acc` accumulates the final color, `throughput` records the attenuation from all materials along the path
- Russian roulette maintains **unbiasedness**: termination probability is $1-p$, surviving paths divide throughput by $p$, so the expected value is unchanged
- Normal offset (`x + nl * 1e-3`) prevents self-intersection due to floating-point precision

### Step 7: Progressive Accumulation and Display

**What**: Perform weighted averaging of multi-frame results, progressively converging to a noise-free image. Apply tone mapping and gamma correction for display.

**Why**: A single frame of path tracing is extremely noisy. Through multi-frame accumulation, sample count grows linearly and noise decreases as $1/\sqrt{N}$.

**Buffer A (path tracing + accumulation)**
```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    srand(ivec2(fragCoord), iFrame);
    // ... camera setup, ray generation ...
    vec3 color = pathtrace(ray);

    // Progressive accumulation
    vec4 prev = texelFetch(iChannel0, ivec2(fragCoord), 0);
    if (iFrame == 0) prev = vec4(0.);
    fragColor = prev + vec4(color, 1.0);
}
```

Accumulation strategy: Store each frame's color and sample count in RGBA (RGB = color accumulation, A = sample count accumulation). Divide by A when displaying to get the average. Clear to zero when `iFrame == 0` to handle ShaderToy's edit reset.

**Image Pass (tone mapping + gamma)**
```glsl
vec3 ACES(vec3 x) {
    float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return (x * (a * x + b)) / (x * (c * x + d) + e);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 data = texelFetch(iChannel0, ivec2(fragCoord), 0);
    vec3 col = data.rgb / max(data.a, 1.0);

    col = ACES(col);                         // Tone mapping
    col = pow(col, vec3(1.0 / 2.2));         // Gamma correction

    // Optional: vignette
    vec2 uv = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);

    fragColor = vec4(col, 1.0);
}
```

ACES tone mapping compresses HDR radiance values into the [0,1] LDR range while preserving detail in highlights and shadows. Gamma correction (2.2) converts linear color space to sRGB display space.

## Common Variants in Detail

### 1. SDF Scene Path Tracing

**Difference from base version**: Replaces analytic sphere intersection with SDF ray marching, supporting arbitrarily complex geometry (fractals, boolean operations, etc.).

Challenges of SDF path tracing:
- SDF marching is much slower than analytic intersection (each step requires 128+ iterations)
- Numerical normals (central difference) are needed at each bounce, adding 6 extra `map()` calls
- Self-intersection issues are more severe, requiring larger epsilon offsets

```glsl
float map(vec3 p) {
    float d = p.y + 0.5;                        // Ground
    d = min(d, length(p - vec3(0., 0.4, 0.)) - 0.4); // Sphere
    return d;
}

float intersectScene(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 128; i++) {
        float h = map(ro + rd * t);
        if (h < 0.0001 || t > tmax) break;
        t += h;
    }
    return t < tmax ? t : -1.0;
}
// Normal via central difference: calcNormal()
// Materials distinguished by ID returned from map()
```

### 2. Disney BRDF Path Tracing

**Difference from base version**: Replaces simple Lambert + perfect mirror with the Disney principled BRDF, supporting metallic/roughness parameterized PBR materials.

Core components of the Disney BRDF:
- **GGX normal distribution (D)**: Describes the statistical distribution of microsurface normals; higher roughness = wider distribution
- **Smith occlusion function (G)**: Accounts for self-shadowing between microsurfaces
- **Fresnel term (F)**: Schlick approximation; metallic controls F0 (metals: F0 = albedo, dielectrics: F0 = 0.04)
- **VNDF sampling**: Visible Normal Distribution Function sampling, more efficient than traditional GGX sampling

```glsl
struct Material {
    vec3 albedo;
    float metallic;   // 0=dielectric, 1=metal
    float roughness;  // 0=smooth, 1=rough
};

// GGX normal distribution
float D_GGX(float a2, float NoH) {
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}

// Smith occlusion function
float G_Smith(float NoV, float NoL, float a2) {
    float g1 = (2.0 * NoV) / (NoV + sqrt(a2 + (1.0 - a2) * NoV * NoV));
    float g2 = (2.0 * NoL) / (NoL + sqrt(a2 + (1.0 - a2) * NoL * NoL));
    return g1 * g2;
}

// VNDF sampling for importance sampling GGX
vec3 SampleGGXVNDF(vec3 V, float ax, float ay, float r1, float r2) {
    vec3 Vh = normalize(vec3(ax * V.x, ay * V.y, V.z));
    float lensq = Vh.x * Vh.x + Vh.y * Vh.y;
    vec3 T1 = lensq > 0. ? vec3(-Vh.y, Vh.x, 0) * inversesqrt(lensq) : vec3(1, 0, 0);
    vec3 T2 = cross(Vh, T1);
    float r = sqrt(r1);
    float phi = 2.0 * PI * r2;
    float t1 = r * cos(phi), t2 = r * sin(phi);
    float s = 0.5 * (1.0 + Vh.z);
    t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;
    vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0., 1. - t1*t1 - t2*t2)) * Vh;
    return normalize(vec3(ax * Nh.x, ay * Nh.y, max(0., Nh.z)));
}
```

When using the Disney BRDF in path tracing, the sampling strategy typically is:
- Use metallic as the probability to choose between diffuse and specular
- Diffuse uses cosine-weighted sampling
- Specular uses VNDF sampling for GGX

### 3. Depth of Field

**Difference from base version**: Uses a thin lens model to simulate the bokeh effect of real cameras.

Principle of the thin lens model: All rays passing through the focal point converge to the same point. By randomly offsetting the ray origin within the aperture while keeping the target point on the focal plane unchanged, the depth of field effect can be simulated.

```glsl
#define APERTURE 0.12    // Adjustable: aperture size; larger = stronger bokeh
#define FOCUS_DIST 8.0   // Adjustable: focus distance

// In mainImage, after generating the ray:
vec3 focalPoint = ro + rd * FOCUS_DIST;
vec3 offset = ca * vec3(uniformDisk() * APERTURE, 0.);
ro += offset;
rd = normalize(focalPoint - ro);

vec2 uniformDisk() {
    vec2 r = vec2(frand(), frand());
    float a = 6.2831853 * r.x;
    return sqrt(r.y) * vec2(cos(a), sin(a));
}
```

Parameter tuning suggestions:
- `APERTURE`: 0.01 (almost no bokeh) to 0.5 (strong bokeh)
- `FOCUS_DIST`: Set to the distance from the camera to the object you want in sharp focus
- Bokeh effects require more samples to converge (since an extra random dimension is added)

### 4. Multiple Importance Sampling (MIS)

**Difference from base version**: Uses both BRDF sampling and light source sampling simultaneously, combining them with the power heuristic, achieving low variance across all scene configurations.

Core idea of MIS: A single sampling strategy may have high variance in certain scene configurations (e.g., NEE performs poorly on glossy surfaces, BRDF sampling performs poorly with small light sources). MIS combines multiple strategies to compensate for each other's weaknesses.

```glsl
// Power heuristic (beta=2)
float misWeight(float pdfA, float pdfB) {
    float a2 = pdfA * pdfA;
    float b2 = pdfB * pdfB;
    return a2 / (a2 + b2);
}

// During shading, compute both:
// 1. BRDF sampled direction -> if it hits a light, weight with misWeight(brdfPdf, lightPdf)
// 2. Light sampled direction -> weight with misWeight(lightPdf, brdfPdf)
// Sum of both replaces the single sampling strategy
```

The power heuristic ($\beta=2$) formula: $w_A = p_A^2 / (p_A^2 + p_B^2)$. Veach proved in his thesis that this is nearly optimal.

### 5. Volumetric Path Tracing (Participating Media)

**Difference from base version**: Performs random walks inside the medium, simulating translucent/subsurface scattering effects via Beer-Lambert attenuation and scattering events.

Core concepts of volumetric rendering:
- **Extinction coefficient** = absorption + scattering
- **Beer-Lambert law**: Transmittance $T = e^{-\sigma_t \cdot d}$
- **Scattering event**: Scattering occurs with probability $\sigma_s / \sigma_t$ (vs. absorption)
- **Phase function**: Determines the distribution of scattering directions. Uniform sphere sampling = isotropic scattering, Henyey-Greenstein = controllable forward/backward scattering

```glsl
// Beer-Lambert transmittance attenuation
vec3 transmittance = exp(-extinction * distance);

// Random walk scattering
float scatterDist = -log(frand()) / extinctionMajorant;
if (scatterDist < hitDist) {
    // Scattering event occurs
    pos += ray.d * scatterDist;
    // Sample new direction with phase function (e.g., uniform or Henyey-Greenstein)
    ray.d = uniformSphereSample();
    throughput *= albedo; // scattering / extinction
}
```

Henyey-Greenstein phase function:
- Parameter g in [-1, 1]: g > 0 forward scattering, g < 0 backward scattering, g = 0 isotropic
- $p(\cos\theta) = \frac{1-g^2}{4\pi(1+g^2-2g\cos\theta)^{3/2}}$

## Performance Optimization Details

### 1. Sampling Strategy
1-4 samples per pixel per frame, relying on inter-frame accumulation for convergence. This maintains real-time frame rates while eventually reaching high quality. For ShaderToy, `SAMPLES_PER_FRAME = 1` or `2` is usually the best choice, since more samples per frame lower the frame rate without accelerating visual convergence.

### 2. Russian Roulette
Starting from bounce 3-4, use the maximum throughput component as the survival probability. This terminates low-energy paths early while maintaining unbiasedness.
```glsl
float p = max(throughput.r, max(throughput.g, throughput.b));
if (frand() > p) break;
throughput /= p;
```
Mathematical guarantee: Termination probability $q = 1 - p$, surviving path throughput multiplied by $1/p$, so the expected value $E[L] = p \cdot L/p + (1-p) \cdot 0 = L$, unbiased.

### 3. Direct Light Sampling (NEE)
Always explicitly sample the light source on diffuse surfaces, avoiding dependence on random paths hitting the light. Particularly significant for small-area light sources. When the light source subtends a very small fraction of the hemisphere's solid angle, pure BRDF sampling can almost never hit the light; NEE is essential.

### 4. Avoiding Self-Intersection
Offset the intersection point along the normal direction (epsilon = 1e-3 ~ 1e-4), or record the last-hit object ID and skip self-intersection. Both approaches have tradeoffs:
- Normal offset: Simple and universal, but may penetrate thin objects
- ID skipping: Precise, but not suitable for concave objects (which may need self-intersection)

### 5. Firefly Suppression
Clamp extreme brightness with `min(color, 10.)` to prevent firefly noise spots. ACES tone mapping also helps compress high dynamic range. The root cause of fireflies is that certain paths find high-energy but low-probability light transport paths, resulting in extremely large Monte Carlo estimate values.

### 6. SDF Scene Optimization
- Limit the maximum marching steps (128-256); treat exceeding the limit as a miss
- Set a reasonable maximum trace distance (tmax) to cull distant objects
- Use larger epsilon during bounces (SDF numerical precision is typically worse than analytic geometry)
- "Relaxed sphere tracing" can be used to increase step size when safe

### 7. High-Quality PRNG
Use integer hashes (such as Visual Studio LCG or Wang hash) instead of sin-hash to avoid periodic artifacts on some GPUs. The problem with sin-hash is that sin precision differs across GPUs (some use only mediump), which can produce visible structured noise.

## Combination Suggestions in Detail

### 1. Path Tracing + SDF Modeling
Use SDF to define complex scene geometry (fractals, smooth boolean operations) while path tracing handles lighting computation. This is the most common combination on ShaderToy. SDF's advantage is the ability to easily create shapes difficult to express with traditional meshes (Mandelbulb, Menger sponge, etc.), while path tracing provides physically accurate lighting for these complex geometries.

### 2. Path Tracing + Environment Maps
Use an HDR cubemap as an infinitely distant environment light source. When a path shoots into the sky, sample the environment map for incident radiance. Can be combined with atmospheric scattering models for a more physically accurate sky.
```glsl
// When path misses the scene:
if (!hit) {
    acc += throughput * texture(iChannel1, rd).rgb; // HDR environment map
    break;
}
```

### 3. Path Tracing + PBR Materials
The Disney BRDF/BSDF provides metallic/roughness parameterized material models, combined with GGX microsurface distribution and VNDF importance sampling for production-quality results. In ShaderToy, material parameters can be generated procedurally (based on position, noise, etc.).

### 4. Path Tracing + Volumetric Rendering
Add participating media to the path tracing framework, using Beer-Lambert law for transmittance and random walks for scattering, to achieve clouds, smoke, subsurface scattering, and other effects.
```glsl
// Add volume check in the path tracing loop:
if (insideVolume) {
    float scatterDist = -log(frand()) / sigma_t;
    if (scatterDist < surfaceDist) {
        // Volume scattering event
        x = r.o + r.d * scatterDist;
        r.d = samplePhaseFunction(r.d, g);
        throughput *= sigma_s / sigma_t; // albedo
        continue;
    }
}
```

### 5. Path Tracing + Spectral Rendering
Each path samples a single wavelength instead of RGB, using Sellmeier/Cauchy equations to compute wavelength-dependent index of refraction, and finally converts to sRGB through CIE XYZ color matching functions. This correctly simulates dispersion and rainbow caustics.

Basic spectral rendering workflow:
1. Each path randomly selects a wavelength λ in [380, 780] nm
2. Compute the index of refraction for that wavelength using the Sellmeier equation: $n^2 = 1 + \sum B_i \lambda^2 / (\lambda^2 - C_i)$
3. All color computations in path tracing become single-channel (spectral power at that wavelength)
4. Finally convert spectral radiance to XYZ via CIE XYZ color matching functions, then to sRGB

### 6. Path Tracing + Temporal Accumulation / TAA
Leverage ShaderToy's inter-frame buffer feedback mechanism for progressive rendering. Can be further extended to temporal reprojection, reusing historical frame data during camera movement to accelerate convergence.

Basic temporal reprojection:
1. Store the previous frame's camera matrix
2. Reproject the current pixel into the previous frame's screen space
3. If the position is valid and geometrically consistent, blend the historical frame with the current frame
4. Otherwise discard historical data and restart accumulation
