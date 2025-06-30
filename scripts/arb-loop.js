#!/usr/bin/env node
require('dotenv').config();
const { ethers } = require('ethers');

// ---------------------------------------------------------------------------
const RPC          = process.env.AMOY_RPC_URL;
const PRIVATE_KEY  = process.env.PRIVATE_KEY;
const CONTRACT     = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5";
const TOKEN_IN     = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"; // WETH
const TOKEN_OUT    = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"; // USDC (6dec)
const AMOUNT_IN    = ethers.utils.parseEther("1");
const MIN_BPS      = parseInt(process.env.MIN_PROFIT_BPS || "30",10);
const LOOP_SEC     = parseInt(process.env.LOOP_SEC || "60",10);

// contracts
const QUICK_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"; // V2 router getAmountsOut
const UNI_QUOTER   = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"; // Uniswap V3 quoter

const QUICK_ABI = ["function getAmountsOut(uint256 amountIn,address[] memory path) external view returns(uint256[] memory)"];
const QUOTER_ABI=["function quoteExactInputSingle(address tokenIn,address tokenOut,uint24 fee,uint256 amountIn,uint160 sqrtPriceLimitX96) external returns (uint256 amountOut)"];
const FLASH_ABI =["function requestFlashLoan(address,uint256,bytes) external"];

async function fetchPrices(provider){
  const quick = new ethers.Contract(QUICK_ROUTER, QUICK_ABI, provider);
  const quoter= new ethers.Contract(UNI_QUOTER,  QUOTER_ABI, provider);
  // quickswap price
  const outQuick = await quick.getAmountsOut(AMOUNT_IN,[TOKEN_IN,TOKEN_OUT]);
  const priceQuick=outQuick[1];
  // uniswap v3 0.3% fee tier = 3000
  const priceUni = await quoter.callStatic.quoteExactInputSingle(TOKEN_IN,TOKEN_OUT,3000,AMOUNT_IN,0);
  return {priceQuick,priceUni};
}

async function main(){
  const provider=new ethers.providers.JsonRpcProvider(RPC);
  const wallet=new ethers.Wallet(PRIVATE_KEY,provider);
  const flash = new ethers.Contract(CONTRACT,FLASH_ABI,wallet);
  while(true){
    try{
      const {priceQuick,priceUni}=await fetchPrices(provider);
      const spread = priceQuick.sub(priceUni);
      const spreadBps=spread.mul(10000).div(priceUni);
      console.log(new Date().toISOString(),"uni",ethers.utils.formatUnits(priceUni,6),"quick",ethers.utils.formatUnits(priceQuick,6),"bps",spreadBps.toString());
      if(spreadBps.gte(MIN_BPS)){
        console.log("Profitable spread >=",MIN_BPS,"bps -> executing flash-loan");
        const tx=await flash.requestFlashLoan(TOKEN_IN,AMOUNT_IN,"0x");
        console.log("TX",tx.hash);
        await tx.wait();
        console.log("Flash-loan executed and mined");
      }
    }catch(e){
      console.error("Error loop:",e.reason||e);
    }
    await new Promise(r=>setTimeout(r,LOOP_SEC*1000));
  }
}

main(); 