"""Parse raw Solana RPC responses into friendly structures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


LAMPORTS_PER_SOL = 1_000_000_000


@dataclass
class TokenBalance:
    mint: str
    symbol: str
    amount: float
    decimals: int
    usd_value: Optional[float] = None


@dataclass
class WalletInfo:
    address: str
    sol_balance: float
    tokens: List[TokenBalance] = field(default_factory=list)


@dataclass
class Transfer:
    direction: str       # "in" | "out" | "self"
    amount_sol: float
    from_addr: str
    to_addr: str


@dataclass
class Transaction:
    signature: str
    block_time: Optional[datetime]
    slot: int
    fee_sol: float
    status: str          # "success" | "failed"
    transfers: List[Transfer] = field(default_factory=list)
    program_ids: List[str] = field(default_factory=list)
    memo: Optional[str] = None

    @property
    def short_sig(self) -> str:
        return f"{self.signature[:8]}…{self.signature[-8:]}"


def lamports_to_sol(lamports: int) -> float:
    return lamports / LAMPORTS_PER_SOL


def parse_wallet(address: str, balance_lamports: int, token_accounts: list) -> WalletInfo:
    tokens = []
    for acct in token_accounts:
        info = acct.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
        token_amount = info.get("tokenAmount", {})
        amount = float(token_amount.get("uiAmount") or 0)
        decimals = int(token_amount.get("decimals", 0))
        mint = info.get("mint", "unknown")
        tokens.append(
            TokenBalance(
                mint=mint,
                symbol=mint[:8],   # symbol lookup would need a token list
                amount=amount,
                decimals=decimals,
            )
        )
    # Filter dust
    tokens = [t for t in tokens if t.amount > 0]
    return WalletInfo(
        address=address,
        sol_balance=lamports_to_sol(balance_lamports),
        tokens=tokens,
    )


def parse_transaction(tx_data: dict, wallet_address: str) -> Optional[Transaction]:
    if not tx_data:
        return None

    meta = tx_data.get("meta", {}) or {}
    tx = tx_data.get("transaction", {}) or {}

    status = "failed" if meta.get("err") else "success"
    fee = lamports_to_sol(meta.get("fee", 0))
    slot = tx_data.get("slot", 0)
    block_time = tx_data.get("blockTime")
    dt = datetime.utcfromtimestamp(block_time) if block_time else None

    # Extract signature
    sigs = tx.get("signatures", [])
    sig = sigs[0] if sigs else "unknown"

    # Parse SOL transfers from pre/post balances
    account_keys = []
    message = tx.get("message", {})
    for ak in message.get("accountKeys", []):
        if isinstance(ak, dict):
            account_keys.append(ak.get("pubkey", ""))
        else:
            account_keys.append(str(ak))

    pre_bals = meta.get("preBalances", [])
    post_bals = meta.get("postBalances", [])

    transfers = []
    for i, (pre, post) in enumerate(zip(pre_bals, post_bals)):
        diff = post - pre
        if abs(diff) < 5000:  # ignore dust
            continue
        addr = account_keys[i] if i < len(account_keys) else "unknown"
        if diff < 0:
            transfers.append(
                Transfer("out", lamports_to_sol(abs(diff)), addr, "unknown")
            )
        else:
            transfers.append(
                Transfer("in", lamports_to_sol(abs(diff)), "unknown", addr)
            )

    # Program IDs
    program_ids = []
    for instr in message.get("instructions", []):
        if isinstance(instr, dict):
            pid = instr.get("programId") or (
                account_keys[instr["programIdIndex"]]
                if "programIdIndex" in instr and instr["programIdIndex"] < len(account_keys)
                else None
            )
            if pid:
                program_ids.append(pid)

    return Transaction(
        signature=sig,
        block_time=dt,
        slot=slot,
        fee_sol=fee,
        status=status,
        transfers=transfers,
        program_ids=list(set(program_ids)),
    )
