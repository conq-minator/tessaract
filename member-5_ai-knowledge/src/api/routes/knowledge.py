import os
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
    "GOTO Conferences", "Corey Schafer", "ArjanCodes", "mCoding", "AssemblyAI",
    "Bro Code", "SuperSimpleDev", "NeetCode", "Hussein Nasser", "Derek Banas", "Programming with Mosh"
]

def get_active_gemini_key() -> str:
    """Resolve active Gemini API key from settings or environment dynamically."""
    key = settings.gemini_api_key or os.getenv("TESSERACT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    if not key:
        from src.config import resolve_gemini_api_key
        key = resolve_gemini_api_key()
    return key.strip()


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
    gemini_key = get_active_gemini_key()
    if gemini_key:
        try:
            cloud_prompt = (
                f"Identify the single highest quality, most authoritative YouTube educational video for: '{clean_q}'.\n"
                f"Prefer top recognized educators (e.g. Andrej Karpathy, 3Blue1Brown, freeCodeCamp, MIT OCW, Jon Gjengset, Fireship, Bro Code).\n"
                f"Return ONLY a JSON object: {{\"title\": \"...\", \"channel\": \"...\", \"video_id\": \"...\", \"duration\": \"...\"}}"
            )
            for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    async with aiohttp.ClientSession() as session:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
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
                except Exception:
                    continue
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


# ---------------------------------------------------------------------------
# Topic relevance filters & Technical taxonomy
# ---------------------------------------------------------------------------
STUDY_NEGATIVE_PATTERNS = [
    # Gaming & esports
    r'\bgta\b', r'\bgta6\b', r'\bgta\s*vi\b', r'\bgta\s*5\b', r'\bgta\s*v\b',
    r'\bpokemon\b', r'\bpokémon\b', r'\bmoba\b', r'\bfortnite\b', r'\bminecraft\b',
    r'\broblox\b', r'\bvalorant\b', r'\bleague of legends\b', r'\bdota\b',
    r'\bcsgo\b', r'\bcounter[- ]strike\b', r'\bapex legends\b', r'\bcall of duty\b',
    r'\bwarzone\b', r'\bgenshin\b', r'\bzelda\b', r'\bplaystation\b', r'\bxbox\b',
    r'\bnintendo\b', r'\bgameplay\b', r'\bspeedrun\b', r'\bboss fight\b',
    r'\bmodded\b', r'\bpvp\b', r'\btier list\b', r'\bunboxing\b',
    r'\bchou\b', r'\bleaks?\b', r'\bgamer\b', r'\bgaming\b',
    # Entertainment, music & lifestyle
    r'\bofficial video\b', r'\bofficial audio\b', r'\blyric video\b', r'\bsong\b',
    r'\bepisode\s*\d+\b', r'\bseason\s*\d+\b', r'\bnetflix\b', r'\btrailer\b',
    r'\bworkout\b', r'\bfitness\b', r'\bcooking\b', r'\brecipe\b', r'\bfashion\b',
    r'\bshopping\b', r'\bmakeup\b', r'\bvlog\b', r'\bprank\b', r'\bcomedy\b'
]

TECH_TAXONOMY = [
    (r'\b(?:c|c\s+lang|c\s+programming|learn\s+c|c\s+full\s+course)\b(?!\s*\+\+|\s*#)', 'C Programming', 'c-programming', 'C'),
    (r'\b(?:c\+\+|cpp)\b', 'C++ Programming', 'cpp-programming', 'CPP'),
    (r'\b(?:c#|csharp|\.net)\b', 'C# & .NET', 'csharp-dotnet', 'NET'),
    (r'\b(?:rust|cargo|rustlang)\b', 'Rust Systems Programming', 'rust-systems', 'RUST'),
    (r'\b(?:python|py|django|flask|fastapi)\b', 'Python Development', 'python-dev', 'PY'),
    (r'\b(?:javascript|js|node|nodejs|express|ecmascript)\b', 'JavaScript Development', 'javascript-dev', 'JS'),
    (r'\b(?:typescript|ts)\b', 'TypeScript Development', 'typescript-dev', 'TS'),
    (r'\b(?:go|golang)\b', 'Go Programming', 'go-programming', 'GO'),
    (r'\b(?:java|spring|springboot)\b(?!\s*script)', 'Java Development', 'java-dev', 'JAVA'),
    (r'\b(?:kotlin|android)\b', 'Kotlin & Android', 'kotlin-android', 'KT'),
    (r'\b(?:swift|swiftui|ios)\b', 'Swift & iOS', 'swift-ios', 'SWIFT'),
    (r'\b(?:html|css|tailwind|web\s+design|frontend)\b', 'Web Frontend Development', 'frontend-web', 'WEB'),
    (r'\b(?:react|reactjs|nextjs|next\.js)\b', 'React & Next.js', 'react-nextjs', 'REACT'),
    (r'\b(?:vue|vuejs|nuxt)\b', 'Vue.js Framework', 'vue-framework', 'VUE'),
    (r'\b(?:pytorch|torch)\b', 'PyTorch & Deep Learning', 'pytorch-deep-learning', 'TORCH'),
    (r'\b(?:tensorflow|keras)\b', 'TensorFlow & Deep Learning', 'tensorflow-ml', 'TF'),
    (r'\b(?:transformer|attention mechanism|llm|llms|gpt|nlp)\b', 'Transformer & LLM Architectures', 'transformer-llms', 'LLM'),
    (r'\b(?:machine\s+learning|deep\s+learning|ai|neural\s+network)\b', 'AI & Machine Learning', 'ai-machine-learning', 'AI'),
    (r'\b(?:embedded|microcontroller|arduino|raspberry\s*pi|firmware|rtos)\b', 'Embedded Systems', 'embedded-systems', 'EMBED'),
    (r'\b(?:docker|kubernetes|k8s|devops|ci/cd|containers?)\b', 'Docker & Kubernetes DevOps', 'devops-containers', 'OPS'),
    (r'\b(?:database|sql|postgres|postgresql|mysql|sqlite|redis|mongodb)\b', 'Database Engineering & SQL', 'databases-sql', 'SQL'),
    (r'\b(?:system\s+design|microservices|distributed\s+systems|software\s+architecture)\b', 'System Design & Architecture', 'system-design', 'ARCH'),
    (r'\b(?:algorithms?|data\s+structures?|leetcode|dsa)\b', 'Algorithms & Data Structures', 'dsa-algorithms', 'DSA'),
    (r'\b(?:linux|kernel|unix|bash|shell)\b', 'Linux & Systems Engineering', 'linux-systems', 'LINUX'),
]

def is_study_related(text: str, channel: str = "") -> bool:
    clean_text = text.lower()
    clean_channel = channel.lower()

    # If it's a verified authoritative educator, consider study-related unless obvious gameplay/vlog
    if any(ac.lower() in clean_channel for ac in AUTHORITATIVE_CHANNELS):
        if not any(re.search(pat, clean_text) for pat in [r'\bgameplay\b', r'\bvlog\b', r'\bcooking\b']):
            return True

    # Filter out off-topic / non-study items (gaming, entertainment, etc.)
    for pat in STUDY_NEGATIVE_PATTERNS:
        if re.search(pat, clean_text):
            if not any(prog in clean_text for prog in ["programming", "coding", "code", "dev in", "developer", "engine in"]):
                return False

    # Check for direct tech taxonomy matches
    for pat, _, _, _ in TECH_TAXONOMY:
        if re.search(pat, clean_text):
            return True

    # Check for general tech/study terminology
    general_tech = [
        r'\bcode\b', r'\bcoding\b', r'\bprogramming\b', r'\bsoftware\b',
        r'\bdeveloper\b', r'\bdevelopment\b', r'\bcomputer science\b',
        r'\bcompiler\b', r'\bdebugging\b', r'\bapi\b', r'\brest api\b',
        r'\bdata science\b', r'\banalytics\b', r'\bcybersecurity\b',
        r'\bnetworking\b', r'\bprotocols?\b', r'\bmath\b', r'\bcalculus\b',
        r'\bstatistics\b', r'\bphysics\b'
    ]
    return any(re.search(pat, clean_text) for pat in general_tech)

def resolve_topic_info(text: str) -> dict:
    clean = text.lower()
    for pat, title, slug, icon in TECH_TAXONOMY:
        if re.search(pat, clean):
            return {"title": title, "slug": slug, "icon": icon}
    
    stopwords = {
        "tutorial", "explained", "how", "to", "in", "what", "is", "for", "with", "and", "the", "a", "an", "of",
        "complete", "course", "full", "from", "scratch", "guide", "learn", "learning", "crash", "vs", "overview",
        "beginner", "beginners", "basics", "fundamentals", "introduction", "intro", "deep", "dive", "video", "youtube",
        "free", "let", "lets", "build", "step", "online", "playlist", "2024", "2025", "2026", "new", "best", "simple",
        "easy", "concepts", "need", "know", "pro", "mastery", "gear", "part", "chapter", "code", "coding"
    }
    cleaned = re.sub(r'[^\w\s+#.-]', ' ', clean)
    tokens = [t for t in cleaned.split() if t and t not in stopwords and (len(t) > 1 or t in {'c', 'r'})]
    if not tokens:
        return {"title": text[:25].strip().title(), "slug": "tech-study", "icon": "DEV"}
    
    if len(tokens) == 1:
        t0 = tokens[0].title()
        if t0.lower() == 'c':
            return {"title": "C Programming", "slug": "c-programming", "icon": "C"}
        return {"title": f"{t0} Technology", "slug": tokens[0].lower(), "icon": t0[:4].upper()}
    
    first = tokens[0].title()
    second = tokens[1].title()
    slug = f"{tokens[0]}-{tokens[1]}".lower()
    tag = f"{first[:2]}{second[:2]}".upper()
    return {"title": f"{first} {second}", "slug": slug, "icon": tag}


# ---------------------------------------------------------------------------
# Comprehensive Multi-Phase Learning Curricula & Cloud Generators
# ---------------------------------------------------------------------------

COMPREHENSIVE_CURRICULA = {
    "c-programming": [
        {
            "phase": 1,
            "title": "Phase 1: C Fundamentals, Compilers & Primitive Types",
            "description": "Set up GCC/Clang tooling, understand compilation stages (preprocess, compile, assemble, link), variables, primitive data types, control structures, and loops.",
            "level": "Beginner",
            "duration": "4h 00m",
            "video_query": "c programming full course bro code",
            "default_title": "C Programming Full Course for free ⚙️",
            "default_channel": "Bro Code"
        },
        {
            "phase": 2,
            "title": "Phase 2: Modular Architecture, Functions, Scope & Structs",
            "description": "Function prototypes, call stack frames, pass-by-value vs pointer referencing, header guards, multi-file builds with Makefiles, and custom structs.",
            "level": "Beginner",
            "duration": "1h 30m",
            "video_query": "c programming tutorial functions structs headers modular code freecodecamp",
            "default_title": "C Programming Tutorial - Functions & Structs",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 3,
            "title": "Phase 3: Pointers, Memory Layout & Dynamic Allocation",
            "description": "Deep-dive into virtual memory, pointer arithmetic, stack vs heap allocation, malloc/calloc/realloc/free, memory leaks, and Valgrind debugging.",
            "level": "Intermediate",
            "duration": "2h 15m",
            "video_query": "c pointers explained dynamic memory allocation malloc free valgrind freecodecamp",
            "default_title": "Pointers in C / C++ [Full Course]",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 4,
            "title": "Phase 4: Data Structures & Algorithms in Pure C",
            "description": "Implement essential data structures from scratch: dynamic arrays, singly & doubly linked lists, hash tables with collision handling, and binary trees.",
            "level": "Intermediate",
            "duration": "2h 45m",
            "video_query": "data structures in c linked list hash table tree implementation freecodecamp",
            "default_title": "Data Structures in C - Full Course",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 5,
            "title": "Phase 5: Low-Level POSIX Systems Programming & File I/O",
            "description": "POSIX system calls (open, read, write, close), file descriptors, process lifecycle (fork, exec, wait), signal handling, pipes, and inter-process communication.",
            "level": "Advanced",
            "duration": "1h 45m",
            "video_query": "c systems programming posix system calls fork file descriptors low level learning",
            "default_title": "Linux Systems Programming in C",
            "default_channel": "Low Level Learning"
        },
        {
            "phase": 6,
            "title": "Phase 6: Concurrency, Performance Profiling & Production Architecture",
            "description": "POSIX threads (pthreads), mutexes, condition variables, race conditions, atomic operations, cache spatial/temporal locality, and GDB/perf profiling.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "advanced c programming pthreads concurrency optimization",
            "default_title": "Advanced C Programming & Concurrency Masterclass",
            "default_channel": "GOTO Conferences"
        }
    ],
    "rust-systems": [
        {
            "phase": 1,
            "title": "Phase 1: Rust Toolchain, Cargo, Syntax & Immutability",
            "description": "Install Rustup, rustc, and Cargo. Master variable shadowing, type inference, control flow, functions, and expression-oriented syntax.",
            "level": "Beginner",
            "duration": "2h 30m",
            "video_query": "rust programming course for beginners freecodecamp",
            "default_title": "Rust Programming Course for Beginners",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 2,
            "title": "Phase 2: Ownership, Borrowing Rules & References",
            "description": "Master Rust's memory safety without garbage collection: move semantics, immutable vs mutable borrowing rules, and slice references.",
            "level": "Beginner",
            "duration": "1h 45m",
            "video_query": "rust ownership and borrowing explained let's get rusty",
            "default_title": "Rust Ownership and Borrowing Explained",
            "default_channel": "Let's Get Rusty"
        },
        {
            "phase": 3,
            "title": "Phase 3: Structs, Enums, Pattern Matching & Traits",
            "description": "Model data with structs and algebraic data types (Option, Result). Implement traits, generics, and exhaustive match pattern semantics.",
            "level": "Intermediate",
            "duration": "2h 00m",
            "video_query": "rust traits generics enums error handling tutorial",
            "default_title": "Rust Traits, Generics, and Error Handling",
            "default_channel": "Jon Gjengset"
        },
        {
            "phase": 4,
            "title": "Phase 4: Lifetimes, Smart Pointers & Interior Mutability",
            "description": "Demystify explicit lifetime annotations ('a), Box, Rc, Arc, RefCell, and Mutex for shared state and complex graph data structures.",
            "level": "Intermediate",
            "duration": "2h 30m",
            "video_query": "crust of rust lifetimes smart pointers jon gjengset",
            "default_title": "Crust of Rust: Lifetime Annotations & Smart Pointers",
            "default_channel": "Jon Gjengset"
        },
        {
            "phase": 5,
            "title": "Phase 5: Asynchronous Rust with Tokio & Async/Await",
            "description": "Build high-throughput network services with Tokio runtime, Futures, async streams, channels (mpsc/oneshot), and graceful shutdown patterns.",
            "level": "Advanced",
            "duration": "2h 15m",
            "video_query": "async rust tokio crash course tutorial",
            "default_title": "Async Rust with Tokio - Building Production Services",
            "default_channel": "Logan Smith"
        },
        {
            "phase": 6,
            "title": "Phase 6: Systems Architecture, FFI & Production Unsafe Rust",
            "description": "Understand the unsafe boundary, raw pointers, C foreign function interface (FFI), zero-cost abstractions, and writing hardened production systems.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "unsafe rust ffi systems architecture jon gjengset",
            "default_title": "Crust of Rust: Unsafe and FFI in Production",
            "default_channel": "Jon Gjengset"
        }
    ],
    "javascript-dev": [
        {
            "phase": 1,
            "title": "Phase 1: Modern JavaScript & ES6+ Fundamentals",
            "description": "Execution contexts, lexical scoping, closures, destructuring, rest/spread operators, modules, and modern JavaScript language semantics.",
            "level": "Beginner",
            "duration": "3h 00m",
            "video_query": "javascript full course bro code",
            "default_title": "JavaScript Full Course for free 🌐",
            "default_channel": "Bro Code"
        },
        {
            "phase": 2,
            "title": "Phase 2: Event Loop, Promises & Asynchronous JavaScript",
            "description": "Deep-dive into microtask vs macrotask queues, async/await, Promise combinators (all, allSettled, race), and handling network I/O gracefully.",
            "level": "Beginner",
            "duration": "1h 30m",
            "video_query": "javascript event loop visualised promises async await fireship",
            "default_title": "JavaScript Event Loop and Async Patterns",
            "default_channel": "Fireship"
        },
        {
            "phase": 3,
            "title": "Phase 3: DOM Manipulation, Web APIs & Browser Performance",
            "description": "Interact with the DOM tree, event delegation, custom events, IntersectionObserver, Web Storage, and rendering performance profiling.",
            "level": "Intermediate",
            "duration": "2h 00m",
            "video_query": "dom manipulation modern web apis supersimpledev",
            "default_title": "DOM Manipulation and Web APIs in Depth",
            "default_channel": "SuperSimpleDev"
        },
        {
            "phase": 4,
            "title": "Phase 4: Component Architecture & State Management (React/Next)",
            "description": "Modern component hierarchy, declarative rendering, hooks lifecycle (useState, useEffect, useMemo), and scalable state management.",
            "level": "Intermediate",
            "duration": "3h 00m",
            "video_query": "react course for beginners freecodecamp",
            "default_title": "React Course - Beginner to Advanced",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 5,
            "title": "Phase 5: Node.js Backend Engineering & RESTful APIs",
            "description": "Server-side JavaScript with Node.js and Express/Fastify. Build REST APIs, middleware pipelines, authentication (JWT/OAuth), and database schemas.",
            "level": "Advanced",
            "duration": "2h 30m",
            "video_query": "nodejs backend api tutorial express freecodecamp",
            "default_title": "Node.js and Express.js Full Course",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 6,
            "title": "Phase 6: Fullstack Architecture, Bundlers & Production Deployment",
            "description": "Vite/esbuild bundling, TypeScript integration, automated CI/CD pipelines, containerization with Docker, and SSR/SSG caching strategies.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "full stack web development architecture deployment fireship",
            "default_title": "Full Stack Architecture & Production Engineering",
            "default_channel": "Fireship"
        }
    ],
    "pytorch-deep-learning": [
        {
            "phase": 1,
            "title": "Phase 1: PyTorch Tensors, Autograd & GPU Acceleration",
            "description": "Tensor dimensions, broadcasting, device allocation (CPU/CUDA), dynamic computational graphs, and automatic differentiation with autograd.",
            "level": "Beginner",
            "duration": "2h 00m",
            "video_query": "pytorch tutorial tensors autograd beginner freecodecamp",
            "default_title": "PyTorch for Deep Learning Bootcamp",
            "default_channel": "freeCodeCamp.org"
        },
        {
            "phase": 2,
            "title": "Phase 2: Neural Network Modules & Forward Passes",
            "description": "Build custom architectures using torch.nn.Module, linear layers, convolutional filters, activation functions, and parameter initialization.",
            "level": "Beginner",
            "duration": "2h 30m",
            "video_query": "building neural networks in pytorch nn module tutorial",
            "default_title": "PyTorch Neural Networks Architecture",
            "default_channel": "Aladdin Persson"
        },
        {
            "phase": 3,
            "title": "Phase 3: Training Pipelines, Loss Functions & Optimizers",
            "description": "Implement robust training loops, validation evaluation, learning rate schedulers, custom Dataset and DataLoader pipelines with batching.",
            "level": "Intermediate",
            "duration": "2h 15m",
            "video_query": "pytorch training loop custom dataset dataloader aladdin persson",
            "default_title": "Custom Datasets and Training Pipelines in PyTorch",
            "default_channel": "Aladdin Persson"
        },
        {
            "phase": 4,
            "title": "Phase 4: Computer Vision & Convolutional Architectures",
            "description": "Implement image classification and feature extraction using ResNet, ConvNeXt, data augmentation (torchvision.transforms), and transfer learning.",
            "level": "Intermediate",
            "duration": "2h 45m",
            "video_query": "pytorch computer vision transfer learning resnet tutorial",
            "default_title": "PyTorch Computer Vision & Transfer Learning",
            "default_channel": "Daniel Bourke"
        },
        {
            "phase": 5,
            "title": "Phase 5: Sequence Modeling & Transformer Architectures",
            "description": "Embeddings, positional encodings, multi-head attention mechanisms, and building sequence-to-sequence neural architectures in PyTorch.",
            "level": "Advanced",
            "duration": "3h 00m",
            "video_query": "let's build gpt from scratch andrej karpathy pytorch",
            "default_title": "Let's build GPT: from scratch, in code, spelled out.",
            "default_channel": "Andrej Karpathy"
        },
        {
            "phase": 6,
            "title": "Phase 6: Distributed GPU Training & Production Model Serving",
            "description": "DistributedDataParallel (DDP), mixed-precision training (torch.cuda.amp), TorchScript JIT compilation, and ONNX runtime export for low-latency serving.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "pytorch distributed training ddp torchscript onnx export",
            "default_title": "PyTorch in Production: DDP and TorchScript Serving",
            "default_channel": "PyTorch"
        }
    ],
    "transformer-llms": [
        {
            "phase": 1,
            "title": "Phase 1: Attention Mechanisms & Mathematical Foundations",
            "description": "Scaled dot-product attention, query/key/value intuition, softmax temperature scaling, multi-head projections, and residual connections.",
            "level": "Beginner",
            "duration": "1h 45m",
            "video_query": "attention mechanism transformers visual 3blue1brown",
            "default_title": "Attention in transformers, visually explained",
            "default_channel": "3Blue1Brown"
        },
        {
            "phase": 2,
            "title": "Phase 2: Building GPT & Transformers from Scratch",
            "description": "Implement the complete decoder-only transformer architecture line-by-line: token embeddings, self-attention, layer normalization, and feedforward blocks.",
            "level": "Intermediate",
            "duration": "2h 15m",
            "video_query": "let's build gpt from scratch andrej karpathy",
            "default_title": "Let's build GPT: from scratch, in code, spelled out.",
            "default_channel": "Andrej Karpathy"
        },
        {
            "phase": 3,
            "title": "Phase 3: Tokenization & Pretraining Corpora",
            "description": "Byte-Pair Encoding (BPE), SentencePiece, dataset curation, causal language modeling loss, and pretraining a small language model on custom text.",
            "level": "Intermediate",
            "duration": "2h 00m",
            "video_query": "building a tokenizer from scratch bpe andrej karpathy",
            "default_title": "Let's build the GPT Tokenizer",
            "default_channel": "Andrej Karpathy"
        },
        {
            "phase": 4,
            "title": "Phase 4: Instruction Tuning & Parameter-Efficient Fine-Tuning (PEFT)",
            "description": "Supervised Fine-Tuning (SFT), Low-Rank Adaptation (LoRA), QLoRA 4-bit quantization, and formatting conversation datasets with chat templates.",
            "level": "Advanced",
            "duration": "2h 30m",
            "video_query": "lora qlora fine tuning llms tutorial huggingface",
            "default_title": "Fine-Tuning LLMs with LoRA and QLoRA",
            "default_channel": "Umar Jamil"
        },
        {
            "phase": 5,
            "title": "Phase 5: Retrieval-Augmented Generation (RAG) Architecture",
            "description": "Chunking strategies, dense embedding retrieval, vector indexing (HNSW), cross-encoder re-ranking, and context synthesis pipelines.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "advanced rag retrieval augmented generation architecture tutorial",
            "default_title": "Building Production RAG Systems",
            "default_channel": "AssemblyAI"
        },
        {
            "phase": 6,
            "title": "Phase 6: Production Inference Serving & Quantization (vLLM / GGUF)",
            "description": "KV-cache optimization, PagedAttention, speculative decoding, model quantization (AWQ/GPTQ/GGUF), and deploying low-latency LLM endpoints with vLLM.",
            "level": "Advanced",
            "duration": "1h 45m",
            "video_query": "vllm pagedattention high throughput llm serving tutorial",
            "default_title": "High-Throughput LLM Serving with vLLM and PagedAttention",
            "default_channel": "Mckay Wrigley"
        }
    ],
    "embedded-systems": [
        {
            "phase": 1,
            "title": "Phase 1: Microcontroller Architectures & Bare-Metal C",
            "description": "ARM Cortex-M architectures, memory maps, toolchains (arm-none-eabi-gcc), link scripts, and writing bare-metal firmware without an OS.",
            "level": "Beginner",
            "duration": "2h 30m",
            "video_query": "bare metal embedded c programming tutorial low level learning",
            "default_title": "Bare Metal Embedded C Programming",
            "default_channel": "Low Level Learning"
        },
        {
            "phase": 2,
            "title": "Phase 2: Registers, GPIOs & Memory-Mapped Hardware I/O",
            "description": "Direct register manipulation, bitwise operations, volatile keyword significance, and controlling hardware peripherals via memory-mapped I/O.",
            "level": "Beginner",
            "duration": "2h 00m",
            "video_query": "embedded systems gpio register manipulation stm32 tutorial",
            "default_title": "STM32 GPIO & Register Level Programming",
            "default_channel": "Controllers Tech"
        },
        {
            "phase": 3,
            "title": "Phase 3: Hardware Timers, Interrupts & PWM Signals",
            "description": "Nested Vectored Interrupt Controller (NVIC), Interrupt Service Routines (ISRs), hardware timer prescalers, and Pulse-Width Modulation (PWM).",
            "level": "Intermediate",
            "duration": "2h 15m",
            "video_query": "embedded interrupts timers pwm nvic explained tutorial",
            "default_title": "Interrupts and Timers in Embedded Systems",
            "default_channel": "Mutex Embedded"
        },
        {
            "phase": 4,
            "title": "Phase 4: Serial Communication Protocols (UART, SPI, I2C)",
            "description": "Implement UART, SPI, and I2C protocols. Master clock synchronization, baud rates, ACK/NACK signaling, and interfacing external sensors.",
            "level": "Intermediate",
            "duration": "2h 45m",
            "video_query": "uart spi i2c communication protocols explained embedded",
            "default_title": "Communication Protocols: UART, SPI, and I2C in Depth",
            "default_channel": "Ben Eater"
        },
        {
            "phase": 5,
            "title": "Phase 5: Real-Time Operating Systems (FreeRTOS) & Schedulers",
            "description": "FreeRTOS kernel primitives: task creation, preemptive scheduling, semaphores, message queues, priority inversion, and mutex protection.",
            "level": "Advanced",
            "duration": "3h 00m",
            "video_query": "freertos tutorial for beginners embedded rtos digikey",
            "default_title": "Introduction to RTOS with FreeRTOS",
            "default_channel": "DigiKey"
        },
        {
            "phase": 6,
            "title": "Phase 6: Hardware Debugging, Logic Analyzers & Production Firmware",
            "description": "SWD/JTAG debugging with OpenOCD and GDB, logic analyzer protocol decoding, watchdog timers, power optimization, and bootloaders.",
            "level": "Advanced",
            "duration": "2h 00m",
            "video_query": "embedded debugging swd jtag logic analyzer tutorial",
            "default_title": "Embedded Systems Debugging and Production Best Practices",
            "default_channel": "Phil's Lab"
        }
    ]
}


async def query_gemini_curriculum(topic: str, standing: str) -> list[dict]:
    """Query Gemini 2.0 / 1.5 Flash for an exhaustive, search-grounded 6-phase learning curriculum."""
    gemini_key = get_active_gemini_key()
    if not gemini_key:
        return []

    prompt = (
        f"You are a principal technical educator and curriculum architect.\n"
        f"Design an exhaustive, professional 6-phase progressive learning roadmap for mastering: '{topic}'.\n"
        f"Current learner standing: {standing}.\n\n"
        f"Each phase MUST represent a real, progressive milestone from fundamentals to production systems mastery.\n"
        f"For each phase, specify:\n"
        f"- 'phase': integer (1 to 6)\n"
        f"- 'title': Phase title (e.g. 'Phase 1: ...')\n"
        f"- 'description': 1-2 sentences on key concepts and skills\n"
        f"- 'level': 'Beginner', 'Intermediate', or 'Advanced'\n"
        f"- 'duration': estimated duration (e.g. '3h 30m')\n"
        f"- 'video_query': YouTube search query targeting the highest-quality tutorial (e.g. 'c programming full course bro code')\n"
        f"- 'default_title': Recommended video title\n"
        f"- 'default_channel': Authoritative YouTube channel (e.g. Bro Code, freeCodeCamp.org, Andrej Karpathy, Fireship, etc.)\n\n"
        f"Respond ONLY with a JSON array of 6 phase objects. No preamble, no markdown backticks."
    )

    for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=8.0)) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        text = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if "[" in text and "]" in text:
                            json_str = text[text.find("["):text.rfind("]") + 1]
                            phases = json.loads(json_str)
                            if isinstance(phases, list) and len(phases) >= 4:
                                return phases
        except Exception as e:
            logger.debug("Gemini curriculum generator exception with %s: %s", model_name, e)
            continue
    return []


async def query_local_ollama_curriculum(topic: str, standing: str) -> list[dict]:
    """Generate dynamic progressive 6-phase curriculum using local Ollama model (Gemma / SmolLM2)."""
    prompt = (
        f"You are a computer science professor and senior curriculum architect.\n"
        f"Generate a customized, professional 6-phase progressive learning curriculum for mastering '{topic}'.\n"
        f"Learner current standing: {standing}.\n\n"
        f"Each phase MUST represent a real milestone from fundamentals to production systems engineering:\n"
        f"Phase 1: Foundations, syntax, core environment\n"
        f"Phase 2: Modular design, functions, data structures\n"
        f"Phase 3: Core internals, memory layout, idioms\n"
        f"Phase 4: Real-world practical systems & project engineering\n"
        f"Phase 5: Concurrency, performance profiling, optimization\n"
        f"Phase 6: Production architecture, capstone, enterprise deployment\n\n"
        f"Respond ONLY with a valid JSON array of 6 objects in this exact schema:\n"
        f"[\n"
        f"  {{\n"
        f"    \"phase\": 1,\n"
        f"    \"title\": \"Phase 1: ...\",\n"
        f"    \"description\": \"1-2 concise sentences summarizing concepts and skills\",\n"
        f"    \"level\": \"Beginner\",\n"
        f"    \"duration\": \"2h 30m\",\n"
        f"    \"video_query\": \"search query for best youtube tutorial\",\n"
        f"    \"default_channel\": \"Channel Name\"\n"
        f"  }}\n"
        f"]"
    )
    try:
        res = await asyncio.wait_for(
            registry.complete(prompt=prompt, task_type="reason", max_tokens=650, temperature=0.2),
            timeout=10.0
        )
        text = res.content.strip()
        if "[" in text and "]" in text:
            json_str = text[text.find("["):text.rfind("]") + 1]
            phases = json.loads(json_str)
            if isinstance(phases, list) and len(phases) >= 4:
                return phases
    except Exception as e:
        logger.debug("Local Ollama curriculum generation notice: %s", e)
    return []


async def generate_comprehensive_roadmap(topic: str, standing: str, interest_id: str) -> list[dict]:
    """Generates a deep 6-phase curriculum with verified YouTube tutorial links."""
    # 1. Try Gemini API first if configured
    phases = await query_gemini_curriculum(topic, standing)
    
    # 2. Try Local Ollama AI Model (Gemma / SmolLM2) dynamically
    if not phases:
        phases = await query_local_ollama_curriculum(topic, standing)

    # 3. Check predefined comprehensive curricula
    if not phases:
        if interest_id in COMPREHENSIVE_CURRICULA:
            phases = COMPREHENSIVE_CURRICULA[interest_id]
        else:
            for k, cur in COMPREHENSIVE_CURRICULA.items():
                if k in interest_id or interest_id in k:
                    phases = cur
                    break
    
    # 4. Dynamic generic 6-phase masterclass fallback
    if not phases:
        phases = [
            {
                "phase": 1,
                "title": f"Phase 1: Foundations, Tooling & Core Syntax of {topic}",
                "description": f"Master the core syntax, dev environment, project tooling, and language fundamentals for {topic}.",
                "level": "Beginner",
                "duration": "3h 00m",
                "video_query": f"{topic} complete beginners tutorial full course",
                "default_title": f"{topic} Full Course for Beginners",
                "default_channel": "freeCodeCamp.org"
            },
            {
                "phase": 2,
                "title": f"Phase 2: Modular Architecture & Core Paradigms in {topic}",
                "description": f"Understand modular organization, functions, classes/structs, scope boundaries, and error handling in {topic}.",
                "level": "Beginner",
                "duration": "2h 00m",
                "video_query": f"{topic} modular architecture design patterns tutorial",
                "default_title": f"{topic} Core Patterns and Architecture",
                "default_channel": "Programming with Mosh"
            },
            {
                "phase": 3,
                "title": f"Phase 3: Data Structures & Core Mechanics of {topic}",
                "description": f"Deep dive into memory layout, data structures, type systems, and idiomatic conventions of {topic}.",
                "level": "Intermediate",
                "duration": "2h 30m",
                "video_query": f"{topic} data structures deep dive internals",
                "default_title": f"{topic} Internals and Data Structures",
                "default_channel": "Fireship"
            },
            {
                "phase": 4,
                "title": f"Phase 4: Real-World Systems & Project Engineering with {topic}",
                "description": f"Build practical, end-to-end applications integrating external APIs, databases, and core libraries in {topic}.",
                "level": "Intermediate",
                "duration": "3h 00m",
                "video_query": f"{topic} full stack practical project build tutorial",
                "default_title": f"Building Real-World Systems with {topic}",
                "default_channel": "Traversy Media"
            },
            {
                "phase": 5,
                "title": f"Phase 5: Concurrency, Performance & Optimization in {topic}",
                "description": f"Master asynchronous I/O, multithreading, concurrency safety, profiling, and cache optimizations for {topic}.",
                "level": "Advanced",
                "duration": "2h 15m",
                "video_query": f"advanced {topic} concurrency performance profiling masterclass",
                "default_title": f"Advanced {topic} Performance & Concurrency",
                "default_channel": "GOTO Conferences"
            },
            {
                "phase": 6,
                "title": f"Phase 6: Production Architecture, Testing & Capstone Mastery in {topic}",
                "description": f"Implement comprehensive test suites, CI/CD pipelines, containerization, and enterprise-grade architecture in {topic}.",
                "level": "Advanced",
                "duration": "2h 30m",
                "video_query": f"enterprise {topic} production architecture best practices",
                "default_title": f"Production-Ready {topic} Architecture & Systems",
                "default_channel": "Hussein Nasser"
            }
        ]

    # Enrich each phase with verified, authoritative YouTube links
    enriched = []
    for idx, p in enumerate(phases):
        p_title = p.get("title", f"Phase {idx + 1}: {topic}")
        p_desc = p.get("description", "")
        p_lvl = p.get("level", "Intermediate")
        p_dur = p.get("duration", "2h 00m")
        p_q = p.get("video_query") or f"{topic} {p_title} tutorial"
        def_title = p.get("default_title", p_title)
        def_channel = p.get("default_channel", "YouTube Educator")

        yt_res = await resolve_youtube_video(p_q, default_title=def_title, default_channel=def_channel, default_duration=p_dur)
        
        is_completed = False
        if standing == "Advanced" and p_lvl in ["Beginner", "Intermediate"]:
            is_completed = True
        elif standing == "Intermediate" and p_lvl == "Beginner":
            is_completed = True

        enriched.append({
            "phase": p.get("phase", idx + 1),
            "title": p_title,
            "description": p_desc,
            "level": p_lvl,
            "duration": yt_res.get("duration") or p_dur,
            "url": yt_res["url"],
            "video_id": yt_res.get("video_id", ""),
            "channel": yt_res.get("channel") or def_channel,
            "completed": is_completed
        })

    # Save to SQLite knowledge store
    knowledge_graph.store.save_roadmap(interest_id, topic, standing, enriched)
    
    # Invalidate cache so future requests see the updated roadmap
    global _interests_cache
    _interests_cache = {"hash": "", "data": None, "timestamp": 0.0}
    
    return enriched


async def handle_generate_roadmap(request: web.Request) -> web.Response:
    """POST /api/v1/knowledge/roadmap/generate — Generate comprehensive 6-phase roadmap on demand."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    interest_id = data.get("interest_id") or ""
    topic = data.get("topic") or ""
    standing = data.get("standing") or "Beginner"

    if not interest_id and not topic:
        return web.json_response({"status": "error", "message": "interest_id or topic is required"}, status=400)

    if not interest_id:
        norm = resolve_topic_info(topic)
        interest_id = norm["slug"]
        topic = norm["title"]
    elif not topic:
        norm = resolve_topic_info(interest_id)
        topic = norm["title"]

    roadmap = await generate_comprehensive_roadmap(topic, standing, interest_id)
    return web.json_response({
        "status": "success",
        "interest_id": interest_id,
        "title": topic,
        "standing": standing,
        "phases_count": len(roadmap),
        "roadmap": roadmap
    })


async def handle_delete_roadmap(request: web.Request) -> web.Response:
    """DELETE /api/v1/knowledge/roadmap/{id} — Remove active roadmap back to discovered interest."""
    interest_id = request.match_info.get("id", "")
    knowledge_graph.store.delete_roadmap(interest_id)
    global _interests_cache
    _interests_cache = {"hash": "", "data": None, "timestamp": 0.0}
    return web.json_response({"status": "success", "interest_id": interest_id})


async def handle_get_interests(request: web.Request) -> web.Response:
    """
    GET /api/v1/knowledge/interests
    Discovers learning interests from browser telemetry (searches, YouTube videos)
    and attaches saved comprehensive roadmaps if activated by the user.
    """
    global _interests_cache

    browser_events_count = 0
    searches = []
    youtube_videos = []

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

    # Fallback to recent events if empty
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

    # 2. Filter out non-study browsing (gaming, entertainment, shopping, social media)
    study_searches = [s for s in searches if is_study_related(s["query"])]
    study_videos = [y for y in youtube_videos if is_study_related(y["title"], y.get("channel", ""))]

    gemini_key = get_active_gemini_key()
    cloud_status = {
        "enabled": bool(gemini_key),
        "model": "gemini-2.0-flash" if gemini_key else "local-only",
        "description": "Cloud-Augmented (Gemini 2.0 Flash)" if gemini_key else "Local Intelligence (Zero Telemetry)"
    }

    if not study_searches and not study_videos:
        return web.json_response({
            "status": "success",
            "total_interests": 0,
            "interests": [],
            "total_browser_events": browser_events_count,
            "cloud_status": cloud_status
        })

    # Cache signature based strictly on study-filtered telemetry and active roadmaps
    active_roadmaps = knowledge_graph.store.get_all_roadmaps()
    raw_signature = f"v3:{len(study_searches)}:{[s['query'] for s in study_searches]}:{len(study_videos)}:{[y['title'] for y in study_videos]}:{list(active_roadmaps.keys())}"
    sig_hash = hashlib.md5(raw_signature.encode()).hexdigest()

    if _interests_cache["data"] and _interests_cache["hash"] == sig_hash and (time.time() - _interests_cache["timestamp"] < 900.0):
        return web.json_response(_interests_cache["data"])

    # High-precision Dynamic Pattern Aggregator
    clusters = {}

    for s in study_searches:
        meta = resolve_topic_info(s["query"])
        slug = meta["slug"]
        if slug not in clusters:
            clusters[slug] = {"title": meta["title"], "slug": slug, "icon": meta["icon"], "searches": [], "videos": []}
        if s["query"] not in clusters[slug]["searches"]:
            clusters[slug]["searches"].append(s["query"])

    for y in study_videos:
        meta = resolve_topic_info(y["title"])
        slug = meta["slug"]
        if slug not in clusters:
            clusters[slug] = {"title": meta["title"], "slug": slug, "icon": meta["icon"], "searches": [], "videos": []}
        if not any(v["url"] == y["url"] for v in clusters[slug]["videos"]):
            clusters[slug]["videos"].append(y)

    final_interests = []

    for slug, cluster in clusters.items():
        t_name = cluster["title"]
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

        # Check if user has explicitly generated a roadmap for this interest
        saved_roadmap = active_roadmaps.get(slug)
        has_roadmap = bool(saved_roadmap and len(saved_roadmap) > 0)
        roadmap_data = saved_roadmap if has_roadmap else []

        final_interests.append({
            "id": slug,
            "title": t_name,
            "icon": cluster["icon"],
            "standing": standing,
            "standing_score": score,
            "standing_badge": badge,
            "standing_color": color,
            "next_milestone": next_mile,
            "has_roadmap": has_roadmap,
            "stats": {
                "searches_count": search_cnt,
                "videos_watched": vid_cnt,
                "watch_time_minutes": w_min,
                "total_events": search_cnt + vid_cnt,
                "last_active": cluster["videos"][0]["timestamp"] if cluster["videos"] else (cluster["searches"][0] if cluster["searches"] else "")
            },
            "recent_searches": cluster["searches"][:6],
            "recent_videos": cluster["videos"][:4],
            "roadmap": roadmap_data
        })

    # Sort interests by standing and engagement
    final_interests.sort(key=lambda x: (x["standing_score"], x["stats"]["total_events"]), reverse=True)

    result_payload = {
        "status": "success",
        "total_interests": len(final_interests),
        "interests": final_interests,
        "total_browser_events": browser_events_count,
        "cloud_status": cloud_status
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
    app.router.add_post("/api/v1/knowledge/roadmap/generate", handle_generate_roadmap)
    app.router.add_delete("/api/v1/knowledge/roadmap/{id}", handle_delete_roadmap)
    app.router.add_get("/api/v1/knowledge/skill/{id}", handle_get_skill)
    app.router.add_get("/api/v1/knowledge/gaps", handle_get_gaps)
    app.router.add_post("/api/v1/knowledge/query", handle_query_knowledge)



