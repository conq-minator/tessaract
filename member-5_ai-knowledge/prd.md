# Member 5 (AI & Knowledge Layer) — Product Requirements Document (PRD)

> **Owner**: Member 5  
> **Component**: `member-5_ai-knowledge`  
> **Status**: In Development  
> **Version**: 1.0.0  

---

## 1. Executive Summary & Purpose

Member 5 serves as the **central cognitive and epistemic engine** of Tesseract. While sensors (Members 1–3) harvest raw interaction signals and the Core Engine (Member 4) deterministically aggregates events and calculates friction scores, Member 5 transforms raw activity indicators into **epistemic meaning, structured knowledge representations, and progressive pedagogical assistance**.

### Core Tenet
> **"Do Not Use an LLM for Everything."**  
> Member 5 strictly respects the master architecture principle: deterministic scoring belongs to Member 4. Member 5 executes AI inference only when reasoning, semantic synthesis, concept mapping, or adaptive pedagogical generation is genuinely required.

---

## 2. Component Scope & Boundaries

### 2.1 What Member 5 Owns
1. **Model Abstraction Layer (MAL)**: Decoupled multi-tier provider interface supporting Ollama (local SLMs/VLMs), cloud fallbacks (Gemini/OpenAI), and in-memory mock providers.
2. **Model Lifecycle & Management**: Lazy-loading models on demand, idle-timeout auto-unloading, and hardware-conscious memory limits.
3. **Model Benchmark Suite**: Rigorous automated evaluation framework testing candidate models (SmolLM2 1.7B, Gemma 4 E2B/E4B, Phi-4 mini, Qwen3) against 10 domain-specific Tesseract tasks.
4. **Personal Knowledge Graph (PKG)**: Dual-layer graph engine (NetworkX for high-speed in-memory topological queries, SQLite for ACID persistence) maintaining user skill nodes, confidence scores, and prerequisite directed edges.
5. **Epistemic Confidence & Decay Engine**: Bayesian-inspired confidence updates driven by behavioral evidence (repeated errors, consecutive successes, tutorial consumption, time-to-resolution).
6. **Vector Store & Semantic Search**: Embedded `sqlite-vec` index for retrieval-augmented generation (RAG) and semantic query resolution.
7. **Progressive Tutor Support Services**: High-fidelity generation of Level 1 through Level 5 assistance (Hints → Concept Explanations → Detailed Breakdowns → Practice Problems → Full Solutions).
8. **Member 5 REST API**: High-throughput async HTTP service on port `9701` serving `/inference/*`, `/knowledge/*`, `/tutor/*`, and `/models/*`.

### 2.2 What Member 5 Does NOT Own
- Direct event capture from browsers, IDEs, or OS (Members 1, 2, 3).
- Real-time event deduplication and friction calculation (Member 4).
- End-user notifications, system tray icon, and visual dashboard frontend (Member 6).

---

## 3. Functional Requirements

### 3.1 Model Abstraction & Inference
- **FR-1.1**: The system must provide a unified `ModelProvider` protocol exposing `complete()`, `classify()`, `embed()`, and `vision()`.
- **FR-1.2**: A central `ModelRegistry` must dynamically route requests according to `task_type` (`classification`, `reasoning`, `vision`, `embedding`) with transparent fallback from local to cloud providers.
- **FR-1.3**: When cloud inference is invoked, all request payloads must pass through an automated PII-sanitization filter removing local absolute paths, user identifiers, and IP addresses.
- **FR-1.4**: Inactivity monitor must track model usage and trigger Ollama unloading when idle for > 300 seconds.

### 3.2 Personal Knowledge Graph (PKG)
- **FR-2.1**: The PKG must model knowledge as a Directed Acyclic Graph (DAG) of `SkillNode`s connected by `prerequisite_of` and `subtopic_of` relationships.
- **FR-2.2**: Each skill node must store a continuous confidence rating in the range $[0.0, 1.0]$ and maintain an append-only audit trail of behavioral evidence.
- **FR-2.3**: The engine must compute prerequisite gaps: identifying required predecessor nodes whose confidence falls below threshold $0.60$.
- **FR-2.4**: Skills must experience gentle time-decay if no reinforcing activity occurs over a 14-day rolling window.

### 3.3 Vector Memory & RAG
- **FR-3.1**: Text chunks must be converted to dense vector embeddings using local Ollama (`all-minilm:l6-v2`) or sentence-transformers.
- **FR-3.2**: Embeddings must be persisted in SQLite with `sqlite-vec` virtual tables executing fast KNN searches.

### 3.4 Progressive Tutoring & Pedagogy
- **FR-4.1**: Hints (Level 1) must be strictly non-spoiling, pointing toward first principles rather than syntax answers.
- **FR-4.2**: Explanations (Level 2 & 3) must dynamically incorporate the learner's known mastered concepts as analogies.
- **FR-4.3**: Practice problems (Level 4) must isolate the specific weak prerequisite identified by the PKG.
- **FR-4.4**: Roadmaps must generate adaptive milestone DAGs respecting daily study constraints (30 min, 1 hr, 2 hrs/day).

---

## 4. Technical Specifications & Interface Contracts

### 4.1 Service Topology
- **Host**: `localhost` (IPv4)
- **Port**: `9701`
- **Protocol**: HTTP/1.1 REST + JSON
- **Security**: Local shared secret transmitted via `Authorization: Bearer <TESSERACT_SHARED_SECRET>`

### 4.2 Endpoint Catalog
| Method | Route | Description |
|:---|:---|:---|
| `POST` | `/api/v1/inference/complete` | Text completion & structured reasoning |
| `POST` | `/api/v1/inference/classify` | Multi-class label classification |
| `POST` | `/api/v1/inference/embed` | Vector embedding generation |
| `POST` | `/api/v1/inference/vision` | Multimodal image understanding |
| `POST` | `/api/v1/knowledge/update` | Ingest behavioral evidence & adjust skill confidence |
| `GET` | `/api/v1/knowledge/graph` | Export full/subgraph topology (JSON nodes & edges) |
| `GET` | `/api/v1/knowledge/skill/{id}` | Inspect specific skill node & history |
| `GET` | `/api/v1/knowledge/gaps` | Query detected prerequisite deficiencies |
| `POST` | `/api/v1/knowledge/query` | Semantic vector search across concepts and notes |
| `POST` | `/api/v1/tutor/hint` | Generate Level 1 progressive hint |
| `POST` | `/api/v1/tutor/explain` | Generate Level 2/3 concept explanation |
| `POST` | `/api/v1/tutor/practice` | Generate Level 4 targeted practice problem |
| `POST` | `/api/v1/tutor/roadmap` | Generate adaptive multi-week learning plan |
| `GET` | `/api/v1/models/status` | Real-time status of loaded models & memory consumption |
| `POST` | `/api/v1/models/benchmark` | Trigger automated benchmark suite run |

---

## 5. Non-Functional Requirements
- **Latency**: Local classification latency $< 400\text{ms}$ on CPU; prompt completion $< 2.5\text{s}$ time-to-first-token.
- **Memory Footprint**: Peak RAM consumption under active inference $\le 4.0\text{GB}$; idle consumption $\le 150\text{MB}$.
- **Privacy & Airgap**: 100% operational in offline mode without internet connection. Cloud calls strictly opt-in.
