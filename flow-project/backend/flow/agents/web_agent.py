"""Web Agent: browsing, search, best-match playback and playback controls (FR-26 to FR-30)."""
from __future__ import annotations

import re
import urllib.parse

import requests

from flow import config, desktop, media_queue, settings
from flow.agents.base import Agent, Result, open_url

SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "bing": "https://www.bing.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
}
VIDEO_RESULTS = "https://www.youtube.com/results?search_query={}"
WATCH = "https://www.youtube.com/watch?v={}"
MATCH_THRESHOLD = 0.6
MEDIA_KEYS = {"pause": "playpause", "resume": "playpause", "next": "nexttrack"}
_RENDERER = re.compile(
    r'"videoRenderer":\{"videoId":"([\w-]{11})".*?"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', re.S)
_WORD = re.compile(r"[a-z0-9]+")


def _search_with_ytdlp(query: str) -> list[tuple[str, str]]:
    """Search YouTube through yt-dlp, which keeps working when the site's page layout changes."""
    try:
        import yt_dlp
    except ImportError:
        return []
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
    except Exception:
        return []
    results = []
    for entry in (info or {}).get("entries") or []:
        vid, title = entry.get("id"), entry.get("title")
        if vid and title:
            results.append((vid, title))
    return results[:5]


def _scrape_results(query: str) -> list[tuple[str, str]]:
    """Fallback: read the results page directly. Fragile, used only when yt-dlp is missing or fails."""
    try:
        html = requests.get(VIDEO_RESULTS.format(urllib.parse.quote_plus(query)),
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
    except requests.RequestException:
        return []
    seen, out = set(), []
    for vid, title in _RENDERER.findall(html):
        if vid not in seen:
            seen.add(vid)
            out.append((vid, title))
        if len(out) == 5:
            break
    return out


def search_candidates(query: str) -> list[tuple[str, str]]:
    """Up to five (video_id, title) pairs for the query."""
    if config.MOCK_MODE:
        return []
    return _search_with_ytdlp(query) or _scrape_results(query)


def rank(query: str, candidates: list[tuple[str, str]]) -> list[tuple[float, str, str]]:
    """Score each title by the share of query words it contains, best first."""
    words = set(_WORD.findall(query.lower()))
    if not words:
        return []
    scored = [(len(words & set(_WORD.findall(title.lower()))) / len(words), vid, title)
              for vid, title in candidates]
    return sorted(scored, key=lambda x: -x[0])


def _play(vid: str, title: str) -> Result:
    """Videos open in the FLOW player window, which can autoplay with sound."""
    url = WATCH.format(vid)
    media_queue.queue(url)
    return Result(True, f"Playing '{title}' in the FLOW player window.", {"media_url": url})


class WebAgent(Agent):
    name = "Web"
    ACTIONS = frozenset({"open_url", "search", "play_media", "media_control"})

    def do_open_url(self, params: dict, ctx: dict) -> Result:
        url = str(params.get("url", "")).strip()
        if not url.startswith(("https://", "http://")) or len(url) > 2000:
            return Result(False, "Only http and https addresses can be opened")
        open_url(url)
        return Result(True, f"Opened {url}")

    def do_search(self, params: dict, ctx: dict) -> Result:
        query = str(params.get("query", "")).strip()
        if not query:
            return Result(False, "There is nothing to search for")
        template = SEARCH_ENGINES.get(settings.get()["search_engine"], SEARCH_ENGINES["google"])
        open_url(template.format(urllib.parse.quote_plus(query)))
        return Result(True, f"Searched the web for '{query}'")

    def do_play_media(self, params: dict, ctx: dict) -> Result:
        query = str(params.get("query", "")).strip()
        if not query:
            return Result(False, "There is nothing to play")
        if params.get("confirmed"):  # the user chose one of the offered results (FR-29)
            options = (params.get("pending") or {}).get("candidates") or []
            index = int(params.get("choice") or 0)
            if not 0 <= index < len(options):
                return Result(False, "That choice is not one of the offered results")
            vid, title = options[index]
            return _play(vid, title)

        candidates = search_candidates(query)
        if not candidates:
            open_url(VIDEO_RESULTS.format(urllib.parse.quote_plus(query)))
            return Result(True, f"Could not pick a result for '{query}' automatically, so I opened the results. "
                                "If this keeps happening, install the search helper: python -m pip install yt-dlp")
        ranked = rank(query, candidates)
        best_score, best_id, best_title = ranked[0]
        if best_score >= MATCH_THRESHOLD:
            return _play(best_id, best_title)
        options = [[vid, title] for _, vid, title in ranked]
        listing = "; ".join(f"{i + 1}) {title}" for i, (_, _, title) in enumerate(ranked))
        return Result(False, f"No clear match for '{query}'. Choose one of the top results: {listing}",
                      {"candidates": options, "options": [t for _, t in options], "choices": len(options)},
                      needs_confirmation=True)

    def do_media_control(self, params: dict, ctx: dict) -> Result:
        command = str(params.get("command", "")).lower()
        key = MEDIA_KEYS.get(command)
        if key is None:
            return Result(False, "Supported media commands are pause, resume and next")
        ok, message = desktop.media_key(key)
        return Result(ok, message)
