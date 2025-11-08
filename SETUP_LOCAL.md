# Local Development Setup

## Problem: Frontend can't reach backend when accessed via IP

If you're accessing the frontend via your IP address (e.g., `http://12.202.180.110:3000`), but the frontend is configured to call `http://localhost:8000`, the browser won't be able to reach the backend.

## Solution

### Option 1: Run Backend Locally (Same Machine)

1. **Start the backend** (must bind to 0.0.0.0, not just localhost):
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Set frontend environment variable** before starting frontend:
   ```bash
   cd frontend
   export NEXT_PUBLIC_API_URL=http://12.202.180.110:8000
   npm run dev
   ```

   Or create a `.env.local` file in the frontend directory:
   ```
   NEXT_PUBLIC_API_URL=http://12.202.180.110:8000
   ```

3. **Verify backend is accessible**:
   ```bash
   curl http://12.202.180.110:8000/health
   ```

### Option 2: Use Railway Backend

1. **Get your Railway backend URL** (e.g., `https://your-backend.railway.app`)

2. **Set frontend environment variable**:
   ```bash
   cd frontend
   export NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   npm run dev
   ```

   Or in `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

### Option 3: Access Frontend via localhost

If you access the frontend via `http://localhost:3000`, the default `http://localhost:8000` will work fine.

## Quick Test

1. Check if backend is running:
   ```bash
   curl http://localhost:8000/health
   # or
   curl http://12.202.180.110:8000/health
   ```

2. Check CORS configuration in `config.yaml` - your IP should be in `cors.allowed_origins`

3. Check browser console for CORS errors - they'll show the exact issue

## Troubleshooting

- **CORS errors**: Make sure your frontend origin (e.g., `http://12.202.180.110:3000`) is in `config.yaml` → `cors.allowed_origins`
- **Connection refused**: Backend isn't running or isn't binding to 0.0.0.0
- **404 errors**: Backend is running but on a different port or path

