const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = Number(process.env.PORT || 9000);
const PUBLIC_DIR = path.join(__dirname, "public");

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", service: "ui" }));
    return;
  }

  if (req.url === "/" || req.url === "/index.html") {
    fs.readFile(path.join(PUBLIC_DIR, "index.html"), (error, data) => {
      if (error) {
        res.writeHead(500, { "Content-Type": "text/plain" });
        res.end("Failed to load placeholder page");
        return;
      }

      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(data);
    });
    return;
  }

  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("Not found");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`UI placeholder listening on ${PORT}`);
});
