import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class DuplicateKeyError(ValueError):
    pass


def _dict_raise_on_duplicates(pairs):
    """object_pairs_hook that fails loudly on a repeated key.

    Plain json.load silently keeps the last occurrence of a repeated key,
    which would hide a duplicate ISIN entry instead of flagging it.
    """
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def find_duplicate_symbols(data: Dict[str, dict]) -> Dict[str, List[str]]:
    """Return {symbol: [isin, ...]} for symbols listed under more than one ISIN.

    This is the case that has actually slipped into these files before
    (e.g. EchoStar Corporation appearing under two different ISINs with the
    same symbol) - the ISIN keys are unique, but the same company/symbol was
    duplicated under a second key.
    """
    by_symbol = defaultdict(list)
    for isin, entry in data.items():
        symbol = entry.get("symbol") if isinstance(entry, dict) else None
        if symbol:
            by_symbol[symbol].append(isin)
    return {symbol: isins for symbol, isins in by_symbol.items() if len(isins) > 1}


def check_file_for_duplicates(file_path: str) -> Tuple[bool, str]:
    """Verify a nasdaq_eq.json/nyse_eq.json-style file has no duplicate entries.

    Checks for:
      1. Duplicate top-level JSON keys (duplicate ISIN entries) in the raw file
         - these are silently collapsed by a plain json.load, so they need a
         custom object_pairs_hook to detect.
      2. Duplicate `symbol` values across different ISIN keys.

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f, object_pairs_hook=_dict_raise_on_duplicates)
    except DuplicateKeyError as e:
        return False, f"✗ Duplicate entry in {file_path}: {e}"
    except json.JSONDecodeError as e:
        return False, f"✗ Invalid JSON in {file_path}: {e}"
    except FileNotFoundError:
        return False, f"✗ File not found: {file_path}"

    dup_symbols = find_duplicate_symbols(data)
    if dup_symbols:
        details = "; ".join(f"{symbol} -> {isins}" for symbol, isins in dup_symbols.items())
        return False, f"✗ Duplicate symbol entries in {file_path}: {details}"

    return True, f"✓ No duplicate entries in {file_path} ({len(data)} entries)"


def main(files: List[str] = None) -> bool:
    if files is None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        files = [
            str(repo_root / "USA" / "nasdaq_eq.json"),
            str(repo_root / "USA" / "nyse_eq.json"),
        ]

    all_valid = True
    for file_path in files:
        is_valid, message = check_file_for_duplicates(file_path)
        print(message)
        if not is_valid:
            all_valid = False
    return all_valid


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
