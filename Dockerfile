# syntax=docker/dockerfile:1
# Next.js 16 + Prisma 7 + SQLite (better-sqlite3). Target: linux/amd64 or linux/arm64.
FROM node:22-bookworm-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends openssl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Native deps for better-sqlite3 compile
FROM base AS deps
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
# Build-time DB for prisma + Next data collection during `next build`
ENV DATABASE_URL="file:./prisma/dev.db"

RUN npx prisma generate \
  && npx prisma db push \
  && npm run db:seed \
  && npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 --ingroup nodejs nextjs \
  && mkdir -p /data \
  && chown nextjs:nodejs /data

# Standalone server + static assets (defines /app layout)
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Prisma client + SQLite native driver (not always fully traced into standalone)
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/@prisma ./node_modules/@prisma
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/better-sqlite3 ./node_modules/better-sqlite3

# Schema-only DB: copied to /data on first run (see docker-entrypoint.sh)
COPY --from=builder --chown=nextjs:nodejs /app/prisma/dev.db /app/db-init/dev.db

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# Windows checkouts may use CRLF; Linux shebang fails with "no such file or directory"
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

USER nextjs

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
