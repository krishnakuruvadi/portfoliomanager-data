import csv
import os
import pathlib


def get_path_to_csv():
    path = pathlib.Path(__file__).parent.parent.parent.absolute()
    csv_file = os.path.join(path, 'mf.csv')
    return csv_file

def get_mf_entries(csv_file=None):
    if not csv_file:
        csv_file = get_path_to_csv()
    data = dict()
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if not header:
                    data[row[0]] = get_new_entry()
                    data[row[0]]['name'] = row[1]
                    data[row[0]]['isin'] = row[2] 
                    data[row[0]]['isin2'] = row[3]
                    data[row[0]]['fund_house'] = row[4]
                    data[row[0]]['ms_name'] = row[5]
                    data[row[0]]['ms_category'] = row[6]
                    data[row[0]]['ms_investment_style'] = row[7]
                    data[row[0]]['ms_id'] = row[8]
                    data[row[0]]['kuvera_name'] = row[9]
                    data[row[0]]['kuvera_fund_category'] = row[10]
                    data[row[0]]['kuvera_code'] = row[11]
                    data[row[0]]['inception_date'] = row[12]
                header = False
    return data

def get_new_entry():
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
        'inception_date': ''
    }

def write_entries(data, csv_file=None):
    if not csv_file:
        csv_file = get_path_to_csv()
    fields = ['code','name','isin','isin2','fund_house','ms_name','ms_category','ms_investment_style','ms_id', 'kuvera_name', 'kuvera_fund_category', 'kuvera_code', 'inception_date']
    with open(csv_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        for i in sorted (data.keys()) :
            csvwriter.writerow([i, data[i]['name'],data[i]['isin'],data[i]['isin2'],data[i]['fund_house'],data[i]['ms_name'], data[i]['ms_category'], data[i]['ms_investment_style'], data[i]['ms_id'], data[i]['kuvera_name'],data[i]['kuvera_fund_category'],data[i]['kuvera_code'], data[i]['inception_date']])
