# Member 5 — AI & Knowledge: Environment Setup

## Required Environment Variables

| Variable | Description | Example |
|:---|:---|:---|
| `TESSERACT_AI_HOST` | Host to bind the AI service | `localhost` |
| `TESSERACT_AI_PORT` | Port for REST API | `9701` |
| `TESSERACT_SHARED_SECRET` | Shared authentication secret | (generate locally) |
| `TESSERACT_OLLAMA_HOST` | Ollama server host | `localhost` |
| `TESSERACT_OLLAMA_PORT` | Ollama server port | `11434` |
| `TESSERACT_KG_DB_PATH` | Path to knowledge graph SQLite database | `~/.tesseract/data/knowledge.db` |
| `TESSERACT_VECTOR_DB_PATH` | Path to vector store SQLite database | `~/.tesseract/data/vectors.db` |

## Optional: Cloud API Keys

| Variable | Description | When Needed |
|:---|:---|:---|
| `TESSERACT_CLOUD_ENABLED` | Enable cloud LLM fallback | Set to `true` for cloud features |
| `TESSERACT_GEMINI_API_KEY` | Google Gemini API key | Only if using Gemini cloud fallback |
| `TESSERACT_OPENAI_API_KEY` | OpenAI API key | Only if using OpenAI cloud fallback |

> **NEVER commit real API keys.** Keep them in your local `.env` only.

## Setup

1. Copy `.env.example` to `.env`
2. Install and start Ollama (`ollama serve`)
3. Pull required models:
   ```bash
   ollama pull smollm2:1.7b
   ollama pull all-minilm:l6-v2
   ```
4. (Optional) Set cloud API keys for fallback

## External Services

| Service | Required | Notes |
|:---|:---|:---|
| Ollama | Yes | Must be running for local inference |
| Google Gemini API | Optional | Cloud fallback |
| OpenAI API | Optional | Cloud fallback |

## Model Downloads

| Model | Size (Q4) | Command |
|:---|:---|:---|
| SmolLM2 1.7B | ~1 GB | `ollama pull smollm2:1.7b` |
| Gemma 4 E2B | ~3 GB | `ollama pull gemma4:e2b` |
| Gemma 4 E4B | ~5 GB | `ollama pull gemma4:e4b` |
| Phi-4 mini | ~2.5 GB | `ollama pull phi4-mini` |
| all-MiniLM-L6-v2 | ~80 MB | `ollama pull all-minilm:l6-v2` |

Pull only the models you are benchmarking. Not all are needed simultaneously.
