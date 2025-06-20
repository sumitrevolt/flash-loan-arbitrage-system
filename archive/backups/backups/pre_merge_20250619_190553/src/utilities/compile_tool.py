"""
Forge Compile Tool

MCP tool wrapper for Foundry's forge build command, providing smart contract
compilation with optimization, artifact generation, and integration with
the existing Hardhat-based flash loan system.
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...server.tool_registry import BaseTool, ToolSchema, create_tool_schema


class ForgeCompileTool(BaseTool):
    """
    Tool for compiling Solidity contracts using Foundry forge.
    
    Integrates with existing Hardhat configuration and synchronizes
    artifacts for the flash loan arbitrage system.
    """
    
    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(config, logger)
        self.forge_path = config["foundry"]["forge_path"]
        self.workspace_path = Path(config["foundry"]["workspace_root"])
        self.contracts_dir = config["foundry"]["contracts_dir"]
        self.artifacts_dir = config["foundry"]["artifacts_dir"]
        self.hardhat_config_path = config["integration"]["hardhat_config_path"]
        
    async def initialize(self) -> bool:
        """Initialize the compile tool."""
        try:
            # Verify forge is available
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace result: str = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
            result: str = await asyncio.create_subprocess_exec(
                self.forge_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                self.logger.error(f"Forge not available: {stderr.decode()}")
                return False
            
            self.logger.info(f"Forge version: {stdout.decode().strip()}")
            
            # Ensure workspace directories exist
            self._ensure_directories()
            
            # Initialize foundry.toml if needed
            await self._ensure_foundry_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize forge compile tool: {e}")
            return False
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        dirs_to_create = [
            self.workspace_path / self.contracts_dir,
            self.workspace_path / self.artifacts_dir,
            self.workspace_path / "cache",
            self.workspace_path / "lib",
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {dir_path}")
    
    async def _ensure_foundry_config(self) -> None:
        """Ensure foundry.toml exists with proper configuration."""
        foundry_toml_path = self.workspace_path / "foundry.toml"
        
        if not foundry_toml_path.exists():
            # Create foundry.toml based on hardhat config
            foundry_config = await self._generate_foundry_config()
            
            with open(foundry_toml_path, 'w') as f:
                f.write(foundry_config)
            
            self.logger.info(f"Created foundry.toml at {foundry_toml_path}")
    
    async def _generate_foundry_config(self) -> str:
        """Generate foundry.toml configuration based on hardhat config."""
        # Read Hardhat configuration for reference
        hardhat_config = await self._read_hardhat_config()
        
        # Extract Solidity version and optimizer settings
        solc_version = "0.8.20"  # Default
        optimizer_runs = 200     # Default
        
        if hardhat_config and "solidity" in hardhat_config:
            solidity_config = hardhat_config["solidity"]
            if isinstance(solidity_config, dict):
                if "compilers" in solidity_config:
                    # Use the latest compiler version
                    compilers = solidity_config["compilers"]
                    if compilers:
                        latest_compiler = compilers[-1]
                        solc_version = latest_compiler.get("version", solc_version)
                        if "settings" in latest_compiler:
                            optimizer = latest_compiler["settings"].get("optimizer", {})
                            if optimizer.get("enabled"):
                                optimizer_runs = optimizer.get("runs", optimizer_runs)
        
        foundry_config = f"""[profile.default]
src = "{self.contracts_dir}"
out = "{self.artifacts_dir}"
libs = ["lib"]
cache_path = "cache"

# Solidity compiler settings
solc_version = "{solc_version}"
optimizer = true
optimizer_runs = {optimizer_runs}
via_ir = true

# Gas reporting
gas_reports = ["*"]

# Additional settings for flash loan contracts
auto_detect_solc = false
force = false
evm_version = "london"

# Network configurations
[rpc_endpoints]
polygon = "https://polygon.gateway.tenderly.co"
mumbai = "https://rpc-mumbai.maticvigil.com"

[etherscan]
polygon = {{ key = "${{POLYGONSCAN_API_KEY}}" }}
"""
        return foundry_config
    
    async def _read_hardhat_config(self) -> Optional[Dict[str, Any]]:
        """Read and parse Hardhat configuration."""
        try:
            hardhat_path = self.workspace_path / self.hardhat_config_path
            if not hardhat_path.exists():
                return None
            
            # This is a simplified parser - in production you might want to use a JS parser
            with open(hardhat_path, 'r') as f:
                content = f.read()
            
            # Extract basic configuration (simplified approach)
            config = {}
            
            # This is a very basic parser - you might want to use a proper JS parser
            # For now, we'll use defaults and let the user configure foundry.toml manually
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Could not read Hardhat config: {e}")
            return None
    
    def get_schema(self) -> ToolSchema:
        """Get the tool schema definition."""
        return create_tool_schema(
            name="forge_compile",
            description="Compile Solidity contracts using Foundry forge with optimization and artifact generation",
            input_schema={
                "type": "object",
                "properties": {
                    "contracts_path": {
                        "type": "string",
                        "description": "Path to contracts directory",
                        "default": "contracts_deploy"
                    },
                    "output_path": {
                        "type": "string", 
                        "description": "Path to output artifacts directory",
                        "default": "artifacts_deploy"
                    },
                    "optimizer_runs": {
                        "type": "integer",
                        "description": "Number of optimizer runs",
                        "default": 200,
                        "minimum": 1,
                        "maximum": 1000000
                    },
                    "solc_version": {
                        "type": "string",
                        "description": "Solidity compiler version",
                        "default": "0.8.20"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force recompilation of all contracts",
                        "default": False
                    },
                    "extra_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional forge build arguments",
                        "default": []
                    }
                }
            },
            category="forge",
            tags=["compilation", "solidity", "foundry"],
            timeout=120,
            requires_foundry=True
        )
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize arguments."""
        validated = {}
        
        # Validate contracts path
        contracts_path = arguments.get("contracts_path", self.contracts_dir)
        validated["contracts_path"] = str(contracts_path)
        
        # Validate output path
        output_path = arguments.get("output_path", self.artifacts_dir)
        validated["output_path"] = str(output_path)
        
        # Validate optimizer runs
        optimizer_runs = arguments.get("optimizer_runs", 200)
        validated["optimizer_runs"] = max(1, min(1000000, int(optimizer_runs)))
        
        # Validate Solidity version
        solc_version = arguments.get("solc_version", "0.8.20")
        validated["solc_version"] = str(solc_version)
        
        # Validate force flag
        validated["force"] = bool(arguments.get("force", False))
        
        # Validate extra args
        extra_args = arguments.get("extra_args", [])
        if isinstance(extra_args, list):
            validated["extra_args"] = [str(arg) for arg in extra_args]
        else:
            validated["extra_args"] = []
        
        return validated
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the forge compile command."""
        try:
            contracts_path = kwargs.get("contracts_path", self.contracts_dir)
            output_path = kwargs.get("output_path", self.artifacts_dir)
            optimizer_runs = kwargs.get("optimizer_runs", 200)
            solc_version = kwargs.get("solc_version", "0.8.20")
            force = kwargs.get("force", False)
            extra_args = kwargs.get("extra_args", [])
            
            self.logger.info(f"Compiling contracts with forge...")
            
            # Build forge command
            cmd = [
                self.forge_path,
                "build",
                "--root", str(self.workspace_path),
                "--contracts", contracts_path,
                "--out", output_path,
                "--optimize",
                "--optimizer-runs", str(optimizer_runs),
                "--use", solc_version,
                "--extra-output", "abi",
                "--extra-output", "metadata",
                "--extra-output", "devdoc",
                "--extra-output", "userdoc",
                "--extra-output", "storageLayout"
            ]
            
            if force:
                cmd.append("--force")
            
            # Add extra arguments
            cmd.extend(extra_args)
            
            # Execute compilation
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            success = process.returncode == 0
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if success:
                self.logger.info("Compilation completed successfully")
                
                # Analyze compilation results
                compilation_stats = await self._analyze_compilation_results(output_path)
                
                # Sync with Hardhat artifacts if enabled
                if self.config["integration"]["sync_configs"]:
                    await self._sync_hardhat_artifacts(output_path)
                
                return {
                    "success": True,
                    "output": output,
                    "compilation_stats": compilation_stats,
                    "artifacts_path": str(self.workspace_path / output_path),
                    "contracts_compiled": compilation_stats["contracts_count"],
                    "compiler_version": solc_version,
                    "optimizer_runs": optimizer_runs
                }
            else:
                self.logger.error(f"Compilation failed: {error_output}")
                return {
                    "success": False,
                    "error": error_output,
                    "output": output,
                    "exit_code": process.returncode
                }
                
        except Exception as e:
            self.logger.error(f"Error executing forge compile: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_compilation_results(self, output_path: str) -> Dict[str, Any]:
        """Analyze compilation results and gather statistics."""
        try:
            artifacts_dir = self.workspace_path / output_path
            
            # Count compiled contracts
            contract_files = list(artifacts_dir.rglob("*.sol/*.json"))
            
            # Gather contract information
            contracts = []
            total_bytecode_size = 0
            
            for contract_file in contract_files:
                try:
                    with open(contract_file, 'r') as f:
                        artifact = json.load(f)
                    
                    bytecode = artifact.get("bytecode", {}).get("object", "")
                    bytecode_size = len(bytecode) // 2  # Convert hex to bytes
                    
                    contracts.append({
                        "name": contract_file.stem,
                        "file": str(contract_file.relative_to(artifacts_dir)),
                        "bytecode_size": bytecode_size,
                        "has_abi": bool(artifact.get("abi")),
                        "has_metadata": bool(artifact.get("metadata"))
                    })
                    
                    total_bytecode_size += bytecode_size
                    
                except Exception as e:
                    self.logger.warning(f"Could not analyze {contract_file}: {e}")
            
            return {
                "contracts_count": len(contracts),
                "contracts": contracts,
                "total_bytecode_size": total_bytecode_size,
                "artifacts_directory": str(artifacts_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing compilation results: {e}")
            return {
                "contracts_count": 0,
                "contracts": [],
                "total_bytecode_size": 0,
                "error": str(e)
            }
    
    async def _sync_hardhat_artifacts(self, output_path: str) -> None:
        """Sync Foundry artifacts with Hardhat artifacts directory."""
        try:
            foundry_artifacts = self.workspace_path / output_path
            hardhat_artifacts = self.workspace_path / "artifacts_deploy"
            
            if foundry_artifacts.exists() and foundry_artifacts != hardhat_artifacts:
                self.logger.info("Syncing Foundry artifacts with Hardhat artifacts...")
                
                # Copy relevant files
                import shutil
                
                # Ensure hardhat artifacts directory exists
                hardhat_artifacts.mkdir(parents=True, exist_ok=True)
                
                # Copy compiled contract artifacts
                for contract_file in foundry_artifacts.rglob("*.sol/*.json"):
                    relative_path = contract_file.relative_to(foundry_artifacts)
                    target_path = hardhat_artifacts / relative_path
                    
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(contract_file, target_path)
                
                self.logger.info("Artifacts synchronized successfully")
                
        except Exception as e:
            self.logger.warning(f"Could not sync artifacts: {e}")