import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone          # sys.path 纠偏先行
import numpy as np
sys.path.insert(0, dub_clone.CV_REPO)

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "dub_cache", "Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV")
JPN = os.path.join(dub_clone.SAI, "Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV.jpn.srt")
data = json.load(open(os.path.join(CACHE, "_speakers_v.json"), encoding="utf-8"))
pt = dub_clone.ja_text_at(JPN, data["refs"]["0"][0]["s"])
ref = os.path.join(CACHE, "refc_spk0.wav")

from cosyvoice.cli.cosyvoice import CosyVoice2
print("loading fp32 model...", flush=True)
c2 = CosyVoice2(dub_clone.MDL, fp16=False)
T = "仓本，怎么了？"
segs = list(c2.inference_zero_shot(T, pt, ref, stream=False, speed=1.1))
speech = np.squeeze(np.concatenate([np.asarray(o["tts_speech"]) for o in segs], axis=0)).astype(np.float32)
import wave as _w
p = os.path.join(CACHE, "fp32_test.wav")
pcm = (np.clip(speech, -1, 1) * 32767).astype(np.int16)
with _w.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(pcm.tobytes())
print(f"fp32 synth done: {len(pcm)/22050:.2f}s")

from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
segs, info = m.transcribe(x, language="zh", vad_filter=True)
got = "".join(s.text for s in segs).replace(" ", "")
print(f"AUDIT fp32: 预期[{T}] 转写[{got}] -> {'PASS' if '仓本' in got or '怎么' in got else 'FAIL'}")
