/**
 * API endpoint to discover the backend port
 * Returns the port number where the backend is currently running
 */

const { getBackendPort } = require('../../utils/backendPort');

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const port = await getBackendPort();
    
    // Set CORS headers to allow frontend access
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    res.setHeader('Cache-Control', 's-maxage=10, stale-while-revalidate');
    
    return res.status(200).json({ 
      port, 
      url: `http://localhost:${port}`,
      wsUrl: `ws://localhost:${port}`
    });
  } catch (error) {
    console.error('Error detecting backend port:', error);
    
    // Return default port on error
    return res.status(200).json({ 
      port: 8000, 
      url: 'http://localhost:8000',
      wsUrl: 'ws://localhost:8000',
      error: 'Failed to detect backend port, using default'
    });
  }
}