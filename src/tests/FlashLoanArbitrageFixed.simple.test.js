const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FlashLoanArbitrageFixed - Simple Tests", function () {
    let flashLoanContract;
    let owner;
    let otherAccount;
    const AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";

    beforeEach(async function () {
        [owner, otherAccount] = await ethers.getSigners();
        const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
        flashLoanContract = await FlashLoanArbitrage.deploy(AAVE_POOL_ADDRESS_PROVIDER);
        await flashLoanContract.deployed();
    });

    describe("Deployment", function () {
        it("Should deploy successfully", async function () {
            expect(await flashLoanContract.owner()).to.equal(owner.address);
            expect(await flashLoanContract.ADDRESSES_PROVIDER()).to.equal(AAVE_POOL_ADDRESS_PROVIDER);
        });

        it("Should initialize with correct parameters", async function () {
            expect((await flashLoanContract.slippageTolerance()).toString()).to.equal("500");
            expect((await flashLoanContract.maxFailedTransactions()).toString()).to.equal("6");
            expect((await flashLoanContract.feePercentage()).toString()).to.equal("500");
            expect(await flashLoanContract.feesEnabled()).to.equal(true);
        });

        it("Should whitelist initial tokens", async function () {
            const WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619";
            const USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";
            
            expect(await flashLoanContract.whitelistedTokens(WETH)).to.equal(true);
            expect(await flashLoanContract.whitelistedTokens(USDC)).to.equal(true);
        });

        it("Should approve initial DEXes", async function () {
            const uniswapV3Router = await flashLoanContract.uniswapV3Router();
            expect(await flashLoanContract.approvedDexes(uniswapV3Router)).to.equal(true);
        });
    });

    describe("Token Management", function () {
        it("Should allow owner to whitelist tokens", async function () {
            const testToken = "0x1234567890123456789012345678901234567890";
            
            await flashLoanContract.connect(owner).whitelistToken(testToken, true);
            expect(await flashLoanContract.whitelistedTokens(testToken)).to.equal(true);
        });

        it("Should not allow non-owner to whitelist tokens", async function () {
            const testToken = "0x1234567890123456789012345678901234567890";
            
            try {
                await flashLoanContract.connect(otherAccount).whitelistToken(testToken, true);
                expect.fail("Should have thrown an error");
            } catch (error) {
                expect(error.message).to.include("Ownable");
            }
        });

        it("Should allow batch whitelisting", async function () {
            const tokens = [
                "0x1234567890123456789012345678901234567890",
                "0x2345678901234567890123456789012345678901"
            ];
            
            await flashLoanContract.connect(owner).whitelistTokensBatch(tokens, true);
            expect(await flashLoanContract.whitelistedTokens(tokens[0])).to.equal(true);
            expect(await flashLoanContract.whitelistedTokens(tokens[1])).to.equal(true);
        });
    });

    describe("DEX Management", function () {
        it("Should allow owner to approve DEXes", async function () {
            const testDex = "0x1234567890123456789012345678901234567890";
            
            await flashLoanContract.connect(owner).approveDex(testDex, true);
            expect(await flashLoanContract.approvedDexes(testDex)).to.equal(true);
        });

        it("Should not allow approving zero address as DEX", async function () {
            try {
                await flashLoanContract.connect(owner).approveDex(ethers.constants.AddressZero, true);
                expect.fail("Should have thrown an error");
            } catch (error) {
                expect(error.message).to.include("Invalid DEX address");
            }
        });
    });

    describe("Configuration", function () {
        it("Should allow owner to set slippage tolerance", async function () {
            await flashLoanContract.connect(owner).setSlippageTolerance(300);
            expect((await flashLoanContract.slippageTolerance()).toString()).to.equal("300");
        });

        it("Should not allow slippage tolerance above 10%", async function () {
            try {
                await flashLoanContract.connect(owner).setSlippageTolerance(1500);
                expect.fail("Should have thrown an error");
            } catch (error) {
                expect(error.message).to.include("Slippage tolerance too high");
            }
        });

        it("Should allow owner to set fee parameters", async function () {
            const feeRecipient = "0x1234567890123456789012345678901234567890";
            
            await flashLoanContract.connect(owner).setFeeParameters(300, feeRecipient, true);
            expect((await flashLoanContract.feePercentage()).toString()).to.equal("300");
            expect(await flashLoanContract.feeRecipient()).to.equal(feeRecipient);
            expect(await flashLoanContract.feesEnabled()).to.equal(true);
        });
    });

    describe("Health Check", function () {
        it("Should return healthy status", async function () {
            const healthStatus = await flashLoanContract.getHealthStatus();
            expect(healthStatus.isHealthy).to.equal(true);
            expect(healthStatus.failedTransactions.toString()).to.equal("0");
            expect(healthStatus.isPaused).to.equal(false);
            expect(healthStatus.hasEnoughBalance).to.equal(true);
        });
    });

    describe("Contract Info", function () {
        it("Should return correct contract info", async function () {
            const contractInfo = await flashLoanContract.getContractInfo();
            expect(contractInfo.owner).to.equal(owner.address);
            expect(contractInfo.addressesProvider).to.equal(AAVE_POOL_ADDRESS_PROVIDER);
            expect(contractInfo.slippageTolerance.toString()).to.equal("500");
            expect(contractInfo.feePercentage.toString()).to.equal("500");
            expect(contractInfo.feesEnabled).to.equal(true);
            expect(contractInfo.isPaused).to.equal(false);
        });
    });

    describe("Pause Functionality", function () {
        it("Should allow owner to pause and unpause", async function () {
            await flashLoanContract.connect(owner).pause();
            expect(await flashLoanContract.paused()).to.equal(true);
            
            await flashLoanContract.connect(owner).unpause();
            expect(await flashLoanContract.paused()).to.equal(false);
        });

        it("Should not allow non-owner to pause", async function () {
            try {
                await flashLoanContract.connect(otherAccount).pause();
                expect.fail("Should have thrown an error");
            } catch (error) {
                expect(error.message).to.include("Ownable");
            }
        });
    });

    describe("Access Control", function () {
        it("Should not allow non-owner to call owner functions", async function () {
            try {
                await flashLoanContract.connect(otherAccount).setSlippageTolerance(300);
                expect.fail("Should have thrown an error");
            } catch (error) {
                expect(error.message).to.include("Ownable");
            }
        });
    });
});
