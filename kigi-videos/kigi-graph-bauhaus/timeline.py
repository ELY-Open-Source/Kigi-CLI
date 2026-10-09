import json, math
vo = json.load(open("vo_timing.json", encoding="utf-8"))
OFF = {"s01": 2.0, "s02": 1.5}
MINTAIL = {"s13": 7.0, "s02": 1.8}
t, out = 0.0, []
for sid, v in vo.items():
    off = OFF.get(sid, 0.5)
    need = off + v["len"] + MINTAIL.get(sid, 0.6)
    dur = math.ceil(need / 2.0) * 2.0
    segs = [{**s, "t0": round(s["t0"] + off, 3), "t1": round(s["t1"] + off, 3)} for s in v["segs"]]
    out.append({"id": sid, "start": t, "dur": dur, "vo_off": off, "vo_len": v["len"], "segs": segs})
    t += dur
json.dump({"bpm": 120, "total": t, "scenes": out}, open("timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for s in out: print(s["id"], s["start"], s["dur"], "bars", s["dur"]/2)
print("total", t)
