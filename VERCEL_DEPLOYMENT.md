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

### CORS Configuration

The backend is already configured to allow Vercel domains:
- `allow_vercel_domains: true` in `config.yaml`
- Regex pattern: `https?://.*\.vercel\.app.*`

This means any Vercel deployment (production, preview, development) will work automatically.


