FROM node:20-alpine AS builder

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ ./
RUN npm run build

FROM nginx:1.27-alpine

ENV UI_PORT=3000
ENV API_BASE_URL=""
ENV API_PROXY_PASS=http://api:8000
ENV NGINX_ENVSUBST_FILTER="UI_PORT|API_PROXY_PASS"

COPY ui/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY ui/docker/40-write-env.sh /docker-entrypoint.d/40-write-env.sh
COPY --from=builder /app/ui/dist /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-write-env.sh

EXPOSE 3000
