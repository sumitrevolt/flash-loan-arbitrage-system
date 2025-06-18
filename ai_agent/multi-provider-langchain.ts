import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { BaseOutputParser } from "@langchain/core/output_parsers";
import { BaseChatModel } from "@langchain/core/language_models/chat_models";
import { z } from "zod";
import axios from "axios";

// Define schemas for structured outputs
const ArbitrageAnalysisSchema = z.object({
  shouldExecute: z.boolean(),
  confidence: z.number().min(0).max(1),
  expectedProfit: z.number(),
  riskLevel: z.enum(["LOW", "MEDIUM", "HIGH"]),
  reasoning: z.string(),
  recommendedTokenPair: z.string().optional(),
  recommendedAmount: z.string().optional()
});

const MarketConditionSchema = z.object({
  volatility: z.enum(["LOW", "MEDIUM", "HIGH"]),
  trend: z.enum(["BULLISH", "BEARISH", "SIDEWAYS"]),
  liquidityHealth: z.enum(["POOR", "FAIR", "GOOD", "EXCELLENT"]),
  riskAssessment: z.string(),
  optimalTimingWindow: z.string()
});

// GitHub Models API wrapper for LangChain
class GitHubChatModel extends BaseChatModel {
  lc_namespace = ["langchain", "chat_models", "github"];
  
  private githubToken: string;
  private model: string;
  private baseURL = "https://models.inference.ai.azure.com";

  constructor(fields: { githubToken: string; model: string }) {
    super({});
    this.githubToken = fields.githubToken;
    this.model = fields.model;
  }

  _llmType(): string {
    return "github-models";
  }
  async _generate(messages: any[], options?: any): Promise<any> {
    try {
      const response = await axios.post(
        `${this.baseURL}/chat/completions`,
        {
          model: this.model,
          messages: messages.map(msg => ({
            role: msg._getType() === "human" ? "user" : "assistant",
            content: msg.content
          })),
          temperature: 0.1,
          max_tokens: 4000
        },
        {
          headers: {
            "Authorization": `Bearer ${this.githubToken}`,
            "Content-Type": "application/json"
          }
        }
      );

      const content = response.data.choices[0].message.content;
      
      return {
        generations: [{
          text: content,
          message: {
            content: content,
            additional_kwargs: {}
          }
        }],
        llmOutput: {}
      };
    } catch (error: any) {
      const errorMsg = error.response?.data?.error?.message || error.message;
      console.error("❌ GitHub Models API error:", errorMsg);
      
      if (error.response?.status === 401) {
        const isPermissionError = errorMsg.includes('models') || errorMsg.includes('permission');
        if (isPermissionError) {
          throw new Error(`
GitHub Models Access Error: Your token needs the 'models' permission.

Quick Fix:
1. Go to: https://github.com/settings/tokens
2. Generate new token with 'models' scope
3. Update GITHUB_TOKEN in .env file

Or switch to OpenAI temporarily:
- Set AI_PROVIDER=openai in .env file
          `);
        }
      }
      
      throw new Error(`GitHub Models API failed: ${errorMsg}`);
    }
  }

  async invoke(input: string): Promise<any> {
    const messages = [{ _getType: () => "human", content: input }];
    const result = await this._generate(messages);
    return { content: result.generations[0].text };
  }
}

// Custom output parser for arbitrage analysis
class ArbitrageAnalysisParser extends BaseOutputParser<z.infer<typeof ArbitrageAnalysisSchema>> {
  lc_namespace = ["langchain", "schema", "output_parser"];

  constructor() {
    super();
  }

  getFormatInstructions(): string {
    return "Please provide the response in JSON format with the required fields.";
  }

  async parse(text: string): Promise<z.infer<typeof ArbitrageAnalysisSchema>> {
    try {
      // Try to extract JSON from the response
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return ArbitrageAnalysisSchema.parse(parsed);
      }
      
      // Fallback parsing if no JSON found
      return {
        shouldExecute: text.toLowerCase().includes("execute") || text.toLowerCase().includes("profitable"),
        confidence: 0.5,
        expectedProfit: 0,
        riskLevel: "MEDIUM" as const,
        reasoning: text.trim()
      };
    } catch (error: any) {
      console.error("Error parsing arbitrage analysis:", error);
      return {
        shouldExecute: false,
        confidence: 0,
        expectedProfit: 0,
        riskLevel: "HIGH" as const,
        reasoning: "Failed to parse analysis"
      };
    }
  }
}

export class MultiProviderFlashLoanAIAnalyzer {
  private llm: BaseChatModel;
  private provider: string;

  constructor(provider?: string) {
    this.provider = provider || process.env.AI_PROVIDER || "openai";
    this.llm = this.createLLM();
  }
  private createLLM(): BaseChatModel {
    switch (this.provider.toLowerCase()) {
      case "github":
        const githubToken = process.env.GITHUB_TOKEN;
        const githubModel = process.env.GITHUB_MODEL || "gpt-4o";
        
        if (!githubToken) {
          console.warn("⚠️ GITHUB_TOKEN not found, falling back to OpenAI");
          return this.createOpenAIFallback();
        }
        
        if (!githubToken.startsWith('github_pat_')) {
          console.warn("⚠️ Invalid GitHub token format, falling back to OpenAI");
          return this.createOpenAIFallback();
        }
        
        console.log(`🤖 Using GitHub Models: ${githubModel}`);
        try {
          return new GitHubChatModel({
            githubToken,
            model: githubModel
          });
        } catch (error: any) {
          console.warn(`⚠️ GitHub Models initialization failed: ${error.message}`);
          console.warn("⚠️ Falling back to OpenAI");
          return this.createOpenAIFallback();
        }

      case "anthropic":
        const anthropicKey = process.env.ANTHROPIC_API_KEY;
        const anthropicModel = process.env.ANTHROPIC_MODEL || "claude-3-5-sonnet-20241022";
        
        if (!anthropicKey) {
          console.warn("⚠️ ANTHROPIC_API_KEY not found, falling back to OpenAI");
          return this.createOpenAIFallback();
        }
        
        console.log(`🤖 Using Anthropic Claude: ${anthropicModel}`);
        return new ChatAnthropic({
          anthropicApiKey: anthropicKey,
          modelName: anthropicModel,
          temperature: 0.1
        });

      case "openai":
      default:
        return this.createOpenAIFallback();
    }
  }

  private createOpenAIFallback(): BaseChatModel {
    const openaiKey = process.env.OPENAI_API_KEY;
    const openaiModel = process.env.OPENAI_MODEL || "gpt-4";
    
    if (!openaiKey || openaiKey === 'your_openai_api_key_here') {
      throw new Error(`
❌ No valid AI provider configured!

Current provider: ${this.provider}
Available options:
1. Get GitHub Models working:
   - Generate token with 'models' permission at: https://github.com/settings/tokens
   - Update GITHUB_TOKEN in .env file
   
2. Use OpenAI:
   - Get API key from: https://platform.openai.com/api-keys
   - Update OPENAI_API_KEY in .env file
   - Set AI_PROVIDER=openai in .env file
   
3. Use Anthropic:
   - Get API key from: https://console.anthropic.com/
   - Update ANTHROPIC_API_KEY in .env file
   - Set AI_PROVIDER=anthropic in .env file
      `);
    }
    
    console.log(`🤖 Using OpenAI: ${openaiModel}`);
    return new ChatOpenAI({
      openAIApiKey: openaiKey,
      modelName: openaiModel,
      temperature: 0.1
    });
  }

  async analyzeArbitrageOpportunity(marketData: {
    tokenA_dex1_price: number;
    tokenA_dex2_price: number;
    tokenB_dex1_price: number;
    tokenB_dex2_price: number;
    liquidity: string;
    gasPrice: number;
    flashLoanFee: number;
    volatility: string;
    networkCongestion: string;
    mevActivity: string;
  }): Promise<z.infer<typeof ArbitrageAnalysisSchema>> {
    try {
      const prompt = `You are an expert DeFi arbitrageur analyzing flash loan opportunities using ${this.provider} AI.

Market Data:
Token A Price on DEX 1: ${marketData.tokenA_dex1_price}
Token A Price on DEX 2: ${marketData.tokenA_dex2_price}
Token B Price on DEX 1: ${marketData.tokenB_dex1_price}
Token B Price on DEX 2: ${marketData.tokenB_dex2_price}
Available Liquidity: ${marketData.liquidity}
Gas Price: ${marketData.gasPrice} gwei
Flash Loan Fee: ${marketData.flashLoanFee}%

Current Market Conditions:
- Volatility: ${marketData.volatility}
- Network Congestion: ${marketData.networkCongestion}
- Recent MEV Activity: ${marketData.mevActivity}

Analyze this arbitrage opportunity and provide your recommendation in the following JSON format:
{
  "shouldExecute": boolean,
  "confidence": number (0-1),
  "expectedProfit": number (in USD),
  "riskLevel": "LOW" | "MEDIUM" | "HIGH",
  "reasoning": "detailed explanation",
  "recommendedTokenPair": "optional token pair",
  "recommendedAmount": "optional recommended flash loan amount"
}

Consider:
1. Price differential and slippage
2. Gas costs and network conditions
3. Flash loan fees
4. MEV competition risk
5. Liquidity depth
6. Market volatility impact`;

      const result = await this.llm.invoke(prompt);
      const parser = new ArbitrageAnalysisParser();
      return await parser.parse(result.content as string);
    } catch (error: any) {
      console.error("Error in arbitrage analysis:", error);
      return {
        shouldExecute: false,
        confidence: 0,
        expectedProfit: 0,
        riskLevel: "HIGH" as const,
        reasoning: `Analysis failed with ${this.provider}: ${error.message}`
      };
    }
  }

  async analyzeMarketConditions(marketMetrics: {
    ethPrice: number;
    gasPrice: number;
    dexTvl: number;
    recentVolume: number;
    volatilityIndex: number;
    recentEvents: string;
  }): Promise<any> {
    try {
      const prompt = `You are a DeFi market analyst using ${this.provider} AI. Analyze the current market conditions for flash loan arbitrage:

Market Metrics:
- ETH Price: $${marketMetrics.ethPrice}
- Gas Price: ${marketMetrics.gasPrice} gwei
- DEX TVL: $${marketMetrics.dexTvl}
- Recent Volume: $${marketMetrics.recentVolume}
- Volatility Index: ${marketMetrics.volatilityIndex}

Recent Events:
${marketMetrics.recentEvents}

Provide market analysis in JSON format:
{
  "volatility": "LOW" | "MEDIUM" | "HIGH",
  "trend": "BULLISH" | "BEARISH" | "SIDEWAYS", 
  "liquidityHealth": "POOR" | "FAIR" | "GOOD" | "EXCELLENT",
  "riskAssessment": "detailed risk analysis",
  "optimalTimingWindow": "recommended timing for trades"
}`;

      const result = await this.llm.invoke(prompt);
      const content = result.content as string;
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      return {
        volatility: "MEDIUM",
        trend: "SIDEWAYS",
        liquidityHealth: "FAIR",
        riskAssessment: content,
        optimalTimingWindow: "Analyze conditions before trading"
      };
    } catch (error: any) {
      console.error("Error in market analysis:", error);
      return {
        volatility: "HIGH",
        trend: "SIDEWAYS", 
        liquidityHealth: "FAIR",
        riskAssessment: `Market analysis failed with ${this.provider}: ${error.message}`,
        optimalTimingWindow: "Wait for better conditions"
      };
    }
  }

  async generateTradingStrategy(
    arbitrageAnalysis: z.infer<typeof ArbitrageAnalysisSchema>,
    marketConditions: any
  ): Promise<string> {
    try {
      const prompt = `Using ${this.provider} AI, generate a detailed trading strategy based on the analysis:

Arbitrage Analysis:
- Should Execute: ${arbitrageAnalysis.shouldExecute}
- Confidence: ${arbitrageAnalysis.confidence}
- Expected Profit: $${arbitrageAnalysis.expectedProfit}
- Risk Level: ${arbitrageAnalysis.riskLevel}
- Reasoning: ${arbitrageAnalysis.reasoning}

Market Conditions:
- Volatility: ${marketConditions.volatility}
- Trend: ${marketConditions.trend}
- Liquidity Health: ${marketConditions.liquidityHealth}

Generate a comprehensive trading strategy including:
1. Entry and exit criteria
2. Risk management measures
3. Position sizing recommendations
4. Monitoring requirements
5. Contingency plans`;

      const result = await this.llm.invoke(prompt);
      return result.content as string;
    } catch (error: any) {
      console.error("Error generating strategy:", error);
      return `Strategy generation failed with ${this.provider}. Please review market conditions manually.`;
    }
  }

  getProvider(): string {
    return this.provider;
  }
}

// Helper function to create analyzer with environment setup
export function createFlashLoanAnalyzer(provider?: string): MultiProviderFlashLoanAIAnalyzer {
  const selectedProvider = provider || process.env.AI_PROVIDER || "openai";
  
  console.log(`🚀 Initializing Flash Loan AI Analyzer with ${selectedProvider.toUpperCase()}`);
  
  switch (selectedProvider.toLowerCase()) {
    case "github":
      if (!process.env.GITHUB_TOKEN) {
        console.warn("GITHUB_TOKEN not found. You can get this from GitHub Settings > Developer settings > Personal access tokens");
        console.warn("Or use your GitHub Copilot subscription token");
      }
      break;
    case "anthropic":
      if (!process.env.ANTHROPIC_API_KEY) {
        console.warn("ANTHROPIC_API_KEY not found in environment variables");
      }
      break;
    case "openai":
    default:
      if (!process.env.OPENAI_API_KEY) {
        console.warn("OPENAI_API_KEY not found in environment variables");
      }
      break;
  }
  
  return new MultiProviderFlashLoanAIAnalyzer(selectedProvider);
}

// Export legacy compatibility
export const FlashLoanAIAnalyzer = MultiProviderFlashLoanAIAnalyzer;

// Export types for use in other modules
export type ArbitrageAnalysis = z.infer<typeof ArbitrageAnalysisSchema>;
export type MarketCondition = z.infer<typeof MarketConditionSchema>;
