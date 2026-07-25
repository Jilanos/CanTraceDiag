FROM node:22-bookworm-slim AS build
WORKDIR /src
COPY . .
RUN node spikes/pwa-local-engine/build-browser.mjs

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/spikes/pwa-local-engine/site/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --spider -q http://127.0.0.1:8080/ || exit 1
