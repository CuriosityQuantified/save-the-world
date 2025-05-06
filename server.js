
const express = require('express');
const next = require('next');
const path = require('path');
const { Client } = require('@replit/object-storage');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const PORT = process.env.PORT || 5000;

// Initialize Replit Object Storage client
const client = new Client();

app.prepare().then(() => {
  const server = express();

  // Serve static files from public directory
  server.use(express.static('public'));

  // Handle media file requests
  server.get('/media/:type/:filename', async (req, res) => {
    try {
      const { type, filename } = req.params;
      const objectKey = `${type}/${filename}`;
      
      const data = await client.download_as_bytes(objectKey);
      
      // Set appropriate content type
      const contentType = type === 'audio' ? 'audio/mpeg' : 'video/mp4';
      res.setHeader('Content-Type', contentType);
      res.send(data);
    } catch (error) {
      console.error('Error serving media:', error);
      res.status(404).send('Media not found');
    }
  });

  // API routes
  server.use('/api', (req, res) => {
    return handle(req, res);
  });

  // Let Next.js handle all other routes
  server.all('*', (req, res) => {
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
