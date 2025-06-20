const https = require('https');
require('dotenv').config();

console.log('🔍 GitHub Token Diagnostic Tool');
console.log('================================');

const token = process.env.GITHUB_TOKEN;

if (!token) {
    console.log('❌ GITHUB_TOKEN not found in environment');
    process.exit(1);
}

console.log(`🔑 Token format: ${token.substring(0, 20)}...`);
console.log(`📏 Token length: ${token.length}`);
console.log(`✅ Token prefix: ${token.startsWith('github_pat_') ? 'Correct (github_pat_)' : 'Incorrect - should start with github_pat_'}`);

// Check if token has the right format
if (!token.startsWith('github_pat_')) {
    console.log('❌ Token format error: GitHub Personal Access Tokens should start with "github_pat_"');
    console.log('📋 Please generate a new token at: https://github.com/settings/tokens');
    process.exit(1);
}

// Test basic GitHub API access
console.log('\n🧪 Testing basic GitHub API access...');

const options = {
    hostname: 'api.github.com',
    path: '/user',
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'User-Agent': 'Flash-Loan-Arbitrage-System',
        'Accept': 'application/vnd.github.v3+json'
    }
};

const req = https.request(options, (res) => {
    let data = '';
    
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        console.log(`📊 Status Code: ${res.statusCode}`);
        
        if (res.statusCode === 200) {
            const user = JSON.parse(data);
            console.log(`✅ Token valid! User: ${user.login}`);
            console.log(`👤 Account type: ${user.type}`);
            console.log(`📅 Account created: ${user.created_at}`);
            
            // Now test GitHub Models API
            testGitHubModels();
        } else {
            console.log(`❌ GitHub API Error: ${res.statusCode}`);
            console.log(`📝 Response: ${data}`);
            
            if (res.statusCode === 401) {
                console.log('\n🔧 Troubleshooting steps:');
                console.log('1. Verify token is correctly copied from GitHub');
                console.log('2. Check token hasn\'t expired');
                console.log('3. Ensure token has required scopes');
                console.log('4. Generate new token at: https://github.com/settings/tokens');
            }
        }
    });
});

req.on('error', (err) => {
    console.error('❌ Request error:', err.message);
});

req.end();

function testGitHubModels() {
    console.log('\n🤖 Testing GitHub Models API access...');
    
    const modelOptions = {
        hostname: 'models.inference.ai.azure.com',
        path: '/chat/completions',
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'User-Agent': 'Flash-Loan-Arbitrage-System'
        }
    };

    const requestData = JSON.stringify({
        messages: [
            {
                role: "user",
                content: "Hello! Can you confirm you're GitHub Copilot?"
            }
        ],
        model: "gpt-4o",
        max_tokens: 50
    });

    const modelReq = https.request(modelOptions, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            console.log(`📊 Models API Status: ${res.statusCode}`);
            
            if (res.statusCode === 200) {
                const response = JSON.parse(data);
                console.log('✅ GitHub Models API working!');
                console.log(`🤖 Response: ${response.choices[0].message.content}`);
            } else {
                console.log(`❌ Models API Error: ${res.statusCode}`);
                console.log(`📝 Response: ${data}`);
                
                if (res.statusCode === 401) {
                    console.log('\n💡 GitHub Models might require:');
                    console.log('1. GitHub Copilot subscription');
                    console.log('2. Specific token scopes');
                    console.log('3. Organization access (if using organization account)');
                } else if (res.statusCode === 403) {
                    console.log('\n💡 Access forbidden - check:');
                    console.log('1. GitHub Copilot subscription is active');
                    console.log('2. Account has access to GitHub Models');
                    console.log('3. Token has required permissions');
                }
            }
        });
    });

    modelReq.on('error', (err) => {
        console.error('❌ Models API request error:', err.message);
    });

    modelReq.write(requestData);
    modelReq.end();
}
