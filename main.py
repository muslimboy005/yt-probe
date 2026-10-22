"""Tiny diagnostic: can this host reach YouTube caption data? (no secrets, no user data)"""
import json, re
import httpx
from fastapi import FastAPI

app = FastAPI()
IOS = {"clientName": "IOS", "clientVersion": "20.10.4", "deviceMake": "Apple", "deviceModel": "iPhone16,2", "osName": "iPhone", "osVersion": "18.3.2.22D82", "hl": "en", "gl": "US"}
UA_IOS = "com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3_2 like Mac OS X;)"

@app.get("/")
def probe(v: str = "UF8uR6Z6KLc"):
    out = {}
    try:
        out["egress_ip"] = httpx.get("https://ifconfig.me/ip", timeout=10).text.strip()
    except Exception as e:
        out["egress_ip"] = f"err {e}"
    try:
        r = httpx.post("https://www.youtube.com/youtubei/v1/player?prettyPrint=false", json={"context": {"client": IOS}, "videoId": v, "contentCheckOk": True, "racyCheckOk": True}, headers={"User-Agent": UA_IOS}, timeout=20)
        j = r.json()
        ps = j.get("playabilityStatus", {})
        tracks = j.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        out["player"] = {"http": r.status_code, "status": ps.get("status"), "reason": ps.get("reason"), "captionTracks": len(tracks)}
        if tracks:
            t = next((t for t in tracks if t.get("languageCode") == "en"), tracks[0])
            rr = httpx.get(t["baseUrl"] + "&fmt=json3", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            out["timedtext"] = {"http": rr.status_code, "bytes": len(rr.content)}
    except Exception as e:
        out["player"] = f"err {e}"
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        tl = YouTubeTranscriptApi().list(v)
        out["youtube_transcript_api"] = f"ok, {len(list(tl))} tracks"
    except Exception as e:
        out["youtube_transcript_api"] = type(e).__name__ + ": " + " ".join(str(e).split())[:160]
    try:
        html = httpx.get(f"https://www.youtube.com/watch?v={v}", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"}, timeout=20).text
        out["watch_page"] = {"captionTracks_in_html": "captionTracks" in html, "bot_check": "confirm you’re not a bot" in html or "confirm you're not a bot" in html}
    except Exception as e:
        out["watch_page"] = f"err {e}"
    return out
