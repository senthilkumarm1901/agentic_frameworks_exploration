from __future__ import annotations

import json
from typing import Any


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))