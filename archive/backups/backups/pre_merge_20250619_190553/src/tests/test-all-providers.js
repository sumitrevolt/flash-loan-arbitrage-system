require('dotenv').config();

console.log('🔄 Testing Multi-Provider LangChain Integration');
console.log('================================================');

// Test all providers to see which ones work
const providers = [
    { name: 'OpenAI', envVar: 'OPENAI_API_KEY', model: 'gpt-4' },
    { name: 'GitHub', envVar: 'GITHUB_TOKEN', model: 'gpt-4o' },
    { name: 'Anthropic', envVar: 'ANTHROPIC_API_KEY', model: 'claude-3-5-sonnet-20241022' }
];

console.log('🔍 Checking available providers:');
providers.forEach(provider => {
    const hasKey = !!process.env[provider.envVar];
    const isGithub = provider.name === 'GitHub';
    const githubNote = isGithub ? ' (needs models permission)' : '';
    
    console.log(`${hasKey ? '✅' : '❌'} ${provider.name}: ${hasKey ? 'Key present' : 'No key'}${githubNote}`);
});

console.log(`\n🎯 Current AI_PROVIDER: ${process.env.AI_PROVIDER || 'not set'}`);

// Suggest working configuration
console.log('\n💡 Quick Start Options:');
console.log('1. Fix GitHub token with models permission (recommended)');
console.log('2. Use OpenAI temporarily: Set AI_PROVIDER=openai in .env');
console.log('3. Use Anthropic: Set AI_PROVIDER=anthropic in .env');

console.log('\n🚀 Testing LangChain demo with current settings...');

// Import and run the LangChain demo
try {
    const { spawn } = require('child_process');
    const demo = spawn('npx', ['ts-node', 'demo-langchain.ts'], {
        stdio: 'inherit',
        shell: true
    });
    
    demo.on('close', (code) => {
        console.log(`\n📊 Demo completed with exit code: ${code}`);
    });
} catch (error) {
    console.error('❌ Error running demo:', error.message);
}
