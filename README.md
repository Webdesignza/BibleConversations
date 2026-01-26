# 📖 Bible Conversations

**Multi-Translation Bible Study System with Voice AI Assistant**

An intelligent, voice-enabled Bible study platform that allows users to explore and compare different Bible translations through natural conversation.

---

## ✨ Features

- 🎤 **Voice Conversations** - Natural spoken dialogue with the Bible AI
- 📚 **Multiple Translations** - Support for any Bible translation (KJV, NIV, ESV, etc.)
- 🔍 **RAG-Powered** - Retrieval Augmented Generation for accurate biblical context
- 🌐 **Embeddable Widget** - Single-line integration into any website
- 🆓 **FREE APIs** - Uses Groq (Whisper + Llama) and Edge TTS
- 🔒 **Secure** - Token-based authentication and session management
- 🚀 **Fast** - Optimized for quick responses and smooth conversations

---

## 🏗️ Architecture

### Backend Stack
- **FastAPI** - High-performance Python API framework
- **LangChain** - RAG orchestration framework
- **ChromaDB** - Vector database for embeddings
- **HuggingFace** - Free local embeddings (sentence-transformers)
- **Groq Whisper** - Speech-to-text (FREE)
- **Groq Llama** - LLM for responses (FREE)
- **Edge TTS** - Text-to-speech (FREE)

### Frontend Stack
- **Vanilla JavaScript** - No dependencies, lightweight widget
- **Web Audio API** - Voice activity detection
- **MediaRecorder API** - Audio recording

---

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd bible-conversations
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the application**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload
```

5. **Open browser**
```
http://localhost:8009
```

### Railway Deployment

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete deployment guide.

**Quick steps:**
1. Push code to GitHub
2. Connect Railway to your repo
3. Add environment variables
4. Deploy automatically!

---

## 📚 API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send question, get response
- `POST /api/chat/stt` - Speech-to-text conversion
- `POST /api/chat/tts` - Text-to-speech conversion

### Translation Management
- `GET /api/translations/list` - List available translations
- `POST /api/translations/create` - Create new translation
- `POST /api/translations/switch` - Switch active translation
- `DELETE /api/translations/delete` - Remove translation

### Document Management
- `POST /api/documents/upload` - Upload Bible text files
- `GET /api/documents/stats` - Get translation statistics

### Interface Endpoints
- `GET /` - Homepage with links
- `GET /admin` - Admin panel
- `GET /chat` - Chat interface
- `GET /agent` - Voice agent interface
- `GET /docs` - API documentation (Swagger)

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...           # For embeddings
GROQ_API_KEY=gsk_...            # For STT and LLM
API_KEY=your-secure-key         # For authentication

# Optional (with defaults)
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=llama-3.1-70b-versatile
GROQ_API_BASE=https://api.groq.com/openai/v1
CHROMA_DB_PATH=./chroma_db
RETRIEVAL_K=3
TEMPERATURE=0.7
UPLOAD_DIR=./uploads
HOST=0.0.0.0
PORT=8009
```

### Generate Secure API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🌐 Widget Integration

### Basic Integration

Add to your HTML before `</body>`:

```html
<script src="https://your-railway-url.up.railway.app/static/bible-widget.js"></script>
```

### Customization

The widget is fully self-contained and automatically:
- Creates a floating button
- Opens modal dialog
- Handles microphone permissions
- Manages voice conversations
- Displays transcripts

---

## 📖 Using the System

### 1. Create a Translation

**Via Admin Interface:**
1. Go to `/admin`
2. Click "Create New Translation"
3. Enter ID (e.g., "kjv"), name, description
4. Click "Create"

**Via API:**
```bash
curl -X POST http://localhost:8009/api/translations/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "translation_id": "kjv",
    "name": "King James Version",
    "description": "Classic English translation"
  }'
```

### 2. Upload Bible Text

**Via Admin Interface:**
1. Select translation from dropdown
2. Click "Choose File"
3. Select .txt, .pdf, or .docx file
4. Click "Upload"

**Via API:**
```bash
curl -X POST http://localhost:8009/api/documents/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@genesis.txt" \
  -F "translation_id=kjv"
```

### 3. Use Voice Interface

1. Open `/agent` or embed widget on website
2. Select translation from dropdown
3. Click "Start" button
4. Allow microphone access
5. Speak your question
6. Listen to AI response
7. Continue conversation naturally

---

## 🎯 Example Questions

The AI can answer questions like:
- "What does John 3:16 say?"
- "Tell me about the creation story in Genesis"
- "What are the Ten Commandments?"
- "Explain the parable of the prodigal son"
- "What does love mean in 1 Corinthians 13?"
- "Compare how different translations phrase this verse"

---

## 📁 Project Structure

```
bible-conversations/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   └── security.py        # Authentication
│   ├── api/
│   │   └── routes/            # API endpoints
│   │       ├── chat.py
│   │       ├── documents.py
│   │       └── translations.py
│   └── services/              # Core services
│       ├── rag_service.py     # RAG & translation management
│       ├── document_service.py # Document processing
│       ├── stt_service.py     # Speech-to-text
│       └── speech_service.py  # Text-to-speech
├── static/
│   ├── bible-widget.js        # Embeddable widget
│   ├── admin.html             # Admin interface
│   ├── chat.html              # Chat interface
│   └── images/                # Assets
├── chroma_db/                 # Vector database storage
├── uploads/                   # Temporary file storage
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container config
├── .dockerignore             # Docker build exclusions
├── railway.json              # Railway deployment config
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 🔒 Security

### Authentication
- All API endpoints require Bearer token authentication
- Session tokens expire after conversation ends
- API key must be kept secret

### HTTPS
- Required for microphone access
- Railway provides automatic SSL
- Local development works on http://localhost

### Data Privacy
- No conversation logging by default
- Temporary audio files deleted immediately
- Translation data stored locally in ChromaDB

---

## 💰 Cost Estimate

### Railway Hosting
- **$5/month** Starter plan
- Typical usage: $2-3/month with moderate traffic

### API Costs
- **Groq**: FREE (Whisper STT + Llama LLM)
- **OpenAI**: ~$0.01/month (embeddings only, very low usage)
- **Edge TTS**: FREE

**Total: ~$5-7/month** for production deployment

---

## 🐛 Troubleshooting

### Build Issues
- Verify `Dockerfile` is in root directory
- Check all dependencies in `requirements.txt`
- Review Railway build logs

### Runtime Errors
- Check environment variables are set correctly
- Verify API keys are valid
- Check Railway application logs

### Widget Not Working
- Ensure HTTPS is enabled
- Check browser microphone permissions
- Verify API URL in `bible-widget.js`
- Check browser console for errors

### No Audio/Voice Issues
- Test with Chrome or Edge browsers
- Check system audio/microphone settings
- Verify voice activity detection threshold

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Groq** - Free Whisper and Llama API
- **Microsoft Edge** - Free TTS service
- **HuggingFace** - Free embedding models
- **LangChain** - RAG framework
- **Railway** - Easy deployment platform

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for deployment help
- Review API documentation at `/docs`

---

**Built with ❤️ for Bible study and exploration**