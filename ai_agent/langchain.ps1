# LangChain Flash Loan AI - PowerShell Commands
# Usage: .\langchain.ps1 [command] [options]

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Param1,
    
    [Parameter(Position=2)]
    [string]$Param2,
    
    [Parameter(Position=3)]
    [string]$Param3
)

# Change to the project directory
$ProjectPath = "c:\Users\Ratanshila\Documents\flash loan"
Set-Location $ProjectPath

Write-Host "🤖 LangChain Flash Loan AI Controller" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

switch ($Command.ToLower()) {
    "help" {
        Write-Host "`n📚 Available Commands:" -ForegroundColor Green
        Write-Host "  help      - Show this help message"
        Write-Host "  test      - Test LangChain connection"
        Write-Host "  analyze   - Analyze current market conditions"
        Write-Host "  decision  - Get flash loan execution decision"
        Write-Host "  strategy  - Generate trading strategy"
        Write-Host "  monitor   - Start continuous monitoring"
        Write-Host "  demo      - Run the full demo"
        Write-Host "  setup     - Setup environment file"
        
        Write-Host "`n💡 Examples:" -ForegroundColor Yellow
        Write-Host "  .\langchain.ps1 test"
        Write-Host "  .\langchain.ps1 analyze"
        Write-Host "  .\langchain.ps1 decision ETH USDC 10"
        Write-Host "  .\langchain.ps1 monitor 5"
        
        Write-Host "`n🔧 Setup:" -ForegroundColor Magenta
        Write-Host "  1. .\langchain.ps1 setup"
        Write-Host "  2. Edit .env file with your OpenAI API key"
        Write-Host "  3. .\langchain.ps1 test"
    }
    
    "setup" {
        Write-Host "`n🔧 Setting up environment..." -ForegroundColor Yellow
        
        if (Test-Path ".env") {
            Write-Host "⚠️  .env file already exists" -ForegroundColor Yellow
        } else {
            Copy-Item ".env.template" ".env"
            Write-Host "✅ Created .env file from template" -ForegroundColor Green
        }
        
        Write-Host "`n📝 Next steps:"
        Write-Host "1. Edit .env file and add your OpenAI API key:"
        Write-Host "   OPENAI_API_KEY=sk-your-key-here"
        Write-Host "2. Run: .\langchain.ps1 test"
        
        # Open .env file for editing
        if (Get-Command notepad -ErrorAction SilentlyContinue) {
            Write-Host "`n🗒️  Opening .env file for editing..."
            Start-Process notepad ".env"
        }
    }
    
    "test" {
        Write-Host "`n🧪 Testing LangChain connection..." -ForegroundColor Yellow
        node langchain-cli.js test
    }
    
    "analyze" {
        Write-Host "`n📊 Analyzing market conditions..." -ForegroundColor Cyan
        node langchain-cli.js analyze
    }
    
    "decision" {
        $tokenA = if ($Param1) { $Param1 } else { "ETH" }
        $tokenB = if ($Param2) { $Param2 } else { "USDC" }
        $amount = if ($Param3) { $Param3 } else { "10" }
        
        Write-Host "`n🤔 Getting decision for $amount $tokenA -> $tokenB..." -ForegroundColor Cyan
        node langchain-cli.js decision $tokenA $tokenB $amount
    }
    
    "strategy" {
        Write-Host "`n📋 Generating trading strategy..." -ForegroundColor Cyan
        node langchain-cli.js strategy
    }
    
    "monitor" {
        $interval = if ($Param1) { $Param1 } else { "5" }
        Write-Host "`n🔄 Starting monitoring (every $interval minutes)..." -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        node langchain-cli.js monitor $interval
    }
    
    "demo" {
        Write-Host "`n🚀 Running full LangChain demo..." -ForegroundColor Cyan
        npm run demo
    }
    
    "status" {
        Write-Host "`n📋 System Status:" -ForegroundColor Green
        
        # Check if .env exists
        if (Test-Path ".env") {
            Write-Host "✅ Environment file exists" -ForegroundColor Green
            
            # Check if OpenAI key is set
            $envContent = Get-Content ".env" -Raw
            if ($envContent -match "OPENAI_API_KEY=sk-") {
                Write-Host "✅ OpenAI API key configured" -ForegroundColor Green
            } else {
                Write-Host "❌ OpenAI API key not configured" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ Environment file missing" -ForegroundColor Red
        }
        
        # Check if dependencies are installed
        if (Test-Path "node_modules") {
            Write-Host "✅ Dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "❌ Dependencies missing - run 'npm install'" -ForegroundColor Red
        }
        
        # Check TypeScript files
        if (Test-Path "ai_agent\langchain-integration.ts") {
            Write-Host "✅ LangChain integration files present" -ForegroundColor Green
        } else {
            Write-Host "❌ Integration files missing" -ForegroundColor Red
        }
    }    default {
        Write-Host "`n❌ Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\langchain.ps1 help' for available commands"
    }
}
}

Write-Host ""
