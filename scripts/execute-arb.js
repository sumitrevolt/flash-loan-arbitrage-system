#!/usr/bin/env node
// Simple arbitrage executor for the FlashLoan contract.
// 1. Fetches price quotes from UniswapV3 & QuickSwap routers on Amoy.
// 2. If spread > MIN_PROFIT_BPS, triggers flash-loan arbitrage.
// NOTE: This is a skeleton – plug in real price/amount logic & gas controls.

require("dotenv").config();
const { ethers } = require("ethers");

// ---------------- env ----------------
const RPC            = process.env.AMOY_RPC_URL;
const PRIVATE_KEY    = process.env.PRIVATE_KEY;          // funder / admin
const CONTRACT_ADDR  = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5"; // update if redeployed
const AAVE_ASSET     = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"; // asset to borrow (WETH)
const AMOUNT         = ethers.utils.parseEther("1");     // 1 WETH flash-loan
const MIN_PROFIT_BPS = parseInt(process.env.MIN_PROFIT_BPS || "30", 10); // 0.30 %

// DEX router addresses
const UNI_ROUTER = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"; // UniswapV3 router
const QUICK_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"; // QuickSwap

// minimal ABI for getAmountsOut (QuickSwap / Uniswap V2-style) – adjust for V3
const ROUTER_ABI = ["function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory)"];
const FLASH_ABI  = [
  "function requestFlashLoan(address asset,uint256 amount,bytes calldata params) external"
];

async function main () {
  const provider = new ethers.providers.JsonRpcProvider(RPC);
  const wallet   = new ethers.Wallet(PRIVATE_KEY, provider);

  const uni   = new ethers.Contract(UNI_ROUTER,   ROUTER_ABI, provider);
  const quick = new ethers.Contract(QUICK_ROUTER, ROUTER_ABI, provider);
  const flash = new ethers.Contract(CONTRACT_ADDR, FLASH_ABI, wallet);

  // Example path: WETH → USDC
  const WETH = AAVE_ASSET;
  const USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";
  const path = [WETH, USDC];

  const outUni   = await uni.getAmountsOut(AMOUNT, path);
  const outQuick = await quick.getAmountsOut(AMOUNT, path);

  const priceUni   = outUni[outUni.length - 1];
  const priceQuick = outQuick[outQuick.length - 1];

  // Spread in basis-points
  const spreadBps = priceQuick.sub(priceUni).mul(10000).div(priceUni).toNumber();
  console.log("Price Uni:", ethers.utils.formatUnits(priceUni, 6), "USDC");
  console.log("Price Quick:", ethers.utils.formatUnits(priceQuick, 6), "USDC");
  console.log("Spread bps:", spreadBps);

  if (spreadBps < MIN_PROFIT_BPS) {
    console.log("No profitable spread ≥", MIN_PROFIT_BPS, "bps – abort.");
    return;
  }

  console.log("Profitable! triggering flash-loan…");
  const tx = await flash.requestFlashLoan(
    AAVE_ASSET,
    AMOUNT,
    "0x" // params if your contract needs
  );
  console.log("Tx sent:", tx.hash);
  await tx.wait();
  console.log("Flash-loan arbitrage executed ✅");
}

main().catch(console.error); 