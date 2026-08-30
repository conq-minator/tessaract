# Member 5 — AI & Knowledge: Development Instructions

> **Owner**: Member 5
> **Language**: Python 3.11+
> **Runtime**: Local async service

---

## 1. Environment Setup

### 1.1 Prerequisites

| Tool | Version | Installation |
|:---|:---|:---|
| Python | 3.11+ (3.12 recommended) | [python.org](https://www.python.org) |
| pip | Latest | Comes with Python |
| Ollama | Latest stable | [ollama.com](https://ollama.com) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### 1.2 Ollama Setup

```bash
# Install Ollama (download from ollama.com or use package manager)
# Verify installation
ollama --version

# Pull initial test models
ollama pull smollm2:1.7b
ollama pull all-minilm:l6-v2

# Ollama runs as a background service on port 11434
# Verify it's running
curl http://localhost:11434/api/tags
```

### 1.3 Initial Setup

```bash
cd member-5_ai-knowledge

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
copy ..\env\member-5\.env.example .env
# Edit .env with your local API keys and settings
```

---

## 2. Dependencies

### 2.1 Python Packages

```
# Core
aiohttp>=3.9.0
httpx>=0.27.0
python-dotenv>=1.0.0

# AI / ML
sentence-transformers>=3.0.0
# Note: This pulls PyTorch — expect ~2 GB download

# Graph
networkx>=3.3.0

# Vector Store
sqlite-vec>=0.1.0

# Database
# sqlite3 is in Python stdlib

# Utilities
uuid6>=2024.0.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-aiohttp>=1.0.0
black>=24.0.0
ruff>=0.5.0
mypy>=1.10.0
```

### 2.2 Heavy Dependencies Note

| Package | Size | Notes |
|:---|:---|:---|
| `sentence-transformers` | ~2 GB (includes PyTorch) | Required for local embeddings |
| `sqlite-vec` | ~5 MB | Lightweight SQLite extension |
| `networkx` | ~10 MB | Pure Python graph library |

If PyTorch size is a concern during development, you can install CPU-only PyTorch first:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```

---

## 3. Configuration

### 3.1 Environment Variables

Located in `../env/member-5/.env.example`:

```env
# Server
TESSERACT_AI_HOST=localhost
TESSERACT_AI_PORT=9701
TESSERACT_SHARED_SECRET=

# Ollama
TESSERACT_OLLAMA_HOST=localhost
TESSERACT_OLLAMA_PORT=11434
TESSERACT_MODEL_IDLE_TIMEOUT_S=300

# Model Assignments (configurable per task)
TESSERACT_MODEL_CLASSIFY=smollm2:1.7b
TESSERACT_MODEL_REASON=gemma4:e2b
TESSERACT_MODEL_VISION=gemma4:e2b
TESSERACT_MODEL_EMBED=all-minilm:l6-v2

# Cloud Fallback
TESSERACT_CLOUD_ENABLED=false
TESSERACT_GEMINI_API_KEY=
TESSERACT_OPENAI_API_KEY=

# Knowledge Graph
TESSERACT_KG_DB_PATH=~/.tesseract/data/knowledge.db

# Vector Store
TESSERACT_VECTOR_DB_PATH=~/.tesseract/data/vectors.db

# Benchmark
TESSERACT_BENCHMARK_DIR=~/.tesseract/benchmarks
```

---

## 4. Development Commands

```bash
# Activate venv
.venv\Scripts\activate

# Run the AI & Knowledge service
python -m ai_knowledge

# Run with mock Ollama (no real models needed)
python -m ai_knowledge --mock-models

# Run with debug logging
python -m ai_knowledge --log-level=DEBUG

# Lint
ruff check .

# Format
black .

# Type check
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run benchmark suite
python -m ai_knowledge.benchmark
```

---

## 5. Testing

### 5.1 Unit Tests

```bash
pytest tests/
```

Test with mock models during unit testing — do not require Ollama for unit tests.

### 5.2 Benchmark Suite

```bash
# Run full benchmark (requires Ollama with models pulled)
python -m ai_knowledge.benchmark --all

# Benchmark specific model
python -m ai_knowledge.benchmark --model smollm2:1.7b

# Benchmark specific task
python -m ai_knowledge.benchmark --task intent-classification
```

Benchmark tasks (from master prompt Section 26):
- Repeated C pointer error classification
- Python beginner learning detection
- YouTube learning sequence detection
- VS Code debugging struggle interpretation
- Handwritten mathematical question (multimodal)
- Technical diagram interpretation (multimodal)
- Intent classification accuracy
- Knowledge-gap detection from episode data
- Hint generation quality
- Practice-question generation quality

### 5.3 Testing the Knowledge Graph

```bash
# Interactive KG exploration
python -m ai_knowledge.kg_explorer
```

---

## 6. Debugging

### 6.1 Ollama Model Status

```bash
# List loaded models
curl http://localhost:11434/api/ps

# List available models
curl http://localhost:11434/api/tags

# Test generation
curl http://localhost:11434/api/generate -d '{"model":"smollm2:1.7b","prompt":"Hello"}'
```

### 6.2 Knowledge Graph Inspection

```bash
python -c "
import sqlite3
conn = sqlite3.connect('~/.tesseract/data/knowledge.db')
cursor = conn.execute('SELECT skill_id, confidence FROM skills ORDER BY confidence ASC LIMIT 10')
for row in cursor:
    print(f'{row[0]}: {row[1]:.2f}')
"
```

### 6.3 Vector Store Inspection

```bash
python -c "
import sqlite3, sqlite_vec
conn = sqlite3.connect('~/.tesseract/data/vectors.db')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
cursor = conn.execute('SELECT COUNT(*) FROM embeddings')
print(f'Total embeddings: {cursor.fetchone()[0]}')
"
```

---

## 7. Model Requirements

### 7.1 Models to Pull for Development

```bash
# Tier 1 — Lightweight (always loaded)
ollama pull smollm2:1.7b

# Tier 2 — Reasoning (on demand)
ollama pull gemma4:e2b
# or: ollama pull phi4-mini

# Embedding model
ollama pull all-minilm:l6-v2
```

### 7.2 Model Benchmarking

Before choosing final models, run the benchmark suite against all candidates:

| Tier | Candidates |
|:---|:---|
| Tier 1 (classify) | SmolLM2 1.7B, Qwen3-0.6B, Qwen3-1.7B |
| Tier 2 (reason) | Gemma 4 E2B, Gemma 4 E4B, Phi-4 mini |
| Tier 3 (vision) | Gemma 4 E2B, Gemma 4 E4B, Gemma 3n E4B |

The benchmark report should rank models by:
1. Accuracy (on Tesseract-specific tasks)
2. Latency (time to first token, total generation time)
3. RAM usage (peak, steady-state)
4. CPU usage (average during inference)

**Choose the smallest model that provides acceptable quality.**

---

## 8. Git Instructions

### 8.1 Branch Naming

```
member-5/{type}-{description}
```

Examples:
- `member-5/feat-model-abstraction`
- `member-5/feat-knowledge-graph`
- `member-5/feat-benchmark-suite`
- `member-5/feat-ollama-integration`

### 8.2 Commit Convention

```
[M5] type: short description
```

### 8.3 Folder Discipline

**You may ONLY modify files inside `member-5_ai-knowledge/`.**

---

## 9. Integration Instructions (Phase 2+)

### With Core Engine (Member 4)
1. Start this service: `python -m ai_knowledge`
2. Start Member 4's Core Engine (without `--mock-ai`)
3. Trigger events that cause Member 4 to request classification
4. Verify inference requests arrive and responses are correct
5. Verify knowledge graph updates from behavioral evidence

### With Tutor/UI (Member 6)
1. Start this service
2. Start Member 6's Tutor/UI
3. Request a hint, explanation, or roadmap from the UI
4. Verify the response is contextually appropriate
5. Verify the knowledge graph is visible in the dashboard

---

## 10. Cloud API Setup (Optional)

### Google Gemini
1. Get an API key from [Google AI Studio](https://aistudio.google.com)
2. Set `TESSERACT_GEMINI_API_KEY` in your `.env`
3. Set `TESSERACT_CLOUD_ENABLED=true`

### OpenAI
1. Get an API key from [OpenAI Platform](https://platform.openai.com)
2. Set `TESSERACT_OPENAI_API_KEY` in your `.env`
3. Set `TESSERACT_CLOUD_ENABLED=true`

Cloud is **optional** — Tesseract runs fully local without it.
