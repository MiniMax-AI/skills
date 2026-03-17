# Motion Recipes

Production-ready animation code snippets. Copy and adapt as needed.

## 1. Scroll-Triggered Reveal (Framer Motion)

Elements fade and slide up when entering viewport.

```tsx
"use client";
import { motion } from "framer-motion";

const fadeSlideUp = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 20 },
  },
};

export function RevealSection({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={fadeSlideUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-80px" }}
    >
      {children}
    </motion.div>
  );
}
```

## 2. Staggered List Orchestration (Framer Motion)

Children animate sequentially with blur effect.

```tsx
"use client";
import { motion } from "framer-motion";

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 24, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { type: "spring", stiffness: 120, damping: 20 },
  },
};

export function StaggerGrid({ items }: { items: React.ReactNode[] }) {
  return (
    <motion.div
      className="grid gap-6"
      variants={container}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
    >
      {items.map((child, i) => (
        <motion.div key={i} variants={item}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
}
```

## 3. GSAP ScrollTrigger Pinned Section

Horizontal scroll panels with pinning.

```tsx
"use client";
import { useRef, useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function PinnedTimeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const panelsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const panels = gsap.utils.toArray<HTMLElement>(".panel");
      gsap.to(panels, {
        xPercent: -100 * (panels.length - 1),
        ease: "none",
        scrollTrigger: {
          trigger: containerRef.current,
          pin: true,
          scrub: 1,
          end: () => "+=" + (panelsRef.current?.scrollWidth ?? 0),
        },
      });
    }, containerRef);

    return () => ctx.revert(); // CRITICAL: full cleanup
  }, []);

  return (
    <div ref={containerRef} className="overflow-hidden">
      <div ref={panelsRef} className="flex">
        {/* .panel elements */}
      </div>
    </div>
  );
}
```

## 4. Parallax Tilt Card (Framer Motion)

Mouse-tracking 3D perspective. Uses `useMotionValue` — never `useState`.

```tsx
"use client";
import { motion, useMotionValue, useTransform } from "framer-motion";

export function TiltCard({ children }: { children: React.ReactNode }) {
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.5);
  const rotateX = useTransform(y, [0, 1], [8, -8]);
  const rotateY = useTransform(x, [0, 1], [-8, 8]);

  return (
    <motion.div
      style={{ rotateX, rotateY, transformPerspective: 800 }}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        x.set((e.clientX - rect.left) / rect.width);
        y.set((e.clientY - rect.top) / rect.height);
      }}
      onMouseLeave={() => {
        x.set(0.5);
        y.set(0.5);
      }}
      className="rounded-2xl bg-white shadow-lg"
    >
      {children}
    </motion.div>
  );
}
```

## 5. Magnetic Button (Framer Motion)

Cursor-attracted button. Pure `useMotionValue` — zero re-renders.

```tsx
"use client";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { useRef } from "react";

export function MagneticButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 200, damping: 15 });
  const springY = useSpring(y, { stiffness: 200, damping: 15 });

  return (
    <motion.button
      ref={ref}
      style={{ x: springX, y: springY }}
      onMouseMove={(e) => {
        const rect = ref.current!.getBoundingClientRect();
        const dx = e.clientX - (rect.left + rect.width / 2);
        const dy = e.clientY - (rect.top + rect.height / 2);
        x.set(dx * 0.3);
        y.set(dy * 0.3);
      }}
      onMouseLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </motion.button>
  );
}
```

## 6. Text Scramble / Decode Effect

Matrix-style character reveal — pure JS, no library needed.

```tsx
"use client";
import { useEffect, useRef, useState } from "react";

const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export function TextScramble({ text, className }: { text: string; className?: string }) {
  const [display, setDisplay] = useState(text);
  const iteration = useRef(0);

  useEffect(() => {
    iteration.current = 0;
    const id = setInterval(() => {
      setDisplay(
        text
          .split("")
          .map((char, i) =>
            i < iteration.current ? char : chars[Math.floor(Math.random() * chars.length)]
          )
          .join("")
      );
      iteration.current += 1 / 3;
      if (iteration.current >= text.length) clearInterval(id);
    }, 30);
    return () => clearInterval(id);
  }, [text]);

  return <span className={className}>{display}</span>;
}
```

## 7. SVG Path Draw on Scroll (CSS Scroll-Driven)

Zero-JS scroll-linked path drawing using native CSS.

```css
@supports (animation-timeline: scroll()) {
  .draw-path {
    stroke-dasharray: 1;
    stroke-dashoffset: 1;
    animation: draw linear;
    animation-timeline: scroll();
    animation-range: entry 0% cover 60%;
  }

  @keyframes draw {
    to {
      stroke-dashoffset: 0;
    }
  }
}
```

## 8. Horizontal Scroll Hijack (GSAP)

Vertical scroll drives horizontal panning.

```tsx
"use client";
import { useRef, useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function HorizontalScroll({ children }: { children: React.ReactNode }) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const track = trackRef.current!;
      const scrollWidth = track.scrollWidth - window.innerWidth;
      gsap.to(track, {
        x: -scrollWidth,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          pin: true,
          scrub: 0.8,
          end: () => `+=${scrollWidth}`,
        },
      });
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="overflow-hidden">
      <div ref={trackRef} className="flex gap-8 w-max">
        {children}
      </div>
    </section>
  );
}
```

## 9. Particle Background (React Three Fiber)

Isolated canvas layer. Purely decorative, pointer-events-none.

```tsx
"use client";
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef, useMemo } from "react";
import * as THREE from "three";

function Particles({ count = 800 }) {
  const mesh = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) arr[i] = (Math.random() - 0.5) * 10;
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    if (mesh.current) mesh.current.rotation.y = clock.getElapsedTime() * 0.05;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.015} color="#94a3b8" transparent opacity={0.6} />
    </points>
  );
}

export function ParticleCanvas() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
        <Particles />
      </Canvas>
    </div>
  );
}
```

## 10. Shared Layout Morph (Framer Motion)

Card-to-modal expansion using `layoutId`.

```tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

export function MorphCard({ id, preview, detail }: {
  id: string;
  preview: React.ReactNode;
  detail: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <motion.div layoutId={`card-${id}`} onClick={() => setOpen(true)}
        className="cursor-pointer rounded-2xl bg-white p-6 shadow-md">
        {preview}
      </motion.div>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-40"
              onClick={() => setOpen(false)}
            />
            <motion.div layoutId={`card-${id}`}
              className="fixed inset-4 md:inset-20 z-50 rounded-2xl bg-white p-8 shadow-2xl overflow-auto">
              {detail}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
```

## Scroll Animation Patterns

### Sticky Scroll Stack
Cards pin to top and stack over each other.
- Each card: `position: sticky; top: calc(var(--index) * 2rem)`
- Depth illusion: `scale(calc(1 - var(--index) * 0.03))`

### Split-Screen Parallax
Two viewport halves scroll at different speeds.
- Left: `translateY` at 0.5x scroll speed (GSAP `scrub`)
- Mobile: collapse to single column, disable parallax

### Zoom Parallax
Hero image scales 1 to 1.5 on scroll.
```tsx
scrollTrigger: { trigger: heroRef, start: "top top", end: "bottom top", scrub: true }
gsap.to(imageRef, { scale: 1.5, ease: "none" });
```

### Text Mask Reveal
Large typography as window into video/image background.
- `background-clip: text` + `color: transparent`
- Animate `background-position` on scroll

### Curtain Reveal
Hero splits in half, each side slides away on scroll.
- Two halves clipped with `clip-path: inset(0 50% 0 0)` and `inset(0 0 0 50%)`
- GSAP animates `xPercent: -100` and `xPercent: 100`
