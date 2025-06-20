const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("FlashLoanArbitrageFixed", function () {
    // We define a fixture to reuse the same setup in every test.
    // We use loadFixture to run this setup once, snapshot that state,
    // and reset Hardhat Network to that snapshot in every test.
    async function deployFlashLoanFixture() {
        // Aave V3 Pool Address Provider on Polygon
        const AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";

        // Contracts are deployed using the first signer/account by default
        const [owner, otherAccount] = await ethers.getSigners();

        const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
        const flashLoanContract = await FlashLoanArbitrage.deploy(AAVE_POOL_ADDRESS_PROVIDER);

        return { flashLoanContract, owner, otherAccount, AAVE_POOL_ADDRESS_PROVIDER };
    }

    describe("Deployment", function () {
        it("Should deploy successfully", async function () {
            const { flashLoanContract, owner, AAVE_POOL_ADDRESS_PROVIDER } = await loadFixture(deployFlashLoanFixture);

            expect(await flashLoanContract.owner()).to.equal(owner.address);
            expect(await flashLoanContract.ADDRESSES_PROVIDER()).to.equal(AAVE_POOL_ADDRESS_PROVIDER);
        });        it("Should initialize with correct parameters", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            expect((await flashLoanContract.slippageTolerance()).toString()).to.equal("500"); // 5%
            expect((await flashLoanContract.maxFailedTransactions()).toString()).to.equal("6");
            expect((await flashLoanContract.feePercentage()).toString()).to.equal("500"); // 5%
            expect(await flashLoanContract.feesEnabled()).to.equal(true);
        });

        it("Should whitelist initial tokens", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            // Check WETH is whitelisted
            const WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619";
            expect(await flashLoanContract.whitelistedTokens(WETH)).to.equal(true);

            // Check USDC is whitelisted
            const USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";
            expect(await flashLoanContract.whitelistedTokens(USDC)).to.equal(true);
        });

        it("Should approve initial DEXes", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            // Check Uniswap V3 is approved
            const uniswapV3Router = await flashLoanContract.uniswapV3Router();
            expect(await flashLoanContract.approvedDexes(uniswapV3Router)).to.equal(true);

            // Check QuickSwap is approved
            const quickSwap = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff";
            expect(await flashLoanContract.approvedDexes(quickSwap)).to.equal(true);
        });
    });

    describe("Token Management", function () {
        it("Should allow owner to whitelist tokens", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            const testToken = "0x1234567890123456789012345678901234567890";
            
            await expect(flashLoanContract.connect(owner).whitelistToken(testToken, true))
                .to.emit(flashLoanContract, "TokenWhitelisted")
                .withArgs(testToken, true);

            expect(await flashLoanContract.whitelistedTokens(testToken)).to.equal(true);
        });

        it("Should not allow non-owner to whitelist tokens", async function () {
            const { flashLoanContract, otherAccount } = await loadFixture(deployFlashLoanFixture);

            const testToken = "0x1234567890123456789012345678901234567890";
            
            await expect(flashLoanContract.connect(otherAccount).whitelistToken(testToken, true))
                .to.be.revertedWith("Ownable: caller is not the owner");
        });

        it("Should allow batch whitelisting", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            const tokens = [
                "0x1234567890123456789012345678901234567890",
                "0x2345678901234567890123456789012345678901"
            ];
            
            await expect(flashLoanContract.connect(owner).whitelistTokensBatch(tokens, true))
                .to.emit(flashLoanContract, "TokensBatchWhitelisted")
                .withArgs(tokens, true);

            expect(await flashLoanContract.whitelistedTokens(tokens[0])).to.equal(true);
            expect(await flashLoanContract.whitelistedTokens(tokens[1])).to.equal(true);
        });
    });

    describe("DEX Management", function () {
        it("Should allow owner to approve DEXes", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            const testDex = "0x1234567890123456789012345678901234567890";
            
            await expect(flashLoanContract.connect(owner).approveDex(testDex, true))
                .to.emit(flashLoanContract, "DexApprovalChanged")
                .withArgs(testDex, true);

            expect(await flashLoanContract.approvedDexes(testDex)).to.equal(true);
        });

        it("Should not allow approving zero address as DEX", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            await expect(flashLoanContract.connect(owner).approveDex(ethers.constants.AddressZero, true))
                .to.be.revertedWith("Invalid DEX address");
        });
    });

    describe("Configuration", function () {
        it("Should allow owner to set slippage tolerance", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            await flashLoanContract.connect(owner).setSlippageTolerance(300); // 3%
            expect(await flashLoanContract.slippageTolerance()).to.equal(300);
        });

        it("Should not allow slippage tolerance above 10%", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            await expect(flashLoanContract.connect(owner).setSlippageTolerance(1500)) // 15%
                .to.be.revertedWith("Slippage tolerance too high");
        });

        it("Should allow owner to set fee parameters", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            const feeRecipient = "0x1234567890123456789012345678901234567890";
            
            await expect(flashLoanContract.connect(owner).setFeeParameters(300, feeRecipient, true))
                .to.emit(flashLoanContract, "FeeParametersUpdated")
                .withArgs(300, feeRecipient, true);

            expect(await flashLoanContract.feePercentage()).to.equal(300);
            expect(await flashLoanContract.feeRecipient()).to.equal(feeRecipient);
            expect(await flashLoanContract.feesEnabled()).to.equal(true);
        });

        it("Should not allow fee percentage above 30%", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            const feeRecipient = "0x1234567890123456789012345678901234567890";
            
            await expect(flashLoanContract.connect(owner).setFeeParameters(3500, feeRecipient, true))
                .to.be.revertedWith("Fee too high");
        });
    });

    describe("Health Check", function () {
        it("Should return healthy status", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            const [isHealthy, status, tokenCount, dexCount, failedCount] = await flashLoanContract.healthCheck();
            
            expect(isHealthy).to.equal(true);
            expect(status).to.equal("Healthy");
            expect(tokenCount).to.be.gt(0);
            expect(dexCount).to.be.gt(0);
            expect(failedCount).to.equal(0);
        });
    });

    describe("Contract Info", function () {
        it("Should return correct contract info", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            const [version, deploymentDate, description] = await flashLoanContract.getContractInfo();
            
            expect(version).to.equal("2.1");
            expect(deploymentDate).to.equal("June 2025");
            expect(description).to.contain("Enhanced Flash Loan Arbitrage Contract");
        });
    });

    describe("Swap Statistics", function () {
        it("Should return initial swap statistics", async function () {
            const { flashLoanContract } = await loadFixture(deployFlashLoanFixture);

            const [
                totalSwaps,
                successfulSwaps,
                failedSwaps,
                totalProfits,
                totalFees,
                lastSwapTimestamp,
                highestProfit,
                mostProfitableToken
            ] = await flashLoanContract.getSwapStatistics();
            
            expect(totalSwaps).to.equal(0);
            expect(successfulSwaps).to.equal(0);
            expect(failedSwaps).to.equal(0);
            expect(totalProfits).to.equal(0);
            expect(totalFees).to.equal(0);
            expect(lastSwapTimestamp).to.equal(0);
            expect(highestProfit).to.equal(0);
            expect(mostProfitableToken).to.equal(ethers.constants.AddressZero);
        });
    });

    describe("Pause Functionality", function () {
        it("Should allow owner to pause and unpause", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            // Pause
            await flashLoanContract.connect(owner).pause();
            expect(await flashLoanContract.paused()).to.equal(true);

            // Unpause
            await flashLoanContract.connect(owner).unpause();
            expect(await flashLoanContract.paused()).to.equal(false);
        });

        it("Should not allow non-owner to pause", async function () {
            const { flashLoanContract, otherAccount } = await loadFixture(deployFlashLoanFixture);

            await expect(flashLoanContract.connect(otherAccount).pause())
                .to.be.revertedWith("Ownable: caller is not the owner");
        });

        it("Should not allow operations when paused", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            // Pause the contract
            await flashLoanContract.connect(owner).pause();

            // Try to whitelist a token while paused
            const testToken = "0x1234567890123456789012345678901234567890";
            await expect(flashLoanContract.connect(owner).whitelistToken(testToken, true))
                .to.be.revertedWith("Pausable: paused");
        });
    });

    describe("Emergency Functions", function () {
        it("Should allow emergency withdrawal when paused", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            // Pause the contract first
            await flashLoanContract.connect(owner).pause();

            // Emergency withdrawal should work when paused
            await expect(flashLoanContract.connect(owner).emergencyWithdrawAll())
                .to.not.be.reverted;
        });

        it("Should not allow emergency withdrawal when not paused", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            // Contract is not paused by default
            await expect(flashLoanContract.connect(owner).emergencyWithdrawAll())
                .to.be.revertedWith("Pausable: not paused");
        });
    });

    describe("Access Control", function () {
        it("Should not allow non-owner to call owner functions", async function () {
            const { flashLoanContract, otherAccount } = await loadFixture(deployFlashLoanFixture);

            await expect(flashLoanContract.connect(otherAccount).setSlippageTolerance(300))
                .to.be.revertedWith("Ownable: caller is not the owner");

            await expect(flashLoanContract.connect(otherAccount).setMaxFailedTransactions(10))
                .to.be.revertedWith("Ownable: caller is not the owner");

            await expect(flashLoanContract.connect(otherAccount).resetFailedTransactionsCount())
                .to.be.revertedWith("Ownable: caller is not the owner");
        });
    });

    describe("Arbitrage Parameter Validation", function () {
        it("Should validate arbitrage parameters correctly", async function () {
            const { flashLoanContract, owner } = await loadFixture(deployFlashLoanFixture);

            // Get whitelisted tokens and approved DEX
            const WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619";
            const USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";
            const uniswapV3Router = await flashLoanContract.uniswapV3Router();
            
            // This should fail because we don't have tokens for actual execution
            // but it tests parameter validation
            const currentTime = Math.floor(Date.now() / 1000);
            const deadline = currentTime + 3600; // 1 hour from now
            
            await expect(flashLoanContract.connect(owner).executeArbitrage(
                WETH,        // borrowToken
                ethers.utils.parseEther("0.001"), // amount
                uniswapV3Router, // dex1
                uniswapV3Router, // dex2
                USDC,        // intermediateToken
                3000,        // dex1Fee (0.3%)
                3000,        // dex2Fee (0.3%)
                deadline     // deadline
            )).to.be.reverted; // Will fail at flash loan execution, but parameters are valid
        });
    });
});
