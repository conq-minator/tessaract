"""Knowledge Graph and semantic search endpoints."""

from aiohttp import web
from src.knowledge.graph import knowledge_graph
from src.embeddings.embedder import embedder
from src.embeddings.vector_store import vector_store


async def handle_update_knowledge(request: web.Request) -> web.Response:
    """POST /api/v1/knowledge/update — Ingest behavioral evidence from Member 4."""
    data = await request.json()
    skill_id = data.get("skill") or data.get("skill_id")
    evidence_type = data.get("evidence_type", "error_resolved")
    delta = float(data.get("confidence_delta", 0.0))
    episode_id = data.get("source_episode_id")
    metadata = data.get("metadata", {})

    if not skill_id:
        return web.json_response(
            {"error": "missing_parameter", "message": "'skill' or 'skill_id' is required"},
            status=400,
        )

    updated = knowledge_graph.record_evidence(
        skill_id=skill_id,
        evidence_type=evidence_type,
        confidence_delta=delta,
        source_episode_id=episode_id,
        metadata=metadata,
    )
    if not updated:
        return web.json_response(
            {"error": "not_found", "message": f"Skill '{skill_id}' not found in Knowledge Graph"},
            status=404,
        )

    return web.json_response(updated.model_dump())


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


def setup_knowledge_routes(app: web.Application):
    app.router.add_post("/api/v1/knowledge/update", handle_update_knowledge)
    app.router.add_get("/api/v1/knowledge/graph", handle_get_graph)
    app.router.add_get("/api/v1/knowledge/skill/{id}", handle_get_skill)
    app.router.add_get("/api/v1/knowledge/gaps", handle_get_gaps)
    app.router.add_post("/api/v1/knowledge/query", handle_query_knowledge)
