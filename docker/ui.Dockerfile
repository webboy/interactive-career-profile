FROM node:20-alpine

WORKDIR /app

COPY apps/ui/package.json apps/ui/server.js ./
COPY apps/ui/public ./public

ENV PORT=9000

EXPOSE 9000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:9000/health').then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["npm", "start"]
