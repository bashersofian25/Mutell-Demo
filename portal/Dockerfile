FROM node:22-alpine AS base
RUN apk add --no-cache libc6-compat

FROM base AS deps
WORKDIR /app
COPY portal/package.json portal/package-lock.json* ./portal/
WORKDIR /app/portal
RUN npm ci || npm install

FROM base AS builder
WORKDIR /app
ARG API_URL=http://localhost:8000
ENV API_URL=$API_URL
COPY --from=deps /app/portal/node_modules ./portal/node_modules
COPY portal/ ./portal/
WORKDIR /app/portal
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/portal/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/portal/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/portal/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
