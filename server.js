const next = require('next');
const { createServer } = require('http');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();
const port = process.env.PORT || 5000;

app.prepare().then(() => {
  createServer((req, res) => {
    handle(req, res);
  }).listen(port, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Ready on http://0.0.0.0:${port}`);
  });
}).catch(err => {
  console.error('Error starting server:', err);
  process.exit(1);
});