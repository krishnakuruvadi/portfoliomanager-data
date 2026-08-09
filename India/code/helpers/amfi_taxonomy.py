import json
import os

_TAXONOMY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'known_amfi_taxonomy.json')

# Case-by-case corrections for known upstream inconsistencies, applied at
# ingestion time (before the value ever reaches the taxonomy check or
# mf.csv) so a fund doesn't silently change type/category depending on
# which AMFI endpoint last refreshed it. Each field is corrected
# independently (a drifted category can show up alongside any fund type,
# and vice versa); add a new entry here only after explicitly deciding
# which form is canonical. Also run normalize_amfi_taxonomy.py to apply a
# newly-added correction to rows already written to mf.csv.
AMFI_FUND_TYPE_ALIASES = {
    'Equity Schemes': 'Equity Scheme',
}
AMFI_CATEGORY_ALIASES = {
    'Sectoral Fund': 'Sectoral/ Thematic',
}


def apply_known_amfi_aliases(fund_type, fund_category):
    '''
    Correct fund_type and fund_category to their explicitly-approved
    canonical forms if either is a known instance of upstream drift;
    otherwise return them unchanged.
    '''
    fund_type = AMFI_FUND_TYPE_ALIASES.get(fund_type, fund_type)
    fund_category = AMFI_CATEGORY_ALIASES.get(fund_category, fund_category)
    return fund_type, fund_category


def load_known_taxonomy(path=None):
    '''
    Load the explicitly-approved set of amfi_fund_type and amfi_category
    values from known_amfi_taxonomy.json. This file is this repo's
    allowlist: mf.csv's amfi_fund_type/amfi_category columns are small,
    closed vocabularies that downstream consumers match on exactly, and
    upstream AMFI sources are occasionally inconsistent about them (see
    AMFI_FUND_TYPE_ALIASES / AMFI_CATEGORY_ALIASES). A value outside this list is treated as
    unapproved on purpose - add it here explicitly once you've confirmed
    it's a legitimate new or changed category, rather than upstream drift
    that should instead be fixed via an alias correction.

    Returns (known_fund_types: set, known_categories: set).
    '''
    if not path:
        path = _TAXONOMY_PATH
    with open(path, 'r') as f:
        data = json.load(f)
    return set(data.get('amfi_fund_types', [])), set(data.get('amfi_categories', []))


def find_unapproved_taxonomy_rows(csv_file, path=None):
    '''
    Scan mf.csv for rows whose amfi_fund_type or amfi_category isn't in
    the approved taxonomy (blank values are always allowed). Returns a
    list of (line_number, field, value) tuples for offending rows.
    '''
    import csv as csv_module

    known_types, known_categories = load_known_taxonomy(path)
    problems = []
    if not os.path.exists(csv_file):
        return problems
    with open(csv_file, 'r', newline='') as f:
        reader = csv_module.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            fund_type = (row.get('amfi_fund_type') or '').strip()
            category = (row.get('amfi_category') or '').strip()
            if fund_type and fund_type not in known_types:
                problems.append((lineno, 'amfi_fund_type', fund_type))
            if category and category not in known_categories:
                problems.append((lineno, 'amfi_category', category))
    return problems
