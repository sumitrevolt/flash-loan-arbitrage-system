# Project Setup Guide

This guide summarizes the canonical setup and maintenance flow for the flash loan MCP project. For details, see the `README.md` in each major directory.

## 1. MCP Server and Agent Organization
- Use `scripts/intelligent_mcp_organizer.py` to analyze, rank, and organize MCP servers and AI agents.
- See `mcp_servers/README.md` for orchestration scripts and the optimized server/agent set.

## 2. Contract and MCP Setup
- Use scripts in `src/scripts/` for MCP-powered contract setup, deployment, and verification:
  - `mcp-setup.js`, `setup.js`, `ai-deploy.js`, `deploy.js`, `verify.js`
- See `src/scripts/README.md` for usage details.

## 3. Dockerized System Deployment
- Use `deployment/docker/start-unified-system.sh` or `.ps1` to launch the unified Docker system.
- Use `docker-compose.unified.yml` as the canonical Compose file.
- See `deployment/docker/README-UNIFIED.md` for orchestration and troubleshooting.

## 4. ABI Management
- Essential ABIs are in `abi/`.
- Use loader scripts in `src/utilities/abi_utils.py` and `src/tools/abi_loader.py`.
- See `abi/README.md` for details.

## 5. Maintenance and Troubleshooting
- Use scripts in `scripts/` for MCP, Docker, and ABI maintenance.
- See each directory's `README.md` for canonical scripts and instructions.

---

Obsolete, duplicate, or backup scripts and files have been archived or removed as part of the project cleanup. 