## WebGL2 Adaptation Requirements

**IMPORTANT: Critical Warning for Standalone HTML Deployment**: Post-processing effects require an input texture to work. When generating standalone HTML, you must:
1. Set `#define USE_DEMO_SCENE 1` to use the built-in demo scene (recommended), or
2. Pass a valid input texture to the `iChannel0` channel, otherwise the screen will be completely black
3. **Critical**: When USE_DEMO_SCENE=1, ensure the #else branch code does not reference non-existent uniforms (e.g., iChannel0)

**IMPORTANT: GLSL Type Strictness Rules**:
- `vec2 = float` is illegal — must use `vec2(x, x)` or `vec2(x)`
- Function parameters must be defined before use; using a variable name in its own initializer is forbidden (e.g., `float w = filmicCurve(w, w)` is an error)
- Variables must be declared before use
- **#version must be the very first line of shader code**: No characters (including whitespace or comments) may precede `#version 300 es`
- **Code in preprocessor branches is still compiled**: Even if `#if USE_DEMO_SCENE` is true, the `#else` branch code is still compiled by the GPU — all branches must be valid GLSL code

Code templates in this document use ShaderToy GLSL style. When generating standalone HTML pages, you must adapt to WebGL2:

- Use `canvas.getContext("webgl2")`
- First line of shader: `#version 300 es`, add `precision highp float;` for fragment shaders
- Vertex shader: `attribute` → `in`, `varying` → `out`
- Fragment shader: `varying` → `in`, `gl_FragColor` → custom `out vec4 fragColor`, `texture2D()` → `texture()`
- ShaderToy's `void mainImage(out vec4 fragColor, in vec2 fragCoord)` must be adapted to standard `void main()` entry
- Must create Framebuffers and render to texture before post-processing

### Complete WebGL2 Standalone HTML Template

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Post-Processing Shader</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>

    <!-- Vertex Shader: #version must be the first line -->
    <script id="vs" type="x-shader/x-vertex">
        #version 300 es
        in vec2 a_position;
        out vec2 v_uv;
        void main() {
            v_uv = a_position * 0.5 + 0.5;
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    </script>

    <!-- Fragment Shader: #version must be the first line, precision follows -->
    <script id="fs" type="x-shader/x-fragment">
        #version 300 es
        precision highp float;

        in vec2 v_uv;
        out vec4 fragColor;

        uniform float iTime;
        uniform vec2 iResolution;
        // Note: Do not use iChannel0 in standalone HTML unless a valid texture is bound
        // Recommended: Use USE_DEMO_SCENE=1 for the built-in demo scene

        #define USE_DEMO_SCENE 1  // Recommended: use built-in demo scene

        // Demo scene function (replaces iChannel0 sampling)
        vec3 demoScene(vec2 uv, float time) {
            vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0.0, 2.0, 4.0));
            float d = length(uv - 0.5) - 0.12;
            col += vec3(3.0, 2.5, 1.8) * smoothstep(0.02, 0.0, d);
            return col;
        }

        // Tone mapping and other post-processing functions...
        // Note: Do not reference iChannel0 in the #else branch of #if USE_DEMO_SCENE
        // If you need iChannel0, use #ifdef or ensure the texture is bound when USE_DEMO_SCENE=0

        void main() {
            vec2 uv = v_uv;
            vec3 color;

            #if USE_DEMO_SCENE
                color = demoScene(uv, iTime);
            #else
                // This branch only executes when USE_DEMO_SCENE=0 and a texture is bound
                // Requires binding in JavaScript: gl.bindTexture(gl.TEXTURE_2D, texture);
                color = vec3(0.0);  // fallback
            #endif

            fragColor = vec4(color, 1.0);
        }
    </script>

    <script>
        const canvas = document.getElementById('canvas');
        const gl = canvas.getContext('webgl2');

        // Compile shader
        function createShader(gl, type, source) {
            const shader = gl.createShader(type);
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                console.error(gl.getShaderInfoLog(shader));
                gl.deleteShader(shader);
                return null;
            }
            return shader;
        }

        // Create program
        const vs = createShader(gl, gl.VERTEX_SHADER, document.getElementById('vs').textContent);
        const fs = createShader(gl, gl.FRAGMENT_SHADER, document.getElementById('fs').textContent);
        const program = gl.createProgram();
        gl.attachShader(program, vs);
        gl.attachShader(program, fs);
        gl.linkProgram(program);

        // Fullscreen quad
        const positions = new Float32Array([-1,-1, 1,-1, -1,1, 1,1]);
        const vao = gl.createVertexArray();
        gl.bindVertexArray(vao);
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

        const posLoc = gl.getAttribLocation(program, 'a_position');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

        // Uniform locations
        const timeLoc = gl.getUniformLocation(program, 'iTime');
        const resLoc = gl.getUniformLocation(program, 'iResolution');

        // Render loop
        function render(time) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            gl.viewport(0, 0, canvas.width, canvas.height);

            gl.useProgram(program);
            gl.uniform1f(timeLoc, time * 0.001);
            gl.uniform2f(resLoc, canvas.width, canvas.height);

            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            requestAnimationFrame(render);
        }
        requestAnimationFrame(render);
    </script>
</body>
</html>
```

### Multi-Pass Post-Processing HTML Template (with FBO)

Bloom separable blur, TAA, multi-step post-processing pipelines, etc. require rendering to intermediate textures. The following skeleton demonstrates the pattern: render scene to FBO → post-processing reads FBO → output to screen:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Multi-Pass Post-Processing</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
</head>
<body>
<canvas id="c"></canvas>
<script>
let frameCount = 0;

const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
const ext = gl.getExtension('EXT_color_buffer_float');

function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
        console.error(gl.getShaderInfoLog(s));
    return s;
}
function createProgram(vsSrc, fsSrc) {
    const p = gl.createProgram();
    gl.attachShader(p, createShader(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(p, createShader(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(p);
    return p;
}

const vsSource = `#version 300 es
in vec2 pos;
void main(){ gl_Position=vec4(pos,0,1); }`;

// fsScene: Scene rendering shader (outputs HDR color to FBO)
// fsPost:  Post-processing shader (samples scene texture from iChannel0, applies bloom/tonemap/etc)
const progScene = createProgram(vsSource, fsScene);
const progPost = createProgram(vsSource, fsPost);

function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // IMPORTANT: Critical: Check for float texture extension, fall back to RGBA8 if unsupported
    const fmt = ext ? gl.RGBA16F : gl.RGBA;
    const typ = ext ? gl.FLOAT : gl.UNSIGNED_BYTE;
    gl.texImage2D(gl.TEXTURE_2D, 0, fmt, w, h, 0, gl.RGBA, typ, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fbo, tex };
}

let W, H, sceneFBO;

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0);
gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

function resize() {
    canvas.width = W = innerWidth;
    canvas.height = H = innerHeight;
    sceneFBO = createFBO(W, H);
}
addEventListener('resize', resize);
resize();

function render(t) {
    t *= 0.001;
    // Pass 1: Scene rendering → FBO
    gl.useProgram(progScene);
    gl.bindFramebuffer(gl.FRAMEBUFFER, sceneFBO.fbo);
    gl.viewport(0, 0, W, H);
    gl.uniform2f(gl.getUniformLocation(progScene, 'iResolution'), W, H);
    gl.uniform1f(gl.getUniformLocation(progScene, 'iTime'), t);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    // Pass 2: Post-processing reads scene texture → screen
    gl.useProgram(progPost);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, sceneFBO.tex);
    gl.uniform1i(gl.getUniformLocation(progPost, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(progPost, 'iResolution'), W, H);
    gl.uniform1f(gl.getUniformLocation(progPost, 'iTime'), t);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frameCount++;
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
</body>
</html>
```

# Screen-Space Post-Processing Effects

## Use Cases

Screen-space image enhancement on already-rendered scenes: Tone Mapping, Bloom, Vignette, Chromatic Aberration, Motion Blur, DoF, FXAA/TAA, Color Grading, Film Grain, Lens Flare, etc.

Typical pipeline order: Scene Rendering → AA → Bloom → Chromatic Aberration → Motion Blur/DoF → Tone Mapping → Color Grading → Contrast → Vignette → Film Grain → Gamma → Dithering.

## Core Principles

The essence of post-processing is **per-pixel transformation of an already-rendered image** — input is a framebuffer texture, output is the transformed color value.

- **Tone Mapping**: HDR [0, ∞) → LDR [0, 1]. Reinhard `c/(1+c)`, Filmic Reinhard (white point/shoulder parameters), ACES (3×3 matrix + rational polynomial), generic rational polynomial
- **Gaussian Blur**: 2D Gaussian kernel is separable into two 1D passes, O(n²) → O(2n)
- **Bloom**: Bright-pass extraction → multi-level Gaussian blur → additive blend back to original
- **Vignette**: Brightness falloff based on pixel distance to center. Multiplicative or radial
- **Chromatic Aberration**: Sample the same texture at different scales for R/G/B channels

## Implementation Steps

### Step 1: Tone Mapping

```glsl
// Reinhard
vec3 reinhard(vec3 color) { return color / (1.0 + color); }

// Filmic Reinhard (W=white point, T2=shoulder parameter)
// IMPORTANT: GLSL critical rule: function parameters must be defined before use; using a variable name in its own initializer is forbidden
const float W = 1.2, T2 = 7.5; // adjustable
float filmic_reinhard_curve(float x) {
    float q = (T2 * T2 + 1.0) * x * x;
    return q / (q + x + T2 * T2);
}
vec3 filmic_reinhard(vec3 x) {
    float w = filmic_reinhard_curve(W);  // compute w using constant W first
    return vec3(filmic_reinhard_curve(x.r), filmic_reinhard_curve(x.g), filmic_reinhard_curve(x.b)) / w;
}

// ACES industry standard
vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(0.59719,0.07600,0.02840, 0.35458,0.90834,0.13383, 0.04823,0.01566,0.83777);
    mat3 m2 = mat3(1.60475,-0.10208,-0.00327, -0.53108,1.10813,-0.07276, -0.07367,-0.00605,1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return clamp(m2 * (a / b), 0.0, 1.0);
}

// Generic rational polynomial
vec3 rational_tonemap(vec3 x) {
    float a=0.010, b=0.132, c=0.010, d=0.163, e=0.101; // adjustable
    return (x * (a * x + b)) / (x * (c * x + d) + e);
}
```

### Step 2: Gamma Correction

```glsl
color = pow(color, vec3(1.0 / 2.2)); // after tone mapping; ACES already includes gamma, skip this step
```

### Step 3: Contrast Enhancement (Hermite S-Curve)

```glsl
color = clamp(color, 0.0, 1.0);
color = color * color * (3.0 - 2.0 * color);
// Controllable intensity: color = mix(color, color*color*(3.0-2.0*color), strength);
// smoothstep equivalent: color = smoothstep(-0.025, 1.0, color);
```

### Step 4: Color Grading

```glsl
color = color * vec3(1.11, 0.89, 0.79); // per-channel multiply (warm tone), adjustable
color = pow(color, vec3(1.3, 1.2, 1.0)); // pow color grading, adjustable
// HSV hue shift: hsv.x = fract(hsv.x + 0.05); hsv.y *= 1.1;
// Desaturation: color = mix(color, vec3(dot(color, vec3(0.299,0.587,0.114))), 0.2);
```

### Step 5: Vignette

```glsl
// Option A: Multiplicative
vec2 q = fragCoord / iResolution.xy;
float vignette = pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.25);
color *= 0.5 + 0.5 * vignette;

// Option B: Radial distance
vec2 centered = (uv - 0.5) * vec2(iResolution.x / iResolution.y, 1.0);
float vig = mix(1.0, max(0.0, 1.0 - pow(length(centered)/1.414 * 0.6, 3.0)), 0.5);
color *= vig;

// Option C: Inverse quadratic falloff
vec2 p = 1.0 - 2.0 * fragCoord / iResolution.xy;
p.y *= iResolution.y / iResolution.x;
float vig2 = 1.25 / (1.1 + 1.1 * dot(p, p)); vig2 *= vig2;
color *= mix(1.0, smoothstep(0.1, 1.1, vig2), 0.25);
```

### Step 6: Gaussian Blur

```glsl
float normpdf(float x, float sigma) {
    return 0.39894 * exp(-0.5 * x * x / (sigma * sigma)) / sigma;
}
vec3 gaussianBlur(sampler2D tex, vec2 fragCoord, vec2 resolution) {
    const int KERNEL_SIZE = 11, HALF = 5; // adjustable: KERNEL_SIZE must be odd
    float sigma = 7.0; // adjustable
    float kernel[KERNEL_SIZE]; float Z = 0.0;
    for (int j = 0; j <= HALF; ++j)
        kernel[HALF + j] = kernel[HALF - j] = normpdf(float(j), sigma);
    for (int j = 0; j < KERNEL_SIZE; ++j) Z += kernel[j];
    vec3 result = vec3(0.0);
    for (int i = -HALF; i <= HALF; ++i)
        for (int j = -HALF; j <= HALF; ++j)
            result += kernel[HALF+j] * kernel[HALF+i]
                    * texture(tex, (fragCoord + vec2(float(i), float(j))) / resolution).rgb;
    return result / (Z * Z);
}
```

### Step 7: Bloom (Single Pass, Hardware Mipmap)

```glsl
vec3 simpleBloom(sampler2D tex, vec2 uv) {
    vec3 bloom = vec3(0.0); float tw = 0.0; float maxB = 5.0; // adjustable
    for (int x = -1; x <= 1; x++)
        for (int y = -1; y <= 1; y++) {
            vec2 off = vec2(float(x), float(y)) / iResolution.xy; float w = 1.0;
            bloom += w * min(vec3(maxB), textureLod(tex, uv+off*exp2(5.0), 5.0).rgb); tw += w;
            bloom += w * min(vec3(maxB), textureLod(tex, uv+off*exp2(6.0), 6.0).rgb); tw += w;
            bloom += w * min(vec3(maxB), textureLod(tex, uv+off*exp2(7.0), 7.0).rgb); tw += w;
        }
    return pow(bloom / tw, vec3(1.5)) * 0.3; // adjustable: gamma and intensity
}
// Usage: color = color * 0.8 + simpleBloom(iChannel0, uv);
```

### Step 8: Chromatic Aberration

```glsl
#define CA_SAMPLES 8       // adjustable
#define CA_STRENGTH 0.003  // adjustable
vec3 chromaticAberration(sampler2D tex, vec2 uv) {
    vec2 center = uv - 0.5; vec3 color = vec3(0.0);
    float rf = 1.0, gf = 1.0, bf = 1.0, f = 1.0 / float(CA_SAMPLES);
    for (int i = 0; i < CA_SAMPLES; ++i) {
        color.r += f * texture(tex, 0.5 - 0.5 * (center * 2.0 * rf)).r;
        color.g += f * texture(tex, 0.5 - 0.5 * (center * 2.0 * gf)).g;
        color.b += f * texture(tex, 0.5 - 0.5 * (center * 2.0 * bf)).b;
        rf *= 1.0 - CA_STRENGTH; gf *= 1.0 - CA_STRENGTH*0.3; bf *= 1.0 + CA_STRENGTH*0.4;
    }
    return clamp(color, 0.0, 1.0);
}
```

### Step 9: Film Grain

```glsl
float hash(float c) { return fract(sin(dot(c, vec2(12.9898, 78.233))) * 43758.5453); }
#define GRAIN_STRENGTH 0.012 // adjustable
color += vec3(GRAIN_STRENGTH * hash(length(fragCoord / iResolution.xy) + iTime));

// Bayer matrix ordered dithering (eliminates color banding)
const mat4 bayerMatrix = mat4(
    vec4(0.,8.,2.,10.), vec4(12.,4.,14.,6.), vec4(3.,11.,1.,9.), vec4(15.,7.,13.,5.));
float orderedDither(vec2 fc) {
    return (bayerMatrix[int(fc.x)&3][int(fc.y)&3] + 1.0) / 17.0;
}
color += (orderedDither(fragCoord) - 0.5) * 4.0 / 255.0;
```

### Step 10: Demo Scene (Required for Standalone HTML!)

**IMPORTANT: Critical Warning**: Standalone HTML deployment must provide an input texture, otherwise post-processing effects will output solid black.

```glsl
// Demo scene fallback: used when no valid input texture is available
vec3 demoScene(vec2 uv, float time) {
    // Dynamic gradient background
    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));

    // Center glowing sphere (for testing bloom)
    float d = length(uv - 0.5) - 0.15;
    col += vec3(2.0) * smoothstep(0.02, 0.0, d); // extremely bright region

    // Moving highlight bar (for testing bloom bleed)
    float bar = step(0.48, uv.y) * step(uv.y, 0.52);
    bar *= step(0.0, sin(uv.x * 10.0 - time * 2.0));
    col += vec3(1.5, 0.8, 0.3) * bar;

    // Colored blocks (for testing chromatic aberration and tone mapping)
    vec2 id = floor(uv * 4.0);
    float rand = fract(sin(dot(id, vec2(12.9898, 78.233))) * 43758.5453);
    vec2 rect = fract(uv * 4.0);
    float box = step(0.1, rect.x) * step(rect.x, 0.9) * step(0.1, rect.y) * step(rect.y, 0.9);
    col += vec3(rand, 1.0 - rand, 0.5) * box * 0.5;

    return col;
}
```

### Step 10: Motion Blur

```glsl
#define MB_SAMPLES 32    // adjustable
#define MB_STRENGTH 0.25 // adjustable
vec3 motionBlur(sampler2D tex, vec2 uv, vec2 velocity) {
    vec2 dir = velocity * MB_STRENGTH; vec3 color = vec3(0.0); float tw = 0.0;
    for (int i = 0; i < MB_SAMPLES; i++) {
        float t = float(i) / float(MB_SAMPLES - 1), w = 1.0 - t;
        color += w * textureLod(tex, uv + dir * t, 0.0).rgb; tw += w;
    }
    return color / tw;
}
```

### Step 11: Depth of Field

```glsl
#define DOF_SAMPLES 64
#define DOF_FOCAL_LENGTH 0.03
float getCoC(float depth, float focusDist) {
    float aperture = min(1.0, focusDist * focusDist * 0.5);
    return abs(aperture * (DOF_FOCAL_LENGTH * (depth - focusDist))
             / (depth * (focusDist - DOF_FOCAL_LENGTH)));
}
float goldenAngle = 3.14159265 * (3.0 - sqrt(5.0));
vec3 depthOfField(sampler2D tex, vec2 uv, float depth, float focusDist) {
    float coc = getCoC(depth, focusDist);
    vec3 result = texture(tex, uv).rgb * max(0.001, coc);
    float tw = max(0.001, coc);
    for (int i = 1; i < DOF_SAMPLES; i++) {
        float fi = float(i);
        float theta = fi * goldenAngle * float(DOF_SAMPLES);
        float r = coc * sqrt(fi) / sqrt(float(DOF_SAMPLES));
        vec2 tapUV = uv + vec2(sin(theta), cos(theta)) * r;
        vec4 s = textureLod(tex, tapUV, 0.0);
        float w = max(0.001, getCoC(s.w, focusDist));
        result += s.rgb * w; tw += w;
    }
    return result / tw;
}
```

### Step 12: FXAA

```glsl
vec3 fxaa(sampler2D tex, vec2 fragCoord, vec2 resolution) {
    vec2 pp = 1.0 / resolution;
    vec4 color = texture(tex, fragCoord * pp);
    vec3 luma = vec3(0.299, 0.587, 0.114);
    float lumaNW = dot(texture(tex, (fragCoord+vec2(-1.,-1.))*pp).rgb, luma);
    float lumaNE = dot(texture(tex, (fragCoord+vec2( 1.,-1.))*pp).rgb, luma);
    float lumaSW = dot(texture(tex, (fragCoord+vec2(-1., 1.))*pp).rgb, luma);
    float lumaSE = dot(texture(tex, (fragCoord+vec2( 1., 1.))*pp).rgb, luma);
    float lumaM  = dot(color.rgb, luma);
    float lumaMin = min(lumaM, min(min(lumaNW,lumaNE), min(lumaSW,lumaSE)));
    float lumaMax = max(lumaM, max(max(lumaNW,lumaNE), max(lumaSW,lumaSE)));
    vec2 dir = vec2(-((lumaNW+lumaNE)-(lumaSW+lumaSE)), ((lumaNW+lumaSW)-(lumaNE+lumaSE)));
    float dirReduce = max((lumaNW+lumaNE+lumaSW+lumaSE)*0.03125, 1.0/128.0);
    dir = clamp(dir * 2.5/(min(abs(dir.x),abs(dir.y))+dirReduce), vec2(-8.0), vec2(8.0)) * pp;
    vec3 rgbA = 0.5 * (texture(tex, fragCoord*pp+dir*(1./3.-0.5)).rgb
                      + texture(tex, fragCoord*pp+dir*(2./3.-0.5)).rgb);
    vec3 rgbB = rgbA*0.5 + 0.25*(texture(tex, fragCoord*pp+dir*-0.5).rgb
                                 + texture(tex, fragCoord*pp+dir*0.5).rgb);
    float lumaB = dot(rgbB, luma);
    return (lumaB < lumaMin || lumaB > lumaMax) ? rgbA : rgbB;
}
```

## Complete Code Template

Can be run directly in ShaderToy. `iChannel0` is the scene texture.

**IMPORTANT: Important Warning**: For standalone HTML deployment, you must:
1. Pass a valid input texture to iChannel0 (or uChannel0)
2. Or set `#define USE_DEMO_SCENE 1` to use the built-in demo scene

```glsl
// Post-Processing Pipeline — ShaderToy Template
#define ENABLE_TONEMAP  1
#define ENABLE_BLOOM    1
#define ENABLE_CA       1
#define ENABLE_VIGNETTE 1
#define ENABLE_GRAIN    1
#define ENABLE_CONTRAST 1
#define USE_DEMO_SCENE  1    // set to 1 to use built-in demo scene (required for standalone HTML)
#define TONEMAP_MODE    2    // 0=Reinhard, 1=Filmic, 2=ACES
#define BRIGHTNESS      1.0
#define WHITE_POINT     1.2
#define SHOULDER        7.5
#define BLOOM_STRENGTH  0.08
#define BLOOM_LOD_START 4.0
#define COLOR_TINT      vec3(1.11, 0.89, 0.79)
#define CA_SAMPLES      8
#define CA_INTENSITY    0.003
#define VIG_POWER       0.25
#define GRAIN_AMOUNT    0.012

float hash11(float p) { return fract(sin(p * 12.9898) * 43758.5453); }

// Demo scene fallback: used when no input texture is available
vec3 demoScene(vec2 uv, float time) {
    // Dynamic gradient background
    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));
    // Center glowing sphere (for testing bloom)
    float d = length(uv - 0.5) - 0.15;
    col += vec3(2.0) * smoothstep(0.02, 0.0, d);
    // Moving highlight bar (for testing bloom bleed)
    float bar = step(0.48, uv.y) * step(uv.y, 0.52);
    bar *= step(0.0, sin(uv.x * 10.0 - time * 2.0));
    col += vec3(1.5, 0.8, 0.3) * bar;
    // Colored blocks (for testing chromatic aberration and tone mapping)
    vec2 id = floor(uv * 4.0);
    float rand = fract(sin(dot(id, vec2(12.9898, 78.233))) * 43758.5453);
    vec2 rect = fract(uv * 4.0);
    float box = step(0.1, rect.x) * step(rect.x, 0.9) * step(0.1, rect.y) * step(rect.y, 0.9);
    col += vec3(rand, 1.0 - rand, 0.5) * box * 0.5;
    return col;
}

vec3 tonemapReinhard(vec3 c) { return c / (1.0 + c); }
// IMPORTANT: Critical: filmicCurve takes only one parameter x; w is computed externally via WHITE_POINT
float filmicCurve(float x) {
    float q = (SHOULDER*SHOULDER+1.0)*x*x; return q/(q+x+SHOULDER*SHOULDER);
}
vec3 tonemapFilmic(vec3 c) {
    float w = filmicCurve(WHITE_POINT);  // compute w using WHITE_POINT constant first
    return vec3(filmicCurve(c.r), filmicCurve(c.g), filmicCurve(c.b)) / w;
}
vec3 tonemapACES(vec3 color) {
    mat3 m1 = mat3(0.59719,0.07600,0.02840, 0.35458,0.90834,0.13383, 0.04823,0.01566,0.83777);
    mat3 m2 = mat3(1.60475,-0.10208,-0.00327, -0.53108,1.10813,-0.07276, -0.07367,-0.00605,1.07602);
    vec3 v = m1*color;
    vec3 a = v*(v+0.0245786)-0.000090537;
    vec3 b = v*(0.983729*v+0.4329510)+0.238081;
    return clamp(m2*(a/b), 0.0, 1.0);
}
vec3 applyTonemap(vec3 c) {
    c *= BRIGHTNESS;
    #if TONEMAP_MODE == 0
        return tonemapReinhard(c);
    #elif TONEMAP_MODE == 1
        return tonemapFilmic(c);
    #else
        return tonemapACES(c);
    #endif
}

vec3 sampleBloom(sampler2D tex, vec2 uv) {
    vec3 bloom = vec3(0.0); float tw = 0.0;
    for (int x = -1; x <= 1; x++)
        for (int y = -1; y <= 1; y++) {
            vec2 off = vec2(float(x),float(y))/iResolution.xy; float w = 1.0;
            bloom += w*textureLod(tex, uv+off*exp2(BLOOM_LOD_START), BLOOM_LOD_START).rgb;
            bloom += w*textureLod(tex, uv+off*exp2(BLOOM_LOD_START+1.0), BLOOM_LOD_START+1.0).rgb;
            bloom += w*textureLod(tex, uv+off*exp2(BLOOM_LOD_START+2.0), BLOOM_LOD_START+2.0).rgb;
            tw += w*3.0;
        }
    return bloom / tw;
}

vec3 applyChromaticAberration(sampler2D tex, vec2 uv) {
    vec2 center = 1.0 - 2.0*uv; vec3 color = vec3(0.0);
    float rf=1.0, gf=1.0, bf=1.0, f=1.0/float(CA_SAMPLES);
    for (int i = 0; i < CA_SAMPLES; ++i) {
        color.r += f*texture(tex, 0.5-0.5*(center*rf)).r;
        color.g += f*texture(tex, 0.5-0.5*(center*gf)).g;
        color.b += f*texture(tex, 0.5-0.5*(center*bf)).b;
        rf *= 1.0-CA_INTENSITY; gf *= 1.0-CA_INTENSITY*0.3; bf *= 1.0+CA_INTENSITY*0.4;
    }
    return clamp(color, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Get input color: demo scene or input texture
    #if USE_DEMO_SCENE
        vec3 color = demoScene(uv, iTime);
    #else
        #if ENABLE_CA
            vec3 color = applyChromaticAberration(iChannel0, uv);
        #else
            vec3 color = texture(iChannel0, uv).rgb;
        #endif
    #endif

    #if ENABLE_BLOOM && !USE_DEMO_SCENE
        color += sampleBloom(iChannel0, uv) * BLOOM_STRENGTH;
    #else
        // In demo scene mode, use simplified bloom sampling from itself
        #if ENABLE_BLOOM
            vec3 bloom = vec3(0.0); float tw = 0.0;
            for (int x = -1; x <= 1; x++)
                for (int y = -1; y <= 1; y++) {
                    vec2 off = vec2(float(x),float(y))/iResolution.xy * 0.02;
                    vec3 s = demoScene(uv + off, iTime);
                    float w = 1.0;
                    bloom += w * min(vec3(5.0), s); tw += w;
                }
            color += bloom / tw * BLOOM_STRENGTH;
        #endif
    #endif

    color *= COLOR_TINT;
    #if ENABLE_TONEMAP
        #if TONEMAP_MODE == 2
            color = applyTonemap(color);
        #else
            color = applyTonemap(color);
            color = pow(color, vec3(1.0/2.2));
        #endif
    #else
        color = pow(color, vec3(1.0/2.2));
    #endif
    #if ENABLE_CONTRAST
        color = clamp(color, 0.0, 1.0);
        color = color*color*(3.0-2.0*color);
    #endif
    #if ENABLE_VIGNETTE
        vec2 q = fragCoord/iResolution.xy;
        color *= 0.5 + 0.5*pow(16.0*q.x*q.y*(1.0-q.x)*(1.0-q.y), VIG_POWER);
    #endif
    #if ENABLE_GRAIN
        color += GRAIN_AMOUNT * hash11(dot(uv, vec2(12.9898,78.233)) + iTime);
    #endif
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
```

## Common Variants

### Variant 1: Multi-Pass Separable Bloom

```glsl
// Buffer A: Horizontal Gaussian blur + bright-pass
#define BLOOM_THRESHOLD vec3(0.2)
#define BLOOM_DOWNSAMPLE 3
#define BLUR_RADIUS 16
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 xy = ivec2(fragCoord);
    if (xy.x >= int(iResolution.x)/BLOOM_DOWNSAMPLE) { fragColor = vec4(0); return; }
    vec3 sum = vec3(0.0); float tw = 0.0;
    for (int k = -BLUR_RADIUS; k <= BLUR_RADIUS; ++k) {
        vec3 texel = max(vec3(0.0), texelFetch(iChannel0, (xy+ivec2(k,0))*BLOOM_DOWNSAMPLE, 0).rgb - BLOOM_THRESHOLD);
        float w = exp(-8.0 * pow(abs(float(k))/float(BLUR_RADIUS), 2.0));
        sum += texel*w; tw += w;
    }
    fragColor = vec4(sum/tw, 1.0);
}
// Buffer B: Vertical blur, same as above but with direction changed to ivec2(0, k)
```

### Variant 2: ACES + Full Color Pipeline (with Built-in Gamma)

```glsl
vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(0.59719,0.07600,0.02840, 0.35458,0.90834,0.13383, 0.04823,0.01566,0.83777);
    mat3 m2 = mat3(1.60475,-0.10208,-0.00327, -0.53108,1.10813,-0.07276, -0.07367,-0.00605,1.07602);
    vec3 v = m1*color;
    vec3 a = v*(v+0.0245786)-0.000090537;
    vec3 b = v*(0.983729*v+0.4329510)+0.238081;
    return pow(clamp(m2*(a/b), 0.0, 1.0), vec3(1.0/2.2));
}
```

### Variant 3: DoF + Motion Blur Combination

```glsl
for (int i = 1; i < BLUR_TAPS; i++) {
    float t = float(i)/float(BLUR_TAPS);
    float randomT = hash(iTime + t + uv.x + uv.y*12.345);
    vec2 tapUV = mix(currentUV, prevFrameUV, (randomT-0.5)*shutterAngle); // motion blur
    float theta = t*goldenAngle*float(BLUR_TAPS);
    float r = coc*sqrt(t*float(BLUR_TAPS))/sqrt(float(BLUR_TAPS));
    tapUV += vec2(sin(theta), cos(theta))*r; // DoF
    vec4 tap = textureLod(sceneTex, tapUV, 0.0);
    float w = max(0.001, getCoC(decodeDepth(tap.w), focusDistance));
    result += tap.rgb*w; totalWeight += w;
}
```

### Variant 4: TAA Temporal Anti-Aliasing

```glsl
vec4 current = textureLod(currentFrame, uv - jitterOffset/iResolution.xy, 0.0);
vec3 vMin = vec3(1e5), vMax = vec3(-1e5);
for (int iy = -1; iy <= 1; iy++)
    for (int ix = -1; ix <= 1; ix++) {
        vec3 s = texelFetch(currentFrame, ivec2(fragCoord)+ivec2(ix,iy), 0).rgb;
        vMin = min(vMin, s); vMax = max(vMax, s);
    }
vec4 history = textureLod(historyBuffer, reprojectToPrevFrame(worldPos, prevViewProjMatrix), 0.0);
float blend = (all(greaterThanEqual(history.rgb, vMin)) && all(lessThanEqual(history.rgb, vMax))) ? 0.9 : 0.0;
color = mix(current.rgb, history.rgb, blend);
```

### Variant 5: Lens Flare + Starburst

```glsl
#define NUM_APERTURE_BLADES 8.0
vec2 toSun = normalize(sunScreenPos - uv);
float angle = atan(toSun.y, toSun.x);
float starburst = pow(0.5+0.5*cos(1.5*3.14159+angle*NUM_APERTURE_BLADES),
                      max(1.0, 500.0-sunDist*sunDist*501.0));
float ghost = smoothstep(0.015, 0.0, length(ghostCenter-uv)-ghostRadius);
totalFlare += wavelengthToRGB(300.0+fract((length(ghostCenter-uv)-ghostRadius)*5.0)*500.0) * ghost * 0.25;
```

## Performance & Composition

**Performance**: Separable blur 121→22 samples | `textureLod` hardware mipmap for free downsampling | Downsample 2-4x before blurring | Sample counts: MB 16-32, DoF 32-64, CA 4-8 | Inter-texel sampling = free bilinear | `#define` switches have zero cost | Use `mix`/`step`/`smoothstep` instead of branches

**Composition**: Bloom+ToneMap (compute bloom in HDR space then tonemap, not reversible) | TAA+MB+DoF (shared sampling loop) | CA+Vignette+Grain (lens trio) | ColorGrading+ToneMap+Contrast (grade in linear space → HDR compression → gamma-space S-curve) | Bloom+LensFlare (shared bright-pass) | Multi-pass pipeline: BufA scene → BufB/C Bloom H/V → BufD TAA → Image compositing

## Further Reading

For complete step-by-step tutorials, mathematical derivations, and advanced usage, see [reference](../reference/post-processing.md)
