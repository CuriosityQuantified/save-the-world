/**
 * Backend Port Detection Utility
 * 
 * This utility helps the frontend discover which port the backend is running on.
 * The backend can run on any port from 8000-8100 when port 8000 is busy.
 */

const fs = require('fs');
const path = require('path');

// Cache the discovered port for performance
let cachedPort = null;
let lastCheck = 0;
const CACHE_DURATION = 30000; // 30 seconds

/**
 * Try to read the backend port from the .backend_port file
 * @returns {number|null} The port number or null if file doesn't exist
 */
function readPortFile() {
  try {
    const portFilePath = path.join(process.cwd(), '.backend_port');
    if (fs.existsSync(portFilePath)) {
      const port = parseInt(fs.readFileSync(portFilePath, 'utf8').trim(), 10);
      if (!isNaN(port) && port >= 8000 && port <= 8100) {
        return port;
      }
    }
  } catch (error) {
    console.error('Error reading .backend_port file:', error);
  }
  return null;
}

/**
 * Check if a backend is running on a specific port
 * @param {number} port - The port to check
 * @returns {Promise<boolean>} True if backend is running on this port
 */
async function checkPort(port) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1000); // 1 second timeout
    
    const response = await fetch(`http://localhost:${port}/docs`, {
      method: 'HEAD',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Probe ports 8000-8100 to find where the backend is running
 * @returns {Promise<number|null>} The port number or null if not found
 */
async function probeForBackend() {
  // Check common ports first for better performance
  const commonPorts = [8000, 8001, 8002, 8003];
  
  for (const port of commonPorts) {
    if (await checkPort(port)) {
      console.log(`Backend found on port ${port}`);
      return port;
    }
  }
  
  // If not found in common ports, check the rest
  for (let port = 8004; port <= 8100; port++) {
    if (await checkPort(port)) {
      console.log(`Backend found on port ${port}`);
      return port;
    }
  }
  
  return null;
}

/**
 * Get the backend port, with caching and multiple detection methods
 * @returns {Promise<number>} The backend port (defaults to 8000 if not found)
 */
async function getBackendPort() {
  // Check cache first
  const now = Date.now();
  if (cachedPort && (now - lastCheck) < CACHE_DURATION) {
    return cachedPort;
  }
  
  // Try to read from file first
  const filePort = readPortFile();
  if (filePort) {
    cachedPort = filePort;
    lastCheck = now;
    return filePort;
  }
  
  // If file doesn't exist, probe for backend
  const probedPort = await probeForBackend();
  if (probedPort) {
    cachedPort = probedPort;
    lastCheck = now;
    return probedPort;
  }
  
  // Default to 8000 if nothing found
  console.warn('Backend not detected, defaulting to port 8000');
  cachedPort = 8000;
  lastCheck = now;
  return 8000;
}

/**
 * Get the backend port synchronously (for Next.js config)
 * This only reads from file and doesn't probe
 * @returns {number} The backend port (defaults to 8000 if not found)
 */
function getBackendPortSync() {
  const filePort = readPortFile();
  return filePort || 8000;
}

// Export for CommonJS (Next.js config and API routes)
module.exports = {
  getBackendPort,
  getBackendPortSync,
  checkPort
};