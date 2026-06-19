from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def clean_payload(
    value: Any, *, omit_none: bool = True, omit_empty: bool = False
) -> Any:
    if is_dataclass(value):
        return {
            key: clean_payload(item, omit_none=omit_none, omit_empty=omit_empty)
            for key, item in asdict(value).items()
            if not (omit_none and item is None) and not (omit_empty and item == "")
        }
    if isinstance(value, list):
        return [
            clean_payload(item, omit_none=omit_none, omit_empty=omit_empty)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: clean_payload(item, omit_none=omit_none, omit_empty=omit_empty)
            for key, item in value.items()
            if not (omit_none and item is None) and not (omit_empty and item == "")
        }
    return value
