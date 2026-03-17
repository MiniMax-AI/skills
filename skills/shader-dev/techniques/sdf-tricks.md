# SDF Advanced Tricks & Optimization

## Use Cases
- Optimizing complex SDF scenes for real-time performance
- Adding fine detail to SDF surfaces without increasing geometric complexity
- Creating special effects with SDF manipulation (hollowing, layered edges, interior structures)
- Debugging and visualizing SDF fields

## Core Techniques

### Hollowing (Shell Creation)
Convert any solid SDF into a thin shell:
```glsl
float hollowed = abs(sdf) - thickness;
// Example: hollow sphere with 0.02 wall thickness
float d = abs(sdSphere(p, 1.0)) - 0.02;
```

### Layered Edges (Concentric Contour Lines)
Create equidistant contour rings from any SDF:
```glsl
float spacing = 0.2;
float thickness = 0.02;
float layered = abs(mod(d + spacing * 0.5, spacing) - spacing * 0.5) - thickness;
```
Useful for: topographic map effects, neon outlines, energy shields, wireframe-like rendering.

### FBM Detail on SDF (Distance-Based LOD)
Add procedural noise detail only where it's visible — near the camera:
```glsl
float map(vec3 p) {
    float d = sdBasicShape(p);
    // Only add expensive FBM detail when close to surface
    if (d < 1.0) {
        d += 0.02 * fbm(p * 8.0) * smoothstep(1.0, 0.0, d);
    }
    return d;
}
```
**Critical**: The `smoothstep` fade prevents the FBM from disrupting the SDF's Lipschitz continuity far from the surface, which would cause ray marching to overshoot.

### SDF Bounding Volumes (Performance Optimization)
Skip expensive SDF evaluation when the point is far from the object:
```glsl
float map(vec3 p) {
    // Cheap bounding sphere test first
    float bound = sdSphere(p - objectCenter, boundingRadius);
    if (bound > 0.1) return bound;  // far away — return bounding distance
    // Expensive detailed SDF only when close
    return complexSDF(p);
}
```
For scenes with multiple distant objects, this can provide 5-10x speedup.

### Binary Search Refinement
After ray marching finds an approximate hit, refine with binary search for sub-pixel precision:
```glsl
// After ray march loop finds t where map(ro+rd*t) < epsilon:
for (int i = 0; i < 6; i++) {
    float mid = map(ro + rd * t);
    t += mid * 0.5;  // or use proper bisection:
    // float dt = step * 0.5^i;
    // t += (map(ro+rd*t) > 0.0) ? dt : -dt;
}
```
Especially useful for: sharp edge rendering, precise shadow termination, accurate reflection points.

### XOR Boolean Operation
Create interesting geometric patterns by combining SDFs with XOR:
```glsl
float opXor(float d1, float d2) {
    return max(min(d1, d2), -max(d1, d2));
}
// Creates a "difference of unions" — geometry exists where exactly one shape is present
```

### Interior SDF Structures
Use the sign of the SDF to create interior geometry:
```glsl
float interiorPattern(vec3 p) {
    float outer = sdSphere(p, 1.0);
    float inner = sdBox(fract(p * 4.0) - 0.5, vec3(0.1)); // repeating inner pattern
    return (outer < 0.0) ? max(outer, inner) : outer;      // inner visible only inside
}
```

## SDF Debugging Visualization

```glsl
// Visualize SDF distance as color bands
vec3 debugSDF(float d) {
    vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3) : vec3(0.4, 0.7, 0.85);  // outside/inside
    col *= 1.0 - exp(-6.0 * abs(d));                    // darken near surface
    col *= 0.8 + 0.2 * cos(150.0 * d);                  // distance bands
    col = mix(col, vec3(1.0), 1.0 - smoothstep(0.0, 0.01, abs(d)));  // white at surface
    return col;
}
```

→ For deeper details, see [reference/sdf-tricks.md](../reference/sdf-tricks.md)
