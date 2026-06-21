FROM python:3.12-slim

WORKDIR /app

COPY apps/mcp /app

ENV PORT=8100

EXPOSE 8100

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health')"

CMD ["python", "app/server.py"]
