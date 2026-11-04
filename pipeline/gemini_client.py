"""Thin Gemini Flash client for Yes Bro. Reads GEMINI_API_KEY. Dry-run if missing or YESBRO_DRY_RUN=1."""
from __future__ import annotations
import json, os, re, time, urllib.error, urllib.request

MODEL = os.environ.get("YESBRO_GEMINI_MODEL", "gemini-3.1-flash-lite")
API = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
_FAILS = 0
_CIRCUIT = False

class GeminiError(RuntimeError):
    pass

def available() -> bool:
    if _CIRCUIT:
        return False
    if os.environ.get("YESBRO_DRY_RUN", "").strip() in ("1", "true", "yes"):
        return False
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())

def _trip(reason: str):
    global _CIRCUIT, _FAILS
    _FAILS += 1
    if _FAILS >= int(os.environ.get("YESBRO_GEMINI_CIRCUIT", "3")):
        _CIRCUIT = True
        print(f"gemini circuit open after {_FAILS} failures ({reason}); using fallback copy", flush=True)

def _extract_text(data: dict) -> str:
    cands = data.get("candidates") or []
    if not cands:
        raise GeminiError(f"no candidates: {json.dumps(data)[:400]}")
    parts = (((cands[0] or {}).get("content") or {}).get("parts")) or []
    return "".join(p.get("text", "") for p in parts)

def _strip_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json|python)?\s*([\s\S]*?)\s*```$", text)
    return m.group(1).strip() if m else text

def generate(prompt: str, *, system: str = "", temperature: float = 0.4, retries: int = 3) -> str:
    """Return model text. Raises if key missing (unless caller checks available())."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise GeminiError("GEMINI_API_KEY not set")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 8192},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    data = json.dumps(body).encode("utf-8")
    url = f"{API}?key={key}"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return _extract_text(json.load(r))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")[:500]
            last = GeminiError(f"HTTP {e.code}: {err}")
            # rate limit / transient
            if e.code in (429, 500, 503):
                time.sleep(min(45, 5 * (2 ** attempt)))
                continue
            raise last
        except Exception as e:
            last = GeminiError(str(e))
            time.sleep(min(30, 2 ** attempt))
    if last and ("429" in str(last) or "503" in str(last) or "UNAVAILABLE" in str(last)):
        _trip(str(last)[:80])
    raise last or GeminiError("unknown failure")

def generate_json(prompt: str, *, system: str = "", temperature: float = 0.3) -> object:
    text = _strip_fence(generate(prompt, system=system, temperature=temperature))
    # tolerate leading junk before first { or [
    for i, ch in enumerate(text):
        if ch in "{[":
            text = text[i:]
            break
    return json.loads(text)
