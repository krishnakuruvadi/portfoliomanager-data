# portfoliomanager-data
Public data for portfolio manager

## Pre-requisites
```bash
pip install -r requirements.txt
cp .env.sample .env
```
Edit the .env file to update values.

### Update gold price for India
```bash
source venv/bin/activate
cd India/code
python update_gold.py
```

### Update NSE/BSE stocks for India
```bash
source venv/bin/activate
cd India/code
python update_share.py
```

### Update USA stock info
```bash
source venv/bin/activate
cd code
python update_isin_usa.py <symbol>
```