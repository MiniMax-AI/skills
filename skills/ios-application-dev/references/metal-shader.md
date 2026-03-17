# Metal Shader Reference

Expert reference for Metal shaders, real-time rendering, and Apple's Tile-Based Deferred Rendering (TBDR) architecture.

## Core Principles

**Half precision first → Leverage TBDR → Function constant specialization → Use Intersector API**

### When to Use

- Metal Shading Language (MSL) development
- Apple GPU optimization (TBDR architecture)
- PBR rendering pipelines
- Compute shaders and parallel processing
- Apple Silicon ray tracing
- GPU profiling and debugging

### When NOT to Use

- WebGL/GLSL (different architecture)
- CUDA (NVIDIA only)
- OpenGL (deprecated on Apple)
- CPU-side optimization

## Expert vs Novice

| Topic | Novice | Expert |
|-------|--------|--------|
| Data types | `float` everywhere | Default `half`, `float` only for position/depth |
| Branching | Runtime conditionals | Function constants for compile-time elimination |
| Memory | Everything in device | Know constant/device/threadgroup tradeoffs |
| Architecture | Treat as desktop GPU | Understand TBDR: tile memory is free, bandwidth is expensive |
| Ray tracing | intersection queries | intersector API (hardware-aligned) |
| Debugging | print debugging | GPU capture, shader profiler, occupancy analysis |

## Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| 32-bit floats | Wastes registers, reduces occupancy, doubles bandwidth | Default `half`, `float` only for position/depth |
| Ignoring TBDR | Not using free tile memory | Use `[[color(n)]]`, memoryless targets |
| Runtime constant branches | Warp divergence, wastes ALU | Function constants + pipeline specialization |
| intersection queries | Not hardware-aligned | Use intersector API |

## Metal Evolution

| Era | Key Development |
|-----|-----------------|
| Metal 2.x | OpenGL migration, basic compute |
| Apple Silicon | Unified memory, tile shaders critical |
| Metal 3 | Mesh shaders, hardware-accelerated ray tracing |
| Latest | Neural Engine + GPU cooperation, Vision Pro foveated rendering |

**Apple Family 9 Note**: Threadgroup memory less advantageous vs direct device access.

## Shader Types

| Type | Purpose | Key Attributes |
|------|---------|----------------|
| Vertex | Vertex transformation | `[[stage_in]]`, `[[buffer(n)]]` |
| Fragment | Pixel shading | `[[color(n)]]`, `[[texture(n)]]` |
| Compute/Kernel | General computation | `[[thread_position_in_grid]]` |
| Tile | TBDR-specific | `[[imageblock]]` |
| Mesh | Metal 3 geometry | `[[mesh_id]]` |

## Rendering Techniques

| Technique | Description |
|-----------|-------------|
| Fullscreen quad | 4 vertex triangle strip, no MVP, post-processing basis |
| PBR Cook-Torrance | Fresnel Schlick + GGX Distribution + Smith Geometry |
| Blinn-Phong | Simple specular, half-vector calculation |

## Procedural Generation

| Technique | Use Case |
|-----------|----------|
| Hash functions | Pseudo-random basis for noise, random sampling |
| Voronoi | Cell textures, stones, cracks |
| Value/Perlin Noise | Continuous random fields |
| FBM | Multi-octave layering, fractal terrain, clouds |
| Domain Warping | Coordinate distortion, organic shapes |

## Numerical Techniques

| Technique | Formula |
|-----------|---------|
| Central difference gradient | `(f(x+h) - f(x-h)) / (2h)` |
| Smoothstep | `x * x * (3 - 2 * x)` |
| SDF operations | `min/max/smooth_min` boolean ops |

## SwiftUI + MTKView Integration

### Architecture Pattern

```
MetalView (UIViewRepresentable)
    └── Coordinator = Renderer (MTKViewDelegate)
            ├── MTLDevice
            ├── MTLCommandQueue
            ├── MTLRenderPipelineState
            └── MTLBuffer (vertices, uniforms)
```

### Uniform Alignment Rules

| Swift Type | Metal Type | Alignment |
|------------|------------|-----------|
| `Float` | `float` | 4 bytes |
| `SIMD2<Float>` | `float2` | 8 bytes |
| `SIMD3<Float>` | `float3` | **16 bytes** |
| `SIMD4<Float>` | `float4` | 16 bytes |

**Key**: `float3` aligns to 16 bytes. Use `MemoryLayout<T>.size` to verify.

## Command Line Tools

| Command | Purpose |
|---------|---------|
| `xcrun metal -c shader.metal -o shader.air` | Compile to AIR |
| `xcrun metallib shader.air -o shader.metallib` | Link to metallib |
| `xcrun metal shader.metal -o shader.metallib` | One-step compile & link |
| `xcrun metal -Weverything -c shader.metal` | Syntax check |
| `xcrun metal-objdump --disassemble shader.metallib` | Disassemble |

## GPU Debugging

### Xcode Workflow

1. **GPU Capture**: ⌘⇧⌥G
2. **Shader Profiler**: Select draw call → View Shader
3. **Memory Viewer**: Inspect buffer/texture
4. **Performance HUD**: Enable in device options

### Key Metrics

| Metric | Healthy Value | Low Value Cause |
|--------|---------------|-----------------|
| GPU Occupancy | > 80% | Memory bandwidth bottleneck |
| ALU Utilization | > 60% | Waiting on memory |
| Bandwidth | As low as possible | TBDR should minimize store |

### Debug Utility Functions

| Function | Purpose |
|----------|---------|
| heatmap | Value visualization (blue→green→red) |
| debugNaN | NaN/Inf detection (magenta marker) |
| visualizeDepth | Linearized depth visualization |

## Performance Optimization Checklist

### Data Types
- [ ] Default `half`, `float` only for position/depth

### Memory Management
- [ ] Constants in constant address space
- [ ] Use `.storageModeShared`
- [ ] Leverage tile memory (TBDR free reads)
- [ ] Avoid unnecessary render target stores

### Branch Optimization
- [ ] Function constants to eliminate branches
- [ ] Fixed loop bounds (GPU unrolling)

### Rendering Tips
- [ ] Fullscreen quad with 4 vertex triangle strip
- [ ] Procedural textures to avoid sampling bandwidth
- [ ] `[[early_fragment_tests]]` for early depth test
- [ ] `setFragmentBytes` for small data

### Compute Optimization
- [ ] Vectorize (SIMD)
- [ ] Reduce register pressure

---

*Metal, Apple Silicon, and Xcode are trademarks of Apple Inc.*
