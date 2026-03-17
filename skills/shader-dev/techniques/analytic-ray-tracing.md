# Analytic Ray Tracing

## Use Cases

- Rendering scenes composed of geometric primitives (spheres, planes, boxes, cylinders, ellipsoids, etc.)
- Requiring precise surface intersection points, normals, and distance calculations (no iterative approximation)
- Building the underlying geometry engine for ray tracers / path tracers
- Scenes requiring accurate shadows, reflections, and refractions

## Core Principles

Substitute the ray equation `P(t) = O + tD` into the geometric body's implicit equation to obtain an algebraic equation in `t`, then solve it in closed form.

**Unified intersection workflow**: Build equation -> Simplify to standard form -> Discriminant test -> Take smallest positive root -> Compute gradient at intersection for normal

**Key formulas**:
- **Sphere** `|P-C|^2 = r^2` -> Quadratic equation
- **Plane** `N·P + d = 0` -> Linear equation
- **Box** Intersection of three pairs of parallel planes -> Slab Method
- **Ellipsoid** `|P/R|^2 = 1` -> Sphere intersection in scaled space
- **Torus** `(|P_xy| - R)^2 + P_z^2 = r^2` -> Quartic equation

## Implementation Steps

### Step 1: Ray Generation

```glsl
vec3 generateRay(vec2 fragCoord, vec2 resolution, vec3 ro, vec3 ta) {
    vec2 p = (2.0 * fragCoord - resolution) / resolution.y;
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0)));
    vec3 cv = cross(cu, cw);
    float fov = 1.5;
    return normalize(p.x * cu + p.y * cv + fov * cw);
}
```

### Step 2: Ray-Sphere Intersection

```glsl
// Optimized version with sphere center at origin
float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d1 = -b - h;
    float d2 = -b + h;
    if (d1 >= distBound.x && d1 <= distBound.y) {
        normal = normalize(ro + rd * d1);
        return d1;
    } else if (d2 >= distBound.x && d2 <= distBound.y) {
        normal = normalize(ro + rd * d2);
        return d2;
    }
    return MAX_DIST;
}
```

```glsl
// General version, supports arbitrary sphere center (sph = vec4(center.xyz, radius))
float sphIntersect(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    return -b - sqrt(h);
}
```

### Step 3: Ray-Plane Intersection

```glsl
float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    if (denom > 0.0) return MAX_DIST;
    float d = -(dot(ro, planeNormal) + planeDist) / denom;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = planeNormal;
    return d;
}

// fast horizontal ground plane
float iGroundPlane(vec3 ro, vec3 rd, float height) {
    return -(ro.y - height) / rd.y;
}
```

### Step 4: Ray-Box Intersection (Slab Method)

```glsl
float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8);
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF <= 0.0) return MAX_DIST;
    if (tN >= distBound.x && tN <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tN;
    } else if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tF;
    }
    return MAX_DIST;
}
```

### Step 5: Ray-Ellipsoid Intersection

```glsl
// Transform to unit sphere space for intersection, transform normal back to original space
float iEllipsoid(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 rad) {
    vec3 ocn = ro / rad;
    vec3 rdn = rd / rad;
    float a = dot(rdn, rdn);
    float b = dot(ocn, rdn);
    float c = dot(ocn, ocn);
    float h = b * b - a * (c - 1.0);
    if (h < 0.0) return MAX_DIST;
    float d = (-b - sqrt(h)) / a;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = normalize((ro + d * rd) / rad);
    return d;
}
```

### Step 6: Ray-Cylinder Intersection (With End Caps)

```glsl
// pa, pb: cylinder axis endpoints, ra: radius
float iCylinder(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
                vec3 pa, vec3 pb, float ra) {
    vec3 ca = pb - pa;
    vec3 oc = ro - pa;
    float caca = dot(ca, ca);
    float card = dot(ca, rd);
    float caoc = dot(ca, oc);
    float a = caca - card * card;
    float b = caca * dot(oc, rd) - caoc * card;
    float c = caca * dot(oc, oc) - caoc * caoc - ra * ra * caca;
    float h = b * b - a * c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d = (-b - h) / a;
    float y = caoc + d * card;
    if (y > 0.0 && y < caca && d >= distBound.x && d <= distBound.y) {
        normal = (oc + d * rd - ca * y / caca) / ra;
        return d;
    }
    d = ((y < 0.0 ? 0.0 : caca) - caoc) / card;
    if (abs(b + a * d) < h && d >= distBound.x && d <= distBound.y) {
        normal = normalize(ca * sign(y) / caca);
        return d;
    }
    return MAX_DIST;
}
```

### Step 7: Scene Intersection and Shading

```glsl
#define MAX_DIST 1e10

vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0);
    vec3 tmpNormal;
    float t;

    t = iPlane(ro, rd, d.xy, normal, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; }

    t = iSphere(ro - vec3(0, 0.5, 0), rd, d.xy, tmpNormal, 0.5);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmpNormal; }

    t = iBox(ro - vec3(2, 0.5, 0), rd, d.xy, tmpNormal, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmpNormal; }

    return d;
}

vec3 shade(vec3 pos, vec3 normal, vec3 rd, vec3 albedo) {
    vec3 lightDir = normalize(vec3(-1.0, 0.75, 1.0));
    float diff = max(dot(normal, lightDir), 0.0);
    float amb = 0.5 + 0.5 * normal.y;
    return albedo * (amb * 0.2 + diff * 0.8);
}
```

> **IMPORTANT: Critical pitfall**: `d.xy` must be passed as distBound, and `d.y` must be updated each time a closer intersection is found! If the deployed code passes the original `dist` directly without updating, the intersection logic will fail (all object distance tests become invalid), resulting in a completely black screen.

```glsl
#define MAX_BOUNCES 4
#define EPSILON 0.001

float schlickFresnel(float cosTheta, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 radiance(vec3 ro, vec3 rd) {
    vec3 color = vec3(0.0);
    vec3 mask = vec3(1.0);
    vec3 normal;
    for (int i = 0; i < MAX_BOUNCES; i++) {
        vec3 res = worldHit(ro, rd, vec2(EPSILON, MAX_DIST), normal);
        if (res.z < 0.5) {
            color += mask * vec3(0.6, 0.8, 1.0);
            break;
        }
        vec3 hitPos = ro + rd * res.y;
        vec3 albedo = getAlbedo(res.z);
        float F = schlickFresnel(max(0.0, dot(normal, -rd)), 0.04);
        color += mask * (1.0 - F) * shade(hitPos, normal, rd, albedo);
        mask *= F * albedo;
        rd = reflect(rd, normal);
        ro = hitPos + EPSILON * rd;
    }
    return color;
}
```

## Complete Code Template

Runs directly on ShaderToy, includes sphere, plane, and box primitives with reflection and Blinn-Phong shading.

> **IMPORTANT: Must follow**: All intersection function calls must use `d.xy` as the `distBound` parameter, and update `d.y` after each closer intersection is found. Incorrect usage: `iSphere(ro, rd, dist, ...)` (always using the original dist). Correct usage: `iSphere(ro, rd, d.xy, ...)` followed by `if (t < d.y) { d.y = t; ... }` to update.

```glsl
// Analytic Ray Tracing - Complete ShaderToy Template
#define MAX_DIST 1e10
#define EPSILON 0.001
#define MAX_BOUNCES 3
#define FOV 1.5
#define GAMMA 2.2
#define SHADOW_ENABLED true

float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d1 = -b - h, d2 = -b + h;
    if (d1 >= distBound.x && d1 <= distBound.y) { normal = normalize(ro + rd * d1); return d1; }
    if (d2 >= distBound.x && d2 <= distBound.y) { normal = normalize(ro + rd * d2); return d2; }
    return MAX_DIST;
}

float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    if (denom > 0.0) return MAX_DIST;
    float d = -(dot(ro, planeNormal) + planeDist) / denom;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = planeNormal;
    return d;
}

float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8);
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;
    vec3 t1 = -n - k, t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF <= 0.0) return MAX_DIST;
    if (tN >= distBound.x && tN <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz); return tN;
    }
    if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz); return tF;
    }
    return MAX_DIST;
}

struct Material { vec3 albedo; float specular; float roughness; };

Material getMaterial(float matId, vec3 pos) {
    if (matId < 1.5) {
        float checker = mod(floor(pos.x) + floor(pos.z), 2.0);
        return Material(vec3(0.4 + 0.4 * checker), 0.02, 0.8);
    } else if (matId < 2.5) { return Material(vec3(1.0, 0.2, 0.2), 0.5, 0.3); }
    else if (matId < 3.5) { return Material(vec3(0.2, 0.4, 1.0), 0.1, 0.6); }
    else if (matId < 4.5) { return Material(vec3(1.0, 1.0, 1.0), 0.8, 0.05); }
    else { return Material(vec3(0.8, 0.6, 0.2), 0.3, 0.4); }
}

vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0); vec3 tmp; float t;
    t = iPlane(ro, rd, d.xy, tmp, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; normal = tmp; }
    t = iSphere(ro - vec3(-2.0, 1.0, 0.0), rd, d.xy, tmp, 1.0);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmp; }
    t = iSphere(ro - vec3(0.0, 0.6, 2.0), rd, d.xy, tmp, 0.6);
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmp; }
    t = iSphere(ro - vec3(2.0, 0.8, -1.0), rd, d.xy, tmp, 0.8);
    if (t < d.y) { d.y = t; d.z = 4.0; normal = tmp; }
    t = iBox(ro - vec3(0.0, 0.5, -2.0), rd, d.xy, tmp, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 5.0; normal = tmp; }
    return d;
}

float shadow(vec3 ro, vec3 rd, float maxDist) {
    vec3 normal;
    vec3 res = worldHit(ro, rd, vec2(EPSILON, maxDist), normal);
    return res.z > 0.5 ? 0.3 : 1.0;
}

float schlick(float cosTheta, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 skyColor(vec3 rd) {
    vec3 col = mix(vec3(1.0), vec3(0.5, 0.7, 1.0), 0.5 + 0.5 * rd.y);
    vec3 sunDir = normalize(vec3(-0.4, 0.7, -0.6));
    float sun = clamp(dot(sunDir, rd), 0.0, 1.0);
    col += vec3(1.0, 0.6, 0.1) * (pow(sun, 4.0) + 10.0 * pow(sun, 32.0));
    return col;
}

vec3 render(vec3 ro, vec3 rd) {
    vec3 color = vec3(0.0), mask = vec3(1.0), normal;
    for (int bounce = 0; bounce < MAX_BOUNCES; bounce++) {
        vec3 res = worldHit(ro, rd, vec2(EPSILON, 100.0), normal);
        if (res.z < 0.5) { color += mask * skyColor(rd); break; }
        vec3 hitPos = ro + rd * res.y;
        Material mat = getMaterial(res.z, hitPos);
        vec3 lightDir = normalize(vec3(-0.4, 0.7, -0.6));
        float diff = max(dot(normal, lightDir), 0.0);
        float amb = 0.5 + 0.5 * normal.y;
        float sha = SHADOW_ENABLED ? shadow(hitPos + normal * EPSILON, lightDir, 50.0) : 1.0;
        vec3 halfVec = normalize(lightDir - rd);
        float spec = pow(max(dot(normal, halfVec), 0.0), 1.0 / max(mat.roughness, 0.001));
        float F = schlick(max(0.0, dot(normal, -rd)), 0.04 + 0.96 * mat.specular);
        vec3 diffCol = mat.albedo * (amb * 0.15 + diff * sha * 0.85);
        vec3 specCol = vec3(spec * sha);
        color += mask * mix(diffCol, specCol, F * mat.specular);
        mask *= F * mat.albedo;
        if (length(mask) < 0.01) break;
        rd = reflect(rd, normal);
        ro = hitPos + normal * EPSILON;
    }
    return color;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    float angle = 0.3 * iTime;
    vec3 ro = vec3(4.0 * cos(angle), 2.5, 4.0 * sin(angle));
    vec3 ta = vec3(0.0, 0.5, 0.0);
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0)));
    vec3 cv = cross(cu, cw);
    vec3 rd = normalize(p.x * cu + p.y * cv + FOV * cw);
    vec3 col = render(ro, rd);
    col = col / (1.0 + col);
    col = pow(col, vec3(1.0 / GAMMA));
    fragColor = vec4(col, 1.0);
}
```

## Common Variants

### Variant 1: Path Tracing

```glsl
vec3 cosWeightedRandomHemisphereDirection(vec3 n, inout uint seed) {
    uint ri = seed * 1103515245u + 12345u;
    seed = ri;
    float r1 = float(ri) / float(0xFFFFFFFFu);
    ri = seed * 1103515245u + 12345u;
    seed = ri;
    float r2 = float(ri) / float(0xFFFFFFFFu);
    vec3 uu = normalize(cross(n, abs(n.y) > 0.5 ? vec3(1,0,0) : vec3(0,1,0)));
    vec3 vv = cross(uu, n);
    float ra = sqrt(r1);
    float rx = ra * cos(6.2831 * r2);
    float ry = ra * sin(6.2831 * r2);
    float rz = sqrt(1.0 - r1);
    return normalize(rx * uu + ry * vv + rz * n);
}
// In the bounce loop, replace reflect with:
// rd = cosWeightedRandomHemisphereDirection(normal, seed);
// ro = hitPos + EPSILON * rd;
// mask *= mat.albedo;
```

### Variant 2: Analytic Soft Shadow

```glsl
float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    float t = -b - sqrt(max(h, 0.0));
    return (t > 0.0) ? max(d, 0.0) / t : 1.0;
}
```

### Variant 3: Analytic Anti-Aliasing

```glsl
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    return vec2(d, -b - sqrt(max(h, 0.0)));
}
// float px = 2.0 / iResolution.y;
// vec2 dt = sphDistances(ro, rd, sph);
// float coverage = 1.0 - clamp(dt.x / (dt.y * px), 0.0, 1.0);
// col = mix(bgColor, sphereColor, coverage);
```

### Variant 4: Refraction (Snell's Law)

```glsl
// Requires a random number function defined first
float hash1(float p) {
    return fract(sin(p) * 43758.5453);
}

// Add refraction branch in the render loop:
float refrIndex = 1.5; // glass ~ 1.5, water ~ 1.33
bool inside = dot(rd, normal) > 0.0;
vec3 n = inside ? -normal : normal;
float eta = inside ? refrIndex : 1.0 / refrIndex;
vec3 refracted = refract(rd, n, eta);
float cosI = abs(dot(rd, n));
float F = schlick(cosI, pow((1.0 - eta) / (1.0 + eta), 2.0));
// Use bounce count as random seed
float randSeed = float(bounce) + 1.0;
if (refracted != vec3(0.0) && hash1(randSeed * 12.9898) > F) {
    rd = refracted;
} else {
    rd = reflect(rd, n);
}
ro = hitPos + rd * EPSILON;
```

### Variant 5: Higher-Order Algebraic Surface (Sphere4)

```glsl
float iSphere4(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float ra) {
    float r2 = ra * ra;
    vec3 d2 = rd*rd, d3 = d2*rd;
    vec3 o2 = ro*ro, o3 = o2*ro;
    float ka = 1.0 / dot(d2, d2);
    float k0 = ka * dot(ro, d3);
    float k1 = ka * dot(o2, d2);
    float k2 = ka * dot(o3, rd);
    float k3 = ka * (dot(o2, o2) - r2 * r2);
    float c0 = k1 - k0 * k0;
    float c1 = k2 + 2.0 * k0 * (k0 * k0 - 1.5 * k1);
    float c2 = k3 - 3.0 * k0 * (k0 * (k0 * k0 - 2.0 * k1) + 4.0/3.0 * k2);
    float p = c0 * c0 * 3.0 + c2;
    float q = c0 * c0 * c0 - c0 * c2 + c1 * c1;
    float h = q * q - p * p * p * (1.0/27.0);
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float s = sign(q+h) * pow(abs(q+h), 1.0/3.0);
    float t = sign(q-h) * pow(abs(q-h), 1.0/3.0);
    vec2 v = vec2((s+t) + c0*4.0, (s-t) * sqrt(3.0)) * 0.5;
    float r = length(v);
    float d = -abs(v.y) / sqrt(r + v.x) - c1/r - k0;
    if (d >= distBound.x && d <= distBound.y) {
        vec3 pos = ro + rd * d;
        normal = normalize(pos * pos * pos);
        return d;
    }
    return MAX_DIST;
}
```

## Common Errors and Safeguards

### Error 1: Distance Bound Not Updated
**Symptom**: Screen is completely black or shows only background
**Cause**: `distBound.y` not updated after each intersection
**Fix**:
```glsl
// WRONG:
t = iSphere(ro, rd, dist, tmpNormal, 1.0);

// CORRECT:
t = iSphere(ro, rd, d.xy, tmpNormal, 1.0);
if (t < d.y) { d.y = t; d.z = matId; normal = tmpNormal; }
```

### Error 2: EPSILON Too Small Causing Self-Intersection Artifacts
**Symptom**: Black spots or artifacts on object surfaces
**Cause**: `EPSILON` value too small, ray still intersects with itself
**Fix**: Adjust EPSILON based on scene scale; typical values 1e-3 ~ 1e-2

### Error 3: Variable Used as Loop Upper Bound
**Symptom**: WebGL2 compilation failure or shader crash
**Cause**: In GLSL ES 3.0, `for` loop upper bounds must be constants
**Fix**: Use `#define` for loop upper bounds, and keep bounds to 4-5 iterations max

### Error 4: Division by Zero Causing NaN
**Symptom**: Stripe patterns from NaN propagation across the screen
**Cause**: Division not protected when ray direction components are zero
**Fix**: Always use `max(abs(x), 1e-8)` or similar protection

### Error 5: Missing Hash Function in Refraction Variant
**Symptom**: Compilation error "undefined function 'hash1'"
**Fix**: Add the function definition when using the refraction variant:
```glsl
float hash1(float p) {
    return fract(sin(p) * 43758.5453);
}
```

## Performance & Composition

**Performance tips**:
- **Distance bound clipping**: Shorten `distBound.y` after each closer intersection; subsequent objects are automatically skipped
- **Bounding sphere pre-test**: Pre-screen with bounding sphere for complex geometry (torus, etc.)
- **Shadow ray simplification**: Only need to determine occlusion, no normal calculation needed
- **Avoid unnecessary sqrt**: Return early when discriminant is negative; `c > 0.0 && b > 0.0` for fast rejection
- **Grid acceleration**: Use 3D DDA grid traversal for large numbers of similar primitives

**Composition approaches**:
- **+ Raymarching SDF**: Analytic primitives define major structures, SDF handles complex details
- **+ Volume effects**: Analytic intersection provides precise entry/exit distances for volume sampling within the range
- **+ PBR materials**: Precise normals plug directly into Cook-Torrance and other BRDFs
- **+ Spatial transforms**: Rotate/translate rays to reuse the same intersection functions
- **+ Analytic AA/AO/soft shadows**: Fully analytic pipeline, zero noise

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/analytic-ray-tracing.md)
