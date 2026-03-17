# Ray Marching Detailed Reference

This document serves as a detailed reference for the Ray Marching Skill, covering prerequisites, step-by-step tutorials, mathematical derivations, and advanced usage.

## Prerequisites

- **GLSL Basics**: uniforms, varyings, built-in functions (`mix`, `clamp`, `smoothstep`, `normalize`, `dot`, `cross`, `reflect`, `refract`)
- **Vector Math**: dot product, cross product, vector normalization, matrix multiplication
- **Coordinate Systems**: transformations from screen space to NDC to view space to world space
- **Basic Lighting Models**: diffuse (Lambertian), specular (Phong/Blinn-Phong)

## Implementation Steps in Detail

### Step 1: UV Coordinate Normalization and Ray Direction Computation

**What**: Convert pixel coordinates to normalized coordinates in the [-1,1] range, and compute the ray direction from the camera.

**Why**: This establishes the mapping from screen pixels to the 3D world. Dividing by `iResolution.y` preserves the aspect ratio; the z component controls the field of view.

```glsl
// Method A: Concise version (common for quick prototyping)
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
vec3 ro = vec3(0.0, 0.0, -3.0);             // Ray origin (camera position)
vec3 rd = normalize(vec3(uv, 1.0));          // Ray direction, z=1.0 gives ~90° FOV

// Method B: Precise FOV control
vec2 xy = fragCoord - iResolution.xy / 2.0;
float z = iResolution.y / tan(radians(FOV) / 2.0); // FOV is adjustable: field of view in degrees
vec3 rd = normalize(vec3(xy, -z));
```

### Step 2: Building the Camera Matrix (Look-At)

**What**: Construct a view matrix from the camera position, target point, and up direction, then transform the view-space ray direction into world space.

**Why**: Without a camera matrix, the ray direction is fixed along -Z. With a Look-At matrix, the camera can be freely positioned and rotated.

```glsl
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);                     // Forward direction
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);            // Up reference (cr controls roll)
    vec3 cu = normalize(cross(cw, cp));                // Right direction
    vec3 cv = cross(cu, cw);                           // Up direction
    return mat3(cu, cv, cw);
}

// Usage:
mat3 ca = setCamera(ro, ta, 0.0);
vec3 rd = ca * normalize(vec3(uv, FOCAL_LENGTH)); // FOCAL_LENGTH adjustable: 1.0~3.0, larger = narrower FOV
```

### Step 3: Defining the Scene SDF

**What**: Write a function that returns the signed distance from any point in space to the nearest surface.

**Why**: The SDF is the core of Ray Marching — it simultaneously defines geometry and step distance.

```glsl
// --- Basic SDF Primitives ---
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// --- CSG Boolean Operations ---
float opUnion(float a, float b)        { return min(a, b); }
float opSubtraction(float a, float b)  { return max(a, -b); }
float opIntersection(float a, float b) { return max(a, b); }

// --- Smooth Boolean Operations (organic blending) ---
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;  // k adjustable: blend radius, 0.1~0.5
}

// --- Spatial Transforms ---
// Translation: apply inverse translation to the sample point
// Rotation: multiply the sample point by a rotation matrix
// Scaling: p /= s, result *= s

// --- Scene Composition Example ---
float map(vec3 p) {
    float d = sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5);   // Sphere
    d = opUnion(d, p.y);                                    // Add ground plane
    d = smin(d, sdBox(p - vec3(1.0, 0.3, 0.0), vec3(0.3)), 0.2); // Smooth blend with box
    return d;
}
```

### Step 4: Core Ray Marching Loop

**What**: Iteratively step along the ray direction, using the SDF value at each step to determine the advance distance, and check whether the ray has hit a surface or exceeded the maximum range.

**Why**: Sphere Tracing guarantees that each step advances the maximum safe distance (without penetrating surfaces), taking large steps in open areas and automatically slowing down near surfaces.

```glsl
#define MAX_STEPS 128   // Adjustable: max step count, 64~256, more = more precise but slower
#define MAX_DIST 100.0  // Adjustable: max travel distance
#define SURF_DIST 0.001 // Adjustable: surface hit threshold, 0.0001~0.01

float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < SURF_DIST) return t;   // Surface hit
        t += d;
        if (t > MAX_DIST) break;        // Out of range
    }
    return -1.0; // No hit
}
```

### Step 5: Normal Estimation

**What**: Compute the surface normal at the hit point using the numerical gradient of the SDF.

**Why**: Normals are the foundation of lighting calculations. The gradient direction of the SDF is the surface normal direction.

```glsl
// Method A: Central differences (6 SDF calls, straightforward)
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);  // e.x adjustable: differentiation step size
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Method B: Tetrahedron trick (4 SDF calls, prevents compiler inline bloat, recommended)
vec3 calcNormal(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = 0; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.001 * e);
    }
    return normalize(n);
}
```

### Step 6: Lighting and Shading

**What**: Compute Phong lighting (ambient + diffuse + specular) at the hit point.

**Why**: Give SDF surfaces realistic shading with highlights and shadow gradients.

```glsl
vec3 shade(vec3 p, vec3 rd) {
    vec3 nor = calcNormal(p);
    vec3 lightDir = normalize(vec3(0.6, 0.35, 0.5));   // Light direction (adjustable)
    vec3 viewDir = -rd;
    vec3 halfDir = normalize(lightDir + viewDir);

    // Diffuse
    float diff = clamp(dot(nor, lightDir), 0.0, 1.0);
    // Specular
    float spec = pow(clamp(dot(nor, halfDir), 0.0, 1.0), SHININESS); // SHININESS adjustable: 8~64
    // Ambient + sky light
    float sky = sqrt(clamp(0.5 + 0.5 * nor.y, 0.0, 1.0));

    vec3 col = vec3(0.2, 0.2, 0.25);             // Material base color (adjustable)
    vec3 lin = vec3(0.0);
    lin += diff * vec3(1.3, 1.0, 0.7) * 2.2;     // Main light
    lin += sky  * vec3(0.4, 0.6, 1.15) * 0.6;    // Sky light
    lin += vec3(0.25) * 0.55;                      // Fill light
    col *= lin;
    col += spec * vec3(1.3, 1.0, 0.7) * 5.0;     // Specular highlight

    return col;
}
```

### Step 7: Post-Processing (Gamma Correction and Tone Mapping)

**What**: Convert linear lighting results to sRGB space and apply tone mapping to prevent overexposure.

**Why**: GPU computations are done in linear space, but displays require gamma-corrected values. Tone mapping compresses HDR values into the [0,1] range.

```glsl
// Gamma correction
col = pow(col, vec3(0.4545));  // i.e., 1/2.2

// Optional: Reinhard tone mapping (before gamma)
col = col / (1.0 + col);

// Optional: Vignette
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.25);
```

## Common Variants in Detail

### 1. Volumetric Ray Marching

**Difference from the basic version**: Instead of finding a surface intersection, the ray advances in **fixed steps**, accumulating density/color at each step. Used for flames, smoke, and clouds.

**Key modified code**:
```glsl
#define VOL_STEPS 150       // Adjustable: volume sample count
#define VOL_STEP_SIZE 0.05  // Adjustable: step size

// Density field (built with FBM noise)
float fbmDensity(vec3 p) {
    float den = 0.2 - p.y;                                    // Base height falloff
    vec3 q = p - vec3(0.0, 1.0, 0.0) * iTime;
    float f  = 0.5000 * noise(q); q = q * 2.02 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.2500 * noise(q); q = q * 2.03 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.1250 * noise(q); q = q * 2.01 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.0625 * noise(q);
    return den + 4.0 * f;
}

// Volumetric marching main function
vec3 volumetricMarch(vec3 ro, vec3 rd) {
    vec4 sum = vec4(0.0);
    float t = 0.05;
    for (int i = 0; i < VOL_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float den = fbmDensity(pos);
        if (den > 0.0) {
            den = min(den, 1.0);
            vec3 col = mix(vec3(1.0, 0.5, 0.05), vec3(0.48, 0.53, 0.5),
                           clamp(pos.y * 0.5, 0.0, 1.0));  // Fire-to-smoke color gradient
            col *= den;
            col.a = den * 0.6;
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);                     // Front-to-back compositing
            if (sum.a > 0.99) break;                         // Early exit
        }
        t += VOL_STEP_SIZE;
    }
    return clamp(sum.rgb, 0.0, 1.0);
}
```

### 2. CSG Scene Construction (Constructive Solid Geometry)

**Difference from the basic version**: Combines multiple SDF primitives using `min` (union), `max` (intersection), and `max(a,-b)` (subtraction), along with rotation/translation transforms to create complex mechanical parts.

**Key modified code**:
```glsl
float sceneSDF(vec3 p) {
    p = rotateY(iTime * 0.5) * p;                                // Rotate entire scene

    float sphere = sdSphere(p, 1.2);
    float cube = sdBox(p, vec3(0.9));
    float cyl = sdCylinder(p, vec2(0.4, 2.0));                   // Vertical cylinder
    float cylX = sdCylinder(p.yzx, vec2(0.4, 2.0));              // X-axis cylinder (swizzled)
    float cylZ = sdCylinder(p.xzy, vec2(0.4, 2.0));              // Z-axis cylinder

    // Sphere ∩ Cube - three-axis cylinders = nut shape
    return opSubtraction(
        opIntersection(sphere, cube),
        opUnion(cyl, opUnion(cylX, cylZ))
    );
}
```

### 3. Physically-Based Volumetric Scattering

**Difference from the basic version**: Uses physically correct extinction coefficients, scattering coefficients, and transmittance formulas, with volumetric shadows (marching toward the light source to compute transmittance). Based on Frostbite engine's energy-conserving integration formula.

**Key modified code**:
```glsl
void getParticipatingMedia(out float sigmaS, out float sigmaE, vec3 pos) {
    float heightFog = 0.3 * clamp((7.0 - pos.y), 0.0, 1.0);  // Height fog
    sigmaS = 0.02 + heightFog;                                  // Scattering coefficient
    sigmaE = max(0.000001, sigmaS);                              // Extinction coefficient (includes absorption)
}

// Energy-conserving scattering integral (Frostbite improved version)
vec3 S = lightColor * sigmaS * phaseFunction() * volShadow;     // Incoming light
vec3 Sint = (S - S * exp(-sigmaE * stepLen)) / sigmaE;          // Integrate current step
scatteredLight += transmittance * Sint;                          // Accumulate
transmittance *= exp(-sigmaE * stepLen);                         // Update transmittance
```

### 4. Glow Accumulation

**Difference from the basic version**: During the Ray March loop, additionally tracks the closest distance from the ray to the surface `dM`. Even without a hit, this produces a glow effect. Commonly used for glowing spheres and plasma.

**Key modified code**:
```glsl
vec2 rayMarchWithGlow(vec3 ro, vec3 rd) {
    float t = 0.0;
    float dMin = MAX_DIST;                    // Track minimum distance
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < dMin) dMin = d;               // Update closest distance
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return vec2(t, dMin);
}

// Add glow based on dMin during shading
float glow = 0.02 / max(dMin, 0.001);        // Closer = brighter
col += glow * vec3(1.0, 0.8, 0.9);
```

### 5. Refraction and Bidirectional Marching (Interior Marching)

**Difference from the basic version**: After hitting a surface, computes the refraction direction and marches **inside the object in reverse** (negating the SDF) to find the exit point. Can achieve glass, water, and liquid metal effects.

**Key modified code**:
```glsl
// Bidirectional marching: determine SDF sign based on whether the origin is inside or outside
float castRay(vec3 ro, vec3 rd) {
    float sign = (map(ro) < 0.0) ? -1.0 : 1.0;   // Negate distance if inside
    float t = 0.0;
    for (int i = 0; i < 120; i++) {
        float h = sign * map(ro + rd * t);
        if (abs(h) < 0.0001 || t > 12.0) break;
        t += h;
    }
    return t;
}

// Refraction: after hitting the outer surface, march inside along the refracted direction
vec3 refDir = refract(rd, nor, IOR);                // IOR adjustable: index of refraction, e.g., 0.9
float t2 = 2.0;
for (int i = 0; i < 50; i++) {
    float h = map(hitPos + refDir * t2);
    t2 -= h;                                         // Reverse marching (from inside outward)
    if (abs(h) > 3.0) break;
}
vec3 nor2 = calcNormal(hitPos + refDir * t2);        // Exit point normal
```

## Performance Optimization in Detail

### 1. Reducing SDF Call Count

- Use the tetrahedron trick for normal computation (4 calls instead of 6 with central differences)
- Use `min(iFrame,0)` as the loop start value to prevent the compiler from unrolling and inlining map() multiple times

### 2. Bounding Box Acceleration

Perform AABB ray intersection before marching to skip empty regions:
```glsl
vec2 tb = iBox(ro - center, rd, halfSize);
if (tb.x < tb.y && tb.y > 0.0) { /* Only march inside the box */ }
```

### 3. Adaptive Precision

- Scale the hit threshold with distance: `SURF_DIST * (1.0 + t * 0.1)` — distant surfaces don't need high precision
- Clamp step size: `t += clamp(h, 0.01, 0.2)` — prevent individual steps from being too large or too small

### 4. Early Exit

- In volume rendering: `if (sum.a > 0.99) break;` — stop immediately when opaque
- In shadow computation: `if (res < 0.004) break;` — stop when fully occluded

### 5. Reducing map() Complexity

- Use simplified SDFs for distant objects
- First test with a cheap bounding SDF; only compute the expensive precise SDF when `sdBox(p, bound) < currentMin`

### 6. Anti-Aliasing

- Supersampling (AA=2 means 2x2 sampling, 4 rays per pixel), but at 4x performance cost
- In volume rendering, use dithering instead of supersampling to reduce banding artifacts

## Combination Suggestions in Detail

### 1. Ray Marching + FBM Noise

Use fractal noise to perturb SDF surfaces for terrain and rock textures, or build volumetric density fields to render clouds/smoke.

### 2. Ray Marching + Domain Warping

Apply spatial distortions (twist, bend, repeat) to sample points to create infinitely repeating corridors or twisted surreal geometry.

### 3. Ray Marching + PBR Materials

SDF provides geometry; combine with Cook-Torrance BRDF, environment map reflections, and Fresnel terms for realistic metal/dielectric materials.

### 4. Ray Marching + Post-Processing

Multi-pass architecture: the first Buffer performs Ray Marching and outputs color + depth (stored in the alpha channel); the second pass applies depth of field (DOF), motion blur, and tone mapping.

### 5. Ray Marching + Procedural Animation

Drive SDF primitive positions/sizes/blend coefficients with time parameters, combined with easing functions (smoothstep, parabolic) to create character animations without a skeletal system.
