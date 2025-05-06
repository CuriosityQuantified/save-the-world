
const express = require('express');
const next = require('next');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const PORT = process.env.PORT || 5000;

app.prepare().then(() => {
  const server = express();
  
  // Static file serving - before any other middleware
  server.use(express.static(path.join(process.cwd(), 'public')));
  
  // Media files route
  server.use('/media', express.static(path.join(process.cwd(), 'public', 'media')));
  
  // API routes - make sure these are before the Next.js handler
  server.use('/api', (req, res, next) => {
    if (req.url === '/') {
      return next();
    }
    return handle(req, res);
  });
  
  // Next.js static files handler
  server.use('/_next', express.static(path.join(process.cwd(), '.next')));
  
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
