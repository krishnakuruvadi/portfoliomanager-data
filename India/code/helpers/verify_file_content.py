import json
import csv
import os
from pathlib import Path
from typing import Tuple, List, Dict


def verify_json_file(file_path: str) -> Tuple[bool, str]:
    """
    Verify if a JSON file is valid and well-formed.
    
    Args:
        file_path: Path to the JSON file to verify
        
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, f"✓ Valid JSON: {file_path}"
    except json.JSONDecodeError as e:
        return False, f"✗ Invalid JSON in {file_path}: {str(e)}"
    except FileNotFoundError:
        return False, f"✗ File not found: {file_path}"
    except Exception as e:
        return False, f"✗ Error reading {file_path}: {str(e)}"


def verify_csv_file(file_path: str) -> Tuple[bool, str]:
    """
    Verify if a CSV file is valid and well-formed.

    Beyond basic parseability, this also checks for rows whose column count
    doesn't match the header - a row with an unquoted comma inside a field
    (e.g. a fund name like "... Direct Plan, IDCW Option") parses as valid
    CSV but silently shifts every later column, so a plain read/row-count
    check wouldn't catch it. For mf.csv specifically, it also runs the
    ISIN-aware check from helpers.mf_entry, which catches the case where
    such a shift happens to land on a row that still has the right column
    count (see find_malformed_rows for why that's possible).

    Args:
        file_path: Path to the CSV file to verify

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to read the CSV file with different delimiters
            csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            reader = csv.reader(f)
            rows = list(reader)
            row_count = len(rows)

            if row_count == 0:
                return False, f"✗ Empty CSV file: {file_path}"

            header_len = len(rows[0])
            ragged = [i for i, row in enumerate(rows[1:], start=2) if len(row) != header_len]
            if ragged:
                sample = ', '.join(str(n) for n in ragged[:10])
                return False, (
                    f"✗ Invalid CSV in {file_path}: {len(ragged)} row(s) don't match "
                    f"the header's {header_len} columns (likely an unquoted comma in a "
                    f"field) at line(s) {sample}"
                )

            if os.path.basename(file_path) == 'mf.csv':
                try:
                    from .mf_entry import find_malformed_rows
                except ImportError:
                    # Running as a standalone script (no parent package),
                    # e.g. `python helpers/verify_file_content.py`.
                    import sys
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from mf_entry import find_malformed_rows
                problems = find_malformed_rows(file_path)
                if problems:
                    sample = ', '.join(str(lineno) for lineno, _ in problems[:10])
                    return False, (
                        f"✗ Invalid CSV in {file_path}: {len(problems)} row(s) have a "
                        f"misaligned isin column (unquoted comma in `name` shifted "
                        f"columns without changing row length) at line(s) {sample}"
                    )

            return True, f"✓ Valid CSV: {file_path} ({row_count} rows)"
    except csv.Error as e:
        return False, f"✗ Invalid CSV in {file_path}: {str(e)}"
    except FileNotFoundError:
        return False, f"✗ File not found: {file_path}"
    except Exception as e:
        return False, f"✗ Error reading {file_path}: {str(e)}"


def main(repository_root: str = None) -> Dict[str, List[Dict]]:
    """
    Verify all JSON and CSV files in the repository.
    
    Args:
        repository_root: Root directory of the repository. 
                        If None, uses the parent directory of this script's location
                        
    Returns:
        Dictionary with validation results containing:
        - 'json_results': List of dicts with file path and validation status
        - 'csv_results': List of dicts with file path and validation status
        - 'summary': Dict with counts of valid/invalid files
    """
    if repository_root is None:
        # Get the repository root (go up from India/code/helpers)
        current_dir = Path(__file__).resolve().parent
        repository_root = current_dir.parent.parent.parent
    
    repository_root = Path(repository_root)
    
    json_results = []
    csv_results = []
    
    print(f"\n{'='*80}")
    print(f"Verifying files in repository: {repository_root}")
    print(f"{'='*80}\n")
    
    # Helper function to check if path should be excluded
    def should_exclude_path(path: Path) -> bool:
        """Check if path contains hidden directories or common dependency folders to skip"""
        excluded_dirs = {'.venv', 'venv', '.env', '__pycache__', 'node_modules', '.git', '.pytest_cache', 'dist', 'build', '.egg-info'}
        return any(part.startswith('.') or part in excluded_dirs for part in path.parts)
    
    # Find and verify all JSON files
    print("JSON Files:")
    print("-" * 80)
    json_files = [f for f in repository_root.rglob("*.json") if not should_exclude_path(f)]
    for json_file in sorted(json_files):
        is_valid, message = verify_json_file(str(json_file))
        json_results.append({"file": str(json_file), "valid": is_valid})
        print(message)
    
    print(f"\n")
    
    # Find and verify all CSV files
    print("CSV Files:")
    print("-" * 80)
    csv_files = [f for f in repository_root.rglob("*.csv") if not should_exclude_path(f)]
    for csv_file in sorted(csv_files):
        is_valid, message = verify_csv_file(str(csv_file))
        csv_results.append({"file": str(csv_file), "valid": is_valid})
        print(message)
    
    print(f"\n")
    
    # Summary
    json_valid = sum(1 for r in json_results if r["valid"])
    json_invalid = len(json_results) - json_valid
    csv_valid = sum(1 for r in csv_results if r["valid"])
    csv_invalid = len(csv_results) - csv_valid
    
    summary = {
        "json": {"total": len(json_results), "valid": json_valid, "invalid": json_invalid},
        "csv": {"total": len(csv_results), "valid": csv_valid, "invalid": csv_invalid},
        "overall": {
            "total": len(json_results) + len(csv_results),
            "valid": json_valid + csv_valid,
            "invalid": json_invalid + csv_invalid
        }
    }
    
    print("Summary:")
    print("-" * 80)
    print(f"JSON Files: {json_valid} valid, {json_invalid} invalid (Total: {len(json_results)})")
    print(f"CSV Files:  {csv_valid} valid, {csv_invalid} invalid (Total: {len(csv_results)})")
    print(f"Overall:    {summary['overall']['valid']} valid, {summary['overall']['invalid']} invalid (Total: {summary['overall']['total']})")
    print(f"{'='*80}\n")
    
    return {
        "json_results": json_results,
        "csv_results": csv_results,
        "summary": summary
    }


if __name__ == "__main__":
    import sys
    repo_root_arg = sys.argv[1] if len(sys.argv) > 1 else None
    results = main(repo_root_arg)
    if results["summary"]["overall"]["invalid"] > 0:
        sys.exit(1)


# To run this script, simply execute it in the terminal. It will automatically find all JSON and CSV files in the repository (excluding common dependency folders) and verify their validity, printing the results and a summary at the end.
# source venv/bin/activate
# python India/code/helpers/verify_file_content.py