# Matrix Transforms & Camera — Detailed Reference

This document is the complete detailed version of [SKILL.md](SKILL.md), covering step-by-step tutorials, mathematical derivations, detailed explanations, and advanced usage.

## Prerequisites

- **Vector Fundamentals**: Meaning of `vec2/vec3/vec4`, dot product `dot()`, cross product `cross()`, `normalize()`
- **Matrix Fundamentals**: Column-major storage of `mat2/mat3/mat4` in GLSL, semantics of matrix multiplication `m * v`
- **Coordinate Systems**: NDC (Normalized Device Coordinates), screen-space to world-space mapping, aspect ratio correction
- **Trigonometry**: Relationship between `sin()`/`cos()` and rotation
- **ShaderToy Built-in Variables**: `iResolution`, `iTime`, `iMouse`, `fragCoord`

## Core Principles

The essence of matrix transforms is **coordinate system transformation**. In ShaderToy's ray marching pipeline, transformation matrices serve two key roles:

1. **Camera Matrix**: Converts screen pixel coordinates to ray directions in world space (view-to-world)
2. **Object Transform Matrix**: Converts sampling points from world space to the object's local space (world-to-local, i.e., "domain transform")

### Key Mathematical Formulas

**2D Rotation Matrix** (rotation by angle θ around the origin):

```
R(θ) = | cos θ  -sin θ |
       | sin θ   cos θ |
```

**3D Single-Axis Rotation** (rotation around Y axis as example):

```
Ry(θ) = | cos θ   0   sin θ |
        |   0     1     0   |
        | -sin θ  0   cos θ |
```

**Rodrigues' Rotation Formula** (rotation by angle θ around arbitrary axis **k**):

```
R = cos θ · I + (1 - cos θ) · k⊗k + sin θ · K
```
where K is the skew-symmetric matrix of axis vector k.

**LookAt Camera** (looking from eye toward target):

```
forward = normalize(target - eye)
right   = normalize(cross(forward, worldUp))
up      = cross(right, forward)
viewMatrix = mat3(right, up, forward)
```

**Perspective Ray Generation**:

```
rayDir = normalize(camMatrix * vec3(uv, focalLength))
```

where `uv` is the aspect-ratio-corrected screen coordinate, and `focalLength` controls the field of view (larger values produce smaller FOV).

## Implementation Steps

### Step 1: Screen Coordinate Normalization and Aspect Ratio Correction

**What**: Convert pixel coordinates `fragCoord` to normalized UV coordinates centered at the screen center, with Y-axis pointing up and correct aspect ratio.

**Why**: All subsequent ray generation depends on correctly normalized screen coordinates. Without aspect ratio correction, circles would become ellipses.

**Code**:
```glsl
// Method A: range [-aspect, aspect] x [-1, 1] (most common)
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Method B: step-by-step approach (equivalent)
vec2 uv = fragCoord / iResolution.xy * 2.0 - 1.0;
uv.x *= iResolution.x / iResolution.y;
```

### Step 2: Building Rotation Matrices

**What**: Choose the appropriate rotation matrix construction method based on requirements.

**Why**: Rotation is the core of all 3D transforms. Different scenarios suit different rotation representations.

**Method A: 2D Rotation (mat2)**

The simplest form, commonly used for two-plane rotations in camera orbits:
```glsl
mat2 rot2D(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c); // Note GLSL column-major order
}
```

**Method B: 3D Single-Axis Rotation (mat3)**

Separate X/Y/Z axis rotation functions that can be freely combined:
```glsl
mat3 rotX(float a) {
    float s = sin(a), c = cos(a);
    return mat3(1, 0, 0,  0, c, s,  0, -s, c);
}
mat3 rotY(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, 0, s,  0, 1, 0,  -s, 0, c);
}
mat3 rotZ(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, s, 0,  -s, c, 0,  0, 0, 1);
}
```

**Method C: Euler Angles to mat3**

Build a complete rotation matrix from three angles (yaw/pitch/roll) in one step:
```glsl
mat3 fromEuler(vec3 ang) {
    vec2 a1 = vec2(sin(ang.x), cos(ang.x));
    vec2 a2 = vec2(sin(ang.y), cos(ang.y));
    vec2 a3 = vec2(sin(ang.z), cos(ang.z));
    mat3 m;
    m[0] = vec3( a1.y*a3.y + a1.x*a2.x*a3.x,
                  a1.y*a2.x*a3.x + a3.y*a1.x,
                 -a2.y*a3.x);
    m[1] = vec3(-a2.y*a1.x, a1.y*a2.y, a2.x);
    m[2] = vec3( a3.y*a1.x*a2.x + a1.y*a3.x,
                  a1.x*a3.x - a1.y*a3.y*a2.x,
                  a2.y*a3.y);
    return m;
}
```

**Method D: Rodrigues Arbitrary-Axis Rotation (mat3)**

Rotation around any normalized axis, based on Rodrigues' formula:
```glsl
mat3 rotationMatrix(vec3 axis, float angle) {
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat3(
        oc*axis.x*axis.x + c,          oc*axis.x*axis.y - axis.z*s, oc*axis.z*axis.x + axis.y*s,
        oc*axis.x*axis.y + axis.z*s,   oc*axis.y*axis.y + c,        oc*axis.y*axis.z - axis.x*s,
        oc*axis.z*axis.x - axis.y*s,   oc*axis.y*axis.z + axis.x*s, oc*axis.z*axis.z + c
    );
}
```

### Step 3: Building a LookAt Camera

**What**: Construct a view-to-world matrix from the camera position (eye) and look-at target (target).

**Why**: LookAt is the most intuitive camera definition — just specify "where to stand" and "where to look", and the matrix automatically computes three orthogonal basis vectors.

**Classic setCamera (mat3)**:
```glsl
// cr = camera roll, usually pass 0.0
// Returns mat3 that transforms local ray direction to world space
mat3 setCamera(in vec3 ro, in vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);                   // forward
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);           // world up with roll
    vec3 cu = normalize(cross(cw, cp));               // right
    vec3 cv = normalize(cross(cu, cw));               // up
    return mat3(cu, cv, cw);
}
```

**Gram-Schmidt Orthogonalization Version (mat3)**:

Projects out the component of camUp along camDir to ensure strict orthogonality:
```glsl
vec3 camDir   = normalize(target - camPos);
vec3 camUp    = normalize(camUp - dot(camDir, camUp) * camDir); // Gram-Schmidt
vec3 camRight = normalize(cross(camDir, camUp));
```

**mat4 LookAt (with translation)**:

Returns a 4x4 matrix with the camera world position stored in the 4th column. Suitable for scenarios requiring homogeneous coordinates:
```glsl
mat4 LookAt(vec3 pos, vec3 target, vec3 up) {
    vec3 dir = normalize(target - pos);
    vec3 x = normalize(cross(dir, up));
    vec3 y = cross(x, dir);
    return mat4(vec4(x, 0), vec4(y, 0), vec4(dir, 0), vec4(pos, 1));
}
```

### Step 4: Generating Perspective Rays

**What**: Transform normalized screen coordinates through the camera matrix into world-space ray directions.

**Why**: Perspective projection simulates the near-large far-small effect by appending a fixed Z component (focal length) after the UV. Larger focal length means smaller FOV.

**Method A: mat3 Camera + normalize**:
```glsl
// focalLength controls FOV: 1.0 ≈ 90°, 2.0 ≈ 53°, 4.0 ≈ 28°
#define FOCAL_LENGTH 2.0 // Adjustable: focal length, larger = narrower FOV
mat3 cam = setCamera(ro, ta, 0.0);
vec3 rd = cam * normalize(vec3(uv, FOCAL_LENGTH));
```

**Method B: Manual Basis Vector Combination**:
```glsl
// FieldOfView controls ray divergence
#define FOV 1.0 // Adjustable: field of view scale factor
vec3 rd = normalize(camDir + (uv.x * camRight + uv.y * camUp) * FOV);
```

**Method C: mat4 Camera + Homogeneous Coordinates**:
```glsl
// Direction vectors use w=0, positions use w=1
mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```

### Step 5: Mouse-Interactive Camera

**What**: Map `iMouse` input to camera orbit angles.

**Why**: An interactive camera is a fundamental need for debugging and showcasing 3D shaders. Mapping mouse X to horizontal rotation and Y to pitch angle is the most universal pattern.

**Spherical Coordinate Orbit Camera**:
```glsl
#define CAM_DIST 5.0     // Adjustable: camera-to-origin distance
#define CAM_HEIGHT 1.0   // Adjustable: default height offset

vec2 mouse = iMouse.xy / iResolution.xy;
float angleH = mouse.x * 6.2832;         // Horizontal: 0 ~ 2π
float angleV = mouse.y * 3.1416 - 1.5708; // Vertical: -π/2 ~ π/2

// Use auto-rotation when mouse is not clicked
if (iMouse.z <= 0.0) {
    angleH = iTime * 0.5;
    angleV = 0.3;
}

vec3 ro = vec3(
    CAM_DIST * cos(angleH) * cos(angleV),
    CAM_DIST * sin(angleV) + CAM_HEIGHT,
    CAM_DIST * sin(angleH) * cos(angleV)
);
vec3 ta = vec3(0.0, 0.0, 0.0); // Look-at target
```

**Euler Angle Driven Camera**:
```glsl
vec3 ang = vec3(0.0, 0.2, iTime * 0.3); // Default animation
if (iMouse.z > 0.0) {
    ang = vec3(0.0, clamp(2.0 - iMouse.y * 0.01, 0.0, 3.1416), iMouse.x * 0.01);
}
mat3 rot = fromEuler(ang);
vec3 ori = vec3(0.0, 0.0, 2.8) * rot;
vec3 dir = normalize(vec3(uv, -2.0)) * rot;
```

### Step 6: SDF Object Domain Transforms (Translation, Rotation, Scaling)

**What**: In the ray marching distance function, apply inverse transforms to sampling points to achieve object translation/rotation/scaling.

**Why**: The SDF domain transform principle is "transform the space, not the object" — inversely transforming the sampling point into the object's local coordinate system to evaluate distance is equivalent to transforming the object itself.

**Basic Transforms**:
```glsl
// ===== Translation: offset the sampling point =====
float sdTranslated = sdSphere(p - vec3(2.0, 0.0, 0.0), 1.0);

// ===== Rotation: transform sampling point with rotation matrix =====
// Note: for orthogonal matrices (rotations), inverse = transpose
float sdRotated = sdBox(rotY(0.5) * p, vec3(1.0));

// ===== Scaling: divide by scale factor, multiply back into distance =====
#define SCALE 2.0 // Adjustable: object scale factor
float sdScaled = sdSphere(p / SCALE, 1.0) * SCALE;
```

**SRT Combination (Scale → Rotate → Translate)**:

mat4 version, using opTx for domain transform:
```glsl
mat4 Loc4(vec3 d) {
    d *= -1.0;
    return mat4(1,0,0,d.x, 0,1,0,d.y, 0,0,1,d.z, 0,0,0,1);
}

mat4 transposeM4(in mat4 m) {
    return mat4(
        vec4(m[0].x, m[1].x, m[2].x, m[3].x),
        vec4(m[0].y, m[1].y, m[2].y, m[3].y),
        vec4(m[0].z, m[1].z, m[2].z, m[3].z),
        vec4(m[0].w, m[1].w, m[2].w, m[3].w)
    );
}

vec3 opTx(vec3 p, mat4 m) {
    return (transposeM4(m) * vec4(p, 1.0)).xyz;
}

// Usage example: translate to (3,0,0), then rotate 45° around Y axis
mat4 xform = Rot4Y(0.785) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), vec3(1.0));
```

### Step 7: Quaternion Rotation (Advanced)

**What**: Use quaternions for rotation around arbitrary axes, suitable for joint animation and other scenarios requiring frequent rotation composition.

**Why**: Quaternions avoid gimbal lock, and interpolation (slerp) is more natural than matrices. The double cross product formula `p + 2·cross(q.xyz, cross(q.xyz, p) + q.w·p)` is the most computationally efficient quaternion rotation implementation.

```glsl
// Axis-angle → quaternion
vec4 axisAngleToQuat(vec3 axis, float angleDeg) {
    float half_angle = angleDeg * 3.14159265 / 360.0; // degrees to half-radians
    vec2 sc = sin(vec2(half_angle, half_angle + 1.5707963));
    return vec4(normalize(axis) * sc.x, sc.y);
}

// Quaternion rotation (double cross product form)
vec3 quatRotate(vec3 pos, vec3 axis, float angleDeg) {
    vec4 q = axisAngleToQuat(axis, angleDeg);
    return pos + 2.0 * cross(q.xyz, cross(q.xyz, pos) + q.w * pos);
}

// Usage example: hierarchical rotation in joint animation
vec3 limbPos = quatRotate(p - shoulderOffset, vec3(1,0,0), swingAngle);
float d = sdEllipsoid(limbPos, limbSize);
```

## Variant Details

### Variant 1: Orthographic Projection Camera

**Difference from basic version**: Ray direction is fixed (parallel rays); different pixel sampling is achieved by changing the ray origin position. Suitable for 2D-style rendering, engineering drawings, isometric views.

**Key modified code**:
```glsl
// Replace the perspective ray generation section
#define ORTHO_SIZE 5.0 // Adjustable: orthographic view size

mat3 cam = setCamera(ro, ta, 0.0);
// Orthographic: offset origin, fixed direction
vec3 rd = cam * vec3(0.0, 0.0, 1.0);  // Fixed direction
ro += cam * vec3(uv * ORTHO_SIZE, 0.0); // Offset origin
```

### Variant 2: Full Euler Angle Rotation Camera

**Difference from basic version**: Does not use LookAt; instead builds the rotation matrix directly from three Euler angles. Suitable for first-person perspective or scenarios requiring roll.

**Key modified code**:
```glsl
mat3 fromEuler(vec3 ang) {
    vec2 a1 = vec2(sin(ang.x), cos(ang.x));
    vec2 a2 = vec2(sin(ang.y), cos(ang.y));
    vec2 a3 = vec2(sin(ang.z), cos(ang.z));
    mat3 m;
    m[0] = vec3(a1.y*a3.y+a1.x*a2.x*a3.x, a1.y*a2.x*a3.x+a3.y*a1.x, -a2.y*a3.x);
    m[1] = vec3(-a2.y*a1.x, a1.y*a2.y, a2.x);
    m[2] = vec3(a3.y*a1.x*a2.x+a1.y*a3.x, a1.x*a3.x-a1.y*a3.y*a2.x, a2.y*a3.y);
    return m;
}

// In mainImage:
vec3 ang = vec3(pitch, yaw, roll);
mat3 rot = fromEuler(ang);
vec3 ori = vec3(0.0, 0.0, 3.0) * rot;
vec3 rd = normalize(vec3(uv, -2.0)) * rot;
```

### Variant 3: Quaternion Joint Rotation

**Difference from basic version**: Uses quaternions instead of matrices for rotation in domain transforms, suitable for hierarchical joint animation (multi-limbed biological systems).

**Key modified code**:
```glsl
vec4 axisAngleToQuat(vec3 axis, float angleDeg) {
    float ha = angleDeg * 3.14159265 / 360.0;
    vec2 sc = sin(vec2(ha, ha + 1.5707963));
    return vec4(normalize(axis) * sc.x, sc.y);
}

vec3 quatRotate(vec3 p, vec3 axis, float angleDeg) {
    vec4 q = axisAngleToQuat(axis, angleDeg);
    return p + 2.0 * cross(q.xyz, cross(q.xyz, p) + q.w * p);
}

// Usage in scene:
vec3 legP = quatRotate(p - hipOffset, vec3(1,0,0), legAngle);
float dLeg = sdEllipsoid(legP, vec3(0.2, 0.6, 0.25));
```

### Variant 4: mat4 SRT Pipeline (Full 4x4 Transform)

**Difference from basic version**: Uses `mat4` homogeneous coordinates to combine scale-rotate-translate into a single matrix, applying `opTx()` domain transform to sampling points. Suitable for complex scenes requiring management of many object transforms.

**Key modified code**:
```glsl
mat4 Rot4Y(float a) {
    float c = cos(a), s = sin(a);
    return mat4(c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1);
}

mat4 Loc4(vec3 d) {
    d *= -1.0;
    return mat4(1,0,0,d.x, 0,1,0,d.y, 0,0,1,d.z, 0,0,0,1);
}

mat4 transposeM4(mat4 m) {
    return mat4(
        vec4(m[0].x,m[1].x,m[2].x,m[3].x),
        vec4(m[0].y,m[1].y,m[2].y,m[3].y),
        vec4(m[0].z,m[1].z,m[2].z,m[3].z),
        vec4(m[0].w,m[1].w,m[2].w,m[3].w));
}

vec3 opTx(vec3 p, mat4 m) {
    return (transposeM4(m) * vec4(p, 1.0)).xyz;
}

// Usage: translate then rotate (note matrix multiplication order is right-to-left)
mat4 xform = Rot4Y(angle) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), boxSize);
```

### Variant 5: Path Camera (Animated Flight)

**Difference from basic version**: The camera moves along a predefined path (e.g., tunnel, racetrack), using `LookAt` to track a forward target point. Common in tunnel-type shaders.

**Key modified code**:
```glsl
// Path function (can be replaced with any curve)
vec2 pathCenter(float z) {
    return vec2(sin(z * 0.17) * 3.0, sin(z * 0.1 + 4.0) * 2.0);
}

// In mainImage:
float z_offset = iTime * 10.0; // Speed
vec3 camPos = vec3(pathCenter(z_offset), 0.0);
vec3 camTarget = vec3(pathCenter(z_offset + 5.0), 5.0);
vec3 camUp = vec3(sin(iTime * 0.3), cos(iTime * 0.3), 0.0);

mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```

## Performance Optimization Details

### 1. Precompute Trigonometric Functions

Compute `sin/cos` of the same angle only once, store in `vec2`:
```glsl
// Bad: sin/cos each called once
mat2(cos(a), sin(a), -sin(a), cos(a));

// Good: compute both with sincos in one step
vec2 sc = sin(vec2(a, a + 1.5707963)); // sin(a), cos(a)
mat2(sc.y, sc.x, -sc.x, sc.y);
```

### 2. Prefer mat3 Over mat4

If translation is not needed (pure rotation), always use `mat3` instead of `mat4`. `mat3*vec3` requires 7 fewer multiply-add operations than `mat4*vec4`.

### 3. Inverse of Rotation Matrix = Transpose

Orthogonal rotation matrix R satisfies `R⁻¹ = Rᵀ`. When the inverse transform is needed, directly use `transpose(m)` or swap the multiplication order `v * m` (equivalent to `transpose(m) * v`), avoiding general matrix inversion.

### 4. Avoid Rebuilding Matrices Inside the SDF

If the rotation angle does not depend on the sampling point `p`, move matrix construction outside the `map()` function or cache it in a global variable:
```glsl
// Bad: rebuild matrix on every map() call
float map(vec3 p) {
    mat3 r = rotY(iTime); // Recomputed per pixel × per step
    return sdBox(r * p, vec3(1.0));
}

// Good: precompute in mainImage
mat3 g_rot; // Global
void mainImage(...) {
    g_rot = rotY(iTime); // Computed only once
    // ... rayMarch ...
}
float map(vec3 p) {
    return sdBox(g_rot * p, vec3(1.0));
}
```

### 5. Merge Consecutive Rotations

The product of multiple rotation matrices is still a rotation matrix. Pre-multiply and store as a single matrix:
```glsl
// Bad: two matrix multiplications per sample
p = rotX(a) * (rotY(b) * p);

// Good: pre-multiply
mat3 combined = rotX(a) * rotY(b);
p = combined * p;
```

## Combination Suggestions

### Combining with Ray Marching / SDF (Most Common)

Matrix transforms are almost always used together with SDF ray marching. The camera matrix generates rays, and domain transform matrices place objects. This is the foundational pipeline for all 3D ShaderToy shaders.

### Combining with Noise / fBm

Use rotation matrices to apply domain warping to noise sampling coordinates, breaking axis-aligned regularity:
```glsl
mat3 rot = rotAxis(vec3(0,0,1), 0.5 * iTime);
float n = fbm(rot * p);  // Rotate noise sampling direction
```
Using time-varying rotation matrices makes water surface noise look more natural.

### Combining with Fractals / IFS

Add rotation transforms within each iteration of a fractal to create more complex geometric patterns:
```glsl
for (int i = 0; i < Iterations; i++) {
    z.xy = rot2D(angle) * z.xy; // Rotate each iteration
    z = abs(z);
    z = Scale * z - Offset * (Scale - 1.0);
}
```
Embedding `mat2` rotation within IFS iterations produces more complex fractal geometry.

### Combining with Lighting / Materials

After normal computation, transform matrices can be used to convert normals from local space back to world space (for lighting calculations). For pure rotation matrices, the normal transform is identical to the vertex transform.

### Combining with Post-Processing

Camera parameters (such as FOV) can be used for depth of field calculations; `mat2` rotation can be used for screen-space chromatic aberration or motion blur direction.
