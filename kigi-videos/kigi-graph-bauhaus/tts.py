import json, sys, urllib.request, pathlib
KEY = pathlib.Path(r"C:\Users\zhang\Documents\Github\Kigi-CLI\env.md").read_text(encoding="utf-8").splitlines()[1].split("：",1)[1].strip()
def tts(text, out, voice, speed=1.0, extra=None):
    body = {"model":"speech-2.8-hd","text":text,"stream":False,"language_boost":"Chinese",
            "output_format":"hex","aigc_watermark":False,
            "voice_setting":{"voice_id":voice,"speed":speed,"vol":1,"pitch":0},
            "audio_setting":{"sample_rate":44100,"bitrate":256000,"format":"mp3","channel":1},
            "subtitle_enable":True,"subtitle_type":"word"}
    if extra: body.update(extra)
    req = urllib.request.Request("https://api.minimax.io/v1/t2a_v2", data=json.dumps(body).encode(),
          headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=180))
    if d["base_resp"]["status_code"] != 0: raise SystemExit(d["base_resp"])
    pathlib.Path(out).write_bytes(bytes.fromhex(d["data"]["audio"]))
    subs = None
    if d["data"].get("subtitle_file"):
        subs = json.load(urllib.request.urlopen(d["data"]["subtitle_file"], timeout=60))
    return d["extra_info"], subs
if __name__ == "__main__":
    info, subs = tts(sys.argv[2], sys.argv[1], sys.argv[3])
    print(info); print(json.dumps(subs, ensure_ascii=False)[:1500])
