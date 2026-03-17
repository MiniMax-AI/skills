# WebGL2 Pitfalls Reference

This is a reference document for the [webgl-pitfalls](../techniques/webgl-pitfalls.md) technique.

## Complete Error Message Reference

| Error Message | Likely Cause | Solution |
|---|---|---|
| `'fragCoord' : undeclared identifier` | Using `fragCoord` instead of `gl_FragCoord.xy` in WebGL2 | Replace with `gl_FragCoord.xy` |
| `'' : Missing main()` | Fragment shader has no `main()` function | Add `void main() { mainImage(fragColor, gl_FragCoord.xy); }` wrapper |
| `'functionName' : no matching overloaded function found` | Wrong argument types OR function declared after use | Check types; reorder or forward-declare functions |
| `'return' : function return is not matching type:` | Return expression type doesn't match declared return type | Verify `vec3 foo()` returns `vec3`, not `float` |
| `#version` must be first | Leading whitespace when extracting from script tag | Use `.trim()` on shader source string |
| Uniform returns `null` from `getUniformLocation` | Uniform optimized away for being unused | Ensure uniform is actually referenced in shader code |

## Type Mismatch Examples

```glsl
// ERROR: terrainM expects vec2, passing vec3
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos + h * nor);  // Wrong: pos + h*nor is vec3
}
// FIX: Extract xz components
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos.xz + h * nor.xz);  // Correct: vec2
}
```

```glsl
// ERROR: can't access .z on vec2
vec2 uv = vec2(1.0, 2.0);
float z = uv.z;  // Wrong: vec2 has no .z
// FIX: use proper swizzle or conversion
float z = uv.y;  // Or if you need third component, use vec3
```

## GLSL ES 3.0 Specific Notes

- All declared `uniform` variables must be used in shader code, otherwise compiler may optimize them away
- When `gl.getUniformLocation()` returns `null`, setting that uniform triggers `INVALID_OPERATION`
- Loop counters must be deterministic at runtime — avoid compile-time constant folding issues
