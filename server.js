const express = require('express');
const next = require('next');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = express();

  // Set up static middleware for media files
  server.use('/media', express.static(path.join(__dirname, 'media')));
  
  // For videos specifically - ensuring they're properly served
  server.use('/media/videos', express.static(path.join(__dirname, 'media/videos')));
  
  // For audio files
  server.use('/media/audio', express.static(path.join(__dirname, 'media/audio')));

  // Handle all other routes with Next.js
  server.all('*', (req, res) => {
    return handle(req, res);
  });

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${PORT}`);
    console.log(`> Media files served from ${path.join(__dirname, 'media')}`);
  });
}); 