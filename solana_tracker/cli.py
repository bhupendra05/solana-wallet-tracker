"""CLI entry point for solana-wallet-tracker."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console

from solana_tracker.display import console, render_tx_detail, render_transactions, render_wallet
from solana_tracker.parser import parse_transaction, parse_wallet
from solana_tracker.rpc import DEVNET, MAINNET, SolanaRPC


def _make_rpc(network: str, rpc_url: str | None) -> SolanaRPC:
    if rpc_url:
        return SolanaRPC(rpc_url)
    endpoints = {"mainnet": MAINNET, "devnet": DEVNET}
    return SolanaRPC(endpoints.get(network, MAINNET))


@click.group()
def cli():
    """solana-wallet-tracker — Track Solana wallets from your terminal."""


@cli.command("balance")
@click.argument("address")
@click.option("--network", "-n", default="mainnet", type=click.Choice(["mainnet", "devnet"]))
@click.option("--rpc", default=None, help="Custom RPC endpoint")
@click.option("--tokens/--no-tokens", default=True, help="Show SPL token holdings")
def balance_cmd(address, network, rpc, tokens):
    """Show SOL balance and token holdings for a wallet."""
    client = _make_rpc(network, rpc)

    with console.status(f"Fetching balance for [cyan]{address[:12]}…[/]"):
        try:
            balance = client.get_balance(address)
            token_accounts = client.get_token_accounts(address) if tokens else []
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            sys.exit(1)

    info = parse_wallet(address, balance, token_accounts)
    render_wallet(info)


@cli.command("history")
@click.argument("address")
@click.option("--limit", "-l", default=20, show_default=True, help="Number of transactions")
@click.option("--network", "-n", default="mainnet", type=click.Choice(["mainnet", "devnet"]))
@click.option("--rpc", default=None, help="Custom RPC endpoint")
@click.option("--before", default=None, help="Paginate: fetch before this signature")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def history_cmd(address, limit, network, rpc, before, as_json):
    """Show recent transaction history for a wallet."""
    client = _make_rpc(network, rpc)

    with console.status("Fetching signatures…"):
        try:
            sigs = client.get_signatures_for_address(address, limit=limit, before=before)
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            sys.exit(1)

    if not sigs:
        console.print("[dim]No transactions found.[/]")
        return

    transactions = []
    with console.status(f"Fetching {len(sigs)} transactions…"):
        for sig_info in sigs:
            sig = sig_info.get("signature")
            if not sig:
                continue
            try:
                tx_data = client.get_transaction(sig)
                if tx_data:
                    tx = parse_transaction(tx_data, address)
                    if tx:
                        transactions.append(tx)
                    else:
                        # Minimal fallback from signature info
                        from solana_tracker.parser import Transaction
                        from datetime import datetime
                        bt = sig_info.get("blockTime")
                        transactions.append(Transaction(
                            signature=sig,
                            block_time=datetime.utcfromtimestamp(bt) if bt else None,
                            slot=sig_info.get("slot", 0),
                            fee_sol=0,
                            status="failed" if sig_info.get("err") else "success",
                        ))
            except Exception:
                pass  # skip failed fetches silently

    if as_json:
        out = [
            {
                "signature": t.signature,
                "time": str(t.block_time),
                "status": t.status,
                "fee_sol": t.fee_sol,
                "slot": t.slot,
            }
            for t in transactions
        ]
        click.echo(json.dumps(out, indent=2))
    else:
        render_transactions(transactions)


@cli.command("tx")
@click.argument("signature")
@click.option("--network", "-n", default="mainnet", type=click.Choice(["mainnet", "devnet"]))
@click.option("--rpc", default=None)
def tx_cmd(signature, network, rpc):
    """Show detailed info for a single transaction."""
    client = _make_rpc(network, rpc)

    with console.status("Fetching transaction…"):
        try:
            tx_data = client.get_transaction(signature)
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            sys.exit(1)

    if not tx_data:
        console.print("[red]Transaction not found[/]")
        sys.exit(1)

    tx = parse_transaction(tx_data, "")
    if tx:
        render_tx_detail(tx)
    else:
        console.print("[red]Could not parse transaction[/]")


@cli.command("watch")
@click.argument("address")
@click.option("--interval", "-i", default=15, show_default=True, help="Poll interval in seconds")
@click.option("--network", "-n", default="mainnet", type=click.Choice(["mainnet", "devnet"]))
@click.option("--rpc", default=None)
def watch_cmd(address, interval, network, rpc):
    """Watch a wallet for new transactions in real time."""
    import time
    client = _make_rpc(network, rpc)

    console.print(f"[bold]Watching[/] [cyan]{address[:16]}…[/]  (interval: {interval}s)")
    console.print("[dim]Press Ctrl+C to stop[/]\n")

    seen: set[str] = set()

    try:
        while True:
            try:
                sigs = client.get_signatures_for_address(address, limit=10)
                for sig_info in sigs:
                    sig = sig_info.get("signature", "")
                    if sig and sig not in seen:
                        seen.add(sig)
                        if len(seen) > 10:  # skip initial batch display
                            try:
                                tx_data = client.get_transaction(sig)
                                tx = parse_transaction(tx_data, address)
                                if tx:
                                    console.rule("[bold green]New Transaction[/]")
                                    render_tx_detail(tx)
                            except Exception:
                                pass
            except Exception as e:
                console.print(f"[dim yellow]Poll error: {e}[/]")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/]")


def main():
    cli()


if __name__ == "__main__":
    main()
