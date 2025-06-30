require('dotenv').config();

const AMOY_CONFIG = {
  // Network Configuration
  NETWORK: {
    RPC_URL: process.env.AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
    CHAIN_ID: 80002,
    NAME: "Polygon Amoy Testnet"
  },

  // Aave V3 Addresses
  AAVE: {
    POOL_ADDRESSES_PROVIDER: "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A",
    POOL: "0x48914C788295b5db23aF2b5F0B3BE775C4eA9440"
  },

  // DEX Router Addresses
  DEXS: {
    UNISWAP_V3: {
      ROUTER: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
      QUOTER: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
      FACTORY: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    },
    QUICKSWAP: {
      ROUTER: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      FACTORY: "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
    },
    SUSHISWAP: {
      ROUTER: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      FACTORY: "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    },
    ONEINCH: {
      ROUTER: "0x111111125421cA6dc452d289314280a0f8842A65" // 1inch V5 Aggregation Router
    }
  },

  // Top 15 Tokens for Arbitrage on Amoy
  TOKENS: {
    WMATIC: {
      address: "0x9c3c9283d3e44854697cd22D3faA240cfB0e7582",
      symbol: "WMATIC",
      decimals: 18,
      coingeckoId: "matic-network"
    },
    USDC: {
      address: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",
      symbol: "USDC",
      decimals: 6,
      coingeckoId: "usd-coin"
    },
    USDT: {
      address: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
      symbol: "USDT",
      decimals: 6,
      coingeckoId: "tether"
    },
    DAI: {
      address: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
      symbol: "DAI",
      decimals: 18,
      coingeckoId: "dai"
    },
    WETH: {
      address: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
      symbol: "WETH",
      decimals: 18,
      coingeckoId: "ethereum"
    },
    WBTC: {
      address: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
      symbol: "WBTC",
      decimals: 8,
      coingeckoId: "wrapped-bitcoin"
    },
    LINK: {
      address: "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
      symbol: "LINK",
      decimals: 18,
      coingeckoId: "chainlink"
    },
    AAVE: {
      address: "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
      symbol: "AAVE",
      decimals: 18,
      coingeckoId: "aave"
    },
    UNI: {
      address: "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
      symbol: "UNI",
      decimals: 18,
      coingeckoId: "uniswap"
    },
    CRV: {
      address: "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
      symbol: "CRV",
      decimals: 18,
      coingeckoId: "curve-dao-token"
    },
    SUSHI: {
      address: "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
      symbol: "SUSHI",
      decimals: 18,
      coingeckoId: "sushi"
    },
    QUICK: {
      address: "0x831753DD7087CaC61aB5644b308642cc1c33Dc13",
      symbol: "QUICK",
      decimals: 18,
      coingeckoId: "quickswap"
    },
    COMP: {
      address: "0x8505b9d2254A7Ae468c0E9dd10Ccea3A837aef5c",
      symbol: "COMP",
      decimals: 18,
      coingeckoId: "compound-governance-token"
    },
    MKR: {
      address: "0x6f7C932e7684666C9fd1d44527765433e01fF61d",
      symbol: "MKR",
      decimals: 18,
      coingeckoId: "maker"
    },
    SNX: {
      address: "0x50B728D8D964fd00C2d0AAD81718b71311feF68a",
      symbol: "SNX",
      decimals: 18,
      coingeckoId: "havven"
    }
  },

  // Trading Parameters
  TRADING: {
    MIN_PROFIT_THRESHOLD: 0.01, // 1%
    SLIPPAGE_TOLERANCE: 500, // 5% in basis points
    MAX_GAS_PRICE: 50000000000, // 50 gwei
    FLASH_LOAN_FEE: 5, // 0.05% Aave flash loan fee
    DEX_FEES: {
      UNISWAP_V3: [500, 3000, 10000], // 0.05%, 0.3%, 1%
      QUICKSWAP: 30, // 0.3%
      SUSHISWAP: 30, // 0.3%
      ONEINCH: 0 // Dynamic
    }
  },

  // API Configuration
  APIS: {
    COINGECKO: {
      BASE_URL: "https://api.coingecko.com/api/v3",
      RATE_LIMIT: 50 // requests per minute
    },
    MORALIS: {
      BASE_URL: "https://deep-index.moralis.io/api/v2",
      RATE_LIMIT: 25 // requests per second
    },
    CHAINLINK: {
      BASE_URL: "https://api.chain.link/v1"
    }
  },

  // Contract Addresses (to be updated after deployment)
  CONTRACTS: {
    FLASH_LOAN_ARBITRAGE: null // Will be set after deployment
  }
};

module.exports = AMOY_CONFIG; 