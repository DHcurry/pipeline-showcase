import sys, os, json, subprocess, time, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dub_clone          # 必须先于 numpy：dub_clone 做了 sys.path 纠偏(venv numpy1.26)
import numpy as np
sys.path.insert(0, dub_clone.CV_REPO)

CACHE = r"C:\Users\16575\daily-movie\dub_cache\Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV"
VOC = r"C:\Users\16575\daily-movie\dub_cache\demucs_E02\htdemucs\Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV\vocals.mp3"
JPN = r"D:\download\【高清剧集网发布 www.DDHDTV.com】灾[全6集][中文字幕].Sai.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV\Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV.jpn.srt"
data = json.load(open(os.path.join(CACHE, "_speakers_v.json"), encoding="utf-8"))
refs0 = data["refs"]["0"]

clips = []
for n, r in enumerate(refs0):
    c = os.path.join(CACHE, f"tmp_r{n}.wav")
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(r["s"]),"-to",str(r["e"]),
                    "-i", VOC, "-ac","1","-ar","16000", c], check=True)
    clips.append(c)
cat = os.path.join(CACHE, "refcat_spk0.wav")
with open(os.path.join(CACHE, "_cl.txt"), "w", encoding="utf-8") as f:
    for c in clips:
        f.write("file '" + c.replace("\\", "/") + "'\n")
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",
                os.path.join(CACHE,"_cl.txt"), cat], check=True)

def ja_at(t):
    raw = open(JPN, encoding="utf-8-sig", errors="replace").read()
    for part in re.split(r"\n\s*\n", raw.strip()):
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.]\d{3}\s*-->\s*(\d{2}):(\d{2}):(\d{2})", part)
        if not m: continue
        g = [int(x) for x in m.groups()]
        s = g[0]*3600+g[1]*60+g[2]
        if abs(s - t) <= 1.2:
            return " ".join(l.strip() for l in part[m.end():].splitlines() if l.strip())
    return ""

pt_single = ja_at(refs0[0]["s"]) or "はい。"
pt_cat = " ".join(filter(None, (ja_at(r["s"]) for r in refs0))) or "はい。"
seg0 = data["segments"][0]["text"]
print("MODE target:", seg0, "| pt_single:", pt_single[:40])

from cosyvoice.cli.cosyvoice import CosyVoice2
c2 = CosyVoice2(dub_clone.MDL, fp16=True)

def save(arr, path):
    arr = np.squeeze(np.asarray(arr)).astype(np.float32)
    pcm = (np.clip(arr, -1, 1) * 32767).astype(np.int16)
    import wave as _w
    with _w.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        w.writeframes(pcm.tobytes())

single_ref = os.path.join(CACHE, "refc_spk0.wav")
outs = {}
t0 = time.time()
outs["A_zero_single"] = list(c2.inference_zero_shot(seg0, pt_single, single_ref, stream=False, speed=1.1))
print(f"MODE A done {time.time()-t0:.0f}s")
t0 = time.time()
outs["B_zero_concat"] = list(c2.inference_zero_shot(seg0, pt_cat, cat, stream=False, speed=1.1))
print(f"MODE B done {time.time()-t0:.0f}s")
t0 = time.time()
outs["C_cross_concat"] = list(c2.inference_cross_lingual(seg0, cat, stream=False, speed=1.1))
print(f"MODE C done {time.time()-t0:.0f}s")

def to16k(path):
    r = subprocess.run(["ffmpeg","-v","error","-i",path,"-f","s16le","-ar","16000","-ac","1","-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0

from resemblyzer import VoiceEncoder
ve = VoiceEncoder(device="cpu")
R = {}
for k in ["0", "1", "2"]:
    p = os.path.join(CACHE, f"refc_spk{k}.wav")
    if os.path.exists(p):
        R[k] = ve.embed_utterance(to16k(p))

for name, o in outs.items():
    p = os.path.join(CACHE, f"variant_{name}.wav")
    save(np.concatenate([x["tts_speech"] for x in o]), p)
    e = ve.embed_utterance(to16k(p))
    sims = {k: float(np.dot(e, R[k]) / (np.linalg.norm(e) * np.linalg.norm(R[k]))) for k in R}
    own = sims.get("0", 0)
    other = max([v for k, v in sims.items() if k != "0"], default=0)
    print(f"RESULT {name}: " + " ".join(f"ref{k}={v:.3f}" for k, v in sims.items()) + f" | 身份余量={own-other:+.3f}")
