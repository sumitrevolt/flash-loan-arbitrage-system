require('dotenv').config();

console.log('🔍 Environment Debug Tool');
console.log('=========================');

console.log('Current working directory:', process.cwd());
console.log('Environment variables:');
console.log('GITHUB_TOKEN length:', process.env.GITHUB_TOKEN?.length || 'undefined');
console.log('GITHUB_TOKEN value:', process.env.GITHUB_TOKEN || 'undefined');
console.log('AI_PROVIDER:', process.env.AI_PROVIDER || 'undefined');

// Check if .env file exists and read it directly
const fs = require('fs');
const path = require('path');

const envPath = path.join(process.cwd(), '.env');
console.log('\n📁 .env file path:', envPath);
console.log('📁 .env file exists:', fs.existsSync(envPath));

if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const lines = envContent.split('\n');
    const githubTokenLine = lines.find(line => line.startsWith('GITHUB_TOKEN='));
    console.log('📝 GITHUB_TOKEN line in .env:', githubTokenLine);
}
