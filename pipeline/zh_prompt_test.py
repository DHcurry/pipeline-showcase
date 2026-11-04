import sys, os, glob, subprocess
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone
import numpy as np
sys.path.insert(0, dub_clone.CV_REPO)

# 中文参考音: piper 时代生成的干净中文 u0000.wav
zh_ref = sorted(glob.glob(os.path.join(dub_clone.DIR, "dub_cache", "*E02*", "u0000.wav")))
assert zh_ref, "no piper wav"
zh_ref = zh_ref[0]
print("ZH_REF:", os.path.basename(os.path.dirname(zh_ref)), "size", os.path.getsize(zh_ref))

from cosyvoice.cli.cosyvoice import CosyVoice2
c2 = CosyVoice2(dub_clone.MDL, fp16=True)
T = "我没问题的，放心吧。这件事情交给我来处理。"
segs = list(c2.inference_zero_shot(T, "仓本，怎么了？", zh_ref, stream=False, speed=1.1))
speech = np.squeeze(np.concatenate([np.asarray(o["tts_speech"]) for o in segs], axis=0)).astype(np.float32)
import wave as _w
p = os.path.join(dub_clone.DIR, "zh_prompt_test.wav")
pcm = (np.clip(speech, -1, 1) * 32767).astype(np.int16)
with _w.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(pcm.tobytes())
print(f"synth done: {len(pcm)/22050:.2f}s")

from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
r = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","s16le","-ac","1","-ar","16000","-"], capture_output=True)
x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)/32768.0
segs, info = m.transcribe(x, language="zh", vad_filter=True)
got = "".join(s.text for s in segs).replace(" ", "")
print(f"AUDIT zh-prompt: 转写[{got}]")
key = "没问题"
print("VERDICT:", "PASS(中文条件化正常,病根=日语参考)" if key in got else "FAIL(环境/模型本身坏)")
