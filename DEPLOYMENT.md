# Deployment Guide

## Quick Start: Vercel + Railway

This guide walks you through deploying the frontend to Vercel and backend to Railway.

## Prerequisites

- GitHub repository with your code
- Accounts on [Vercel](https://vercel.com) and [Railway](https://railway.app)
- (Optional) OpenAI API key

## Step 1: Deploy Backend to Railway

### 1.1 Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"

### 1.2 Deploy from GitHub

1. Select "Deploy from GitHub repo"
2. Choose your repository
3. Railway will auto-detect Python

### 1.3 Configure Backend Service

1. In the service settings, set:
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. Railway will automatically:
   - Detect Python
   - Install dependencies from `requirements.txt`
   - Run the start command

### 1.4 Set Environment Variables

In Railway dashboard → Variables tab, add:

```
OPENAI_API_KEY=your-key-here  # Optional
USE_MOCK_MODE=true            # Set to true if no API key
OPENAI_MODEL=gpt-4o-mini      # Optional
```

### 1.5 Get Backend URL

1. Railway will generate a URL like: `https://your-app.up.railway.app`
2. Copy this URL - you'll need it for the frontend
3. Test it: Visit `https://your-app.up.railway.app/health` - should return `{"status":"ok"}`

## Step 2: Update Backend CORS

Update `backend/main.py` to allow your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",  # Will be your Vercel URL
        "http://localhost:3000"  # For local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: You can use `"*"` for development, but restrict to your Vercel domain for production.

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click "Add New Project"

### 3.2 Import Repository

1. Select your GitHub repository
2. Vercel will auto-detect Next.js

### 3.3 Configure Frontend

1. Set **Root Directory**: `frontend`
2. Framework Preset: Next.js (auto-detected)
3. Build settings (usually auto-detected):
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

### 3.4 Set Environment Variables

In Vercel dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

Replace with your actual Railway backend URL.

### 3.5 Deploy

1. Click "Deploy"
2. Vercel will build and deploy your frontend
3. You'll get a URL like: `https://your-app.vercel.app`

## Step 4: Update CORS with Actual Vercel URL

After deployment, update `backend/main.py` with your actual Vercel URL:

```python
allow_origins=[
    "https://your-actual-app.vercel.app",  # Your real Vercel URL
    "http://localhost:3000"
],
```

Then redeploy the backend (Railway auto-deploys on git push).

## Step 5: Test Deployment

1. Visit your Vercel URL
2. Try asking: "What is the latest version of Nextflow?"
3. Check browser console for any CORS errors
4. If errors, verify:
   - Backend URL is correct in Vercel env vars
   - CORS origins include your Vercel URL
   - Backend is running (check Railway logs)

## Troubleshooting

### CORS Errors

**Symptoms**: Browser console shows CORS errors

**Fix**:
1. Ensure backend CORS includes your Vercel URL
2. Check that `NEXT_PUBLIC_API_URL` is set correctly in Vercel
3. Verify backend is accessible: visit `https://your-backend/health`

### Backend Not Responding

**Symptoms**: Frontend shows connection errors

**Fix**:
1. Check Railway logs for errors
2. Verify `uvicorn` is installed: check `requirements.txt`
3. Ensure start command is correct: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables Not Working

**Symptoms**: App works locally but not in production

**Fix**:
1. Verify env vars are set in Railway/Vercel dashboards
2. For Vercel, ensure variables start with `NEXT_PUBLIC_` for client-side access
3. Redeploy after changing env vars

## Alternative: Render Instead of Railway

If you prefer Render:

1. Go to [render.com](https://render.com)
2. Create new "Web Service"
3. Connect GitHub repo
4. Configure:
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Render will give you a URL like: `https://your-app.onrender.com`

Use this URL in Vercel's `NEXT_PUBLIC_API_URL` instead of Railway's URL.

## Cost Estimate

- **Vercel**: Free tier includes generous limits
- **Railway**: Free tier with $5 credit/month (enough for demo)
- **Render**: Free tier available (may sleep after inactivity)

## Next Steps

- Add your deployed URLs to the README
- Test all the required questions from the spec
- Consider adding analytics (optional)
- Set up custom domain (optional)

