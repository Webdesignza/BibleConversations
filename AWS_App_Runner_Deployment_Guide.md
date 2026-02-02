# 🚀 AWS App Runner Deployment Guide
## Bible Conversations - Complete Setup Instructions

---

## 📋 Prerequisites

Before starting, you need:

1. **AWS Account** with free tier available
2. **GitHub Account** with your code
3. **API Keys:**
   - Groq API Key (free from console.groq.com)
   - OpenAI API Key (for embeddings only - minimal cost)
   - Your generated API_KEY for security

---

## 💰 Expected Costs (After Free Tier)

- **App Runner**: ~$5-8/month
  - 0.25 vCPU @ $0.064/vCPU-hour
  - 0.5 GB RAM @ $0.007/GB-hour
- **CloudWatch Logs**: ~$0.50/month (first 5GB free)
- **Data Transfer**: Usually free tier covers it

**Total: ~$5-8/month** 🎉

---

## 🔧 Step 1: Prepare Your Repository

### 1.1 Update Your Files

Replace these files in your project:

```bash
# Copy the optimized versions I provided
- Dockerfile (App Runner optimized)
- .dockerignore (App Runner optimized)
- main.py (with PORT environment variable support)
- apprunner.yaml (new file - App Runner configuration)
```

### 1.2 Commit and Push to GitHub

```bash
git add .
git commit -m "Optimize for AWS App Runner deployment"
git push origin main
```

---

## 🏗️ Step 2: AWS Setup

### 2.1 Login to AWS Console

1. Go to https://console.aws.amazon.com
2. Login with your AWS account
3. Select your preferred region (e.g., `us-east-1` for lowest cost)

### 2.2 Navigate to App Runner

1. In the search bar, type **"App Runner"**
2. Click on **AWS App Runner**

---

## 🚀 Step 3: Create App Runner Service

### 3.1 Start Service Creation

1. Click **"Create service"**
2. Choose **"Source code repository"**

### 3.2 Connect to GitHub

1. Click **"Add new"** under Repository
2. Choose **GitHub**
3. Click **"Install GitHub App"**
4. Authorize AWS Connector for GitHub
5. Select your **bible-conversations** repository
6. Choose branch: **main**
7. Click **Next**

### 3.3 Configure Build Settings

**Build settings:**
- Configuration source: **Use a configuration file**
- Configuration file: `apprunner.yaml`

**Deployment settings:**
- Deployment trigger: **Automatic**
  *(App Runner will auto-deploy on every git push)*

Click **Next**

### 3.4 Configure Service

**Service name:** `bible-conversations`

**Virtual CPU & memory:**
- CPU: **0.25 vCPU** (cheapest option)
- Memory: **0.5 GB**

**Environment variables** - Click "Add environment variable":

```
GROQ_API_KEY=gsk_your-actual-groq-key-here
OPENAI_API_KEY=sk-your-openai-key-here
API_KEY=your-generated-secure-api-key
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=llama-3.1-70b-versatile
GROQ_API_BASE=https://api.groq.com/openai/v1
CHROMA_DB_PATH=./chroma_db
RETRIEVAL_K=3
TEMPERATURE=0.7
UPLOAD_DIR=./uploads
```

**Port:** `8080` (default)

**Health check:**
- Protocol: **HTTP**
- Path: `/health`
- Interval: **20 seconds**
- Timeout: **5 seconds**
- Healthy threshold: **1**
- Unhealthy threshold: **5**

### 3.5 Security Settings

**Auto Scaling:**
- Min instances: **1**
- Max instances: **2** (for cost control)
- Max concurrency: **100** requests per instance

**Observability:**
- Enable AWS X-Ray tracing: **Yes** (optional, helps with debugging)

### 3.6 Review and Create

1. Review all settings
2. Click **"Create & deploy"**
3. Wait for deployment (5-10 minutes)

---

## ✅ Step 4: Verify Deployment

### 4.1 Check Deployment Status

In App Runner console:
- Status should show: **"Running"**
- Health: **"Healthy"**

### 4.2 Get Your App URL

1. In the App Runner service page, find **"Default domain"**
2. Your URL will be: `https://xxxxx.us-east-1.awsapprunner.com`

### 4.3 Test Endpoints

#### Health Check
```bash
curl https://your-app-url.awsapprunner.com/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Bible Conversations",
  "version": "2.0.0"
}
```

#### Homepage
Visit: `https://your-app-url.awsapprunner.com`

#### API Docs
Visit: `https://your-app-url.awsapprunner.com/docs`

---

## 🔧 Step 5: Update Widget for Production

### 5.1 Update Widget API URL

In your `static/bible-widget.js` (or wherever your widget is configured):

**Change:**
```javascript
apiBase: 'http://127.0.0.1:8009',
```

**To:**
```javascript
apiBase: 'https://your-app-url.awsapprunner.com',
```

### 5.2 Deploy the Update

```bash
git add static/bible-widget.js
git commit -m "Update widget API URL for AWS App Runner"
git push origin main
```

App Runner will automatically detect the change and redeploy! 🎉

---

## 📊 Step 6: Monitor Your Service

### 6.1 CloudWatch Logs

1. In App Runner console, click **"Logs"** tab
2. View application logs in real-time
3. Filter by log level: ERROR, WARNING, INFO

### 6.2 Metrics Dashboard

1. Click **"Metrics"** tab
2. Monitor:
   - Requests per minute
   - Response time (latency)
   - HTTP status codes
   - Active instances

### 6.3 Cost Monitoring

1. Go to **AWS Billing Dashboard**
2. Click **"Bills"**
3. Filter by service: **App Runner**
4. Set up billing alerts (recommended!)

---

## 🎛️ Optional: Custom Domain Setup

### 7.1 Add Custom Domain

If you want `bible.yourdomain.com` instead of the App Runner URL:

1. In App Runner service, click **"Custom domains"**
2. Click **"Link domain"**
3. Enter your domain: `bible.yourdomain.com`
4. App Runner will provide DNS records
5. Add these records in your domain registrar
6. Wait for verification (5-30 minutes)

**Cost:** Free with App Runner!

---

## 🔒 Step 7: Security Best Practices

### 7.1 Enable VPC Connector (Optional for Production)

For extra security, connect App Runner to a VPC:

1. Create VPC in AWS VPC console
2. In App Runner, go to **"Networking"**
3. Add VPC connector
4. This isolates your app from public internet

**Cost:** Free for VPC, ~$0.01/hour for NAT Gateway if needed

### 7.2 Set Up AWS WAF (Optional)

For DDoS protection and rate limiting:

1. Go to **AWS WAF** console
2. Create web ACL
3. Attach to App Runner service

**Cost:** ~$5/month base + $1 per million requests

---

## 🐛 Troubleshooting

### Build Failed

**Check:**
1. App Runner logs for error messages
2. Dockerfile syntax
3. requirements.txt dependencies
4. apprunner.yaml configuration

**Common fixes:**
- Increase build timeout in settings
- Check GitHub connection
- Verify branch name is correct

### Service Unhealthy

**Check:**
1. Health check endpoint returns 200
2. Port 8080 is exposed
3. Environment variables are set correctly
4. Application logs for startup errors

**Fix:**
```bash
# Test health check locally
curl https://your-app-url.awsapprunner.com/health
```

### High Costs

**Optimize:**
1. Reduce max instances to 1
2. Lower max concurrency
3. Check CloudWatch logs retention (reduce to 7 days)
4. Delete unused services

---

## 📚 Upload Bible Translations

### Using Admin Interface

1. Visit: `https://your-app-url.awsapprunner.com/admin`
2. Create translations (KJV, NIV, ESV)
3. Upload PDF/DOCX files for each translation

### Using API

```bash
# Create translation
curl -X POST https://your-app-url.awsapprunner.com/api/translations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "kjv",
    "name": "King James Version",
    "abbreviation": "KJV"
  }'

# Upload document
curl -X POST https://your-app-url.awsapprunner.com/api/documents/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@bible_kjv.pdf" \
  -F "translation_id=kjv"
```

---

## 🎉 You're Done!

Your Bible Conversations app is now live on AWS App Runner!

**Your URLs:**
- Homepage: `https://xxxxx.us-east-1.awsapprunner.com`
- Widget: `https://xxxxx.us-east-1.awsapprunner.com/static/bibleconversation.html`
- Admin: `https://xxxxx.us-east-1.awsapprunner.com/admin`
- API Docs: `https://xxxxx.us-east-1.awsapprunner.com/docs`

---

## 🔄 Continuous Deployment

Every time you push to GitHub:
1. App Runner detects the change
2. Builds new Docker image
3. Deploys automatically
4. Zero downtime deployment

---

## 📞 Support Resources

- **App Runner Docs:** https://docs.aws.amazon.com/apprunner
- **Pricing Calculator:** https://calculator.aws
- **AWS Support:** console.aws.amazon.com/support

---

## 💡 Next Steps

1. ✅ Set up custom domain
2. ✅ Configure CloudWatch alerts
3. ✅ Set billing alerts
4. ✅ Upload Bible translations
5. ✅ Test voice and text modes
6. ✅ Embed widget on your website

**Happy Bible studying! 📖✨**