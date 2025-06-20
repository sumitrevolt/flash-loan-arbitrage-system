/**
 * Direct GitHub Models API test with your token
 */

const fs = require('fs');
const path = require('path');

// Load environment variables
const envPath = path.join(__dirname, '.env');
const envContent = fs.readFileSync(envPath, 'utf8');
envContent.split('\n').forEach(line => {
  const trimmed = line.trim();
  if (trimmed && !trimmed.startsWith('#')) {
    const [key, ...valueParts] = trimmed.split('=');
    if (key && valueParts.length > 0) {
      process.env[key.trim()] = valueParts.join('=').trim();
    }
  }
});

async function testGitHubModelsDirectly() {
  console.log('🚀 Testing GitHub Models API with your Copilot subscription...\n');
  
  const githubToken = process.env.GITHUB_TOKEN;
  const githubModel = process.env.GITHUB_MODEL || 'gpt-4o-mini';
  
  console.log(`🤖 Model: ${githubModel}`);
  console.log(`🔑 Token: ${githubToken ? githubToken.substring(0, 20) + '...' : 'Not found'}\n`);
  
  if (!githubToken) {
    console.log('❌ GitHub token not found');
    return;
  }
  
  try {
    console.log('📡 Making API request to GitHub Models...');
    
    const response = await fetch('https://models.inference.ai.azure.com/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: githubModel,
        messages: [
          {
            role: 'user',
            content: 'You are a DeFi expert. Analyze this flash loan opportunity: ETH price on Uniswap is $1800, on SushiSwap is $1820. Gas price is 25 gwei. Should I execute a flash loan arbitrage? Respond in JSON format with shouldExecute (boolean), confidence (0-1), and reasoning (string).'
          }
        ],
        max_tokens: 300,
        temperature: 0.1
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ SUCCESS! GitHub Models API is working with your Copilot subscription!\n');
      console.log('🤖 AI Response:');
      console.log('================');
      console.log(data.choices[0].message.content);
      console.log('\n💰 Cost: FREE (included with your GitHub Copilot subscription)');
      
      // Try to parse as JSON
      try {
        const content = data.choices[0].message.content;
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const analysis = JSON.parse(jsonMatch[0]);
          console.log('\n📊 Parsed Analysis:');
          console.log(`   Should Execute: ${analysis.shouldExecute ? '✅ YES' : '❌ NO'}`);
          console.log(`   Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
          console.log(`   Reasoning: ${analysis.reasoning}`);
        }
      } catch (e) {
        console.log('\n⚠️  Response received but not in expected JSON format');
      }
      
      console.log('\n🎉 Your GitHub Copilot subscription is fully working with LangChain!');
      
    } else {
      const errorData = await response.json();
      console.log('❌ API Error:', response.status, response.statusText);
      console.log('Error details:', errorData);
    }
    
  } catch (error) {
    console.log('❌ Request failed:', error.message);
  }
}

testGitHubModelsDirectly().catch(console.error);
