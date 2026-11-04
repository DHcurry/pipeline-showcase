import sys, os, json, subprocess
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone
import numpy as np
sys.path.insert(0, dub_clone.CV_REPO)

BANK = os.path.join(dub_clone.DIR, "voice_bank")
man = json.load(open(os.path.join(BANK, "manifest.json"), encoding="utf-8"))
f_spk = next(k for k, v in man.items() if v["gender"] == "female")
m_spk = next(k for k, v in man.items() if v["gender"] == "male")
print(f"REF female={f_spk} male={m_spk}")

from cosyvoice.cli.cosyvoice import CosyVoice2
c2 = CosyVoice2(dub_clone.MDL, fp16=True)

TESTS = [(f_spk, "仓本，怎么了？你可以帮我看一下这个吗？"),   # 女角台词
         (m_spk, "我没问题的，放心吧。这件事情交给我来处理。")]  # 男角台词
import wave as _w
outs = []
for spk, text in TESTS:
    segs = list(c2.inference_zero_shot(text, man[spk]["text"], man[spk]["ref"], stream=False, speed=1.1))
    a = np.squeeze(np.concatenate([np.asarray(o["tts_speech"]) for o in segs], axis=0)).astype(np.float32)
    p = os.path.join(BANK, f"test_{spk}.wav")
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with _w.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(pcm.tobytes())
    outs.append((spk, p, text))
    print(f"synth {spk}: {len(pcm)/22050:.2f}s")

from faster_whisper import WhisperModel
import librosa
m = WhisperModel("small", device="cpu", compute_type="int8")
for spk, p, text in outs:
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
    segs, _ = m.transcribe(x, language="zh", vad_filter=True, condition_on_previous_text=False)
    got = "".join(s.text for s in segs)
    from opencc import OpenCC
    got = OpenCC("t2s").convert(got).replace(" ", "")
    exp = text.replace("，", "").replace("？", "").replace("。", "")[:6]
    hit = exp in got
    f0 = librosa.yin(x, fmin=60, fmax=400, sr=16000)
    v = f0[(f0 > 65) & (f0 < 395)]
    med = float(np.median(v)) if len(v) else 0
    print(f"AUDIT {spk}({man[spk]['gender']}参考): 转写[{got}] -> {'PASS' if hit else 'FAIL'} | 输出F0={med:.0f}Hz")
print("TEST-DONE")
