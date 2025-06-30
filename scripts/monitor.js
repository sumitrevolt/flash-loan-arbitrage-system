// Simple health-monitor for the Flash-Loan contract
// Logs owner address & total flash-loan count every run.
// Schedule with cron/TaskScheduler at your preferred interval.

require("dotenv").config();
const { ethers } = require("ethers");

const RPC     = process.env.AMOY_RPC_URL;
const ADDRESS = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5"; // contract address

// Minimal ABI (adjust if your contract exposes different functions)
const ABI = [
  "function owner() view returns (address)",
  "function totalFlashCount() view returns (uint256)"
];

async function main() {
  const provider = new ethers.providers.JsonRpcProvider(RPC);
  const c = new ethers.Contract(ADDRESS, ABI, provider);

  const owner = await c.owner();
  let count = "?";
  try {
    count = (await c.totalFlashCount()).toString();
  } catch (_) {}

  console.log(new Date().toISOString(), "| owner:", owner, "| flash-loans:", count);
}

main().catch(console.error); 