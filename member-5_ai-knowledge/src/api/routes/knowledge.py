import asyncio
import logging
import json
import hashlib
import time
import re
from urllib.parse import quote_plus

import aiohttp
from aiohttp import web
from src.knowledge.graph import knowledge_graph
from src.embeddings.embedder import embedder
from src.embeddings.vector_store import vector_store
from src.models.registry import registry
from src.config import settings

logger = logging.getLogger("tesseract.knowledge.routes")


async def handle_update_knowledge(request: web.Request) -> web.Response:
    """POST /api/v1/knowledge/update — Ingest behavioral evidence from Member 4."""
    data = await request.json()
    concepts = data.get("concepts", [])
    domain = data.get("domain") or data.get("topic") or "general"
    skill_id = data.get("skill") or data.get("skill_id") or data.get("topic")
    evidence_type = data.get("evidence_type") or ("success" if data.get("outcome") == "success" else "error_resolved")
    delta = float(data.get("confidence_delta", 0.10 if data.get("outcome") == "success" else -0.10))
    episode_id = data.get("source_episode_id")
    metadata = data.get("metadata") or {}
    metadata["domain"] = domain
    metadata["file_path"] = data.get("file_path", "")

    updated_nodes = []
    if concepts and isinstance(concepts, list):
        for concept_name in concepts:
            clean_name = str(concept_name).strip()
            cid = f"{domain}-{clean_name.lower().replace(' ', '-').replace('/', '-').replace('&', 'and')}"
            meta = {**metadata, "name": clean_name, "domain": domain}
            node = knowledge_graph.record_evidence(
                skill_id=cid,
                evidence_type=evidence_type,
                confidence_delta=delta,
                source_episode_id=episode_id,
                metadata=meta,
            )
            if node:
                updated_nodes.append(node.model_dump())

    if skill_id and not concepts:
        node = knowledge_graph.record_evidence(
            skill_id=skill_id,
            evidence_type=evidence_type,
            confidence_delta=delta,
            source_episode_id=episode_id,
            metadata=metadata,
        )
        if node:
            updated_nodes.append(node.model_dump())

    return web.json_response({
        "status": "success",
        "updated_skills": updated_nodes,
        "count": len(updated_nodes)
    })


async def handle_get_graph(request: web.Request) -> web.Response:
    """GET /api/v1/knowledge/graph — Return snapshot for Member 6 dashboard."""
    snapshot = knowledge_graph.get_snapshot()
    return web.json_response(snapshot.model_dump())


async def handle_get_skill(request: web.Request) -> web.Response:
    """GET /api/v1/knowledge/skill/{id}"""
    skill_id = request.match_info.get("id", "")
    skill = knowledge_graph.get_skill(skill_id)
    if not skill:
        return web.json_response({"error": "not_found", "message": f"Skill '{skill_id}' not found"}, status=404)

    evidence = knowledge_graph.store.get_evidence_for_skill(skill_id, limit=20)
    return web.json_response({
        "skill": skill.model_dump(),
        "recent_evidence": [e.model_dump() for e in evidence],
    })


async def handle_get_gaps(request: web.Request) -> web.Response:
    """GET /api/v1/knowledge/gaps?skill=<id>"""
    skill_id = request.query.get("skill", "")
    if not skill_id:
        # Return all weak skills across the whole graph
        snapshot = knowledge_graph.get_snapshot()
        weak_skills = [s.model_dump() for s in snapshot.nodes if s.status == "weak"]
        return web.json_response({"gaps": weak_skills})

    gaps = knowledge_graph.find_prerequisite_gaps(skill_id)
    return web.json_response({"skill": skill_id, "gaps": [g.model_dump() for g in gaps]})


async def handle_query_knowledge(request: web.Request) -> web.Response:
    """POST /api/v1/knowledge/query — Semantic vector retrieval."""
    data = await request.json()
    query = data.get("query", "")
    top_k = int(data.get("top_k", 5))
    if not query:
        return web.json_response({"error": "missing_parameter", "message": "'query' is required"}, status=400)

    query_vec = await embedder.embed_query(query)
    matches = vector_store.search(query_embedding=query_vec, top_k=top_k)
    return web.json_response({"query": query, "results": matches})


# In-memory cache for analyzed browser interests to prevent redundant LLM invocations
_interests_cache = {
    "hash": "",
    "data": None,
    "timestamp": 0.0
}

_yt_video_cache: dict[str, dict] = {}

# Authoritative channel boosts for technical subjects
AUTHORITATIVE_CHANNELS = [
    "Andrej Karpathy", "freeCodeCamp.org", "3Blue1Brown", "StatQuest with Josh Starmer",
    "Jon Gjengset", "MIT OpenCourseWare", "Stanford Online", "Computerphile",
    "Fireship", "The Cherno", "Traversy Media", "Tech With Tim", "Sentdex",
    "GOTO Conferences", "Corey Schafer", "ArjanCodes", "mCoding", "AssemblyAI"
]

async def resolve_youtube_video(query: str, default_title: str = "", default_channel: str = "YouTube Creator", default_duration: str = "30 min") -> dict:
    """
    Resolves authoritative, high-quality YouTube videos for learning roadmaps.
    Uses Gemini API with search grounding if configured, otherwise uses channel-weighted resolver.
    """
    clean_q = query.strip()
    if not clean_q:
        return {
            "video_id": "",
            "title": default_title or "YouTube Video",
            "channel": default_channel,
            "duration": default_duration,
            "url": "https://www.youtube.com"
        }

    if clean_q in _yt_video_cache:
        return _yt_video_cache[clean_q]

    # 1. Cloud Search Recommendation (if Gemini API key is available)
    if settings.cloud_enabled and settings.gemini_api_key:
        try:
            cloud_prompt = (
                f"Identify the single highest quality, most authoritative YouTube educational video for: '{clean_q}'.\n"
                f"Prefer top recognized educators (e.g. Andrej Karpathy, 3Blue1Brown, freeCodeCamp, MIT OCW, Jon Gjengset, Fireship).\n"
                f"Return ONLY a JSON object: {{\"title\": \"...\", \"channel\": \"...\", \"video_id\": \"...\", \"duration\": \"...\"}}"
            )
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
                payload = {"contents": [{"parts": [{"text": cloud_prompt}]}]}
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        text = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if "{" in text and "}" in text:
                            parsed = json.loads(text[text.find("{"):text.rfind("}") + 1])
                            vid_id = parsed.get("video_id", "").strip()
                            if vid_id and len(vid_id) == 11:
                                res = {
                                    "video_id": vid_id,
                                    "title": parsed.get("title", default_title or clean_q),
                                    "channel": parsed.get("channel", default_channel),
                                    "duration": parsed.get("duration", default_duration),
                                    "url": f"https://www.youtube.com/watch?v={vid_id}"
                                }
                                _yt_video_cache[clean_q] = res
                                return res
        except Exception as e:
            logger.debug("Cloud video resolver notice: %s", e)

    # 2. Local Channel-Weighted YouTube Resolver
    url = f"https://www.youtube.com/results?search_query={quote_plus(clean_q)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', html)
                    candidates = []
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            sections = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                            for sec in sections:
                                items = sec.get("itemSectionRenderer", {}).get("contents", [])
                                for it in items:
                                    if "videoRenderer" in it:
                                        vr = it["videoRenderer"]
                                        vid_id = vr.get("videoId")
                                        title_runs = vr.get("title", {}).get("runs", [])
                                        v_title = "".join(r.get("text", "") for r in title_runs)
                                        owner_runs = vr.get("ownerText", {}).get("runs", [])
                                        v_channel = "".join(r.get("text", "") for r in owner_runs)
                                        v_duration = vr.get("lengthText", {}).get("simpleText", default_duration)
                                        if vid_id and v_title:
                                            # Channel authority boost score
                                            is_auth = any(ac.lower() in v_channel.lower() for ac in AUTHORITATIVE_CHANNELS)
                                            candidates.append({
                                                "video_id": vid_id,
                                                "title": v_title,
                                                "channel": v_channel or default_channel,
                                                "duration": v_duration,
                                                "url": f"https://www.youtube.com/watch?v={vid_id}",
                                                "score": 10 if is_auth else 1
                                            })
                        except Exception:
                            pass

                    if candidates:
                        best = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]
                        _yt_video_cache[clean_q] = best
                        return best

                    v_matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                    if v_matches:
                        top_id = v_matches[0]
                        res = {
                            "video_id": top_id,
                            "title": default_title or clean_q,
                            "channel": default_channel,
                            "duration": default_duration,
                            "url": f"https://www.youtube.com/watch?v={top_id}"
                        }
                        _yt_video_cache[clean_q] = res
                        return res
    except Exception as e:
        logger.debug("YouTube resolver notice for '%s': %s", clean_q, e)

    fallback_res = {
        "video_id": "",
        "title": default_title or clean_q,
        "channel": default_channel,
        "duration": default_duration,
        "url": f"https://www.youtube.com/results?search_query={quote_plus(clean_q)}"
    }
    return fallback_res


async def handle_clear_knowledge(request: web.Request) -> web.Response:
    """DELETE /api/v1/knowledge/clear — Wipe all nodes, edges, and evidence."""
    global _interests_cache
    knowledge_graph.clear_all()
    _interests_cache = {"hash": "", "data": None, "timestamp": 0.0}
    return web.json_response({"status": "success", "message": "Knowledge graph database completely cleared"})


async def handle_get_interests(request: web.Request) -> web.Response:
    """
    GET /api/v1/knowledge/interests
    Dynamically categorizes browser sensor activity (searches, YouTube videos, pages)
    using SmolLM (or active AI model) into learning topics, evaluates user standing,
    and generates adaptive video learning roadmaps with ZERO hardcoded topic lists.
    """
    global _interests_cache

    browser_events_count = 0
    searches = []
    youtube_videos = []
    visited_pages = []

    # 1. Fetch aggregated browser activity from Member 4 Core Engine
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://127.0.0.1:9700/api/v1/browser/activity",
                timeout=aiohttp.ClientTimeout(total=2.5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    b_data = data.get("data", {})
                    browser_events_count = b_data.get("total_browser_events", 0)
                    for s in b_data.get("recent_searches", []):
                        if s.get("query") and not any(x["query"].lower() == s["query"].lower() for x in searches):
                            searches.append({"query": s["query"], "engine": s.get("engine", "Search"), "timestamp": s.get("timestamp")})
                    for y in b_data.get("youtube_videos", []):
                        if y.get("url") and not any(x["url"] == y["url"] for x in youtube_videos):
                            youtube_videos.append({
                                "title": y.get("title", "YouTube Video").replace(" - YouTube", "").strip(),
                                "url": y.get("url"),
                                "channel": y.get("channel", "YouTube"),
                                "watch_time_s": int(y.get("watch_time_s") or y.get("duration_s") or 60),
                                "timestamp": y.get("timestamp")
                            })
    except Exception as e:
        logger.debug("Browser activity fetch notice: %s", e)

    # If no searches or videos found from aggregator, query raw recent events as fallback
    if not searches and not youtube_videos:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://127.0.0.1:9700/api/v1/events/recent?source=browser&limit=300",
                    timeout=aiohttp.ClientTimeout(total=2.5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_evs = data.get("events", [])
                        browser_events_count = max(browser_events_count, len(raw_evs))
                        for ev in raw_evs:
                            etype = ev.get("event_type", "")
                            payload = ev.get("payload") or {}
                            if etype == "search_performed":
                                q = (payload.get("query") or "").strip()
                                if q and not any(s["query"].lower() == q.lower() for s in searches):
                                    searches.append({"query": q, "engine": payload.get("engine", "Search"), "timestamp": ev.get("timestamp")})
                            elif etype == "youtube_watching":
                                v_title = (payload.get("video_title") or payload.get("title") or "").replace(" - YouTube", "").strip()
                                v_url = payload.get("video_url") or payload.get("url") or ""
                                if v_title and not any(y["url"] == v_url for y in youtube_videos):
                                    youtube_videos.append({
                                        "title": v_title,
                                        "url": v_url,
                                        "channel": payload.get("channel") or "YouTube",
                                        "watch_time_s": int(payload.get("watch_time_s") or payload.get("duration_s") or 60),
                                        "timestamp": ev.get("timestamp")
                                    })
        except Exception:
            pass

    if not searches and not youtube_videos:
        return web.json_response({
            "status": "success",
            "total_interests": 0,
            "interests": [],
            "total_browser_events": browser_events_count
        })

    # Generate cache key based on raw telemetry signature
    raw_signature = f"{len(searches)}:{[s['query'] for s in searches]}:{len(youtube_videos)}:{[y['title'] for y in youtube_videos]}"
    sig_hash = hashlib.md5(raw_signature.encode()).hexdigest()

    # Check cache (valid for 15 minutes if signature matches to prevent continuous AI re-runs)
    if _interests_cache["data"] and _interests_cache["hash"] == sig_hash and (time.time() - _interests_cache["timestamp"] < 900.0):
        return web.json_response(_interests_cache["data"])

    # 2. Build AI prompt for SmolLM to analyze and categorize learning topics
    history_summary = []
    if searches:
        history_summary.append("Searches performed by user:\n" + "\n".join(f"- {s['query']} (via {s['engine']})" for s in searches[:8]))
    if youtube_videos:
        history_summary.append("Educational YouTube videos watched:\n" + "\n".join(f"- {y['title']} (Channel: {y['channel']}, Watched: {round(y['watch_time_s']/60, 1)}m)" for y in youtube_videos[:6]))
    if visited_pages:
        history_summary.append("Technical documentation/pages visited:\n" + "\n".join(f"- {p['title']}" for p in visited_pages[:6]))

    full_history_text = "\n\n".join(history_summary)

    prompt = (
        f"You are an expert AI curriculum and learning analyst in Tesseract.\n"
        f"Analyze this raw user browsing and research telemetry:\n\n"
        f"{full_history_text}\n\n"
        f"Identify what technical skills, languages, or conceptual topics the user is actively trying to learn.\n"
        f"For EACH distinct topic discovered:\n"
        f"1. 'id': url-safe slug (e.g. 'rust-programming', 'transformer-neural-networks')\n"
        f"2. 'title': clear subject name (e.g. 'Rust Programming', 'Transformer & Neural Networks')\n"
        f"3. 'icon': relevant single emoji\n"
        f"4. 'standing': 'Beginner', 'Intermediate', or 'Advanced' evaluated from their search depth and video watch time\n"
        f"5. 'standing_score': integer percentage 25-95\n"
        f"6. 'standing_badge': '🔴 Beginner', '🟡 Intermediate', or '🟢 Advanced'\n"
        f"7. 'standing_color': '#f43f5e', '#f59e0b', or '#10b981'\n"
        f"8. 'next_milestone': concise actionable single sentence advice\n"
        f"9. 'roadmap': list of 3 progressive milestone videos (Phase 1 Beginner, Phase 2 Intermediate, Phase 3 Advanced) with 'title', 'channel', 'duration', 'level'\n\n"
        f"Respond ONLY with valid JSON in this exact structure:\n"
        f"{{\n"
        f"  \"interests\": [\n"
        f"    {{\n"
        f"      \"id\": \"...\",\n"
        f"      \"title\": \"...\",\n"
        f"      \"icon\": \"...\",\n"
        f"      \"standing\": \"...\",\n"
        f"      \"standing_score\": 60,\n"
        f"      \"standing_badge\": \"...\",\n"
        f"      \"standing_color\": \"...\",\n"
        f"      \"next_milestone\": \"...\",\n"
        f"      \"roadmap\": [\n"
        f"        {{\"title\": \"...\", \"channel\": \"...\", \"duration\": \"...\", \"level\": \"...\"}}\n"
        f"      ]\n"
        f"    }}\n"
        f"  ]\n"
        f"}}"
    )

    parsed_interests = []
    try:
        # Call SmolLM (or active model) with 5.0s timeout
        res = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="classify", max_tokens=400, temperature=0.1),
            timeout=5.0
        )
        raw = res.content.strip()
        if "{" in raw and "}" in raw:
            json_str = raw[raw.find("{"):raw.rfind("}") + 1]
            parsed_data = json.loads(json_str)
            if isinstance(parsed_data.get("interests"), list):
                parsed_interests = parsed_data["interests"]
    except Exception as e:
        logger.info("AI dynamic categorization notice: %s. Using dynamic pattern analyzer.", e)

    # If AI returned valid list, enrich with real telemetry metrics and URL links
    final_interests = []

    if parsed_interests:
        for item in parsed_interests:
            t_title = item.get("title") or "Technical Topic"
            t_id = item.get("id") or re.sub(r'[^a-z0-9]+', '-', t_title.lower()).strip('-')
            
            # Match related searches and videos from history
            rel_searches = [s["query"] for s in searches if any(w in s["query"].lower() for w in t_title.lower().split() if len(w) > 2)]
            if not rel_searches and searches:
                rel_searches = [s["query"] for s in searches[:2]]

            rel_videos = [y for y in youtube_videos if any(w in y["title"].lower() for w in t_title.lower().split() if len(w) > 2)]
            if not rel_videos and youtube_videos:
                rel_videos = [youtube_videos[0]]

            total_watch_min = round(sum(y.get("watch_time_s", 0) for y in rel_videos) / 60, 1)

            # Build enriched roadmap with real direct YouTube video links
            enriched_roadmap = []
            for rm in item.get("roadmap", []):
                rm_title = rm.get("title") or f"{t_title} Tutorial"
                rm_level = rm.get("level") or "Beginner"
                rm_url = ""
                rm_channel = rm.get("channel") or "YouTube"
                rm_duration = rm.get("duration") or "30 min"
                
                # Check if matches any video directly in history
                for y in rel_videos:
                    if y["title"].lower() in rm_title.lower() or rm_title.lower() in y["title"].lower():
                        rm_url = y["url"]
                        rm_title = y["title"]
                        rm_channel = y["channel"]
                        break

                if not rm_url:
                    yt_info = await resolve_youtube_video(f"{t_title} {rm_title} tutorial", default_title=rm_title, default_channel=rm_channel)
                    rm_url = yt_info["url"]
                    if yt_info.get("channel"):
                        rm_channel = yt_info["channel"]
                    if yt_info.get("duration"):
                        rm_duration = yt_info["duration"]

                # Milestone completion requires verified watch time (1 min does not complete stage)
                is_completed = (rm_level == "Beginner" and total_watch_min >= 20.0) or \
                               (rm_level == "Intermediate" and total_watch_min >= 60.0) or \
                               (rm_level == "Advanced" and total_watch_min >= 120.0)

                enriched_roadmap.append({
                    "title": rm_title,
                    "channel": rm_channel,
                    "duration": rm_duration,
                    "level": rm_level,
                    "url": rm_url,
                    "completed": is_completed
                })

            final_interests.append({
                "id": t_id,
                "title": t_title,
                "icon": item.get("icon") or "💡",
                "standing": item.get("standing") or "Beginner",
                "standing_score": int(item.get("standing_score") or 40),
                "standing_badge": item.get("standing_badge") or "🔴 Beginner",
                "standing_color": item.get("standing_color") or "#f43f5e",
                "next_milestone": item.get("next_milestone") or f"Deepen foundations in {t_title}",
                "stats": {
                    "searches_count": len(rel_searches),
                    "videos_watched": len(rel_videos),
                    "watch_time_minutes": total_watch_min,
                    "total_events": len(rel_searches) + len(rel_videos),
                    "last_active": rel_videos[0]["timestamp"] if rel_videos else (rel_searches[0] if rel_searches else "")
                },
                "recent_searches": rel_searches[:5],
                "recent_videos": rel_videos[:4],
                "roadmap": enriched_roadmap
            })

    # Dynamic Topic Aggregator: cluster telemetry by primary subject keywords dynamically
    if not final_interests:
        stopwords = {
            "tutorial", "explained", "how", "to", "in", "what", "is", "for", "with", "and", "the", "a", "an", "of",
            "complete", "course", "full", "from", "scratch", "guide", "learn", "learning", "crash", "vs", "overview",
            "beginner", "beginners", "basics", "fundamentals", "introduction", "intro", "deep", "dive", "video", "youtube"
        }

        # Cluster storage: key -> { "title": str, "searches": set, "videos": list, "pages": list }
        clusters = {}

        def get_topic_key(text: str) -> str:
            clean = re.sub(r'[^\w\s+#.-]', ' ', text.lower())
            tokens = [t for t in clean.split() if t and t not in stopwords and len(t) > 1]
            if not tokens:
                return text[:20].strip().title()
            
            primary = tokens[0]
            for existing_key in list(clusters.keys()):
                if primary in existing_key.lower().split() or existing_key.lower() in clean:
                    return existing_key
            
            if len(tokens) >= 2:
                first = tokens[0].title()
                second = tokens[1].title()
                if second.lower() in ("low", "crust", "borrow", "new", "simple", "easy", "latency", "checker"):
                    nouns = [t.title() for t in tokens[1:] if t.lower() not in ("low", "crust", "borrow", "new", "simple", "easy", "latency", "checker")]
                    second = nouns[0] if nouns else "Engineering"
                return f"{first} {second}"
            return f"{tokens[0].title()} Concepts"

        # Group searches
        for s in searches:
            q = s["query"]
            t_key = get_topic_key(q)
            if t_key not in clusters:
                clusters[t_key] = {"title": t_key, "searches": [], "videos": [], "pages": []}
            if q not in clusters[t_key]["searches"]:
                clusters[t_key]["searches"].append(q)

        # Group YouTube videos
        for y in youtube_videos:
            title = y["title"]
            t_key = get_topic_key(title)
            if t_key not in clusters:
                clusters[t_key] = {"title": t_key, "searches": [], "videos": [], "pages": []}
            if not any(v.get("url") == y.get("url") for v in clusters[t_key]["videos"]):
                clusters[t_key]["videos"].append(y)

        # Group visited pages
        for p in visited_pages:
            title = p["title"]
            t_key = get_topic_key(title)
            if t_key in clusters:
                clusters[t_key]["pages"].append(p)

        for t_name, cluster in clusters.items():
            slug = re.sub(r'[^a-z0-9]+', '-', t_name.lower()).strip('-')
            w_time_total = sum(v.get("watch_time_s", 0) for v in cluster["videos"])
            w_min = round(w_time_total / 60, 1)
            search_cnt = len(cluster["searches"])
            vid_cnt = len(cluster["videos"])

            # Evaluate standing dynamically
            if w_min >= 30 or (search_cnt >= 3 and w_min >= 10):
                standing, score, badge, color = "Advanced", min(85 + int(w_min // 10), 96), "🟢 Advanced", "#10b981"
                next_mile = f"Master advanced concurrent architectures and production patterns in {t_name}"
            elif w_min >= 8 or search_cnt >= 2:
                standing, score, badge, color = "Intermediate", min(55 + int(w_min // 2), 78), "🟡 Intermediate", "#f59e0b"
                next_mile = f"Build idiomatic projects and deep-dive into internal mechanics of {t_name}"
            else:
                standing, score, badge, color = "Beginner", max(25, 30 + search_cnt * 5), "🔴 Beginner", "#f43f5e"
                next_mile = f"Complete foundational syntax and core concept exercises in {t_name}"

            # Dynamic icon detection
            t_lower = t_name.lower()
            if "rust" in t_lower:
                icon = "🦀"
            elif any(k in t_lower for k in ("transformer", "pytorch", "neural", "deep learning", "ai", "llm")):
                icon = "🤖"
            elif any(k in t_lower for k in ("python", "django", "flask", "fastapi")):
                icon = "🐍"
            elif any(k in t_lower for k in ("javascript", "typescript", "react", "vue", "node")):
                icon = "⚡"
            elif any(k in t_lower for k in ("docker", "k8s", "kubernetes", "cloud", "aws")):
                icon = "☁️"
            elif any(k in t_lower for k in ("database", "sql", "postgres", "redis")):
                icon = "🗄️"
            elif any(k in t_lower for k in ("linux", "kernel", "systems", "c++", "c ")):
                icon = "⚙️"
            else:
                icon = "💡"

            # Formulate 3-stage progressive roadmap with direct YouTube video links
            matched_vids = cluster["videos"]
            if matched_vids:
                b_url = matched_vids[0]["url"]
                b_title = matched_vids[0]["title"]
                b_chan = matched_vids[0]["channel"]
                b_dur = f"{matched_vids[0].get('duration_s', 1800)//60}m" if matched_vids[0].get('duration_s') else "30 min"
            else:
                yt1 = await resolve_youtube_video(f"{t_name} beginners tutorial crash course", default_title=f"Introduction & Fundamentals of {t_name}")
                b_url = yt1["url"]
                b_title = yt1["title"]
                b_chan = yt1["channel"]
                b_dur = yt1.get("duration") or "30 min"

            if len(matched_vids) > 1:
                i_url = matched_vids[1]["url"]
                i_title = matched_vids[1]["title"]
                i_chan = matched_vids[1]["channel"]
                i_dur = f"{matched_vids[1].get('duration_s', 2400)//60}m" if matched_vids[1].get('duration_s') else "45 min"
            else:
                yt2 = await resolve_youtube_video(f"{t_name} core patterns practical deep dive tutorial", default_title=f"{t_name} Core Patterns & Practical Implementation")
                i_url = yt2["url"]
                i_title = yt2["title"]
                i_chan = yt2["channel"]
                i_dur = yt2.get("duration") or "45 min"

            yt3 = await resolve_youtube_video(f"Advanced {t_name} architecture production systems masterclass", default_title=f"Advanced {t_name} Architecture & Real-World Systems")
            a_url = yt3["url"]
            a_title = yt3["title"]
            a_chan = yt3["channel"]
            a_dur = yt3.get("duration") or "1h 30m"

            final_interests.append({
                "id": slug or "tech-topic",
                "title": t_name,
                "icon": icon,
                "standing": standing,
                "standing_score": score,
                "standing_badge": badge,
                "standing_color": color,
                "next_milestone": next_mile,
                "stats": {
                    "searches_count": search_cnt,
                    "videos_watched": vid_cnt,
                    "watch_time_minutes": w_min,
                    "total_events": search_cnt + vid_cnt + len(cluster["pages"]),
                    "last_active": matched_vids[0]["timestamp"] if matched_vids else (cluster["searches"][0] if cluster["searches"] else "")
                },
                "recent_searches": cluster["searches"][:6],
                "recent_videos": cluster["videos"][:4],
                "roadmap": [
                    {
                        "title": b_title,
                        "channel": b_chan,
                        "duration": b_dur,
                        "level": "Beginner",
                        "url": b_url,
                        "completed": (w_min >= 20.0)
                    },
                    {
                        "title": i_title,
                        "channel": i_chan,
                        "duration": i_dur,
                        "level": "Intermediate",
                        "url": i_url,
                        "completed": (w_min >= 60.0)
                    },
                    {
                        "title": a_title,
                        "channel": a_chan,
                        "duration": a_dur,
                        "level": "Advanced",
                        "url": a_url,
                        "completed": (w_min >= 120.0)
                    }
                ]
            })

    # Sort interests by standing and engagement
    final_interests.sort(key=lambda x: (x["standing_score"], x["stats"]["total_events"]), reverse=True)

    result_payload = {
        "status": "success",
        "total_interests": len(final_interests),
        "interests": final_interests,
        "total_browser_events": browser_events_count
    }

    _interests_cache = {
        "hash": sig_hash,
        "data": result_payload,
        "timestamp": time.time()
    }

    return web.json_response(result_payload)


def setup_knowledge_routes(app: web.Application):
    app.router.add_post("/api/v1/knowledge/update", handle_update_knowledge)
    app.router.add_get("/api/v1/knowledge/graph", handle_get_graph)
    app.router.add_delete("/api/v1/knowledge/clear", handle_clear_knowledge)
    app.router.add_get("/api/v1/knowledge/interests", handle_get_interests)
    app.router.add_get("/api/v1/knowledge/skill/{id}", handle_get_skill)
    app.router.add_get("/api/v1/knowledge/gaps", handle_get_gaps)
    app.router.add_post("/api/v1/knowledge/query", handle_query_knowledge)


