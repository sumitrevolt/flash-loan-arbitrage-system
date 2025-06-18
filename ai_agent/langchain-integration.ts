import { ChatOpenAI } from "@langchain/openai";
import { PromptTemplate } from "@langchain/core/prompts";
import { BaseOutputParser } from "@langchain/core/output_parsers";
import { z } from "zod";

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

export class FlashLoanAIAnalyzer {
  private llm: ChatOpenAI;

  constructor(apiKey?: string, model: string = "gpt-4") {
    this.llm = new ChatOpenAI({
      openAIApiKey: apiKey || process.env.OPENAI_API_KEY,
      modelName: model,
      temperature: 0.1 // Low temperature for consistent financial analysis
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
      const prompt = `You are an expert DeFi arbitrageur analyzing flash loan opportunities. 

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
        reasoning: `Analysis failed: ${error.message}`
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
      const prompt = `You are a DeFi market analyst. Analyze the current market conditions for flash loan arbitrage:

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
        riskAssessment: `Market analysis failed: ${error.message}`,
        optimalTimingWindow: "Wait for better conditions"
      };
    }
  }

  async generateTradingStrategy(
    arbitrageAnalysis: z.infer<typeof ArbitrageAnalysisSchema>,
    marketConditions: any
  ): Promise<string> {
    try {
      const prompt = `Based on the arbitrage analysis and market conditions, generate a detailed trading strategy:

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
      return "Strategy generation failed. Please review market conditions manually.";
    }
  }
}

// Helper function to create analyzer with environment setup
export function createFlashLoanAnalyzer(): FlashLoanAIAnalyzer {
  if (!process.env.OPENAI_API_KEY) {
    console.warn("OPENAI_API_KEY not found in environment variables");
  }
  
  return new FlashLoanAIAnalyzer(
    process.env.OPENAI_API_KEY,
    process.env.OPENAI_MODEL || "gpt-4"
  );
}

// Export types for use in other modules
export type ArbitrageAnalysis = z.infer<typeof ArbitrageAnalysisSchema>;
export type MarketCondition = z.infer<typeof MarketConditionSchema>;
