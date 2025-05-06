
const express = require('express');
const next = require('next');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();

  // Serve static files from public directory
  server.use(express.static(path.join(process.cwd(), 'public')));
  
  // Handle Next.js specific routes first
  server.get('/_next/*', (req, res) => {
    return handle(req, res);
  });

  // Serve media files with explicit path
  server.use('/media', express.static(path.join(process.cwd(), 'public', 'media')));

  // API routes
  server.get('/api/*', (req, res) => {
    return handle(req, res);
  });

  // Handle all other routes with Next.js
  server.get('*', (req, res) => {
    return handle(req, res);
  });

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Ready on http://0.0.0.0:${PORT}`);
  });
});
