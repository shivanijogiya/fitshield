# ── Stage 1: build React app ──────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# VITE_API_BASE_URL can be overridden at build time via docker-compose build args
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ── Stage 2: serve with Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Custom Nginx config: serves SPA with history fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
