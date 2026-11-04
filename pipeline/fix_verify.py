import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone          # 先做 sys.path 纠偏(venv numpy1.26)
import numpy as np
import dub_clone
sys.path.insert(0, dub_clone.CV_REPO)

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "dub_cache", "Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV")
JPN = os.path.join(dub_clone.SAI, "Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV.jpn.srt")
data = json.load(open(os.path.join(CACHE, "_speakers_v.json"), encoding="utf-8"))
refs0 = data["refs"]["0"]
ref = os.path.join(CACHE, "refc_spk0.wav")
pt = dub_clone.ja_text_at(JPN, refs0[0]["s"])
print("CLEAN_PT:", repr(pt))

from cosyvoice.cli.cosyvoice import CosyVoice2
c2 = CosyVoice2(dub_clone.MDL, fp16=True)

lines = ["仓本，怎么了？", "你可以帮我看一下这个吗？", "我有完全推进去。"]
outs = []
for i, t in enumerate(lines):
    segs = list(c2.inference_zero_shot(t, pt, ref, stream=False, speed=1.1))
    speech = np.concatenate([np.asarray(o["tts_speech"]) for o in segs], axis=0)
    speech = np.squeeze(speech).astype(np.float32)
    import wave as _w
    p = os.path.join(CACHE, f"fixtest_{i}.wav")
    pcm = (np.clip(speech, -1, 1) * 32767).astype(np.int16)
    with _w.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(pcm.tobytes())
    outs.append(p)
    print(f"synth {i}: {t} -> {len(pcm)/22050:.2f}s")

from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
okc = 0
for i, (t, p) in enumerate(zip(lines, outs)):
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
    segs, info = m.transcribe(x, language="zh", vad_filter=True)
    got = "".join(s.text for s in segs).replace(" ", "")
    key = t.replace("，", "").replace("。", "")[:4]
    hit = key in got
    okc += hit
    print(f"AUDIT {i}: 预期[{t}] 转写[{got}] -> {'PASS' if hit else 'FAIL'}")
print("VERDICT:", "PASS" if okc == len(lines) else f"{okc}/{len(lines)}")
