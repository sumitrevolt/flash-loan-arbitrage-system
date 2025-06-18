/**
 * Demo script showing how to use the LangChain integration
 * with the Flash Loan Arbitrage System
 */

import FlashLoanAIService from './ai_agent/flashloan-ai-service';
import * as fs from 'fs';
import * as path from 'path';

// Load environment variables from .env file
function loadEnvFile() {
  try {
    const envPath = path.join(__dirname, '.env');
    if (fs.existsSync(envPath)) {
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
      console.log("✅ Loaded environment variables from .env file");
    } else {
      console.log("⚠️  No .env file found");
    }  } catch (error: any) {
    console.log("⚠️  Error loading .env file:", error.message);
  }
}

// Simple environment variable loader (alternative to dotenv)
function loadEnvVars() {
  loadEnvFile();
  
  const provider = process.env.AI_PROVIDER || 'openai';
  console.log(`🤖 AI Provider: ${provider.toUpperCase()}`);
  
  switch (provider.toLowerCase()) {
    case 'github':
      if (!process.env.GITHUB_TOKEN) {
        console.log("⚠️  Note: No GITHUB_TOKEN found in environment.");
        console.log("To enable GitHub AI analysis, add your GitHub token to .env file.");
      } else {
        const maskedToken = process.env.GITHUB_TOKEN.substring(0, 12) + "...";
        console.log(`✅ GitHub Token configured: ${maskedToken}`);
      }
      break;
    case 'anthropic':
      if (!process.env.ANTHROPIC_API_KEY) {
        console.log("⚠️  Note: No ANTHROPIC_API_KEY found in environment.");
      } else {
        console.log("✅ Anthropic API key configured");
      }
      break;
    case 'openai':
    default:
      if (!process.env.OPENAI_API_KEY) {
        console.log("⚠️  Note: No OPENAI_API_KEY found in environment.");
        console.log("To enable AI analysis, add your OpenAI API key to .env file.");
      } else {
        console.log("✅ OpenAI API key configured");
      }
      break;
  }
}

async function runLangChainDemo() {
  console.log("🚀 Starting LangChain Flash Loan Demo...\n");

  // Check if OpenAI API key is configured
  if (!process.env.OPENAI_API_KEY) {
    console.log("⚠️  OpenAI API key not found in environment variables.");
    console.log("Please add OPENAI_API_KEY to your .env file to enable AI analysis.");
    console.log("For now, running with mock data...\n");
  }
  try {
    // Initialize the AI service with the configured provider
    const aiProvider = process.env.AI_PROVIDER;
    const aiService = new FlashLoanAIService(undefined, aiProvider);

    console.log("📊 Running market analysis...");
    
    // Perform a single market analysis
    const analysisResult = await aiService.analyzeCurrentMarket();
    
    if (analysisResult && !analysisResult.error) {
      console.log("\n✅ Market Analysis Complete!");
      console.log(`📈 Arbitrage Opportunity: ${analysisResult.arbitrageAnalysis.shouldExecute ? 'YES' : 'NO'}`);
      console.log(`🎯 Confidence: ${(analysisResult.arbitrageAnalysis.confidence * 100).toFixed(1)}%`);
      console.log(`💰 Expected Profit: $${analysisResult.arbitrageAnalysis.expectedProfit}`);
      console.log(`⚠️  Risk Level: ${analysisResult.arbitrageAnalysis.riskLevel}`);
      console.log(`💡 Reasoning: ${analysisResult.arbitrageAnalysis.reasoning}`);
      
      if (analysisResult.strategy) {
        console.log("\n📋 AI Generated Strategy:");
        console.log(analysisResult.strategy);
      }
    } else {
      console.log("❌ Analysis failed:", analysisResult?.error || "Unknown error");
    }

    // Test flash loan decision making
    console.log("\n🔍 Testing Flash Loan Decision Making...");
    const decision = await aiService.shouldExecuteFlashLoan("ETH", "USDC", "10");
    console.log(`Decision: ${decision.shouldExecute ? 'EXECUTE' : 'SKIP'}`);
    console.log(`Confidence: ${(decision.confidence * 100).toFixed(1)}%`);
    console.log(`Reasoning: ${decision.reasoning}`);

    // Demo continuous analysis (optional - commented out to avoid long running)
    console.log("\n🔄 To start continuous analysis, uncomment the next line:");
    console.log("// await aiService.startContinuousAnalysis(5); // Every 5 minutes");

  } catch (error) {
    console.error("❌ Demo failed:", error);
  }
}

async function showLangChainFeatures() {
  console.log("\n🧠 LangChain Integration Features:");
  console.log("=====================================");
  console.log("✅ AI-powered arbitrage opportunity analysis");
  console.log("✅ Market condition assessment");
  console.log("✅ Risk evaluation and confidence scoring");
  console.log("✅ Dynamic trading strategy generation");
  console.log("✅ Continuous market monitoring");
  console.log("✅ Natural language reasoning for decisions");
  console.log("✅ Structured output parsing with Zod validation");
  console.log("✅ Configurable confidence thresholds");
  console.log("✅ Integration with existing flash loan contracts");
  
  console.log("\n📚 Supported Analysis Types:");
  console.log("• Price differential analysis across DEXs");
  console.log("• Gas price and network congestion assessment");
  console.log("• Liquidity depth evaluation");
  console.log("• MEV competition risk analysis");
  console.log("• Market volatility impact assessment");
  console.log("• Optimal timing recommendations");
}

async function main() {
  console.log("🏦 Flash Loan Arbitrage System - LangChain Integration Demo");
  console.log("===========================================================\n");
  
  // Load environment variables
  loadEnvVars();
  
  await showLangChainFeatures();
  await runLangChainDemo();

  console.log("\n📖 Next Steps:");
  console.log("1. Add your OpenAI API key to .env file");
  console.log("2. Install dependencies: npm install");
  console.log("3. Run the demo: npm run demo");
  console.log("4. Integrate with your existing flash loan contracts");
  console.log("5. Configure continuous monitoring");

  console.log("\n🔧 Configuration Files:");
  console.log("• .env.template - Environment variables template");
  console.log("• ai_agent/langchain-integration.ts - Core AI analyzer");
  console.log("• ai_agent/flashloan-ai-service.ts - Service wrapper");
  console.log("• package.json - Updated with LangChain dependencies");
}

// Run the demo if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}

export { runLangChainDemo, showLangChainFeatures };
