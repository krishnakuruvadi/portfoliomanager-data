"""Fail if index_returns.json contains an index not in expected_index_names.json."""
import json
import os
import sys

HELPERS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HELPERS_DIR))
EXPECTED_FILE = os.path.join(HELPERS_DIR, 'expected_index_names.json')
RETURNS_FILE = os.path.join(REPO_ROOT, 'index_returns.json')


def find_unexpected(returns, expected):
    """Return {section: [names]} for indices missing from the expected list."""
    expected = set(expected)
    unexpected = {}
    for section, entries in returns.items():
        if not isinstance(entries, list):
            continue
        names = sorted({e['name'] for e in entries if e['name'] not in expected})
        if names:
            unexpected[section] = names
    return unexpected


def main(returns_file=RETURNS_FILE, expected_file=EXPECTED_FILE):
    with open(returns_file) as f:
        returns = json.load(f)
    with open(expected_file) as f:
        expected = json.load(f)
    unexpected = find_unexpected(returns, expected)
    for section, names in unexpected.items():
        for name in names:
            print(f"{returns_file}: unexpected index in {section}: {name}")
    if unexpected:
        print(f"Add intended indices to {expected_file}; otherwise remove them from the data.")
        return 1
    print("index_returns.json: all indices are expected")
    return 0


if __name__ == '__main__':
    sys.exit(main())
