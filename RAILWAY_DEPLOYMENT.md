# 🚀 Railway Deployment Guide - Bible Conversations

Complete guide to deploying your Multi-Translation Bible Study System to Railway.app

---

## 📋 Pre-Deployment Checklist

### 1. **Get Your API Keys**

You need two API keys:

#### Groq API Key (FREE)
1. Visit https://console.groq.com
2. Sign up or log in
3. Go to API Keys section
4. Create a new key
5. Copy it (starts with `gsk_...`)

#### OpenAI API Key (for embeddings)
1. Visit https://platform.openai.com
2. Go to API Keys
3. Create new key
4. Copy it (starts with `sk-...`)

### 2. **Generate Secure API Key**

Run this in your terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save this output - you'll need it for `API_KEY`.

---

## 🚂 Railway Setup

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Verify your email

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Connect your GitHub account if not already connected
4. Select the **Webdesignza/BibleConversations** repository

### Step 3: Configure Environment Variables

In Railway dashboard:

1. Go to your project
2. Click on the service
3. Go to **"Variables"** tab
4. Click **"+ New Variable"**

Add these variables one by one:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
GROQ_API_KEY=gsk_your-actual-key-here
API_KEY=your-generated-secure-key-here
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=llama-3.1-70b-versatile
GROQ_API_BASE=https://api.groq.com/openai/v1
CHROMA_DB_PATH=./chroma_db
RETRIEVAL_K=3
TEMPERATURE=0.7
UPLOAD_DIR=./uploads
HOST=0.0.0.0
```

**Note:** Railway automatically provides `PORT` - don't set it manually!

### Step 4: Deploy

1. Railway will automatically detect your `Dockerfile`
2. It will start building immediately
3. Watch the **"Deploy Logs"** tab for progress

Build takes 3-5 minutes typically.

---

## ✅ Verify Deployment

### 1. Check Deploy Logs

Look for these success indicators:
```
✓ Embeddings initialized
✓ LLM initialized
✓ Translation system initialized
✓ Document Service initialized
Application startup complete.
```

### 2. Get Your URL

1. In Railway dashboard, find your service
2. Click on **"Settings"** tab
3. Scroll to **"Domains"** section
4. Click **"Generate Domain"**
5. Copy your URL: `https://your-app-name.up.railway.app`

### 3. Test Endpoints

#### Health Check
```bash
curl https://your-app-name.up.railway.app/health
```

Should return:
```json
{"status": "healthy", "service": "Bible Conversations"}
```

#### API Docs
Visit: `https://your-app-name.up.railway.app/docs`

#### Homepage
Visit: `https://your-app-name.up.railway.app`

---

## 🔧 Configure Widget for Production

### Update bible-widget.js

Open `static/bible-widget.js` and change line ~11:

**FROM:**
```javascript
apiBase: 'http://127.0.0.1:8009',
```

**TO:**
```javascript
apiBase: 'https://your-app-name.up.railway.app',
```

Then commit and push:
```bash
git add static/bible-widget.js
git commit -m "Update widget API URL for production"
git push
```

Railway will automatically redeploy!

---

## 📚 Upload Bible Translations

### Option 1: Using Admin Interface

1. Visit `https://your-app-name.up.railway.app/admin`
2. Create a new translation (e.g., "KJV", "NIV", "ESV")
3. Upload your Bible text files (.txt, .pdf, .docx)

### Option 2: Using API

```bash
# Create translation
curl -X POST https://your-app-name.up.railway.app/api/translations/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "translation_id": "kjv",
    "name": "King James Version",
    "description": "Classic English translation"
  }'

# Upload document
curl -X POST https://your-app-name.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@genesis.txt" \
  -F "translation_id=kjv"
```

---

## 🌐 Embed Widget on Your Website

Add this single line before `</body>`:

```html
<script src="https://your-app-name.up.railway.app/static/bible-widget.js"></script>
```

That's it! The Bible study assistant will appear on your page.

---

## 🔍 Monitoring & Troubleshooting

### View Logs

In Railway dashboard:
1. Click on your service
2. Go to **"Observability"** tab
3. View real-time logs

### Common Issues

#### Build Fails
- Check you have `Dockerfile` in root directory
- Verify `requirements.txt` is complete
- Check Railway build logs for specific errors

#### App Crashes on Startup
- Verify all environment variables are set
- Check API keys are valid
- Look for missing dependencies in logs

#### Widget Can't Connect
- Check CORS settings in `main.py`
- Verify Railway domain is generated
- Check browser console for errors

#### No Audio/Microphone Issues
- Widget must be on HTTPS (Railway provides this)
- Check browser microphone permissions
- Test with Chrome/Edge (best compatibility)

---

## 💰 Pricing

### Railway Costs

**Starter Plan: $5/month**
- $5 credit per month
- Usage-based after credit
- Bible app typically uses < $2/month with moderate traffic

**What Uses Credits:**
- CPU time (minimal for text processing)
- RAM (512MB-1GB typical)
- Network egress (audio streaming)

### API Costs

**Groq: FREE**
- STT (Whisper): Unlimited free
- LLM (Llama): Unlimited free

**OpenAI:**
- Embeddings: ~$0.0001 per 1000 tokens
- Very low cost for Bible text

**Edge TTS: FREE**
- Built into widget
- No API costs

**Total monthly cost: ~$5-7**

---

## 🔐 Security Best Practices

### 1. Protect Your API Keys

- Never commit `.env` to Git
- Use Railway's environment variables
- Rotate keys periodically

### 2. API Authentication

Your app uses Bearer token authentication:
```
Authorization: Bearer YOUR_API_KEY
```

Keep this key secret!

### 3. HTTPS Only

Railway provides automatic HTTPS - always use it.

### 4. Rate Limiting (Optional)

Consider adding rate limiting for production:
```bash
pip install slowapi
```

---

## 🚀 Next Steps

### 1. Custom Domain (Optional)

In Railway:
1. Settings → Domains
2. Add custom domain (e.g., `bible.yoursite.com`)
3. Follow DNS setup instructions

### 2. Add More Translations

Upload multiple Bible translations:
- KJV, NIV, ESV, NASB, etc.
- Different languages (Spanish, French, etc.)

### 3. Enhance Widget

- Customize colors in `bible-widget.js`
- Add your branding
- Modify voice settings

### 4. Monitor Usage

- Check Railway metrics
- Monitor API costs
- Track user conversations

---

## 📞 Support

### Railway Support
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

### Groq Support
- Docs: https://console.groq.com/docs
- Status: https://status.groq.com

---

## 🎉 You're Done!

Your Bible Conversations system is now live on Railway! 

Test it thoroughly, upload your translations, and embed the widget on your website.

**Need help?** Check the troubleshooting section or review the logs in Railway dashboard.