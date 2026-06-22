import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PORT = Number(process.env.PORT || 9000);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.join(__dirname, "dist", "spa");
const INDEX_FILE = path.join(DIST_DIR, "index.html");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

function sendFile(response, filePath) {
  const extension = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[extension] || "application/octet-stream";
  fs.readFile(filePath, (error, data) => {
    if (error) {
      response.writeHead(404, { "Content-Type": "text/plain" });
      response.end("Not found");
      return;
    }
    response.writeHead(200, { "Content-Type": contentType });
    response.end(data);
  });
}

const server = http.createServer((request, response) => {
  const url = request.url?.split("?")[0] || "/";

  if (url === "/health") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ status: "ok", service: "ui" }));
    return;
  }

  if (url === "/" || url === "/index.html") {
    sendFile(response, INDEX_FILE);
    return;
  }

  const assetPath = path.join(DIST_DIR, url);
  if (assetPath.startsWith(DIST_DIR) && fs.existsSync(assetPath) && fs.statSync(assetPath).isFile()) {
    sendFile(response, assetPath);
    return;
  }

  sendFile(response, INDEX_FILE);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`UI server listening on ${PORT}`);
});
