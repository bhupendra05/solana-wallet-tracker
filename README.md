# solana-wallet-tracker

> Track any Solana wallet from your terminal — balances, SPL tokens, transaction history, and live monitoring. No API key needed (uses public RPC).

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Solana](https://img.shields.io/badge/chain-Solana-9945FF)

## Features

- **SOL balance + SPL token holdings** — see all tokens in one view
- **Transaction history** — rich table with timestamps, fees, and transfer amounts
- **Transaction detail** — inspect any tx by signature with transfer breakdown
- **Live wallet watch** — poll for new transactions in real time
- **Program labels** — recognises Jupiter, Serum, Metaplex, Whirlpool and more
- **JSON output** — pipe `--json` output to `jq` or scripts
- **Devnet support** — `--network devnet` for testing
- **Custom RPC** — use your Helius/QuickNode/Triton endpoint via `--rpc`

## Installation

```bash
git clone https://github.com/bhupendra05/solana-wallet-tracker.git
cd solana-wallet-tracker
pip install -e .
```

No API key required for public RPC. For higher rate limits, use a private endpoint with `--rpc`.

## Usage

### Check balance

```bash
# SOL balance + SPL tokens
sol-track balance 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM

# SOL only (skip token fetch)
sol-track balance <address> --no-tokens

# Devnet
sol-track balance <address> --network devnet
```

### Transaction history

```bash
# Last 20 transactions
sol-track history 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM

# Last 50
sol-track history <address> --limit 50

# JSON output for scripting
sol-track history <address> --json | jq '.[0]'

# Paginate (fetch before a given signature)
sol-track history <address> --before <signature>
```

### Inspect a transaction

```bash
sol-track tx 5J7X9PqFbVtTZqUQKtR3UkdXfVtNeNJvBHqfexM2XJrR1HEZv4KjRvB6KqWHGdNbXtPvME3FUXYqyB8ZPTnCdeN
```

### Watch for new transactions (live)

```bash
# Poll every 15 seconds (default)
sol-track watch <address>

# Custom interval
sol-track watch <address> --interval 30
```

### Use a custom RPC endpoint

```bash
sol-track history <address> --rpc https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
```

## Example Output

```
╭─ Wallet Balance ──────────────────────────────╮
│  12.4823 SOL                                  │
│  9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM│
╰───────────────────────────────────────────────╯

 Token Holdings
┌──────────────────────┬────────────────┐
│ Mint                 │         Amount │
├──────────────────────┼────────────────┤
│ EPjFWdd5AufqSSqeM…   │  1,250.0000    │
│ Es9vMFrzaCERmJfrF…   │    500.0000    │
└──────────────────────┴────────────────┘

 Recent Transactions (20)
┌───────────┬─────────────────┬────────┬──────────┬────────────────┬─────────────┐
│ Signature │ Time (UTC)      │ Status │ Fee(SOL) │ Transfers      │ Programs    │
├───────────┼─────────────────┼────────┼──────────┼────────────────┼─────────────┤
│ 5J7X9P…  │ 2025-01-15 14:32│ ✓      │ 0.000005 │ → 1.2000       │ Jupiter v6  │
```

## Screenshots

![solana-wallet-tracker demo](docs/demo.png)

## Project Structure

```
solana-wallet-tracker/
├── solana_tracker/
│   ├── cli.py       # Click CLI (balance / history / tx / watch)
│   ├── rpc.py       # Solana JSON-RPC client (pure requests, no SDK)
│   ├── parser.py    # Parse RPC responses into dataclasses
│   └── display.py   # Rich terminal rendering
├── requirements.txt
└── setup.py
```

## License

MIT © bhupendra05
