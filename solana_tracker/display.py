"""Rich terminal display for wallet data."""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from solana_tracker.parser import Transaction, WalletInfo

console = Console()

KNOWN_PROGRAMS = {
    "11111111111111111111111111111111": "System",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "Token",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1gc8": "Associated Token",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter v6",
    "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin": "Serum DEX",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Whirlpool",
    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s": "Metaplex",
    "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo": "Solend",
    "MagicEden": "Magic Eden",
    "hausS13jsjafwWwGqZTUQRmWyvyxn9EQpqMwV1PBBmk": "Mango",
}


def shorten(addr: str, n: int = 6) -> str:
    if len(addr) <= n * 2 + 3:
        return addr
    return f"{addr[:n]}…{addr[-n:]}"


def program_label(pid: str) -> str:
    return KNOWN_PROGRAMS.get(pid, shorten(pid))


def render_wallet(info: WalletInfo) -> None:
    console.print(
        Panel(
            f"[bold yellow]{info.sol_balance:.4f} SOL[/]\n"
            f"[dim]{info.address}[/]",
            title="[bold]Wallet Balance[/]",
            border_style="yellow",
        )
    )

    if info.tokens:
        table = Table(title="Token Holdings", box=box.ROUNDED, show_lines=True)
        table.add_column("Mint", style="dim")
        table.add_column("Amount", justify="right")
        for t in sorted(info.tokens, key=lambda x: -x.amount):
            table.add_row(shorten(t.mint), f"{t.amount:,.4f}")
        console.print(table)
    else:
        console.print("[dim]No token holdings.[/]")


def render_transactions(txs: List[Transaction]) -> None:
    if not txs:
        console.print("[dim]No transactions found.[/]")
        return

    table = Table(
        title=f"Recent Transactions ({len(txs)})",
        box=box.ROUNDED,
        show_lines=True,
        expand=True,
    )
    table.add_column("Signature", no_wrap=True)
    table.add_column("Time (UTC)", no_wrap=True, style="dim")
    table.add_column("Status")
    table.add_column("Fee (SOL)", justify="right")
    table.add_column("Transfers")
    table.add_column("Programs")

    for tx in txs:
        status = "[green]✓[/]" if tx.status == "success" else "[red]✗[/]"
        time_str = tx.block_time.strftime("%Y-%m-%d %H:%M") if tx.block_time else "—"

        transfer_parts = []
        for tr in tx.transfers[:3]:
            arrow = "←" if tr.direction == "in" else "→"
            transfer_parts.append(f"{arrow} {tr.amount_sol:.4f}")
        transfer_str = "  ".join(transfer_parts) if transfer_parts else "—"

        prog_labels = ", ".join(program_label(p) for p in tx.program_ids[:2])

        table.add_row(
            tx.short_sig,
            time_str,
            status,
            f"{tx.fee_sol:.6f}",
            transfer_str,
            prog_labels,
        )

    console.print(table)


def render_tx_detail(tx: Transaction) -> None:
    console.rule(f"[bold]Transaction[/] {tx.short_sig}")
    console.print(f"[dim]Full signature:[/] {tx.signature}")
    console.print(f"[dim]Time:[/] {tx.block_time} UTC" if tx.block_time else "[dim]Time:[/] unknown")
    console.print(f"[dim]Slot:[/] {tx.slot:,}")
    console.print(f"[dim]Fee:[/] {tx.fee_sol:.8f} SOL")
    status = "[green]Success[/]" if tx.status == "success" else "[red]Failed[/]"
    console.print(f"[dim]Status:[/] {status}")

    if tx.transfers:
        t = Table("Direction", "Amount (SOL)", "From", "To", box=box.SIMPLE)
        for tr in tx.transfers:
            color = "green" if tr.direction == "in" else "red"
            t.add_row(
                f"[{color}]{tr.direction.upper()}[/]",
                f"{tr.amount_sol:.6f}",
                shorten(tr.from_addr),
                shorten(tr.to_addr),
            )
        console.print(t)

    if tx.program_ids:
        console.print("[dim]Programs:[/] " + ", ".join(program_label(p) for p in tx.program_ids))
