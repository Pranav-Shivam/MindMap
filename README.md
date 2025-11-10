# PDF Study App

A production-quality MVP for page-scoped PDF study with AI-powered Q&A, multi-provider LLM support, and semantic search.

## Architecture Overview

**Backend:**
- FastAPI + Uvicorn
- CouchDB (document/user/QA storage)
- Qdrant (vector search with embeddings)
- Redis + RQ (background job queue)
- PyMuPDF (PDF processing)

**Frontend:**
- Vite + React (JavaScript only)
- TailwindCSS + shadcn/ui
- react-pdf (PDF.js)
- TanStack Query + Zustand
- Server-Sent Events (SSE)

**LLM Providers:** Runtime-switchable GPT, Ollama, Gemini, Claude  
**Embeddings:** OpenAI (text-embedding-3-small, ada-002), Ollama (nomic-embed-text)

## Features

✅ Upload PDF slides and automatic ingestion  
✅ Page-by-page study with AI-generated explanations & key terms  
✅ Ask questions with streaming answers (SSE)  
✅ Context-grounded Q&A with citations  
✅ Scope controls: This page / ±2 pages / Entire deck  
✅ Hybrid retrieval (vector + text search)  
✅ Persistent Q&A history per page  
✅ Global search across documents and Q&A  
✅ Multi-provider LLM support with runtime switching  
✅ **Model Selection UI**: Easy switching between OpenAI, Claude (Sonnet), Gemini, and Ollama  
✅ JWT authentication  
✅ Resizable split-pane UI  

## Prerequisites

- Python 3.10+
- Node.js 18+
- CouchDB 3.x
- Qdrant (vector database)
- Redis 6+
- (Optional) Ollama for local LLMs

## Quick Start

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Setup Services

**CouchDB:**
```bash
# Install CouchDB from https://couchdb.apache.org/
# Default: http://localhost:5984
# Create admin user: admin/password
```

**Qdrant:**
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or download from https://qdrant.tech/
```

**Redis:**
```bash
# Using Docker
docker run -p 6379:6379 redis

# Or install locally
```

### 3. Configure Environment

Create `backend/.env` from the template:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and add your API keys:
```env
# CouchDB
COUCHDB_URL=http://admin:password@localhost:5984

# Qdrant
QDRANT_URL=http://localhost:6333

# Redis
REDIS_URL=redis://localhost:6379

# LLM Provider API Keys (add at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# App Settings
JWT_SECRET=your-secret-key-here
```

### 4. Initialize Database

```bash
cd backend
python -c "from app.db.setup import setup_databases; from app.vector import initialize_collections; setup_databases(); initialize_collections()"
```

### 5. Start Services

**Terminal 1 - Backend API:**
```bash
cd backend
python -m app.main
# Runs on http://localhost:8000
```

**Terminal 2 - RQ Worker:**
```bash
cd backend
python worker.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 6. Access the App

Open http://localhost:5173 in your browser.

## Usage Guide

### 1. Register/Login
- Create an account or login
- JWT token stored in localStorage

### 2. Upload PDF
- Click "Upload PDF" on homepage
- Select a PDF file (slides work best)
- Upload starts ingestion job
- Pages become ready progressively

### 3. Study Mode
- Navigate to document
- **Left pane:** PDF viewer with thumbnails, zoom controls
- **Right pane:** Explanation, key terms, Q&A
- Ask questions about the current page
- Answers stream in real-time with citations

### 4. Scope Controls
- **This Page:** Search only current page (default)
- **±2 Pages:** Include nearby pages
- **Entire Deck:** Search whole document

### 5. Model Selection
- Click the **Settings** button in the header to open model selection dialog
- **LLM Provider:** Choose between OpenAI GPT, Anthropic Claude (Sonnet), Google Gemini, or Ollama
- **Model:** Select specific model within chosen provider (e.g., gpt-4o-mini, claude-3-5-sonnet)
- **Embedding Provider:** Choose embedding model (affects new uploads and search)
- Green checkmark indicates available providers, red X shows unavailable ones
- Settings persist in localStorage and apply immediately

### 6. Search
- Global search across all Q&A and page content
- Click results to jump to specific pages

## LLM Provider Setup

### OpenAI (GPT)
1. Get API key from https://platform.openai.com/
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. Models available: gpt-4o, gpt-4o-mini, gpt-3.5-turbo

### Anthropic (Claude)
1. Get API key from https://console.anthropic.com/
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Models: claude-3-5-sonnet, claude-3-opus, claude-3-haiku

### Google (Gemini)
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env`: `GOOGLE_API_KEY=...`
3. Models: gemini-1.5-flash, gemini-1.5-pro

### Ollama (Local)
1. Install Ollama from https://ollama.ai/
2. Pull models: `ollama pull llama3.1`
3. Pull embedding model: `ollama pull nomic-embed-text`
4. Ensure `OLLAMA_BASE_URL=http://localhost:11434`

## How It Works

### Ingestion Flow
1. User uploads PDF
2. Backend enqueues RQ job
3. Worker extracts text per page (PyMuPDF)
4. Generates page previews (PNG images)
5. Chunks text (500-800 tokens, sentence-aware)
6. Embeds chunks with selected provider
7. Upserts to Qdrant vector collection
8. Generates page summary + key terms (LLM)
9. Marks page as "ready"

### Q&A Flow
1. User asks question on a page
2. Question embedded with same provider
3. Qdrant vector search with page filter
4. Top-k chunks retrieved (default: 6)
5. Build context-only prompt with chunk IDs
6. Stream answer via SSE
7. Extract citations from response
8. Persist Q&A to CouchDB
9. Display in timeline with citations

### Retrieval Strategy
- **Hybrid:** Vector similarity (Qdrant) + text search (CouchDB)
- **Chunking:** Sentence-aware with 50-100 token overlap
- **Scope Filtering:** Page-level filters in Qdrant
- **Citations:** Chunk IDs in prompt → parsed from LLM response

## API Endpoints

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Get current user

### Documents
- `POST /documents/upload` - Upload PDF
- `GET /documents` - List user's documents
- `GET /documents/{doc_id}` - Get document details
- `DELETE /documents/{doc_id}` - Delete document

### Pages
- `GET /documents/{doc_id}/pages` - List pages
- `GET /documents/{doc_id}/page/{page_no}` - Get page details
- `GET /documents/{doc_id}/page/{page_no}/preview` - Get preview image

### Q&A
- `POST /documents/{doc_id}/page/{page_no}/qa` - Ask question (SSE stream)
- `GET /documents/{doc_id}/qa` - Get all Q&A for document

### Search
- `GET /search?q=...` - Search Q&A and pages

### Health
- `GET /healthz` - API health
- `GET /readyz` - Service readiness (CouchDB, Qdrant, Redis)

## Design Notes

### CouchDB Choice
Using CouchDB instead of PostgreSQL (per user preference). Documents are denormalized for efficient retrieval. Design documents with MapReduce views provide indexed queries.

### Qdrant as Vector DB
Since CouchDB lacks native vector search, Qdrant handles all embedding storage and semantic retrieval. Separate collections per embedding dimension (1536 for OpenAI, 768 for Ollama).

### RQ for Background Jobs
Chosen for simplicity and stability. Perfect for PDF ingestion and embedding generation. Workers can be scaled horizontally.

### Provider Abstraction
Single unified interface (`ChatClient`, `EmbeddingClient`) allows runtime switching between providers without code changes. Factory pattern with error handling.

### Embeddings Strategy
New ingestions use the selected embedding provider. Existing vectors remain queryable. Dimension mismatch handled by separate Qdrant collections.

### Citation Tracking
Chunk IDs embedded in prompts allow precise source attribution. Frontend parses citation patterns `[page:X, chunk:Y]` from LLM responses.

### Progressive Readiness
Pages marked ready as soon as processed, allowing users to start studying before full deck ingestion completes.

### SSE Streaming
Server-Sent Events provide efficient, low-latency token streaming for answers. Frontend accumulates tokens for smooth UX.

## Project Structure

```
MindMap/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Dataclass config
│   │   ├── auth/                # JWT auth
│   │   ├── db/                  # CouchDB client
│   │   ├── vector/              # Qdrant client
│   │   ├── utils/
│   │   │   ├── llm/             # LLM abstraction
│   │   │   ├── embeddings/      # Embeddings abstraction
│   │   │   ├── pdf.py           # PDF processing
│   │   │   ├── chunking.py      # Text chunking
│   │   │   ├── retrieval.py     # Hybrid retrieval
│   │   │   └── sse.py           # SSE helpers
│   │   ├── workers/             # RQ jobs
│   │   └── api/                 # API routes
│   ├── requirements.txt
│   └── worker.py                # RQ worker entry
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app
│   │   ├── main.jsx             # Entry point
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── PDFViewer.jsx    # PDF display
│   │   │   ├── StudyPanel.jsx   # Q&A panel
│   │   │   └── Header.jsx       # Top bar
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── DocumentPage.jsx
│   │   │   └── SearchPage.jsx
│   │   ├── hooks/               # Custom hooks
│   │   ├── store/               # Zustand stores
│   │   └── lib/                 # API client
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

## Troubleshooting

### CouchDB Connection Failed
- Verify CouchDB is running: `curl http://localhost:5984`
- Check credentials in `.env`
- Ensure databases are created (run setup script)

### Qdrant Connection Failed
- Verify Qdrant is running: `curl http://localhost:6333/collections`
- Check URL in `.env`

### RQ Worker Not Processing
- Ensure Redis is running: `redis-cli ping`
- Check worker.py is running
- View RQ dashboard: `rq info`

### PDF Upload Fails
- Check file permissions on `uploads/` directory
- Verify PDF is valid (not encrypted)
- Check logs in `logs/app.log`

### Streaming Doesn't Work
- Verify SSE endpoint returns correct headers
- Check browser console for errors
- Ensure LLM provider API key is valid

### Embeddings Dimension Mismatch
- Different providers have different dimensions
- Qdrant collections are provider-specific
- Re-upload document with correct provider

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### Code Style
- Backend: PEP 8 (Python)
- Frontend: ESLint + Prettier (JavaScript)

### Adding New LLM Provider
1. Create client in `backend/app/utils/llm/{provider}_client.py`
2. Implement `ChatClient` protocol
3. Add to factory in `factory.py`
4. Update frontend provider picker

## License

MIT

## Support

For issues, please check logs in `backend/logs/app.log` and browser console. Ensure all services are running and API keys are valid.

