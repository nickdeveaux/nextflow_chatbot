# Vercel Deployment Guide

## Overview

This guide covers deploying the Nextflow Chat Assistant frontend to Vercel, with the backend deployed on Railway.

## Architecture

- **Frontend**: Deployed on Vercel
- **Backend**: Deployed on Railway at `https://nextflowchatbot-production.up.railway.app`
- **CORS**: Backend is configured to allow all Vercel domains (via regex pattern)

## Prerequisites

1. A [Vercel account](https://vercel.com) (free tier available)
2. Backend deployed on Railway (see Railway deployment guide)
3. GitHub repository with your code

## Deployment Steps

### 1. Prepare Frontend for Vercel

The frontend is already configured for Vercel deployment. Key files:
- `frontend/next.config.js` - Next.js configuration (standalone output removed for Vercel)
- `frontend/package.json` - Dependencies and build scripts
- `vercel.json` - Vercel configuration (optional, Vercel auto-detects Next.js)

### 2. Set Environment Variables in Vercel

**IMPORTANT**: Set this environment variable in Vercel before deploying:

In your Vercel project settings → Environment Variables:

**Required:**
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://nextflowchatbot-production.up.railway.app`
- **Environment**: Production, Preview, Development (select all)

**Optional:**
- **Name**: `NEXT_PUBLIC_LOADING_MESSAGES`
- **Value**: `Thinking,Pondering,Considering`
- **Environment**: Production, Preview, Development (select all)

### 3. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend` ⚠️ **IMPORTANT**: Set this to `frontend`
   - **Build Command**: `npm run build` (default, or leave empty for auto-detection)
   - **Output Directory**: `.next` (default, or leave empty for auto-detection)
   - **Install Command**: `npm install` (default)
5. **Add environment variable** (before first deploy):
   - Click "Environment Variables"
   - Add `NEXT_PUBLIC_API_URL` = `https://nextflowchatbot-production.up.railway.app`
   - Select all environments (Production, Preview, Development)
6. Click "Deploy"

#### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project root (not frontend directory)
cd /path/to/nextflow_chatbot

# Deploy (Vercel will use rootDirectory from vercel.json)
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No (first time) or Yes (updates)
# - What's your project's name? nextflow-chatbot-frontend
# - In which directory is your code located? ./frontend
# - Override settings? No

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://nextflowchatbot-production.up.railway.app
# Select: Production, Preview, Development (all)

# Redeploy with environment variable
vercel --prod
```

**Note**: The `vercel.json` file configures `rootDirectory: "frontend"`, so Vercel will automatically use the frontend directory.

### 4. Verify Deployment

1. Visit your Vercel deployment URL (e.g., `https://your-project.vercel.app`)
2. Check browser console for any errors
3. Test the chat functionality
4. Verify backend connectivity by checking network requests

## Configuration

### Environment Variables

Set in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://nextflowchatbot-production.up.railway.app` | Backend API URL (required) |
| `NEXT_PUBLIC_LOADING_MESSAGES` | `Thinking,Pondering,...` | Custom loading messages (optional) |

### CORS Configuration

The backend is already configured to allow Vercel domains:
- `allow_vercel_domains: true` in `config.yaml`
- Regex pattern: `https?://.*\.vercel\.app.*`

This means any Vercel deployment (production, preview, development) will work automatically.

## Troubleshooting

### Frontend can't reach backend

1. **Check environment variable**: Ensure `NEXT_PUBLIC_API_URL` is set correctly in Vercel
2. **Check CORS**: Verify backend allows your Vercel domain
3. **Check backend health**: Test `https://nextflowchatbot-production.up.railway.app/health`
4. **Check browser console**: Look for CORS or network errors

### Build failures

1. **Check Node version**: Vercel uses Node 18.x by default (compatible)
2. **Check dependencies**: Ensure `package.json` has all required dependencies
3. **Check build logs**: Review Vercel build logs for specific errors

### CORS errors

1. **Verify backend CORS config**: Check `config.yaml` → `cors.allow_vercel_domains`
2. **Check backend logs**: Verify CORS middleware is working
3. **Test backend directly**: Use `curl` to test CORS headers

## Production URLs

- **Frontend (Vercel)**: `https://your-project.vercel.app`
- **Backend (Railway)**: `https://nextflowchatbot-production.up.railway.app`

## Local Development

For local development, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then run:
```bash
cd frontend
npm run dev
```

## Continuous Deployment

Vercel automatically deploys on every push to your main branch:
- **Production**: Deploys from `main` branch
- **Preview**: Deploys from pull requests and other branches

Each deployment gets a unique URL, and all will work with your Railway backend thanks to the Vercel domain regex in CORS config.

