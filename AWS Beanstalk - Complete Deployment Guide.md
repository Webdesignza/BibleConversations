# 🚀 AWS Elastic Beanstalk Deployment Guide
## Bible Conversations - Complete Setup

---

## 📋 What We're Deploying

**Your Bible Conversations app on AWS Elastic Beanstalk using Docker**
- Docker container for easy deployment
- t3.micro EC2 instance (free tier eligible)
- Application Load Balancer
- Auto-scaling (set to 1 instance for free tier)
- CloudWatch monitoring

---

## 📦 Part 1: Prepare Your Code

### Step 1.1: Create Required Files

Add these files to your project:

**File Structure:**
```
bible-conversations/
├── .ebextensions/
│   ├── 01_environment.config  (I created this)
│   └── 02_docker.config       (I created this)
├── app/
├── static/
├── Dockerfile                  (I created optimized version)
├── Dockerrun.aws.json         (I created this)
├── requirements.txt
├── .dockerignore
└── .gitignore
```

### Step 1.2: Create .ebextensions Directory

```bash
# In your project root
mkdir -p .ebextensions
```

Then create the two config files I provided:
- `.ebextensions/01_environment.config`
- `.ebextensions/02_docker.config`

### Step 1.3: Create Dockerrun.aws.json

Copy the `Dockerrun.aws.json` file I created to your project root.

### Step 1.4: Update .gitignore

Add to your `.gitignore`:
```
# Elastic Beanstalk
.elasticbeanstalk/
.ebextensions/
!.ebextensions/*.config

# AWS
.aws/
*.pem

# Environment
.env.local
```

### Step 1.5: Commit Everything

```bash
git add .ebextensions/ Dockerrun.aws.json Dockerfile
git commit -m "Add AWS Elastic Beanstalk configuration"
git push
```

---

## 🔑 Part 2: AWS Preparation

### Step 2.1: Install AWS EB CLI

The EB CLI makes deployment much easier.

**Windows (PowerShell):**
```powershell
pip install awsebcli --upgrade --user
```

**Mac:**
```bash
brew install awsebcli
```

**Linux:**
```bash
pip install awsebcli --upgrade --user
```

**Verify installation:**
```bash
eb --version
```

### Step 2.2: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Enter:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: us-east-1
# Default output format: json
```

**To get AWS credentials:**
1. Login to AWS Console
2. Click your name → Security Credentials
3. Access Keys → Create New Access Key
4. Download and save the keys

---

## 🏗️ Part 3: Initialize Elastic Beanstalk

### Step 3.1: Initialize EB in Your Project

```bash
# Navigate to your project
cd bible-conversations

# Initialize Elastic Beanstalk
eb init
```

**Answer the prompts:**

```
Select a default region: 
→ 1) us-east-1

Enter Application Name:
→ bible-conversations

It appears you are using Docker. Is this correct?
→ Y

Select a platform branch:
→ Docker running on 64bit Amazon Linux 2023

Do you want to set up SSH for your instances?
→ Y (recommended)

Select a keypair:
→ Create new keypair (if you don't have one)
```

This creates `.elasticbeanstalk/config.yml` file.

---

## 🚀 Part 4: Create Environment and Deploy

### Step 4.1: Create Elastic Beanstalk Environment

```bash
eb create bible-conversations-env
```

**Or with specific settings:**
```bash
eb create bible-conversations-env \
  --instance-type t3.micro \
  --single \
  --region us-east-1 \
  --platform "Docker running on 64bit Amazon Linux 2023"
```

**This will:**
1. Create EC2 instance (t3.micro)
2. Set up Application Load Balancer
3. Configure security groups
4. Deploy your application
5. Set up CloudWatch monitoring

**Time: ~10-15 minutes**

### Step 4.2: Watch Deployment Progress

```bash
# Watch events in real-time
eb events --follow

# Or check status
eb status
```

Look for:
```
Status: Ready
Health: Green
```

---

## 🔐 Part 5: Set Environment Variables

### Method 1: Via EB CLI (Recommended)

```bash
# Set one variable
eb setenv GROQ_API_KEY=gsk_your-key-here

# Set multiple variables
eb setenv \
  GROQ_API_KEY=gsk_your-groq-key \
  OPENAI_API_KEY=sk-your-openai-key \
  API_KEY=your-secure-api-key \
  EMBEDDING_MODEL=text-embedding-3-small \
  CHAT_MODEL=llama-3.1-70b-versatile \
  GROQ_API_BASE=https://api.groq.com/openai/v1 \
  CHROMA_DB_PATH=./chroma_db \
  RETRIEVAL_K=3 \
  TEMPERATURE=0.7 \
  UPLOAD_DIR=./uploads
```

### Method 2: Via AWS Console

1. Go to Elastic Beanstalk Console
2. Select your environment
3. Click **Configuration**
4. Under **Software**, click **Edit**
5. Scroll to **Environment properties**
6. Add all your variables
7. Click **Apply**

---

## 🌐 Part 6: Get Your Application URL

### Get URL via CLI:

```bash
eb status
```

Look for:
```
CNAME: bible-conversations-env.us-east-1.elasticbeanstalk.com
```

### Or via Console:

Your URL will be:
```
http://bible-conversations-env.us-east-1.elasticbeanstalk.com
```

---

## ✅ Part 7: Test Your Deployment

### Test Health Endpoint

```bash
curl http://bible-conversations-env.us-east-1.elasticbeanstalk.com/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Bible Conversations",
  "version": "2.0.0"
}
```

### Test Homepage

Visit in browser:
```
http://bible-conversations-env.us-east-1.elasticbeanstalk.com
```

### Test API Docs

```
http://bible-conversations-env.us-east-1.elasticbeanstalk.com/docs
```

---

## 🔄 Part 8: Update Your Application

### When You Make Code Changes:

```bash
# 1. Commit your changes
git add .
git commit -m "Update application"

# 2. Deploy to Elastic Beanstalk
eb deploy

# 3. Watch deployment
eb events --follow
```

**Deployment time: ~5-8 minutes**

---

## 📊 Part 9: Monitor Your Application

### View Logs

```bash
# Recent logs
eb logs

# Save logs to file
eb logs --all

# Stream logs in real-time
eb ssh
# Then: tail -f /var/log/eb-docker/containers/eb-current-app/*.log
```

### Check Health

```bash
# Quick status
eb status

# Detailed health
eb health

# Open in browser
eb health --refresh
```

### View Metrics

```bash
# Open CloudWatch dashboard
eb console
```

Or go to:
**Elastic Beanstalk Console → Your Environment → Monitoring**

---

## 💰 Part 10: Cost Management

### Free Tier Includes:

✅ **750 hours/month** of t2.micro or t3.micro (one instance 24/7)
✅ **750 hours/month** of Elastic Load Balancing
✅ **25 GB** of storage
✅ **15 GB** of bandwidth

**As long as you:**
- Use t3.micro instance
- Keep 1 instance only
- Stay within free tier limits

**Your cost: $0/month** (during free tier period)

### After Free Tier:

**Estimated costs:**
- t3.micro EC2: ~$7.50/month
- Application Load Balancer: ~$16/month (optional)
- **Total: ~$7.50-23/month**

**To minimize costs after free tier:**
```bash
# Disable load balancer (optional)
eb config

# Find and set:
# LoadBalancerType: None (for single instance)
```

---

## 🌐 Part 11: Custom Domain (Optional)

### Step 11.1: Get SSL Certificate

```bash
# Request certificate via AWS Certificate Manager
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

### Step 11.2: Configure Custom Domain

1. Go to **Elastic Beanstalk → Your Environment**
2. Click **Configuration → Load Balancer**
3. Add your SSL certificate
4. In your domain registrar, add CNAME:
   ```
   CNAME: www
   Value: bible-conversations-env.us-east-1.elasticbeanstalk.com
   ```

---

## 🔧 Part 12: Useful Commands

### Application Management

```bash
# Deploy new version
eb deploy

# Restart application
eb restart

# SSH into instance
eb ssh

# Open application in browser
eb open

# Terminate environment (careful!)
eb terminate bible-conversations-env
```

### Configuration

```bash
# View current config
eb config

# Save current config
eb config save bible-conversations-env --cfg production

# Use saved config
eb create new-env --cfg production
```

### Scaling

```bash
# Scale to 2 instances
eb scale 2

# Scale back to 1
eb scale 1
```

---

## 🐛 Part 13: Troubleshooting

### Problem: Environment Creation Failed

**Check:**
```bash
eb events
eb logs
```

**Common issues:**
- IAM roles not created (first-time setup)
- Port conflicts
- Invalid Dockerrun.aws.json

**Fix:**
```bash
# Delete failed environment
eb terminate

# Create again
eb create bible-conversations-env
```

### Problem: Health is Red/Yellow

**Check health:**
```bash
eb health --refresh
```

**Check logs:**
```bash
eb logs
```

**Common causes:**
- Health check failing (/health endpoint)
- Application not starting
- Port mismatch

**Fix:**
```bash
# SSH into instance
eb ssh

# Check Docker logs
sudo docker logs $(sudo docker ps -q)

# Check if app is running
curl localhost:8080/health
```

### Problem: Can't Connect to Application

**Check security group:**
1. Go to EC2 Console
2. Find your instance
3. Check Security Groups
4. Ensure port 80/443 is open

**Or via CLI:**
```bash
eb status
# Check "Health: Green"
```

### Problem: Environment Variables Not Set

**Verify:**
```bash
eb printenv
```

**Reset:**
```bash
eb setenv GROQ_API_KEY=gsk_your-new-key
```

---

## 📦 Part 14: Backup & Restore

### Create Application Version

```bash
# Elastic Beanstalk automatically versions
eb appversion
```

### Restore Previous Version

```bash
# List versions
eb appversion

# Deploy specific version
eb deploy --version v1
```

---

## 🎯 Quick Reference Commands

```bash
# Deploy
eb deploy

# Status
eb status

# Logs
eb logs

# Open in browser
eb open

# SSH
eb ssh

# Health
eb health

# Restart
eb restart

# Environment variables
eb setenv KEY=value
eb printenv
```

---

## 🎉 You're Done!

Your Bible Conversations app is now running on AWS Elastic Beanstalk!

**Your URLs:**
- Homepage: `http://bible-conversations-env.us-east-1.elasticbeanstalk.com`
- Admin: `http://bible-conversations-env.us-east-1.elasticbeanstalk.com/admin`
- API: `http://bible-conversations-env.us-east-1.elasticbeanstalk.com/docs`

**Commands you'll use regularly:**
```bash
eb deploy          # Deploy updates
eb logs            # View logs
eb health          # Check health
eb open            # Open in browser
```

---

## 📞 Support Resources

- **EB CLI Docs:** https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html
- **Docker Platform:** https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/docker.html
- **Troubleshooting:** https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/troubleshooting.html

**Happy deploying! 🚀**