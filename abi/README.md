# ABI Directory

This directory contains all essential Application Binary Interface (ABI) files required for the flash loan and arbitrage system.

## Essential ABIs

- **arbitrage_abi.json**
- **sushiswap_router.json**
- **uniswap_router.json**
- **aave_pool.json**
- **flash_loan_contract.json**
- **iuniswap_v2_pair.json**
- **aave_lending_pool.json**
- **aave_price_oracle.json**
- **aave_data_provider.json**
- **uniswap_v3_pool.json**

## ABI Loader Scripts

- **src/utilities/abi_utils.py**: Python utility for loading and validating ABIs.
- **src/tools/abi_loader.py**: Python utility for loading contract ABIs from various locations, with fallback creation.

## Usage

Use the loader scripts to access ABIs in your Python code. Only essential ABIs are kept after the project-wide cleanup.

---

Obsolete or backup ABIs have been archived or removed as part of the project cleanup.

---

## Loader Script Locations

- Python: `src/utilities/abi_utils.py`, `src/tools/abi_loader.py`
- JavaScript/TypeScript: (see `src/scripts/` for contract setup scripts) 