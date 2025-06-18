/**
 * Quick test script for GitHub Copilot + LangChain integration
 * This shows you exactly how to use your Copilot subscription
 */

// Simple test without complex imports
console.log("🚀 GitHub Copilot + LangChain Integration Test");
console.log("==============================================\n");

// Check environment setup
function checkGitHubSetup() {
  console.log("🔍 Checking GitHub Copilot Setup...\n");
  
  // Check AI provider setting
  const provider = process.env.AI_PROVIDER || "not set";
  console.log(`📝 AI Provider: ${provider}`);
  
  // Check GitHub token
  const githubToken = process.env.GITHUB_TOKEN;
  if (githubToken) {
    const maskedToken = githubToken.substring(0, 8) + "...";
    console.log(`✅ GitHub Token: ${maskedToken}`);
  } else {
    console.log("❌ GitHub Token: Not configured");
    console.log("💡 Add GITHUB_TOKEN to your .env file");
  }
  
  // Check GitHub model
  const githubModel = process.env.GITHUB_MODEL || "gpt-4o";
  console.log(`🤖 GitHub Model: ${githubModel}`);
  
  console.log("\n📋 Available GitHub Models with your Copilot subscription:");
  console.log("  • gpt-4o - Latest GPT-4 Omni (Recommended)");
  console.log("  • gpt-4o-mini - Faster, cheaper version");
  console.log("  • claude-3-5-sonnet - Anthropic's Claude");
  console.log("  • llama-3.1-405b - Meta's Llama");
  
  console.log("\n🔧 To configure GitHub Models:");
  console.log("1. Get your GitHub token:");
  console.log("   - Go to: https://github.com/settings/personal-access-tokens/tokens");
  console.log("   - Or use: gh auth token");
  console.log("2. Add to .env file:");
  console.log("   AI_PROVIDER=github");
  console.log("   GITHUB_TOKEN=your_token_here");
  console.log("   GITHUB_MODEL=gpt-4o");
  
  return { provider, hasToken: !!githubToken, model: githubModel };
}

// Simple API test function
async function testGitHubModelsAPI() {
  console.log("\n🧪 Testing GitHub Models API Connection...");
  
  const githubToken = process.env.GITHUB_TOKEN;
  if (!githubToken) {
    console.log("❌ Cannot test - GITHUB_TOKEN not configured");
    return false;
  }
  
  try {
    // Simple test using fetch (built-in to Node.js)
    const response = await fetch("https://models.inference.ai.azure.com/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${githubToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "gpt-4o-mini", // Use mini for testing
        messages: [
          {
            role: "user",
            content: "Test message: Can you analyze DeFi arbitrage opportunities?"
          }
        ],
        max_tokens: 100,
        temperature: 0.1
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log("✅ GitHub Models API connection successful!");
      console.log(`📝 Test response: ${data.choices[0].message.content.substring(0, 100)}...`);
      return true;
    } else {
      const errorData = await response.json();
      console.log("❌ GitHub Models API error:", errorData.error?.message || response.statusText);
      return false;
    }
    
  } catch (error) {
    console.log("❌ Connection failed:", error.message);
    return false;
  }
}

// Main test function
async function main() {
  const setup = checkGitHubSetup();
  
  if (setup.provider === "github" && setup.hasToken) {
    const success = await testGitHubModelsAPI();
    
    if (success) {
      console.log("\n🎉 SUCCESS! Your GitHub Copilot subscription is ready for LangChain!");
      console.log("\n🚀 Next steps:");
      console.log("1. Run: .\\langchain.bat demo");
      console.log("2. Try: .\\langchain.bat analyze");
      console.log("3. Test decision making: .\\langchain.bat decision ETH USDC 10");
    } else {
      console.log("\n⚠️  Setup needed - follow the configuration steps above");
    }
  } else {
    console.log("\n⚙️  Configuration needed:");
    console.log("1. Set AI_PROVIDER=github in .env");
    console.log("2. Add your GITHUB_TOKEN to .env");
    console.log("3. Choose GITHUB_MODEL (gpt-4o recommended)");
  }
  
  console.log("\n💰 Cost Benefits:");
  console.log("✅ FREE with your existing GitHub Copilot subscription");
  console.log("✅ No additional API costs");
  console.log("✅ High rate limits");
  console.log("✅ Multiple model options");
}

// Run the test
main().catch(console.error);
