# WebGL2 Pitfalls & Common Errors

## Use Cases

- Avoiding common GLSL compilation errors when generating standalone WebGL2 shader pages
- Debugging shader compilation failures
- Ensuring shader templates from ShaderToy work correctly in WebGL2

## Critical WebGL2 Rules

### 1. Fragment Coordinate — Use `gl_FragCoord.xy`

**ERROR**: `'fragCoord' : undeclared identifier`

In WebGL2 fragment shaders, `fragCoord` is not a built-in variable. Use `gl_FragCoord.xy` instead.

```glsl
// WRONG
void main() {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
}

// CORRECT
void main() {
    vec2 uv = (2.0 * gl_FragCoord.xy - iResolution.xy) / iResolution.y;
}
```

### 2. Shadertoy mainImage — Must Wrap in `main()`

**ERROR**: `'' : Missing main()`

If your fragment shader uses `void mainImage(out vec4, in vec2)`, you must provide a `main()` wrapper.

```glsl
// WRONG — only defines mainImage but no main()
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

// CORRECT
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}
```

### 3. Function Declaration Order — Declare Before Use

**ERROR**: `'functionName' : no matching overloaded function found`

GLSL requires functions to be declared before they are used. Forward declarations or reordering is needed.

```glsl
// WRONG — getAtmosphere() calls getSunDirection() which is defined after
vec3 getAtmosphere(vec3 dir) {
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;  // Error!
}
vec3 getSunDirection() {
    return normalize(vec3(-0.5, 0.8, -0.6));
}

// CORRECT — reorder functions
vec3 getSunDirection() {  // Define first
    return normalize(vec3(-0.5, 0.8, -0.6));
}
vec3 getAtmosphere(vec3 dir) {  // Now can call getSunDirection()
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;
}
```

### 4. Macro Limitations — `#define` Cannot Use Functions

**ERROR**: Various compilation errors with `#define` macros

Macros are text substitution and cannot call functions or use parentheses in the same way as C++.

```glsl
// WRONG
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6))
#define WORLD_TIME (iTime * speed())

// CORRECT — use const
const vec3 SUN_DIR = vec3(0.756, 0.378, -0.567);  // Pre-computed normalized value
const float WORLD_TIME = 1.0;
```

### 5. Vector Component Access — Terrain Functions

**ERROR**: `'terrainM' : no matching overloaded function found`

When passing positions to terrain functions that expect `vec2`, extract the XZ components properly.

```glsl
// WRONG — terrainM expects vec2, but passing vec3
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos + h * nor);  // Error: pos + h*nor is vec3
    ...
}

// CORRECT — extract xz components
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos.xz + h * nor.xz);
    ...
}
```

### 6. Loop Index — Use Runtime Constants

**ERROR**: Loop index must be a runtime expression

GLSL ES requires loop indices to be determinable at runtime, not compile-time constants in some contexts.

```glsl
// WRONG — AA is a #define constant
for (int i = 0; i < AA; i++) { ... }

// CORRECT — use a runtime-safe approach
for (int i = 0; i < 4; i++) { ... }  // Or pass as uniform
```

### 7. Uniform Usage — Avoid Unused Uniforms

**ERROR**: Uniform optimized away causes `gl.getUniformLocation()` to return `null`

If a uniform is declared but not used, the compiler may optimize it out.

```glsl
// WRONG — iTime declared but used in a conditional that might be false
uniform float iTime;
if (false) { x = iTime; }  // iTime optimized away

// CORRECT — always use the uniform in a way the compiler can't optimize out
uniform float iTime;
float t = iTime * 0.0;  // Always use iTime somehow
if (someCondition) { x = t; }
```

## Complete WebGL2 Adaptation Checklist

When generating standalone HTML pages:

1. **Shader Version**: `#version 300 es` must be the very first line
2. **Fragment Output**: Declare `out vec4 fragColor;`
3. **Entry Point**: Wrap `mainImage()` in `void main()` that calls `mainImage(fragColor, gl_FragCoord.xy)`
4. **Fragment Coord**: Use `gl_FragCoord.xy` not `fragCoord`
5. **Preprocessor**: Don't use functions in `#define` macros
6. **Function Order**: Declare functions before they are used, or use forward declarations
7. **Texture**: Use `texture()` not `texture2D()`
8. **Attributes**: `attribute` → `in`, `varying` → `in`/`out`

## Common Error Messages Reference

| Error Message | Likely Cause | Solution |
|---|---|---|
| `'fragCoord' : undeclared identifier` | Using `fragCoord` instead of `gl_FragCoord.xy` | Replace with `gl_FragCoord.xy` |
| `'' : Missing main()` | No `main()` function defined | Add wrapper `void main() { mainImage(...); }` |
| `'function' : no matching overloaded function` | Wrong argument types or function order | Check parameter types, reorder functions |
| `return' : function return is not matching` | Return type mismatch | Verify return expression matches declared return type |
| `#version` must be first | Leading whitespace in shader source | Use `.trim()` when extracting from script tags |
| Uniform `null` from `getUniformLocation` | Uniform optimized away | Ensure uniform is actually used in shader code |

## Further Reading

See [reference/webgl-pitfalls.md](../reference/webgl-pitfalls.md) for additional debugging techniques.
