
const express = require('express');
const next = require('next');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const PORT = process.env.PORT || 5000;

app.prepare().then(() => {
  const server = express();

  // Static files and media handling
  server.use(express.static('public'));
  server.use('/media', express.static(path.join(__dirname, 'public/media')));
  server.use('/_next', express.static(path.join(__dirname, '.next')));

  // API routes
  server.use('/api', (req, res) => {
    return handle(req, res);
  });

  // Let Next.js handle all other routes
  server.get('*', (req, res) => {
    return handle(req, res);
  });

  server.listen(PORT, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Ready on http://0.0.0.0:${PORT}`);
  });
}).catch((err) => {
  console.error('Error starting server:', err);
  process.exit(1);
});
