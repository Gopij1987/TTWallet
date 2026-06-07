#!/usr/bin/env node

/**
 * TT Dashboard Startup Script
 * Launches both backend and frontend servers with proper logging
 * Run: npm run start:all (from project root after npm install)
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset', prefix = '') {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${colors[color]}[${timestamp}] ${prefix}${message}${colors.reset}`);
}

function startServer(name, folder, command, args, color) {
  const folderPath = path.join(__dirname, folder);
  
  if (!fs.existsSync(folderPath)) {
    log(`${folder} folder not found!`, 'red', '❌ ');
    return null;
  }

  log(`Starting ${name}...`, color, '🚀 ');

  const process = spawn(command, args, {
    cwd: folderPath,
    stdio: 'inherit',
    shell: true,
  });

  process.on('error', (err) => {
    log(`Failed to start ${name}: ${err.message}`, 'red', '❌ ');
  });

  process.on('close', (code) => {
    if (code !== 0) {
      log(`${name} exited with code ${code}`, 'red', '⚠️  ');
    }
  });

  return process;
}

function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║          🚀 TT DASHBOARD STARTUP                                   ║
║                                                                    ║
║  Starting both Backend and Frontend servers...                    ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
  `);

  // Start backend
  const backend = startServer(
    'Backend API',
    'backend',
    'npm',
    ['run', 'dev'],
    'blue'
  );

  // Small delay before starting frontend
  setTimeout(() => {
    // Start frontend
    const frontend = startServer(
      'Frontend React',
      'frontend',
      'npm',
      ['run', 'dev'],
      'cyan'
    );

    // Print helpful info
    setTimeout(() => {
      console.log(`
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  ✅ Both servers are starting...                                   ║
║                                                                    ║
║  📊 Dashboard:    http://localhost:3000                           ║
║  🔌 API Backend:  http://localhost:5000/api/health               ║
║                                                                    ║
║  Press Ctrl+C to stop both servers                               ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
      `);
    }, 1000);

    // Handle Ctrl+C gracefully
    process.on('SIGINT', () => {
      log('Shutting down...', 'yellow', '🛑 ');
      
      if (backend) backend.kill();
      if (frontend) frontend.kill();
      
      setTimeout(() => {
        log('Both servers stopped', 'green', '✅ ');
        process.exit(0);
      }, 500);
    });
  }, 2000);
}

main();
