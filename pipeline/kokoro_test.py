import sys, os, subprocess, time, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone
import numpy as np

OUT = os.path.join(dub_clone.DIR, "kokoro_test")
os.makedirs(OUT, exist_ok=True)

from kokoro import KPipeline
t0 = time.time()
pipe = KPipeline(lang_code='z')
print(f"pipeline {time.time()-t0:.0f}s")

TEXTS = {
    "zm_yunxi":   "我没问题的，放心吧。这件事情交给我来处理。",
    "zf_xiaoxiao": "仓本，怎么了？你可以帮我看一下这个吗？",
}
results = {}
for voice, text in TEXTS.items():
    t0 = time.time()
    waves = []
    for seg in pipe(text, voice=voice):
        a = np.asarray(seg.audio)
        waves.append(a)
    audio = np.concatenate(waves) if len(waves) > 1 else waves[0]
    p = os.path.join(OUT, f"{voice}.wav")
    import soundfile as sf
    sf.write(p, audio, 24000)
    dur = len(audio) / 24000
    print(f"synth {voice}: {dur:.2f}s ({time.time()-t0:.0f}s)")
    results[voice] = p

# Whisper 内容审听
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
for voice, p in results.items():
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
    segs, info = m.transcribe(x, language="zh", vad_filter=True)
    got = "".join(s.text for s in segs).replace(" ", "")
    exp = TEXTS[voice].replace("，", "").replace("？", "").replace("。", "")[:6]
    ok = exp[:4] in got
    print(f"AUDIT {voice}: 转写[{got}] -> {'PASS' if ok else 'FAIL'}")

# F0 基频(性别客观指标: 男 <180Hz < 女)
import librosa
for voice, p in results.items():
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
    y = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
    f0 = librosa.yin(y, fmin=60, fmax=400, sr=16000)
    voiced = f0[(f0 > 65) & (f0 < 395)]
    med = float(np.median(voiced)) if len(voiced) else 0
    gender = "男声" if 0 < med < 180 else "女声"
    print(f"F0 {voice}: 中位={med:.0f}Hz -> {gender}")
print("ALL-DONE")
