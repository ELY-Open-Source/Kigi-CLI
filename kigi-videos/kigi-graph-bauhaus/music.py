"""Procedural 120 BPM score for the 34 s cut: every hit is placed on the same beat grid the picture uses."""
import json, subprocess, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

FFMPEG = r"C:\Users\zhang\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
SR, TOTAL, BEAT = 48000, 34.0, 0.5
N = int(SR * TOTAL)
rng = np.random.default_rng(7)
bus = {k: np.zeros(N) for k in ["drums", "music", "fx"]}


def env(n, decay, attack=0.002):
    t = np.arange(n) / SR
    a = np.minimum(1, t / attack) if attack > 0 else 1
    return a * np.exp(-t / decay)


def put(b, t, sig, gain=1.0):
    i = int(round(t * SR))
    if i >= N: return
    sig = sig[: N - i]
    bus[b][i : i + len(sig)] += sig * gain


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2): return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------- instruments ----------
def kick(g=1.0):
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.22)
    s += hp(rng.standard_normal(n), 2000) * env(n, 0.004) * 0.4
    return np.tanh(s * 1.6) * g

def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    return hp(rng.standard_normal(n), 7000, 4) * env(n, 0.09 if open_ else 0.018) * 0.35

def clap():
    n = int(0.3 * SR); s = bp(rng.standard_normal(n), 900, 3000)
    e = sum(env(n, 0.008) * (np.arange(n) >= int(k * SR)) for k in (0, 0.011, 0.022)) + env(n, 0.09) * 0.6
    return s * e * 0.55

def tick():
    n = int(0.03 * SR); return hp(rng.standard_normal(n), 4000) * env(n, 0.004) * 0.5

def marimba(m, dur=0.35, g=0.3):
    n = int(dur * 2 * SR); t = np.arange(n) / SR; f = hz(m)
    s = np.sin(2*np.pi*f*t)*env(n, dur*0.6) + 0.35*np.sin(2*np.pi*f*3.93*t)*env(n, dur*0.12) + 0.1*np.sin(2*np.pi*f*9.2*t)*env(n, 0.02)
    return s * g

def bass(m, dur=0.24, g=0.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    saw = 2 * ((f * t) % 1) - 1
    s = lp(saw, 500) + 0.6 * np.sin(2 * np.pi * f * t)
    e = env(n, dur * 0.8, 0.004) * np.minimum(1, (n - np.arange(n)) / (0.01 * SR))
    return np.tanh(s * e * 1.4) * g

def pad(ms, dur, g=0.11):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in ms:
        for d in (-0.08, 0.0, 0.08):
            f = hz(m + d); s += 2 * ((f * t + rng.random()) % 1) - 1
    s = lp(s, 1400)
    a = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.5)
    return s * a * g / len(ms)

def impact(g=1.0):
    n = int(2.5 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 40 * np.exp(-t / 0.08)) * t) * env(n, 0.7)
    crash = hp(rng.standard_normal(n), 3000) * env(n, 0.9) * 0.25
    return (np.tanh(boom * 1.4) * 0.9 + crash) * g

def riser(dur=1.0, g=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n); out = np.zeros(n); seg = int(0.05 * SR)
    for i in range(0, n, seg):  # stepped filter sweep
        f = 400 + 7000 * (i / n) ** 2
        out[i:i+seg] = bp(x[i:i+seg], f, min(f * 1.6, 20000))
    return out * (t / dur) ** 2 * g

def whoosh(g=0.5):
    n = int(0.35 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 600, 6000)
    return s * np.sin(np.pi * t / t[-1]) ** 2 * g

def stamp(g=0.8, pitch=60):
    n = int(0.4 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (hz(pitch - 24) + 80 * np.exp(-t / 0.02)) * t) * env(n, 0.12)
    s += bp(rng.standard_normal(n), 1500, 5000) * env(n, 0.01) * 0.6
    return np.tanh(s * 2) * g

def buzz(g=0.35):
    n = int(0.45 * SR); t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 110 * t)) + np.sign(np.sin(2 * np.pi * 116.5 * t))
    return lp(s, 1800) * env(n, 0.18) * g


# ---------- arrangement (A minor; bar = 2 s) ----------
CHORDS = {0: (57, [57, 60, 64]), 1: (53, [53, 57, 60]), 2: (48, [52, 55, 60]), 3: (55, [55, 59, 62])}  # Am F C G
def chord(bar): return CHORDS[bar % 4]
def on(t0, t1, step):
    return [round(x, 4) for x in np.arange(t0, t1 - 1e-9, step)]

# intro: metronome eighths 0-2, kick at 0.5 (square drop)
for t in on(0, 2, 0.25): put("drums", t, tick(), 0.6 if (t * 4) % 2 == 0 else 0.3)
put("fx", 0.5, impact(0.7)); put("drums", 0.5, kick(1.0))

def groove(t0, t1, hats=0.5, claps=True, kicks=True, hat16=False):
    for t in on(t0, t1, BEAT):
        if kicks: put("drums", t, kick())
        if claps and round((t / BEAT)) % 2 == 1: put("drums", t, clap())
    for t in on(t0, t1, 0.125 if hat16 else 0.25):
        off = abs((t / 0.5) % 1 - 0.5) < 1e-6
        put("drums", t, hat(open_=off and not hat16), hats * (1.0 if off else 0.6))

def ostinato(t0, t1, octave=12, g=0.26, step=0.125, cycle=3):
    for k, t in enumerate(on(t0, t1, step)):
        root, tri = chord(int(t // 2)); note = tri[[0, 1, 2, 1, 2][k % cycle] if cycle == 5 else k % 3]
        put("music", t, marimba(note + octave, 0.3, g * (1.0 if k % 4 == 0 else 0.7)))

def bassline(t0, t1, g=0.5):
    for t in on(t0, t1, 0.25):
        root, _ = chord(int(t // 2)); pos = round((t % 0.5) / 0.25)
        if pos == 1 or (t % 2) < 1e-6: put("music", t, bass(root - 12 + (12 if pos == 1 and (t % 1) > 0.5 else 0), 0.22, g))

def pads(t0, t1):
    for b in range(int(t0 // 2), int(t1 // 2)):
        put("music", b * 2.0, pad(chord(b)[1], 2.05))

# hook 2-6
groove(2, 6, hats=0.35, claps=False); ostinato(2, 6, g=0.2); bassline(4, 6, 0.4)
put("fx", 5.0, riser(1.0, 0.3))
# title 6-10
put("fx", 6.0, impact(1.0))
groove(6, 10); ostinato(6, 10); bassline(6, 10); pads(6, 10)
for t in (6.5, 6.75, 7.0, 7.25): put("fx", t, stamp(0.45, 72))
for t in on(7.5, 8.0, 0.0625): put("fx", t, tick(), 0.5)
put("fx", 8.0, stamp(0.9, 48))
# principle 10-18
put("fx", 10.0, impact(0.55))
groove(10, 18, hats=0.45); ostinato(10, 18); bassline(10, 18); pads(10, 18)
for t in on(13.0, 15.5, 0.25): put("fx", t, tick(), 0.35)  # ruler ticks while edges draw
for t in (16.0, 16.5, 17.0): put("fx", t, marimba(84, 0.4, 0.35))
put("fx", 17.0, riser(1.0, 0.35))
# fan-out 18-24 (peak)
put("fx", 18.0, impact(0.9))
groove(18, 24, hats=0.45, hat16=True); ostinato(18, 24, g=0.24); ostinato(18.125, 24, octave=24, g=0.12, step=0.25, cycle=5)
bassline(18, 24, 0.55); pads(18, 24)
put("fx", 21.0, buzz())
for t in (22.0, 22.5, 23.0): put("fx", t, stamp(0.8, 67))
put("fx", 23.0, riser(1.0, 0.35))
# gn-final 24-27.5: suspense (no kick), then the verdict hit
put("fx", 24.0, impact(0.8))
ostinato(24, 27.5, g=0.2); pads(24, 28)
for t in on(24, 27.5, 0.5): put("drums", t, hat(), 0.25)
for t in (24.0, 24.5, 25.0, 25.5): put("fx", t, marimba(88, 0.25, 0.25))
put("fx", 26.5, riser(1.0, 0.4))
put("fx", 27.5, impact(1.1)); put("fx", 27.5, stamp(0.9, 52))
# bones & flesh 27.5-30: full groove
groove(27.5, 30, hats=0.5); ostinato(27.5, 30); bassline(27.5, 30); pads(28, 30)
# logo 30-34
put("fx", 30.0, impact(0.7)); groove(30, 32, hats=0.4); ostinato(30, 32, g=0.22); bassline(30, 32)
for t, m in ((31.0, 76), (31.5, 79), (32.0, 81)): put("fx", t, marimba(m, 0.6, 0.45))
put("fx", 32.0, impact(1.0)); put("drums", 32.0, kick(1.1))
put("music", 32.0, pad([45, 57, 60, 64, 69], 2.0, 0.22))
for m in (57, 60, 64, 69): put("music", 32.0, marimba(m, 1.2, 0.25))
# transition whooshes (end on the cut)
for t in (6.0, 10.0, 18.0, 24.0, 30.0): put("fx", t - 0.3, whoosh(0.45))

# ---------- reverb, voice, ducking, master ----------
def reverb(x, sec=1.4, wet=0.18):
    n = int(sec * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (sec / 5))
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    return x + fftconvolve(x, ir)[: len(x)] * wet

music = reverb(bus["music"], wet=0.25) + bus["drums"] * 0.9 + reverb(bus["fx"], wet=0.2)

vo = np.zeros(N)
tl = json.load(open("timeline.json", encoding="utf-8"))["scenes"]
for sid, (st, dur, off) in tl.items():
    raw = subprocess.run([FFMPEG, "-v", "quiet", "-i", f"audio/vo_{sid}.mp3", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    v = np.frombuffer(raw, dtype=np.float32).astype(float)
    i = int((st + off) * SR); vo[i : i + len(v)] += v[: N - i]
vo = hp(vo, 70) / (np.abs(vo).max() + 1e-9) * 0.85

# sidechain: duck music ~7 dB under narration, 30 ms attack, 250 ms release
lvl = np.abs(vo); k = int(0.02 * SR)
lvl = np.convolve(lvl, np.ones(k) / k, mode="same")
gate = (lvl > 0.02).astype(float)
duck = np.zeros(N); a, r = np.exp(-1 / (0.03 * SR)), np.exp(-1 / (0.25 * SR)); g = 0.0
for i in range(0, N, 64):  # block-rate envelope follower
    target = gate[i]; c = a ** 64 if target > g else r ** 64
    g = target + (g - target) * c; duck[i : i + 64] = g
music *= 1 - 0.55 * duck
music = music / (np.abs(music).max() + 1e-9) * 0.62

mix = np.tanh((music + vo) * 1.1)
fade = np.ones(N); fl = int(0.6 * SR); fade[-fl:] = np.linspace(1, 0, fl)
mix *= fade
mix = mix / np.abs(mix).max() * 0.94
stereo = np.stack([mix, mix], 1)
sf.write("audio/mix.wav", stereo, SR, subtype="PCM_16")
sf.write("audio/score.wav", np.stack([music, music], 1) * 0.9, SR, subtype="PCM_16")
print("ok", stereo.shape, "peak", np.abs(mix).max())
