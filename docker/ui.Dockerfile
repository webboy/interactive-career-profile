FROM node:20-alpine AS build

WORKDIR /app

COPY apps/ui/package.json ./
RUN npm install

COPY apps/ui/ ./

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY apps/ui/server.js ./server.js
COPY --from=build /app/dist/spa ./dist/spa

ENV PORT=9000

EXPOSE 9000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:9000/health').then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
