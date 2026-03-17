# SDF Tricks Detailed Reference

## Prerequisites
- Understanding of signed distance fields and ray marching
- Basic SDF primitives and boolean operations
- FBM / procedural noise fundamentals

## Lipschitz Condition and FBM Detail

An SDF must satisfy the **Lipschitz condition**: `|f(a) - f(b)| ≤ |a - b|` (gradient magnitude ≤ 1). This guarantees that stepping by the SDF value is always safe — no surface exists within that radius.

When adding FBM noise to an SDF, the noise derivatives can violate Lipschitz:
- Raw noise amplitude of 0.1 with frequency 20 has gradient ~2.0, breaking the condition
- This causes ray marching to overshoot, creating holes and artifacts

**Solutions**:
1. **Amplitude limiting**: Keep `amplitude × frequency < 1.0` across all octaves
2. **Distance fade**: `d += amp * fbm(p * freq) * smoothstep(fadeStart, 0.0, d)` — detail only appears near the surface where overshoot distance is small
3. **Step size reduction**: Multiply ray step by 0.5-0.7, trading speed for stability

## Bounding Volume Strategies

### Hierarchical Bounding
For scenes with N objects, test bounding volumes in order of increasing cost:
```
Level 1: Scene bounding sphere (1 evaluation)
Level 2: Object group bounds (few evaluations)
Level 3: Individual object SDF (full cost)
```

### Spatial Partitioning
For repeating structures, combine domain repetition with bounds:
```glsl
float map(vec3 p) {
    vec3 q = mod(p + 2.0, 4.0) - 2.0;  // repeat every 4 units
    // Only evaluate detail if within local bounding sphere
    float bound = length(q) - 1.5;
    if (bound > 0.2) return bound;
    return detailedSDF(q);
}
```

## Binary Search Convergence

After N iterations of binary search, the position error is `initialStep / 2^N`:
- 4 iterations: 1/16 of initial step size
- 6 iterations: 1/64 of initial step size (sub-pixel at typical resolutions)
- 8 iterations: 1/256 (overkill for most uses)

6 iterations is the practical sweet spot — gives sub-pixel precision without wasting GPU cycles.

## XOR Operation Mathematics

`opXor(a, b) = max(min(a, b), -max(a, b))`

This is equivalent to: `union(a, b) AND NOT intersection(a, b)` — the symmetric difference. Geometry exists where exactly one shape is present but not both. Useful for creating lattice structures and interlocking patterns.

## Interior SDF Pattern Techniques

When the camera is inside an SDF (d < 0), the negative distance still gives useful information:
- `abs(d)` gives distance to nearest surface from inside
- Combine with repeating patterns using `fract()` to create infinite interior structures
- Use `max(outerSDF, innerSDF)` to confine interior patterns within the outer shell
