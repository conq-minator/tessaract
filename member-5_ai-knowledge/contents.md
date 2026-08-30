# Member 5 — AI & Knowledge

> **Owner**: Member 5
> **Folder**: `member-5_ai-knowledge/`
> **Status**: Phase 0 — Documentation

---

## 1. Component Responsibility

Member 5 owns the **AI Inference Layer** and the **Personal Knowledge Graph**. This is the intelligence center of Tesseract — it manages model selection, local/cloud inference, embeddings, semantic search, and the evolving skill graph.

This member is the **only component that directly interacts with AI models**. All other members request AI services through Member 5's REST API.

---

## 2. Features

### 2.1 Model Abstraction Layer
- Provide a unified API for all AI inference (text, vision, embedding, classification)
- Abstract away model-specific details (Ollama, cloud APIs)
- Support per-task model assignment
- Enable model swapping without downstream code changes

### 2.2 Model Registry & Configuration
- Maintain a registry of available models (local and cloud)
- Track model status (loaded, unloaded, downloading)
- Configure model assignment per task type
- Support model fallback chains (local → cloud)

### 2.3 Ollama Integration
- Interface with Ollama for local model management
- Handle model downloads, loading, unloading
- Manage lazy loading (load on first request)
- Implement idle unloading (unload after configurable idle time)

### 2.4 Cloud API Integration
- Provide fallback to cloud LLMs (Gemini, OpenAI) when local is insufficient
- PII stripping before sending requests
- Context abstraction (send summaries, not raw data)
- Response caching to minimize cloud calls

### 2.5 Benchmark Suite
- Define benchmark tasks representative of Tesseract's workloads
- Evaluate candidate models on accuracy, latency, RAM, CPU
- Generate benchmark reports for model selection decisions
- Re-run benchmarks when new models become available

### 2.6 Embedding Pipeline
- Generate text embeddings using a local embedding model
- Store embeddings in sqlite-vec for semantic search
- Support batch embedding generation
- Provide semantic search/query functionality

### 2.7 RAG (Retrieval-Augmented Generation)
- Retrieve relevant context from the vector store
- Augment prompts with retrieved context
- Support document-level and chunk-level retrieval

### 2.8 Personal Knowledge Graph
- Maintain a directed graph of skills, concepts, and prerequisites
- Store in SQLite (persistent) + NetworkX (in-memory for graph operations)
- Track confidence scores per skill node (0.0–1.0)
- Update confidence based on behavioral evidence from Member 4
- Support temporal evidence (confidence changes over time)
- Detect prerequisite gaps

### 2.9 Concept Mapping
- Map observed topics to a concept taxonomy
- Link related concepts (e.g., "C pointers" → "memory management" → "C programming")
- Identify prerequisite chains

### 2.10 Tutor Support Endpoints
- Generate contextual hints at progressive difficulty levels
- Generate concept explanations adapted to user level
- Generate practice problems for weak areas
- Generate/update personalized learning roadmaps
- Recommend learning resources based on knowledge gaps

---

## 3. Internal Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  AI & Knowledge Service                       │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             REST API Server (port 9701)                │  │
│  │   /inference/*  /knowledge/*  /tutor/*  /models/*      │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
│         ┌───────────────┼───────────────────┐                │
│         ↓               ↓                   ↓                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │Model         │ │Knowledge     │ │Tutor Support     │    │
│  │Abstraction   │ │Graph Engine  │ │Engine            │    │
│  │Layer         │ │              │ │                  │    │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘    │
│         │               │                    │               │
│         ↓               ↓                    │               │
│  ┌──────────────┐ ┌──────────────┐          │               │
│  │Model Registry│ │SQLite + NX   │          │               │
│  │              │ │(Graph Store) │          │               │
│  └──────┬───────┘ └──────────────┘          │               │
│         │                                    │               │
│    ┌────┴──────────────┐                    │               │
│    ↓                   ↓                    │               │
│  ┌───────────┐  ┌──────────────┐           │               │
│  │Ollama     │  │Cloud APIs    │           │               │
│  │(Local)    │  │(Gemini/OAI)  │           │               │
│  └───────────┘  └──────────────┘           │               │
│                                             │               │
│  ┌────────────────────────────────────────┐ │               │
│  │        Embedding Pipeline              │ │               │
│  │  ┌──────────────┐  ┌───────────────┐  │ │               │
│  │  │MiniLM-L6-v2  │  │sqlite-vec     │  │ │               │
│  │  │(Embed Model) │  │(Vector Store) │  │ │               │
│  │  └──────────────┘  └───────────────┘  │ │               │
│  └────────────────────────────────────────┘ │               │
│                                             │               │
│  ┌────────────────────────────────────────┐                 │
│  │        Benchmark Suite                 │                 │
│  └────────────────────────────────────────┘                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Inputs

| Input | Source | Protocol |
|:---|:---|:---|
| Inference requests | Member 4 (Core Engine) | REST |
| Knowledge graph updates | Member 4 (Core Engine) | REST |
| Tutor requests | Member 6 (Tutor/UI) | REST |
| Model management commands | Admin / config | REST |

---

## 5. Outputs

### 5.1 REST API Endpoints

**Inference:**

| Method | Path | Purpose |
|:---|:---|:---|
| POST | `/api/v1/inference/complete` | Text completion / reasoning |
| POST | `/api/v1/inference/classify` | Intent / topic classification |
| POST | `/api/v1/inference/vision` | Image understanding |
| POST | `/api/v1/inference/embed` | Generate embeddings |

**Knowledge Graph:**

| Method | Path | Purpose |
|:---|:---|:---|
| POST | `/api/v1/knowledge/update` | Update skill node confidence |
| GET | `/api/v1/knowledge/graph` | Get full knowledge graph |
| GET | `/api/v1/knowledge/skill/{id}` | Get skill details and history |
| POST | `/api/v1/knowledge/query` | Semantic search over knowledge |
| GET | `/api/v1/knowledge/gaps` | Get detected prerequisite gaps |
| GET | `/api/v1/knowledge/progress` | Get learning progress summary |

**Tutor Support:**

| Method | Path | Purpose |
|:---|:---|:---|
| POST | `/api/v1/tutor/hint` | Generate contextual hint |
| POST | `/api/v1/tutor/explain` | Generate concept explanation |
| POST | `/api/v1/tutor/practice` | Generate practice problem |
| POST | `/api/v1/tutor/roadmap` | Generate/update learning roadmap |
| POST | `/api/v1/tutor/recommend` | Recommend learning resources |

**Model Management:**

| Method | Path | Purpose |
|:---|:---|:---|
| GET | `/api/v1/models/status` | Get loaded/available models |
| POST | `/api/v1/models/benchmark` | Trigger benchmark run |
| GET | `/api/v1/models/benchmark/{id}` | Get benchmark results |

---

## 6. Data Structures

### 6.1 Knowledge Graph Node (Skill)

```json
{
  "skill_id": "c-pointers-dereferencing",
  "name": "Pointer Dereferencing",
  "parent": "c-pointers",
  "domain": "c-programming",
  "confidence": 0.25,
  "evidence_count": 14,
  "last_updated": "ISO-8601",
  "history": [
    { "timestamp": "ISO-8601", "confidence": 0.20, "evidence": "repeated_error" },
    { "timestamp": "ISO-8601", "confidence": 0.25, "evidence": "tutorial_watched" }
  ],
  "prerequisites": ["c-variables", "c-memory-model"],
  "status": "weak"
}
```

### 6.2 Confidence Update Evidence

```json
{
  "skill": "c-pointers-dereferencing",
  "evidence_type": "error_resolved | tutorial_watched | practice_completed | repeated_error | search_performed | successful_execution",
  "confidence_delta": 0.05,
  "source_episode_id": "uuid-v4",
  "timestamp": "ISO-8601"
}
```

### 6.3 Inference Request/Response

```json
// Request
{
  "prompt": "Classify the following learning topic: ...",
  "task_type": "classification",
  "max_tokens": 100,
  "constraints": {
    "prefer_local": true,
    "max_latency_ms": 5000
  }
}

// Response
{
  "result": "c-programming/pointers",
  "model_used": "smollm2:1.7b",
  "latency_ms": 340,
  "tokens_used": 45,
  "source": "local"
}
```

---

## 7. Dependencies

### Internal Dependencies (at runtime)

None. Member 5 is a service that **other members depend on**. It does not depend on other Tesseract components at runtime.

### External Dependencies

| Package | Purpose |
|:---|:---|
| `aiohttp` | Async HTTP server (REST API) |
| `httpx` | Async HTTP client (Ollama, cloud APIs) |
| `sqlite-vec` | Vector similarity search in SQLite |
| `sentence-transformers` | Local embedding model |
| `networkx` | In-memory graph operations |
| `python-dotenv` | Environment config |
| `sqlite3` (stdlib) | Graph persistence, config |

### External Services

| Service | Purpose | Required |
|:---|:---|:---|
| Ollama | Local model inference | Yes (for local AI) |
| Google Gemini API | Cloud fallback | Optional |
| OpenAI API | Cloud fallback | Optional |

---

## 8. Interfaces

### 8.1 Inbound: REST API Server

- **Owner**: Member 5 (this component)
- **Consumers**: Members 4, 6
- **Protocol**: REST (HTTP)
- **Base URL**: `http://localhost:9701/api/v1`
- **Auth**: `Authorization: Bearer <TESSERACT_SHARED_SECRET>`

### 8.2 Outbound: Ollama API

- **Protocol**: REST (HTTP)
- **Base URL**: `http://localhost:11434` (Ollama default)
- **Endpoints**: `/api/generate`, `/api/chat`, `/api/embed`

### 8.3 Outbound: Cloud APIs

- **Google Gemini**: `https://generativelanguage.googleapis.com/v1beta`
- **OpenAI**: `https://api.openai.com/v1`
- **Auth**: API key from `.env`

---

## 9. Testing

### Unit Tests
- Model abstraction layer correctly routes requests
- Knowledge graph CRUD operations work correctly
- Confidence scoring updates correctly with evidence
- Prerequisite gap detection works
- Embedding pipeline generates correct-dimension vectors
- sqlite-vec similarity search returns relevant results
- Cloud PII stripping removes sensitive data

### Benchmark Tests
- Run benchmark suite against all candidate models
- Compare accuracy, latency, RAM usage
- Generate comparison reports

### Integration Tests (Phase 2+)
- Member 4 successfully calls inference endpoints
- Member 6 successfully calls tutor endpoints
- Knowledge graph updates from Member 4's behavioral data
- Model loading/unloading via Ollama works correctly

---

## 10. Definition of Done

- [ ] REST API serves all documented endpoints
- [ ] Model abstraction layer works with at least one local model via Ollama
- [ ] Cloud fallback works with at least one provider
- [ ] Knowledge graph stores and retrieves skill nodes
- [ ] Confidence scoring updates correctly with behavioral evidence
- [ ] Prerequisite gap detection identifies missing skills
- [ ] Embedding pipeline generates and stores vectors
- [ ] Semantic search returns relevant results
- [ ] Tutor endpoints generate hints, explanations, and practice problems
- [ ] Benchmark suite runs and produces reports
- [ ] Lazy model loading works (not loaded until first request)
- [ ] Idle model unloading works (unloaded after configurable timeout)
- [ ] PII stripping works for cloud requests
- [ ] All unit tests pass

---

## 11. What This Member Owns

- Model abstraction layer
- Model registry and configuration
- Ollama integration (load, unload, inference)
- Cloud API integration (Gemini, OpenAI)
- PII stripping for cloud requests
- Benchmark suite
- Embedding model management
- Embedding pipeline (generate + store)
- Vector store (sqlite-vec)
- RAG engine
- Personal Knowledge Graph (data model, CRUD, graph operations)
- Confidence scoring algorithm
- Prerequisite gap detection
- Concept mapping / taxonomy
- Tutor support endpoints (hint, explain, practice, roadmap, recommend)
- REST API server (port 9701)

---

## 12. What This Member Does NOT Own

- Event collection (Members 1, 2, 3)
- Event aggregation / normalization (Member 4)
- Behavioral analysis / stuck detection (Member 4)
- Session / episode management (Member 4)
- User interface / notifications (Member 6)
- Automation engine (Member 6)
- Permission guard / autonomy levels (Member 6)
- OCR processing (Member 3)
