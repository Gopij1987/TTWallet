#!/usr/bin/env node

/**
 * TT Dashboard Setup Script
 * Checks system prerequisites and project setup status
 * Run: node setup.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function header(text) {
  console.log('\n' + '='.repeat(70));
  log(text, 'cyan');
  console.log('='.repeat(70) + '\n');
}

function success(text) {
  log(`✅ ${text}`, 'green');
}

function error(text) {
  log(`❌ ${text}`, 'red');
}

function warning(text) {
  log(`⚠️  ${text}`, 'yellow');
}

function info(text) {
  log(`ℹ️  ${text}`, 'blue');
}

let allChecks = [];

// Check Node.js version
function checkNode() {
  header('1. Checking Node.js');
  try {
    const version = execSync('node -v', { encoding: 'utf8' }).trim();
    const versionNumber = parseFloat(version.substring(1));
    
    if (versionNumber >= 14) {
      success(`Node.js ${version} installed`);
      allChecks.push(true);
    } else {
      error(`Node.js ${version} is too old (need 14+)`);
      allChecks.push(false);
    }
  } catch (e) {
    error('Node.js not found. Install from https://nodejs.org/');
    allChecks.push(false);
  }
}

// Check npm version
function checkNpm() {
  header('2. Checking npm');
  try {
    const version = execSync('npm -v', { encoding: 'utf8' }).trim();
    success(`npm ${version} installed`);
    allChecks.push(true);
  } catch (e) {
    error('npm not found');
    allChecks.push(false);
  }
}

// Check backend structure
function checkBackend() {
  header('3. Checking Backend Folder Structure');
  const backendPath = path.join(__dirname, 'backend');
  const requiredFiles = ['server.js', 'db.js', 'package.json'];
  const requiredDirs = ['routes'];

  let backendOk = true;

  for (const file of requiredFiles) {
    const filePath = path.join(backendPath, file);
    if (fs.existsSync(filePath)) {
      success(`Found: ${file}`);
    } else {
      error(`Missing: ${file}`);
      backendOk = false;
    }
  }

  for (const dir of requiredDirs) {
    const dirPath = path.join(backendPath, dir);
    if (fs.existsSync(dirPath)) {
      success(`Found directory: ${dir}/`);
    } else {
      error(`Missing directory: ${dir}/`);
      backendOk = false;
    }
  }

  allChecks.push(backendOk);
}

// Check backend .env
function checkBackendEnv() {
  header('4. Checking Backend Configuration (.env)');
  const envPath = path.join(__dirname, 'backend', '.env');
  const envExamplePath = path.join(__dirname, 'backend', '.env.example');

  if (fs.existsSync(envPath)) {
    success('.env file exists');
    
    // Check if it has required values
    const envContent = fs.readFileSync(envPath, 'utf8');
    const hasDb = envContent.includes('DB_HOST');
    const hasCookies = envContent.includes('TT_COOKIES_B64');
    
    if (hasDb && hasCookies) {
      success('Environment variables appear to be configured');
      allChecks.push(true);
    } else {
      warning('.env exists but missing some variables');
      warning('Required: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, TT_COOKIES_B64_*');
      allChecks.push(false);
    }
  } else {
    warning('.env file not found');
    if (fs.existsSync(envExamplePath)) {
      info('You can create it from .env.example:');
      info('  cp backend/.env.example backend/.env');
      info('  Then edit and fill in your credentials');
    }
    allChecks.push(false);
  }
}

// Check backend node_modules
function checkBackendModules() {
  header('5. Checking Backend Dependencies');
  const backendModulesPath = path.join(__dirname, 'backend', 'node_modules');

  if (fs.existsSync(backendModulesPath)) {
    success('Backend node_modules found');
    allChecks.push(true);
  } else {
    warning('Backend node_modules not found');
    info('Run: cd backend && npm install');
    allChecks.push(false);
  }
}

// Check frontend structure
function checkFrontend() {
  header('6. Checking Frontend Folder Structure');
  const frontendPath = path.join(__dirname, 'frontend');
  const requiredFiles = ['package.json', 'index.html', 'vite.config.js'];
  const requiredDirs = ['src'];

  let frontendOk = true;

  for (const file of requiredFiles) {
    const filePath = path.join(frontendPath, file);
    if (fs.existsSync(filePath)) {
      success(`Found: ${file}`);
    } else {
      error(`Missing: ${file}`);
      frontendOk = false;
    }
  }

  for (const dir of requiredDirs) {
    const dirPath = path.join(frontendPath, dir);
    if (fs.existsSync(dirPath)) {
      success(`Found directory: ${dir}/`);
    } else {
      error(`Missing directory: ${dir}/`);
      frontendOk = false;
    }
  }

  allChecks.push(frontendOk);
}

// Check frontend node_modules
function checkFrontendModules() {
  header('7. Checking Frontend Dependencies');
  const frontendModulesPath = path.join(__dirname, 'frontend', 'node_modules');

  if (fs.existsSync(frontendModulesPath)) {
    success('Frontend node_modules found');
    allChecks.push(true);
  } else {
    warning('Frontend node_modules not found');
    info('Run: cd frontend && npm install');
    allChecks.push(false);
  }
}

// Check PostgreSQL
function checkPostgres() {
  header('8. Checking PostgreSQL Connection');
  try {
    // Try to connect using psql if available
    execSync('psql --version', { encoding: 'utf8', stdio: 'pipe' });
    success('PostgreSQL client (psql) found');
    
    // Try to connect to localhost
    try {
      execSync('psql -h localhost -U postgres -d alphametrix -c "SELECT 1" 2>/dev/null', {
        encoding: 'utf8',
        stdio: 'pipe'
      });
      success('Connected to alphametrix database');
      allChecks.push(true);
    } catch (e) {
      warning('Could not connect to alphametrix database');
      info('Make sure PostgreSQL is running and database exists');
      info('To create database: createdb alphametrix');
      allChecks.push(false);
    }
  } catch (e) {
    warning('PostgreSQL client (psql) not found');
    info('PostgreSQL may still be running (checked at runtime)');
    allChecks.push(false);
  }
}

// Summary
function printSummary() {
  header('SETUP STATUS SUMMARY');
  
  const passed = allChecks.filter(c => c).length;
  const total = allChecks.length;
  const percentage = Math.round((passed / total) * 100);

  log(`Checks passed: ${passed}/${total} (${percentage}%)\n`);

  if (percentage === 100) {
    success('All checks passed! Ready to start.');
    log('\nNext steps:');
    log('  1. Terminal 1: cd backend && npm run dev');
    log('  2. Terminal 2: cd frontend && npm run dev');
    log('  3. Visit: http://localhost:3000\n');
  } else if (percentage >= 70) {
    warning('Most checks passed. Some setup steps remaining.');
    log('\nNext steps:');
    log('  1. Install dependencies (see above for commands)');
    log('  2. Configure .env in backend/');
    log('  3. Verify PostgreSQL is running');
    log('  4. Re-run this script to verify\n');
  } else {
    error('Several setup steps need attention (see above)');
    log('\nFollow the setup instructions in QUICKSTART.md\n');
  }

  console.log('='.repeat(70) + '\n');
}

// Run all checks
function runAll() {
  header('🚀 TT DASHBOARD SETUP CHECK');
  log('Verifying project setup...\n');

  checkNode();
  checkNpm();
  checkBackend();
  checkBackendEnv();
  checkBackendModules();
  checkFrontend();
  checkFrontendModules();
  checkPostgres();

  printSummary();
}

// Main
runAll();
