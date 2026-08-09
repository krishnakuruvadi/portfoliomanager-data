import csv
import os
import pathlib
import re


ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')


def get_path_to_csv():
    '''
    get_path_to_csv returns full path of the file mf.csv
    '''
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    csv_file = os.path.join(path, 'mf.csv')
    return csv_file


def find_malformed_rows(csv_file):
    '''
    find_malformed_rows scans mf.csv for rows that a naive/unquoted comma
    would have split incorrectly: either the row doesn't have the expected
    number of columns, or its isin column doesn't look like an ISIN (and
    isn't blank or the '-' placeholder used for "no ISIN"). Such rows
    usually mean a `name` contains a literal comma that wasn't CSV-quoted
    when the row was written (e.g. a bulk import), which makes
    csv.DictReader silently shift isin/isin2/fund_house into the wrong
    columns instead of raising an error.

    Returns a list of (line_number, raw_line) tuples for offending rows.
    '''
    problems = []
    if not os.path.exists(csv_file):
        return problems
    with open(csv_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, [])
        expected_len = len(header)
        try:
            isin_idx = header.index('isin')
        except ValueError:
            isin_idx = None
        for lineno, row in enumerate(reader, start=2):
            if len(row) != expected_len:
                problems.append((lineno, ','.join(row)))
                continue
            if isin_idx is not None and isin_idx < len(row):
                value = row[isin_idx].strip()
                if value and value != '-' and not ISIN_RE.match(value):
                    problems.append((lineno, ','.join(row)))
    return problems


def get_mf_entries(csv_file=None):
    '''
    get_mf_entries reads mf.csv file and return entries in dict format

    :param csv_file: Provide location of mf.csv.  If not provided, gets path using get_path_to_csv function
    '''
    if not csv_file:
        csv_file = get_path_to_csv()
    data = dict()
    if os.path.exists(csv_file):
        problems = find_malformed_rows(csv_file)
        if problems:
            lines = ', '.join(str(lineno) for lineno, _ in problems)
            raise ValueError(
                f'{csv_file} has {len(problems)} malformed row(s) at line(s) {lines}: '
                'a `name` likely contains an unquoted comma, which would silently '
                'misalign isin/isin2/fund_house on read. Fix these rows (see '
                'code/fix_mf_csv.py) before reading/writing this file.'
            )
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('code')
                data[code] = get_new_entry()
                data[code]['name'] = row.get('name')
                data[code]['isin'] = row.get('isin') 
                data[code]['isin2'] = row.get('isin2')
                data[code]['fund_house'] = row.get('fund_house')
                data[code]['ms_name'] = row.get('ms_name')
                data[code]['ms_category'] = row.get('ms_category')
                data[code]['ms_investment_style'] = row.get('ms_investment_style')
                data[code]['ms_id'] = row.get('ms_id')
                data[code]['kuvera_name'] = row.get('kuvera_name')
                data[code]['kuvera_fund_category'] = row.get('kuvera_fund_category')
                data[code]['kuvera_code'] = row.get('kuvera_code')
                data[code]['inception_date'] = row.get('inception_date', '')
                data[code]['end_date'] = row.get('end_date', '')
                data[code]['amfi_fund_type'] = row.get('amfi_fund_type', '')
                data[code]['amfi_category'] = row.get('amfi_category', '')
    return data

def get_new_entry():
    '''
    get_new_entry returns an empty entry of mf.csv file in dict format
    '''
    return {
        'name': '', 
        'isin': '', 
        'isin2': '', 
        'fund_house': '',
        'ms_name': '',
        'ms_category': '',
        'ms_investment_style': '',
        'ms_id': '',
        'kuvera_name': '',
        'kuvera_fund_category': '',
        'kuvera_code': '',
        'inception_date': '',
        'amfi_fund_type': '',
        'amfi_category': '',
        'end_date': ''
    }

def write_entries(data, phase, csv_file=None):
    '''
    write_entries writes provided data to mf.csv file
    
    :param data: data to write to mf.csv file
    :param phase: phase after which this write is being done
    :param csv_file: location of mf.csv.  If not provided, path is obtained from get_path_to_csv function
    '''
    print(f'writing data to csv after {phase}')
    if not csv_file:
        csv_file = get_path_to_csv()
    fields = ['code','name','isin','isin2','fund_house', 'inception_date','end_date','amfi_fund_type','amfi_category','ms_name','ms_category','ms_investment_style','ms_id', 'kuvera_name', 'kuvera_fund_category', 'kuvera_code']
    with open(csv_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, lineterminator='\n')
        csvwriter.writerow(fields)
        for i in sorted (data.keys()):
            csvwriter.writerow([i, data[i]['name'],
                                data[i]['isin'],
                                data[i]['isin2'],
                                data[i]['fund_house'],
                                data[i].get('inception_date', ''),
                                data[i].get('end_date', ''),
                                data[i].get('amfi_fund_type', ''),
                                data[i].get('amfi_category', ''),
                                data[i].get('ms_name', ''),
                                data[i].get('ms_category', ''),
                                data[i].get('ms_investment_style', ''),
                                data[i].get('ms_id', ''),
                                data[i].get('kuvera_name', ''),
                                data[i].get('kuvera_fund_category', ''),
                                data[i].get('kuvera_code', '')])
