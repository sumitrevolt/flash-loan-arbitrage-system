const { ethers } = require("hardhat");

/**
 * Whitelist common tokens and approve common DEX routers.
 * Edit the arrays below if you need a different set.
 *
 * Run with:
 *   npx hardhat run scripts/setup.js --network amoy
 */
async function main() {
  const CONTRACT_ADDRESS = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5"; // <- change if redeployed
  const FlashLoan = await ethers.getContractAt("FlashLoanArbitrageFixed", CONTRACT_ADDRESS);
  const [owner] = await ethers.getSigners();
  console.log("Using admin/owner:", owner.address);

  // ---- editable lists ------------------------------------------------------
  const TOKENS = [
    { symbol: "WETH", addr: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619" },
    { symbol: "WBTC", addr: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6" },
    { symbol: "USDC", addr: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174" },
    { symbol: "USDT", addr: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F" },
    { symbol: "DAI",  addr: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063" },
    { symbol: "WMATIC", addr: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270" },
    { symbol: "LINK", addr: "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39" },
    { symbol: "AAVE", addr: "0xD6DF932A45C0f255f85145f286eA0b292B21C90B" },
  ];

  const DEXES = [
    { name: "UniswapV3", addr: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45" },
    { name: "QuickSwap", addr: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff" },
    { name: "SushiSwap", addr: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506" },
  ];
  // -------------------------------------------------------------------------

  // Whitelist tokens
  for (const t of TOKENS) {
    console.log(`Whitelisting ${t.symbol}…`);
    const tx = await FlashLoan.whitelistToken(t.addr, true);
    await tx.wait();
  }

  // Approve DEXes
  for (const d of DEXES) {
    console.log(`Approving DEX ${d.name}…`);
    const tx = await FlashLoan.approveDex(d.addr, true);
    await tx.wait();
  }

  console.log("✅ Setup complete.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
}); 