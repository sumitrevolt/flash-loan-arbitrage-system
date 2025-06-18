#!/usr/bin/env node
/**
 * LangChain Command Line Interface for Flash Loan System
 * Usage: node langchain-cli.js [command] [options]
 */

const { FlashLoanAIAnalyzer } = require('./ai_agent/langchain-integration');
const FlashLoanAIService = require('./ai_agent/flashloan-ai-service').default;

// Command line argument parsing
const args = process.argv.slice(2);
const command = args[0];

// Available commands
const commands = {
  'analyze': 'Analyze current market conditions',
  'decision': 'Get flash loan execution decision',
  'strategy': 'Generate trading strategy',
  'monitor': 'Start continuous monitoring',
  'test': 'Test connection with mock data',
  'help': 'Show this help message'
};

async function showHelp() {
  console.log('🤖 LangChain Flash Loan AI - Command Line Interface');
  console.log('===================================================\n');
  
  console.log('Available Commands:');
  Object.entries(commands).forEach(([cmd, desc]) => {
    console.log(`  ${cmd.padEnd(10)} - ${desc}`);
  });
  
  console.log('\nExamples:');
  console.log('  node langchain-cli.js analyze');
  console.log('  node langchain-cli.js decision ETH USDC 10');
  console.log('  node langchain-cli.js test');
  console.log('  node langchain-cli.js monitor 5');
  
  console.log('\nSetup:');
  console.log('  1. Add OPENAI_API_KEY to .env file');
  console.log('  2. Run: node langchain-cli.js test');
}

async function testConnection() {
  console.log('🧪 Testing LangChain Connection...\n');
  
  try {
    const aiService = new FlashLoanAIService();
    console.log('✅ FlashLoanAIService initialized');
    
    // Test with mock data (will work even without API key)
    console.log('📊 Testing market analysis...');
    const analysis = await aiService.analyzeCurrentMarket();
    
    if (analysis && !analysis.error) {
      console.log('✅ Market analysis successful');
      console.log(`📈 Should Execute: ${analysis.arbitrageAnalysis.shouldExecute}`);
      console.log(`🎯 Confidence: ${(analysis.arbitrageAnalysis.confidence * 100).toFixed(1)}%`);
    } else {
      console.log('⚠️  Analysis completed with limitations:', analysis?.error);
    }
    
  } catch (error) {
    console.log('❌ Connection test failed:', error.message);
    console.log('\n💡 Solution: Add your OpenAI API key to .env file');
  }
}

async function analyzeMarket() {
  console.log('📊 Analyzing Market Conditions...\n');
  
  try {
    const aiService = new FlashLoanAIService();
    const analysis = await aiService.analyzeCurrentMarket();
    
    if (analysis && !analysis.error) {
      console.log('✅ Market Analysis Complete!\n');
      
      const arb = analysis.arbitrageAnalysis;
      console.log('🎯 Arbitrage Analysis:');
      console.log(`   Execute: ${arb.shouldExecute ? '✅ YES' : '❌ NO'}`);
      console.log(`   Confidence: ${(arb.confidence * 100).toFixed(1)}%`);
      console.log(`   Expected Profit: $${arb.expectedProfit}`);
      console.log(`   Risk Level: ${arb.riskLevel}`);
      console.log(`   Reasoning: ${arb.reasoning}\n`);
      
      const market = analysis.marketConditions;
      console.log('📈 Market Conditions:');
      console.log(`   Volatility: ${market.volatility}`);
      console.log(`   Trend: ${market.trend}`);
      console.log(`   Liquidity: ${market.liquidityHealth}`);
      console.log(`   Risk Assessment: ${market.riskAssessment}`);
      
      if (analysis.strategy) {
        console.log('\n📋 AI Strategy:');
        console.log(analysis.strategy);
      }
    } else {
      console.log('❌ Analysis failed:', analysis?.error);
    }
    
  } catch (error) {
    console.log('❌ Analysis failed:', error.message);
  }
}

async function getDecision() {
  const tokenA = args[1] || 'ETH';
  const tokenB = args[2] || 'USDC';
  const amount = args[3] || '10';
  
  console.log(`🤔 Getting Flash Loan Decision for ${amount} ${tokenA} -> ${tokenB}...\n`);
  
  try {
    const aiService = new FlashLoanAIService();
    const decision = await aiService.shouldExecuteFlashLoan(tokenA, tokenB, amount);
    
    console.log('🎯 Decision Result:');
    console.log(`   Execute: ${decision.shouldExecute ? '✅ YES' : '❌ NO'}`);
    console.log(`   Confidence: ${(decision.confidence * 100).toFixed(1)}%`);
    console.log(`   Reasoning: ${decision.reasoning}`);
    
    if (decision.shouldExecute && decision.confidence > 0.7) {
      console.log('\n🚀 Recommendation: EXECUTE FLASH LOAN');
    } else {
      console.log('\n⏸️  Recommendation: WAIT FOR BETTER CONDITIONS');
    }
    
  } catch (error) {
    console.log('❌ Decision failed:', error.message);
  }
}

async function startMonitoring() {
  const interval = parseInt(args[1]) || 5;
  
  console.log(`🔄 Starting Continuous Monitoring (every ${interval} minutes)...\n`);
  
  try {
    const aiService = new FlashLoanAIService();
    await aiService.startContinuousAnalysis(interval);
    
    console.log('✅ Monitoring started successfully');
    console.log('Press Ctrl+C to stop monitoring');
    
  } catch (error) {
    console.log('❌ Monitoring failed:', error.message);
  }
}

async function generateStrategy() {
  console.log('📋 Generating Trading Strategy...\n');
  
  try {
    const aiService = new FlashLoanAIService();
    const analysis = await aiService.analyzeCurrentMarket();
    
    if (analysis && analysis.strategy) {
      console.log('🧠 AI-Generated Trading Strategy:');
      console.log('=====================================');
      console.log(analysis.strategy);
    } else {
      console.log('⚠️  Could not generate strategy. Try running market analysis first.');
    }
    
  } catch (error) {
    console.log('❌ Strategy generation failed:', error.message);
  }
}

// Main command handler
async function main() {
  switch (command) {
    case 'analyze':
      await analyzeMarket();
      break;
    case 'decision':
      await getDecision();
      break;
    case 'strategy':
      await generateStrategy();
      break;
    case 'monitor':
      await startMonitoring();
      break;
    case 'test':
      await testConnection();
      break;
    case 'help':
    case undefined:
      await showHelp();
      break;
    default:
      console.log(`❌ Unknown command: ${command}`);
      console.log('Run "node langchain-cli.js help" for available commands');
  }
}

// Run the CLI
if (require.main === module) {
  main().catch(console.error);
}
