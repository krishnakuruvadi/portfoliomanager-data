import argparse

from helpers.mf_check import update_kuvera_name_in_csv


def main():
    parser = argparse.ArgumentParser(
        description="Look up a Kuvera fund name, find its matching AMFI entry in mf.csv "
                    "(via ISIN), and fill in kuvera_name/kuvera_fund_category/kuvera_code "
                    "if that kuvera name isn't already present in mf.csv."
    )
    parser.add_argument('kuvera_name', help='Exact fund name as shown on Kuvera')
    args = parser.parse_args()
    update_kuvera_name_in_csv(args.kuvera_name)


if __name__ == '__main__':
    main()
