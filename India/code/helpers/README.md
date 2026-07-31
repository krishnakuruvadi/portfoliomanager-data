# Mutual fund update flow notes

## What changed

The mutual-fund update flow now supports an interactive review step before changes are written to the CSV.

When the update pipeline detects changes, it will:

1. show each changed field for an existing entry,
2. print the old value and the new value,
3. ask whether to accept the change,
4. keep the old value if the user answers no or n.

For new entries, the workflow will:

1. print each field name and its value,
2. ask whether the entry looks correct,
3. skip the entry entirely if the user answers no or n.

## Fund-house rename handling

The update flow also handles fund-house renames more safely.

When AMFI updates a fund house name for an entry, the workflow will:

1. update the fund house name in the entry,
2. check whether the new fund-house name can be matched to an existing Kuvera fund-house mapping,
3. keep the existing Kuvera values if a match is found,
4. clear the Kuvera fields only when the new name cannot be matched and the old Kuvera mapping is considered stale.

## Fields affected

The following fields may be cleared when a rename is detected and no matching new-name mapping is found:

- kuvera_name
- kuvera_fund_category
- kuvera_code

## Why this is useful

This avoids wiping valid Kuvera data when a fund house has simply been renamed in a way that still maps to an existing Kuvera entry. It also gives the user a chance to review and reject individual field changes or whole new entries before they are written to the file.

## When this runs

This behavior is applied during the AMFI, AMFI detail, and Kuvera update stages in the MF update pipeline.

## Verification

The interactive review behavior is covered by regression tests in:

- India/code/test/test_update_mf.py
- India/code/test/test_mf_kuvera.py

You can run the focused tests with:

```bash
source venv/bin/activate
python -m pytest India/code/test/test_update_mf.py India/code/test/test_mf_kuvera.py -k "update_mf or fund_house_name_change"
```
