import os
import pathlib
from helpers.stock_nse import update_nse
from helpers.stock_bse import update_bse


def download_dir():
    return str(pathlib.Path(__file__).parent.parent.absolute())

if __name__ == "__main__":
    update_nse(download_dir())
    update_bse(download_dir())
    