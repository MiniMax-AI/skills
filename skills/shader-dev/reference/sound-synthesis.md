# Sound Synthesis — Detailed Reference

This document is a complete reference supplement to [SKILL.md](SKILL.md), covering prerequisites, detailed explanations of each step, in-depth variant descriptions, performance optimization analysis, and complete combination code examples.

## Prerequisites

- **GLSL Fundamentals**: Functions, vector operations, `float`/`vec2` types, math functions like `sin()`/`exp()`/`fract()`
- **Audio Fundamentals**: Sample rate (typically 44100Hz), frequency-to-pitch relationship, waveform concepts (sine, sawtooth, square)
- **Music Theory Basics**: MIDI note numbers, equal temperament, octave relationship (frequency doubles), chord construction
- **ShaderToy Sound Mode**: `vec2 mainSound(int samp, float time)` returns a `vec2` stereo sample value in the range `[-1, 1]`

## Implementation Steps

### Step 1: mainSound Entry Point and Basic Framework

**What**: Establish the standard entry function for a sound shader, outputting a stereo signal.

**Why**: ShaderToy requires the fixed signature `vec2 mainSound(int samp, float time)`, where the return value's `.x` and `.y` are the left and right channels respectively, with a range of `[-1, 1]`. `samp` is the sample index, and `time` is the corresponding time (in seconds).

```glsl
// ShaderToy sound shader basic framework
#define TAU 6.28318530718
#define BPM 120.0                    // Adjustable: tempo
#define SPB (60.0 / BPM)             // Seconds per beat

vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);

    // Layer instruments/tracks here
    // audio += instrument(time);

    // Master volume control + anti-click fade-in
    audio *= 0.5 * smoothstep(0.0, 0.5, time);

    return clamp(audio, -1.0, 1.0);
}
```

### Step 2: MIDI Note to Frequency Conversion

**What**: Convert a MIDI note number to its corresponding frequency value.

**Why**: In equal temperament, each semitone up multiplies the frequency by `2^(1/12)`. MIDI 69 = A4 = 440Hz is the standard reference point. This is the foundation of all melodic synthesis.

```glsl
// MIDI note number to frequency
// 69 = A4 = 440Hz, every +12 is one octave (frequency doubles)
float noteFreq(float note) {
    return 440.0 * pow(2.0, (note - 69.0) / 12.0);
}
```

### Step 3: Basic Oscillators

**What**: Implement four standard waveform generators — sine, sawtooth, square, and triangle waves.

**Why**: Different waveforms have different harmonic characteristics. Sine waves are pure (fundamental only), sawtooth waves are rich in all harmonics (bright), square waves contain only odd harmonics (hollow), and triangle waves have faster harmonic decay (soft). These four are the building blocks of all timbre synthesis.

```glsl
// Sine wave - pure tone, fundamental only
float osc_sin(float t) {
    return sin(TAU * t);
}

// Sawtooth wave - contains all harmonics, bright and sharp
float osc_saw(float t) {
    return fract(t) * 2.0 - 1.0;
}

// Square wave - odd harmonics only, hollow texture
float osc_sqr(float t) {
    return step(fract(t), 0.5) * 2.0 - 1.0;
}

// Triangle wave - fast harmonic decay, soft and warm
float osc_tri(float t) {
    return abs(fract(t) - 0.5) * 4.0 - 1.0;
}
```

### Step 4: Additive Synthesis Instrument

**What**: Build a timbre by layering multiple harmonics (integer multiples of the fundamental), each with independent amplitude and decay rate.

**Why**: The timbre of real instruments is determined by their harmonic content (spectrum). Layering 3-8 harmonics with faster decay for higher harmonics can simulate piano, bell, and other timbres. This is the core technique for additive timbre synthesis.

```glsl
// Additive synthesis instrument
// freq: fundamental frequency, t: time within note
// Additive synthesis with harmonic layering
float instrument_additive(float freq, float t) {
    float y = 0.0;

    // Layer harmonics: fundamental × 1, 2, 4
    // Decreasing amplitude + frequency-dependent decay (higher harmonics decay faster)
    y += 0.50 * sin(TAU * 1.00 * freq * t) * exp(-0.0015 * 1.0 * freq * t);
    y += 0.30 * sin(TAU * 2.01 * freq * t) * exp(-0.0015 * 2.0 * freq * t);
    y += 0.20 * sin(TAU * 4.01 * freq * t) * exp(-0.0015 * 4.0 * freq * t);

    // Nonlinear waveshaping to enrich harmonics
    y += 0.1 * y * y * y;                          // Adjustable: 0.0-0.35, higher = more distortion

    // Tremolo
    y *= 0.9 + 0.1 * cos(40.0 * t);                // Adjustable: 40.0 = tremolo frequency

    // Smooth attack to avoid clicks
    y *= smoothstep(0.0, 0.01, t);                  // Adjustable: 0.01 = attack time

    return y;
}
```

### Step 5: FM Synthesis Instrument

**What**: Use one oscillator's (modulator) output as the phase offset of another oscillator (carrier) to produce rich harmonics.

**Why**: FM synthesis can generate extremely rich timbres with very few oscillators. Varying modulation depth over time can simulate the "bright→dark" decay characteristic of instruments. Electric pianos and sitar-like timbres are both based on this principle.

```glsl
// FM synthesis electric piano
// FM electric piano synthesis
vec2 fm_epiano(float freq, float t) {
    // Stereo micro-detuning for chorus effect
    vec2 f0 = vec2(freq * 0.998, freq * 1.002);    // Adjustable: detune amount

    // "Glass" layer - high-frequency FM, fast decay → metallic attack quality
    vec2 glass = sin(TAU * (f0 + 3.0) * t
        + sin(TAU * 14.0 * f0 * t) * exp(-30.0 * t)  // Adjustable: 14.0=mod ratio, -30.0=mod decay
    ) * exp(-4.0 * t);                                 // Adjustable: -4.0 = glass layer decay
    glass = sin(glass);                                 // Second-order nonlinearity

    // "Body" layer - low-frequency FM, slow decay → sustained warm tone
    vec2 body = sin(TAU * f0 * t
        + sin(TAU * f0 * t) * exp(-0.5 * t) * pow(440.0 / f0.x, 0.5)  // Low-frequency compensation
    ) * exp(-t);                                        // Adjustable: -1.0 = body decay

    return (glass + body) * smoothstep(0.0, 0.001, t) * 0.1;
}

// FM synthesis generic instrument (struct-parameterized)
// FM synthesis generic instrument (struct-parameterized)
struct Instr {
    float att;      // Attack speed (higher = faster)
    float fo;       // Decay rate
    float vibe;     // Vibrato speed
    float vphas;    // Vibrato phase
    float phas;     // FM modulation depth
    float dtun;     // Detune amount
};

float fm_instrument(float freq, float t, float beatTime, Instr ins) {
    float f = freq - beatTime * ins.dtun;
    float phase = f * t * TAU;
    float vibrato = cos(beatTime * ins.vibe * 3.14159 / 8.0 + ins.vphas * 1.5708);
    float fm = sin(phase + vibrato * sin(phase * ins.phas));
    float env = exp(-beatTime * ins.fo) * (1.0 - exp(-beatTime * ins.att));
    return fm * env * (1.0 - beatTime * 0.125);
}
```

### Step 6: Percussion Synthesis

**What**: Synthesize kick drum, snare/clap, and hi-hat percussion instruments.

**Why**: Percussion is typically composed of pitch sweeps (kick) or noise pulses (hi-hat/clap) with fast envelopes. The kick's core is a sine sweep from high to low frequency; hi-hats are noise with exponential decay. Nearly all complete music shaders require these.

```glsl
// Pseudo-random hash (replaces noise texture)
float hash(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}

// 909-style kick drum
// 909-style kick drum synthesis
float kick(float t) {
    float df = 512.0;                               // Adjustable: frequency sweep depth
    float dftime = 0.01;                             // Adjustable: sweep time constant
    float freq = 60.0;                               // Adjustable: base frequency

    // Exponential frequency sweep: rapidly slides from high to base frequency
    float phase = TAU * (freq * t - df * dftime * exp(-t / dftime));
    float body = sin(phase) * smoothstep(0.3, 0.0, t) * 1.5;

    // Transient noise click
    float click = sin(TAU * 8000.0 * fract(t)) * hash(t * 2000.0)
                * smoothstep(0.007, 0.0, t);

    return body + click;
}

// Hi-hat (open / closed)
// Hi-hat synthesis (open / closed)
float hihat(float t, float decay) {
    // decay: 5.0 = open hat (long decay), 15.0 = closed hat (short decay)
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * exp(-decay * t) * smoothstep(0.0, 0.02, t);
}

// Clap / snare
float clap(float t) {
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * smoothstep(0.1, 0.0, t);
}
```

### Step 7: Note Sequence Arrangement

**What**: Implement melody/chord temporal arrangement, determining which note should play at each moment.

**Why**: Music = timbre × timing. ShaderToy has three mainstream arrangement approaches: (A) D() macro accumulation for handwritten melodies, (B) array lookup for complex arrangements, (C) hash pseudo-random for algorithmic composition.

```glsl
// === Approach A: D() Macro Accumulation ===
// Usage: D(duration, MIDI note number) arranged sequentially
// b = accumulated time, x = current note start time, n = current note
#define D(duration, note) b += float(duration); if(t > b) { x = b; n = float(note); }

float melody_macro(float time) {
    float t = time / 0.18;                          // Adjustable: 0.18 = seconds per unit duration
    float n = 0.0, b = 0.0, x = 0.0;

    D(10,71) D(2,76) D(3,79) D(1,78) D(2,76) D(4,83) D(2,81) D(6,78)
    // ... continue arranging notes ...

    float freq = noteFreq(n);
    float noteTime = 0.18 * (t - x);
    return instrument_additive(freq, noteTime);
}

// === Approach B: Array Lookup ===
const float NOTES[16] = float[16](
    60., 62., 64., 65., 67., 69., 71., 72.,         // Adjustable: note sequence
    60., 64., 67., 72., 65., 69., 64., 60.
);

float melody_array(float time, float bpm) {
    float beat = time * bpm / 60.0;
    int idx = int(mod(beat, 16.0));
    float noteTime = fract(beat);
    float freq = noteFreq(NOTES[idx]);
    return instrument_additive(freq, noteTime * 60.0 / bpm);
}

// === Approach C: Hash Pseudo-Random ===
float nse(float x) {
    return fract(sin(x * 110.082) * 19871.8972);
}

// Scale quantization: filter out dissonant notes
float scale_filter(float note) {
    float n2 = mod(note, 12.0);
    // Major scale: filter out semitones 1,3,6,8,10
    if (n2==1.||n2==3.||n2==6.||n2==8.||n2==10.) return -100.0;
    return note;
}

float melody_random(float time, float bpm) {
    float beat = time * bpm / 60.0;
    float seqn = nse(floor(beat));
    float note = 48.0 + floor(seqn * 24.0);         // Adjustable: 48.0=lowest note, 24.0=range
    note = scale_filter(note);
    float freq = noteFreq(note);
    float noteTime = fract(beat) * 60.0 / bpm;
    return instrument_additive(freq, noteTime);
}
```

### Step 8: Chord Construction

**What**: Layer multiple notes according to chord relationships to form harmony.

**Why**: A chord is a combination of multiple pitches sounding simultaneously. The common structure is root + third + fifth (triad), with added seventh and ninth degrees for jazz chords. Jazz chord progressions can be built this way.

```glsl
// Chord construction
vec2 chord(float time, float root, float isMinor) {
    vec2 result = vec2(0.0);
    float bass = root - 24.0;                        // Root two octaves lower

    // Root (bass)
    result += fm_epiano(noteFreq(bass), time, 2.0);
    // Root
    result += fm_epiano(noteFreq(root), time - SPB * 0.5, 1.25);
    // Third (major third = 4 semitones, minor third = 3 semitones)
    result += fm_epiano(noteFreq(root + 4.0 - isMinor), time - SPB, 1.5);
    // Fifth
    result += fm_epiano(noteFreq(root + 7.0), time - SPB * 0.5, 1.25);
    // Seventh
    result += fm_epiano(noteFreq(root + 11.0 - isMinor), time - SPB, 1.5);
    // Ninth
    result += fm_epiano(noteFreq(root + 14.0), time - SPB, 1.5);

    return result;
}
```

### Step 9: Delay and Reverb Effects

**What**: Simulate spatial echo and reverb effects by layering time-offset copies of the audio signal.

**Why**: Dry audio sounds "flat". Multi-tap delay creates spatial depth by layering signal copies at different delays and decay amounts. Ping-pong delay bounces alternately between left and right channels, enhancing stereo width.

```glsl
// Multi-tap echo/reverb
// Multi-tap echo/reverb
// NOTE: in GLSL ES 3.00, "sample" is a reserved word — use "samp" instead
vec2 echo_reverb(float time) {
    vec2 tot = vec2(0.0);
    float hh = 1.0;
    for (int i = 0; i < 6; i++) {                   // Adjustable: 6 = echo count
        float h = float(i) / 5.0;
        float delayedTime = time - 0.7 * h;         // Adjustable: 0.7 = echo interval

        // Call your instrument function to get audio at that time point
        float samp = get_instrument_sample(delayedTime);

        // Stereo spread: each echo has different L/R ratio
        tot += samp * vec2(0.5 + 0.1 * h, 0.5 - 0.1 * h) * hh;
        hh *= 0.5;                                   // Adjustable: 0.5 = decay per echo
    }
    return tot;
}

// Ping-pong stereo delay
// Ping-pong stereo delay
vec2 pingpong_delay(float time) {
    vec2 mx = get_stereo_sample(time) * 0.5;
    float ec = 0.4;                                  // Adjustable: initial echo volume
    float fb = 0.6;                                  // Adjustable: feedback decay coefficient
    float delay_time = 0.222;                        // Adjustable: delay time (seconds)
    float et = delay_time;

    // 4 alternating left/right ping-pong taps
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += delay_time;

    return mx;
}
```

### Step 10: Beat and Arrangement Structure

**What**: Define a time grid using BPM, arrange different instruments at different beat positions, and control the overall song structure (intro, verse, interlude, etc.).

**Why**: The rhythmic skeleton of music is built on a uniform beat grid. Using `floor(time * BPM / 60)` gets the current beat number, and `fract()` gets the position within the beat. `smoothstep` gating controls instrument entry and exit at specific sections.

```glsl
vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);

    float beat = time * BPM / 60.0;                  // Current beat count
    float bar = beat / 4.0;                           // Current bar (4/4 time)
    float beatInBar = mod(beat, 4.0);                 // Beat position within bar

    // --- Rhythm layer ---
    // Kick: trigger every beat
    float kickTime = mod(time, SPB);
    audio += vec2(kick(kickTime) * 0.5);

    // Hi-hat: trigger every half beat
    float hatTime = mod(time, SPB * 0.5);
    audio += vec2(hihat(hatTime, 15.0) * 0.15);

    // --- Melody layer ---
    audio += vec2(melody_array(time, BPM)) * 0.3;

    // --- Arrangement automation ---
    // Use smoothstep to control instrument entry/exit
    float introFade = smoothstep(0.0, 4.0, bar);     // Fade in over first 4 bars
    float dropGate = smoothstep(16.0, 16.1, bar);    // Drop at bar 16

    audio *= introFade;

    // Master volume + anti-click
    audio *= 0.35 * smoothstep(0.0, 0.5, time);
    return clamp(audio, -1.0, 1.0);
}
```

## Variant Details

### Variant 1: Subtractive Synthesis / TB-303 Acid Synthesizer

**Difference from basic version**: Instead of building timbre by layering harmonics, generates a harmonic-rich waveform (sawtooth) and then sculpts it with a resonant low-pass filter to remove high frequencies. The filter cutoff frequency is modulated by an envelope, producing the classic "wah" sound.

**Key modified code**:

```glsl
#define NSPC 128                                    // Adjustable: synthesis harmonic count (higher = better quality)

// Resonant low-pass frequency response
float lpf_response(float h, float cutoff, float reso) {
    cutoff -= 20.0;
    float df = max(h - cutoff, 0.0);
    float df2 = abs(h - cutoff);
    return exp(-0.005 * df * df) * 0.5              // Adjustable: -0.005 = rolloff slope
         + exp(df2 * df2 * -0.1) * reso;            // Adjustable: resonance peak
}

// TB-303 acid synthesizer
vec2 acid_synth(float freq, float noteTime) {
    vec2 v = vec2(0.0);
    // Envelope-driven filter cutoff frequency
    float cutoff = exp(noteTime * -1.5) * 50.0      // Adjustable: -1.5=envelope speed, 50.0=sweep range
                 + 10.0;                             // Adjustable: minimum cutoff
    float sqr = step(0.5, fract(noteTime * 4.5));   // Sawtooth/square switching

    for (int i = 0; i < NSPC; i++) {
        float h = float(i + 1);
        float inten = 1.0 / h;                      // Sawtooth spectrum
        inten = mix(inten, inten * mod(h, 2.0), sqr); // Square wave variant
        inten *= lpf_response(h, cutoff, 2.2);
        v.x += inten * sin((TAU + 0.01) * noteTime * freq * h);
        v.y += inten * sin(TAU * noteTime * freq * h);
    }
    float amp = smoothstep(0.05, 0.0, abs(noteTime - 0.31) - 0.26)
              * exp(noteTime * -1.0);
    return clamp(v * amp * 2.0, -1.0, 1.0);
}
```

### Variant 2: IIR Biquad Filter

**Difference from basic version**: Uses a time-domain IIR filter based on the Audio EQ Cookbook instead of frequency-domain methods. Supports 7 filter types including low-pass, high-pass, band-pass, notch, peak, and shelf — closer to real hardware. Requires maintaining past sample state.

**Key modified code**:

```glsl
// Sawtooth oscillator (sample-domain, anti-aliasing friendly)
float waveSaw(float freq, int samp) {
    return fract(freq * float(samp) / iSampleRate) * 2.0 - 1.0;
}

// Stereo widening
vec2 widerSaw(float freq, int samp) {
    int offset = int(freq) * 64;                    // Adjustable: 64 = width factor
    return vec2(waveSaw(freq, samp - offset), waveSaw(freq, samp + offset));
}

// Biquad low-pass filter coefficient calculation
void biquadLPF(float freq, float Q, float sr,
    out float b0, out float b1, out float b2,
    out float a0, out float a1, out float a2) {
    float omega = TAU * freq / sr;
    float sn = sin(omega), cs = cos(omega);
    float alpha = sn / (2.0 * Q);                   // Adjustable: Q = resonance (0.5-20)
    b0 = (1.0 - cs) * 0.5;
    b1 = 1.0 - cs;
    b2 = (1.0 - cs) * 0.5;
    a0 = 1.0 + alpha;
    a1 = -2.0 * cs;
    a2 = 1.0 - alpha;
}
```

### Variant 3: Vocal / Formant Synthesis

**Difference from basic version**: Uses a sinusoidal tract model to simulate the human voice. By setting formants at different frequencies with their bandwidths, vowels can be synthesized. Consonants are implemented through fricative noise.

**Key modified code**:

```glsl
// Vocal tract formant model
float tract(float x, float formantFreq, float bandwidth) {
    return sin(TAU * formantFreq * x)
         * exp(-bandwidth * 3.14159 * x);
}

// "Ah" vowel synthesis
float vowel_aah(float t, float pitch) {
    float period = 1.0 / pitch;
    float x = mod(t, period);
    // Formant frequencies and bandwidths (Hz) — adjustable to simulate different vowels
    float aud = tract(x, 710.0, 70.0) * 0.5         // F1: 710Hz ('a' vowel)
              + tract(x, 1000.0, 90.0) * 0.6         // F2: 1000Hz
              + tract(x, 2450.0, 140.0) * 0.4;       // F3: 2450Hz
    return aud;
}

// Fricative consonant noise
float fricative(float t, float formantFreq) {
    return (hash11(floor(formantFreq * t) * 20.0) - 0.5) * 3.0;
}
```

### Variant 4: Algorithmic Composition (Generative Music)

**Difference from basic version**: Does not use handwritten note sequences; instead uses hash functions to generate pseudo-random melodies, with scale quantization to ensure harmonic consistency. Multi-level rhythmic subdivision (1-beat/2-beat/4-beat) produces fractal-like musical structure.

**Key modified code**:

```glsl
// 8-note pseudo-random loop
vec2 noteRing(float n) {
    float r = 0.5 + 0.5 * fract(sin(mod(floor(n), 32.123) * 32.123) * 41.123);
    n = mod(n, 8.0);
    // Adjustable: modify these intervals to change the melodic character
    float note = n<1.?0. : n<2.?5. : n<3.?-2. : n<4.?4. : n<5.?7. : n<6.?4. : n<7.?2. : 0.;
    return vec2(note, r);                            // (interval, volume)
}

// FBM-style layered note generation
vec2 generativeNote(float beat) {
    float b0 = floor(beat);
    float b1 = floor(beat * 0.5);
    float b2 = floor(beat * 0.25);
    // Large-scale + medium-scale + small-scale layering
    vec2 note = noteRing(b2 * 0.0625)
              + noteRing(b2 * 0.25)
              + noteRing(b2);
    return note;
}
```

### Variant 5: Chord Progression System (Circle of Fifths)

**Difference from basic version**: Automatically generates harmonic progressions based on the circle of fifths interval. Every 4 beats advances one fifth (+7 semitones), automatically alternating major/minor chords with jazz chord extensions (seventh, ninth).

**Key modified code**:

```glsl
vec2 mainSound(int samp, float time) {
    float id = floor(time / SPB / 4.0);             // Current chord number
    float offset = id * 7.0;                         // Circle of fifths: +7 semitones per step
    float minor = mod(id, 4.0) >= 3.0 ? 1.0 : 0.0; // Every 4th chord is minor
    float t = mod(time, SPB * 4.0);

    float root = 57.0 + mod(offset, 12.0);           // Adjustable: 57.0 = starting root (A3)
    vec2 result = chord(t, root, minor);

    // Two-tap ping-pong delay
    result += vec2(0.5, 0.2) * chord(t - SPB * 0.5, root, minor);
    result += vec2(0.05, 0.1) * chord(t - SPB, root, minor);

    return result;
}
```

## Performance Optimization Details

1. **Reduce Harmonic Count**: In additive synthesis and frequency-domain filters, the harmonic count (`NUM_HARMONICS` / `NSPC`) is the biggest performance bottleneck. Start with 4-8 harmonics and don't add more once the sound is satisfactory. Using 256 harmonics is an extreme case.

2. **Avoid Sample History in Loops**: IIR filters need to process 128 historical samples, meaning each output sample requires 128 loop iterations. Prefer frequency-domain methods or reduce `PAST_SAMPLES`.

3. **Simplify Echo/Delay**: Each delay tap requires recomputing the complete signal chain. 4 taps means 5x computation. Consider reducing the complexity (fewer harmonics) for delayed signals.

4. **Use `fract()` Instead of `mod()`**: When the divisor is 1.0, `fract(x)` is faster than `mod(x, 1.0)`.

5. **Precompute Constants**: Move loop-invariant expressions like `TAU * freq` outside the loop.

6. **Use the Common Pass**: Place constant definitions and shared functions in ShaderToy's Common tab, accessible by both Sound and Image, avoiding redundant computation of BPM/SPB, etc.

## Combination Suggestions

### 1. Combining with Audio Visualization

Sound shader output can be read in the Image shader via `iChannel0` (set to this shader's Sound output). Use `texture(iChannel0, vec2(freq, 0.0))` to get spectrum data to drive visual effects (waveforms, spectrum bar charts, etc.).

### 2. Combining with Raymarching Scenes

Sound-visual synchronization can be achieved by sharing timeline/cue events. Define shared timeline/cue events in the Common Pass, referenced by both Sound and Image shaders simultaneously, ensuring visual-audio synchronization.

### 3. Combining with Particle Systems

Use beat events (kick trigger moments) to drive particle emission. In the Image shader, use the same BPM/SPB to calculate the current beat position, and increase particle count or velocity at the kick trigger moment.

### 4. Combining with Post-Processing Effects

Share Sound shader envelope values (e.g., sidechain compression coefficient) with the Image shader via the Common Pass, driving bloom intensity, color shifting, screen shake, and other effects.

### 5. Combining with Text/Graphic Overlays

Use `message()` functions in the Image shader to render text hints, parameter displays, or interaction instructions to help users understand what is being played.
