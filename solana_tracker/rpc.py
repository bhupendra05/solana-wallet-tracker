"""Solana JSON-RPC client (no external SDK required)."""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import requests

MAINNET = "https://api.mainnet-beta.solana.com"
DEVNET = "https://api.devnet.solana.com"


class SolanaRPC:
    def __init__(self, endpoint: str = MAINNET, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
        self._id = 0

    def _call(self, method: str, params: list) -> Any:
        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params,
        }
        resp = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error: {data['error']}")
        return data.get("result")

    def get_balance(self, pubkey: str) -> int:
        """Returns balance in lamports."""
        return self._call("getBalance", [pubkey])["value"]

    def get_account_info(self, pubkey: str) -> Optional[dict]:
        result = self._call(
            "getAccountInfo",
            [pubkey, {"encoding": "jsonParsed", "commitment": "confirmed"}],
        )
        return result.get("value")

    def get_token_accounts(self, owner: str) -> list[dict]:
        result = self._call(
            "getTokenAccountsByOwner",
            [
                owner,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )
        return result.get("value", [])

    def get_signatures_for_address(
        self, pubkey: str, limit: int = 20, before: Optional[str] = None
    ) -> list[dict]:
        params: list = [pubkey, {"limit": limit, "commitment": "confirmed"}]
        if before:
            params[1]["before"] = before
        return self._call("getSignaturesForAddress", params) or []

    def get_transaction(self, signature: str) -> Optional[dict]:
        return self._call(
            "getTransaction",
            [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        )

    def get_multiple_accounts(self, pubkeys: list[str]) -> list[Optional[dict]]:
        if not pubkeys:
            return []
        result = self._call(
            "getMultipleAccounts",
            [pubkeys, {"encoding": "jsonParsed"}],
        )
        return result.get("value", [])
