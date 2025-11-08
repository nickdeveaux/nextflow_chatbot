FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Copy config files and sync script (assumes build context is project root)
COPY config.yaml ./config.yaml
COPY scripts/sync-config.js ./scripts/sync-config.js
# Run sync-config before build
RUN node scripts/sync-config.js
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Use PORT environment variable for Railway compatibility
EXPOSE ${PORT:-3000}

ENV PORT=${PORT:-3000}

CMD ["node", "server.js"]

