#!/usr/bin/env node

// Test filesystem MCP server connection
const { spawn } = require('child_process');
const path = require('path');

console.log('Testing filesystem MCP server...');

const workspaceDir = 'c:/Users/Ratanshila/Documents/flash loan';
console.log(`Testing with workspace: ${workspaceDir}`);

// Test npx command
const child = spawn('npx', [
  '-y',
  '@modelcontextprotocol/server-filesystem',
  workspaceDir
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let stdout = '';
let stderr = '';

child.stdout.on('data', (data) => {
  stdout += data.toString();
});

child.stderr.on('data', (data) => {
  stderr += data.toString();
});

child.on('close', (code) => {
  console.log(`\nProcess exited with code: ${code}`);
  
  if (stdout) {
    console.log('\nSTDOUT:');
    console.log(stdout);
  }
  
  if (stderr) {
    console.log('\nSTDERR:');
    console.log(stderr);
  }
});

// Send a simple MCP request
setTimeout(() => {
  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {}
    }
  };
  
  console.log('\nSending initialize request...');
  child.stdin.write(JSON.stringify(initRequest) + '\n');
  
  setTimeout(() => {
    child.kill();
  }, 2000);
}, 500);