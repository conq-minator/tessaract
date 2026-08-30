# Member 5 (AI & Knowledge Layer) — Memory & Architectural Log

> **Owner**: Member 5  
> **Status**: Active & Fully Operational with All Local Model Tiers  

---

## 1. Architectural Decisions (ADRs)

### ADR-01: Dual-Layer Knowledge Graph (NetworkX + SQLite)
- **Decision**: Use an in-memory `networkx.DiGraph` for all topological operations (prerequisite traversal, cycle detection, reachable nodes) and an embedded SQLite database for ACID persistence and audit history.
- **Rationale**: Graph path queries and topological sorts are orders of magnitude faster in NetworkX in-memory than recursive SQL CTEs. SQLite provides bulletproof, zero-server disk persistence on restart.

### ADR-02: Native Ollama Embedding Over Heavy Local PyTorch
- **Decision**: Prioritize Ollama's native `/api/embed` endpoint using `all-minilm:l6-v2` for embeddings, with sentence-transformers as a secondary fallback.
- **Rationale**: Ollama is already running natively as a C++ service. Calling its embedding endpoint saves loading ~2GB of PyTorch into Python runtime memory, preserving system RAM for the user's IDE and browser.

### ADR-03: Multi-Signal Epistemic Confidence Formula
- **Decision**: Update skill confidence dynamically using evidence weights:
  $$C_{t+1} = \text{clamp}\left(C_t + \sum w_i \cdot \Delta_i - \lambda \cdot \Delta t_{\text{days}}, 0.0, 1.0\right)$$
  Where positive events (`error_resolved`: $+0.08$, `tutorial_watched`: $+0.04$, `practice_completed`: $+0.12$) increase confidence and negative friction events (`repeated_error`: $-0.06$) decrease confidence.
- **Rationale**: Master prompt explicitly requires that single errors do NOT immediately declare a knowledge gap; multi-signal confidence modeling provides stable, resilient skill estimation.

### ADR-04: Non-Blocking Model Swapping via Protocol Abstraction
- **Decision**: All model consumption goes through the `ModelProvider` protocol. The application never directly hardcodes model names in business logic.
- **Rationale**: Allows benchmark-driven model replacement (e.g. swapping SmolLM2 for Gemma 4 or Phi-4) simply by updating configuration, without rewriting a single line of code.

---

## 2. Hardware & Environment Baseline
- **Host OS**: Windows 11 64-bit
- **CPU**: Intel Core Ultra 5 125H (14 Cores / 18 Logical Processors) with Intel Arc GPU & Meteor Lake NPU
- **Python Version**: 3.13.14
- **Local AI Daemon**: Ollama v0.33.2 (active at `http://localhost:11434`)
- **Assigned Service Port**: `9701`
- **Total System RAM**: 16.4 GB
- **Models Installed in Ollama**:
  - `gemma4:e2b` (Tier 2/3 Reasoning & Multimodal VLM) — ✅ Installed & Verified (7.2 GB)
  - `smollm2:1.7b` (Tier 1 Fast Classifier & Reasoning) — ✅ Installed & Verified (1.8 GB)
  - `gemma2:2b` (SLM Reasoning) — ✅ Installed & Verified (1.6 GB)
  - `all-minilm:l6-v2` (Dense Embeddings) — ✅ Installed & Verified (45 MB)

---

## 3. Interface Contracts Summary

| Interface | Upstream / Downstream | Protocol | Schema / Contract |
|:---|:---|:---|:---|
| `SensorEventStream` | M1, M2, M3 → M4 | WebSocket `9700/events` | Handled by Member 4 |
| `CoreDataAPI` | M4 → M5, M6 | REST `9700/api/v1` | Core context, session, episode data |
| `AIInferenceAPI` | M4, M6 → M5 | REST `9701/api/v1` | Inference, Knowledge Graph, Embeddings |
| `TutorAIAPI` | M6 → M5 | REST `9701/api/v1` | Progressive hints, explanations, roadmaps |

---

## 4. Verification History
- **2026-08-30**: Architecture finalized, seven top-level folders verified, root documentation approved.
- **2026-08-30**: Created Member 5 specific documentation (`prd.md`, `phases.md`, `memory.md`).
- **2026-08-30**: Built all 7 core modules in `src/`.
- **2026-08-30**: Executed test suite — **20/20 tests passed in 1.46s (100% pass rate)**.
- **2026-08-30**: Upgraded Ollama to v0.33.2 and installed complete model lineup.
- **2026-08-30**: Live verified `gemma4:e2b` inference via `OllamaProvider`.
