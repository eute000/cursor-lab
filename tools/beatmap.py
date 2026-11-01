# -*- coding: utf-8 -*-
"""测 BPM + 拍点时间轴（谱通量 onset + 自相关）"""
import sys
import wave

import numpy as np

P = r"E:\deepseek\.tmp\vibe\bgm.wav"
with wave.open(P, "rb") as fh:
    sr = fh.getframerate()
    n = fh.getnframes()
    ch = fh.getnchannels()
    raw = fh.readframes(n)
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
if ch == 2:
    x = x.reshape(-1, 2).mean(axis=1)

hop, win = 512, 1024
frames = 1 + (len(x) - win) // hop
print("时长 %.1f 秒, 帧数 %d" % (len(x) / sr, frames))

# 谱通量（用 rfft 幅度差分）
env = np.zeros(frames, dtype=np.float32)
prev = None
w = np.hanning(win).astype(np.float32)
for i in range(frames):
    seg = x[i * hop: i * hop + win] * w
    mag = np.abs(np.fft.rfft(seg))[:256]
    if prev is not None:
        env[i] = np.maximum(mag - prev, 0).sum()
    prev = mag

env = env / (env.max() + 1e-9)
fps = sr / hop

# 自相关找主周期
e = env - env.mean()
ac = np.correlate(e, e, mode="full")[len(e) - 1:]
ac[:2] = 0
lo, hi = int(0.28 * fps), int(1.2 * fps)          # 50–214 BPM
seg = ac[lo:hi]
k = int(np.argmax(seg)) + lo
lag = k / fps
bpm = 60.0 / lag
print("自相关主周期: %.3f 秒 -> %.1f BPM" % (lag, bpm))

# 拍点：在估计 BPM 的网格上找局部最强能量，做相位校正
beat = 60.0 / bpm
phase_best, score_best = 0.0, -1
for ph in np.arange(0, beat, 0.01):
    idx = np.arange(ph, len(env) / fps - 0.05, beat) * fps
    idx = idx.astype(int)
    idx = idx[(idx >= 0) & (idx < len(env))]
    s = env[idx].mean()
    if s > score_best:
        score_best, phase_best = s, ph
print("相位校正: 首拍 %.3f 秒, 平均拍能量 %.3f" % (phase_best, score_best))

# 能量包络（每拍强度，用于"律动"驱动）
beats = np.arange(phase_best, len(env) / fps - 0.1, beat)
strength = [float(env[int(b * fps)]) for b in beats]
print("拍点数 %d, 强度范围 %.2f..%.2f" % (len(beats), min(strength), max(strength)))

np.savez(r"E:\deepseek\.tmp\vibe\beatmap.npz", bpm=bpm, beat=beat,
         phase=phase_best, beats=beats, strength=np.array(strength))
print("已存 beatmap.npz")
