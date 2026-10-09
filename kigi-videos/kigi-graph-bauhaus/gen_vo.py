import json, pathlib, concurrent.futures as cf
from tts import tts
VOICE = "moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85"
script = json.load(open("script.json", encoding="utf-8"))
def run(sc):
    text = "".join(s.get("tts", s["zh"]) for s in sc["segs"])
    info, subs = tts(text, f"audio/vo_{sc['id']}.mp3", VOICE, speed=1.05)
    words = [w for seg in subs for w in seg["timestamped_words"]]
    # map segment char ranges -> times
    out, pos = [], 0
    for s in sc["segs"]:
        t = s.get("tts", s["zh"]); a, b = pos, pos + len(t); pos = b
        ws = [w for w in words if w["word_begin"] >= a and w["word_end"] <= b and w["word"].strip("，。：；——？！、“” ")]
        out.append({"zh": s["zh"], "en": s["en"], "t0": ws[0]["time_begin"]/1000, "t1": ws[-1]["time_end"]/1000})
    return sc["id"], {"len": info["audio_length"]/1000, "segs": out}
with cf.ThreadPoolExecutor(6) as ex:
    res = dict(ex.map(run, script))
json.dump({k: res[k] for k in sorted(res)}, open("vo_timing.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
for k in sorted(res): print(k, res[k]["len"], [ (round(s["t0"],2), round(s["t1"],2)) for s in res[k]["segs"]])
