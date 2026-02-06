from helpers.use_llm import query_llm
from dateutil.parser import parse
import json
import re


def get_stock_isin_info(country:str, symbol: str):
    try:
        question_type = None
        if country in ['USA']:
            question_type = 'isin'
        if question_type:
            res = query_llm(question_type, symbol)
            # Remove Markdown code block markers (like ```json or ```)
            clean_content = re.sub(r"```(?:json)?\n?|\n?```", "", res).strip()
            try:
                res = json.loads(clean_content)
                listing_date = parse(res.get("inception_date", None)).isoformat() if res.get("inception_date", None) else None
                delisting_date = parse(res.get("delisted_date", None)).strftime("%d-%b-%Y").upper() if res.get("delisted_date", None) else None
                listing_date = parse(res.get("inception_date", None)).strftime("%d-%b-%Y").upper() if res.get("inception_date", None) else None
                ret = dict()
                ret[res["isin"]] = {
                    "status": res.get("status", None),
                    "listing_date": listing_date,
                    "delisted_date": delisting_date,
                    "name": res.get("company_name", None),
                    "symbol": symbol,
                    "cap": res.get("cap", None),
                    "market_cap_type": res.get("market_cap_type", None),
                    "industry": res.get("industry", None),
                    "sector": res.get("sector", None),
                    "etf": res.get("etf", False),
                }
                return ret, res["exchange"]
            except json.JSONDecodeError as e:
                print(f"ERROR: failed to decode JSON: {e}")
    except Exception as ex:
        print(f"ERROR: exception {ex} when trying to find ISIN for {country} {symbol}")
    return None, None

def update_isin_info_for_usa(symbol: str):
    try:
        info, exchange = get_stock_isin_info("USA", symbol)
        if info is None:
            print(f"Failed to get ISIN info for {symbol} in USA")
            return
        file_path = f"../USA/{exchange.lower()}_eq.json"
        # read existing data if exists
        try:        
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {}
        except Exception as ex:
            print(f"ERROR: exception {ex} when trying to read existing ISIN info for USA {symbol} at {file_path}")
            raise ex
        # update existing data with new info
        existing_data.update(info)
        # write back to file
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=2)
    except Exception as ex:
        print(f"ERROR: exception {ex} when trying to update ISIN info for USA {symbol}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python update_isin_usa.py <symbol>")
        sys.exit(1)
    symbol = sys.argv[1].upper()
    update_isin_info_for_usa(symbol)
