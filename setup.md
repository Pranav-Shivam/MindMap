# PDF Study App - Setup Guide

Complete step-by-step guide to set up and run the PDF Study App locally.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **CouchDB 3.x** - [Download CouchDB](https://couchdb.apache.org/)
- **Git** (optional) - For cloning the repository

**Note:** No Redis or Docker needed! Background tasks use asyncio (built into Python).

## Step 1: Clone/Download the Project

If you have the project in a repository:
```bash
git clone <repository-url>
cd MindMap
```

Or navigate to your project directory if you already have it.

## Step 2: Install CouchDB

### Windows
1. Download CouchDB installer from https://couchdb.apache.org/
2. Run the installer
3. During installation, set up an admin user:
   - Username: `admin`
   - Password: `password` (or your preferred password)
4. CouchDB will run on `http://localhost:5984`

### macOS
```bash
brew install couchdb
brew services start couchdb
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y couchdb
sudo systemctl start couchdb
sudo systemctl enable couchdb
```

### Verify CouchDB is Running
```bash
curl http://localhost:5984
```

You should see a JSON response with CouchDB version information.

## Step 3: Setup Backend

**Note:** Background tasks use asyncio (built into Python), so no Redis or Docker is needed!

### 3.1 Create Virtual Environment (Recommended)

```bash
cd backend
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3.3 Configure Environment Variables

1. Copy the environment template:
```bash
cp ../env.copy.txt .env
```

2. Edit `.env` file and update the following:

```env
# CouchDB Configuration
COUCHDB_URL=http://admin:password@localhost:5984
COUCHDB_USER=admin
COUCHDB_PASSWORD=password  # Change to your CouchDB password

# ChromaDB Configuration (no setup needed - runs embedded)
CHROMA_PERSIST_DIR=./chroma_db

# LLM Provider API Keys (add at least one)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
OLLAMA_BASE_URL=http://localhost:11434

# Feature Flags
USE_RERANKER=false
ALLOW_DECK_SCOPE=true
ALLOW_LOCAL_OLLAMA=true

# Application Settings
JWT_SECRET=your-secure-random-string-min-32-characters-long
UPLOAD_DIR=./uploads
PREVIEW_DIR=./previews

# Default Providers
DEFAULT_LLM_PROVIDER=gpt
DEFAULT_EMBEDDING_PROVIDER=openai_small
```

**Important Notes:**
- Replace `password` with your actual CouchDB admin password
- Add at least one LLM provider API key (OpenAI recommended for easiest setup)
- Generate a secure `JWT_SECRET` (you can use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

### 3.4 Initialize Databases

Run the database setup script:

```bash
python -c "from app.db.setup import setup_databases; from app.vector import initialize_collections; setup_databases(); initialize_collections()"
```

This will:
- Create CouchDB databases (users, documents, pages, qa, annotations)
- Create design documents with views
- Initialize ChromaDB collections

You should see success messages in the console.

## Step 4: Setup Frontend

### 4.1 Navigate to Frontend Directory

```bash
cd ../frontend
```

### 4.2 Install Node Dependencies

```bash
npm install
```

This may take a few minutes as it installs all required packages.

## Step 5: Get API Keys (Choose at least one LLM provider)

### Option A: OpenAI (Recommended - Easiest)

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key and add it to your `.env` file as `OPENAI_API_KEY`

**Models available:** gpt-4o, gpt-4o-mini, gpt-3.5-turbo

### Option B: Anthropic (Claude)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key and add it to your `.env` file as `ANTHROPIC_API_KEY`

**Models available:** claude-3-5-sonnet, claude-3-opus, claude-3-haiku

### Option C: Google (Gemini)

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and add it to your `.env` file as `GOOGLE_API_KEY`

**Models available:** gemini-1.5-flash, gemini-1.5-pro

### Option D: Ollama (Local - No API Key Needed)

1. Install Ollama from https://ollama.ai/
2. Pull a model:
   ```bash
   ollama pull llama3.1
   ```
3. Pull embedding model:
   ```bash
   ollama pull nomic-embed-text
   ```
4. Start Ollama (usually runs automatically)
5. Verify it's running:
   ```bash
   curl http://localhost:11434
   ```

**No API key needed** - just ensure `OLLAMA_BASE_URL=http://localhost:11434` in your `.env`

## Step 6: Run the Application

You'll need **2 terminal windows** running simultaneously:

### Terminal 1: Backend API Server

```bash
cd backend
# Activate virtual environment if you created one
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

python -m app.main
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Frontend Development Server

```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Step 7: Access the Application

1. Open your browser and navigate to: **http://localhost:5173**
2. You should see the login page
3. Create an account or log in
4. Start uploading PDFs!

## Verification Checklist

Before using the app, verify everything is working:

- [ ] CouchDB is running (`curl http://localhost:5984`)
- [ ] Backend API is running (http://localhost:8000/healthz)
- [ ] Frontend is running (http://localhost:5173)
- [ ] At least one LLM API key is configured
- [ ] Databases are initialized

## Troubleshooting

### Issue: CouchDB Connection Failed

**Symptoms:** Error message about CouchDB connection

**Solutions:**
1. Verify CouchDB is running: `curl http://localhost:5984`
2. Check credentials in `.env` match your CouchDB admin user
3. Try accessing CouchDB Fauxton UI: http://localhost:5984/_utils
4. Restart CouchDB service

### Issue: ChromaDB Errors

**Symptoms:** Vector database errors

**Solutions:**
1. Ensure `CHROMA_PERSIST_DIR` directory exists or can be created
2. Check file permissions on the directory
3. Delete `./chroma_db` folder and let it recreate

### Issue: API Key Errors

**Symptoms:** LLM provider not available

**Solutions:**
1. Verify API key is correct in `.env`
2. Check API key has sufficient credits/quota
3. For OpenAI, verify billing is set up
4. Check logs in `backend/logs/app.log` for detailed errors

### Issue: PDF Upload Fails

**Symptoms:** Upload button doesn't work or errors

**Solutions:**
1. Check `UPLOAD_DIR` and `PREVIEW_DIR` directories exist
2. Verify file permissions
3. Ensure PDF is not encrypted or corrupted
4. Background tasks run automatically - check backend logs if processing fails

### Issue: Frontend Can't Connect to Backend

**Symptoms:** Network errors in browser console

**Solutions:**
1. Verify backend is running on port 8000
2. Check CORS settings in `backend/app/main.py`
3. Verify proxy settings in `frontend/vite.config.js`
4. Check browser console for specific error messages

### Issue: Streaming Q&A Doesn't Work

**Symptoms:** Answers don't stream in real-time

**Solutions:**
1. Check browser console for SSE errors
2. Verify backend SSE endpoint is working
3. Check LLM provider API key is valid
4. Ensure network doesn't block SSE connections

## Directory Structure After Setup

```
MindMap/
├── backend/
│   ├── .env                    # Your environment variables
│   ├── venv/                   # Virtual environment (if created)
│   ├── chroma_db/              # ChromaDB storage (auto-created)
│   ├── uploads/                # Uploaded PDFs (auto-created)
│   ├── previews/               # Page previews (auto-created)
│   └── logs/                   # Application logs
├── frontend/
│   ├── node_modules/           # Node dependencies
│   └── dist/                   # Build output (after build)
└── .env.copy.txt               # Environment template
```

## Next Steps

Once everything is running:

1. **Upload a PDF** - Go to the upload page and select a PDF file
2. **Wait for Processing** - The RQ worker will process your PDF (check Terminal 2 for progress)
3. **Start Studying** - Navigate to your document and start asking questions!
4. **Try Different Providers** - Switch between LLM providers in the header
5. **Explore Features** - Try different scope modes, search, and citations

## Production Deployment Notes

For production deployment:

1. **Change JWT_SECRET** to a strong random value
2. **Set up proper CouchDB authentication** (don't use default admin/password)
3. **Configure Redis persistence** if needed
4. **Set up proper file storage** (S3, etc.) instead of local directories
5. **Use environment-specific configurations**
6. **Set up proper logging and monitoring**
7. **Configure HTTPS** for the frontend
8. **Set up process managers** (PM2, systemd) for backend and workers

## Getting Help

If you encounter issues:

1. Check the logs in `backend/logs/app.log`
2. Check browser console for frontend errors
3. Verify all services are running
4. Review the README.md for architecture details
5. Check that all environment variables are set correctly

## Quick Start Commands Summary

```bash
# 1. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../env.copy.txt .env
# Edit .env with your API keys
python -c "from app.db.setup import setup_databases; from app.vector import initialize_collections; setup_databases(); initialize_collections()"

# 2. Setup frontend
cd ../frontend
npm install

# 3. Run (in 2 separate terminals)
# Terminal 1: Backend (handles background tasks automatically)
cd backend && source venv/bin/activate && python -m app.main

# Terminal 2: Frontend
cd frontend && npm run dev
```

Happy studying! 📚✨

