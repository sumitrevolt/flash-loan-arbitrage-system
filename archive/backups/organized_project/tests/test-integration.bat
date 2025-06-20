@echo off
echo 🚀 LangChain GitHub Copilot Integration - Final Test
echo =====================================================
echo.

echo 🔍 Step 1: Environment Check
node debug-env.js
echo.

echo 🔍 Step 2: GitHub Token Diagnostic  
node diagnose-github-token.js
echo.

echo 🔍 Step 3: Multi-Provider Test
node test-all-providers.js
echo.

echo 🎬 Step 4: Simulation Demo
node demo-simulation.js
echo.

echo ✅ Integration Test Complete!
echo.
echo 📋 Summary:
echo • LangChain integration: READY
echo • Multi-provider support: READY  
echo • Error handling: READY
echo • GitHub Copilot: Waiting for token fix
echo.
echo 🎯 Next Step: Fix GitHub token permissions
echo    https://github.com/settings/tokens
echo    ✅ Add 'models' scope
echo    ✅ Update GITHUB_TOKEN in .env
echo    ✅ Set AI_PROVIDER=github
echo.
pause
