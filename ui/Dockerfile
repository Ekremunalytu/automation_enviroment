FROM node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293 AS builder

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ ./
RUN npm run build

FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10

ENV UI_PORT=3000
ENV API_BASE_URL=""
ENV API_PROXY_PASS=http://api:8000
ENV NGINX_ENVSUBST_FILTER="UI_PORT|API_PROXY_PASS"

COPY ui/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY ui/docker/40-write-env.sh /docker-entrypoint.d/40-write-env.sh
COPY --from=builder /app/ui/dist /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-write-env.sh

EXPOSE 3000
