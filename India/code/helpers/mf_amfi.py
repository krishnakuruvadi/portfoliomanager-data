from mftool import Mftool
import datetime
import re
import requests
from .utils import get_date_or_none_from_string, get_date_or_none_from_string, get_float_or_zero_from_string
from .amfi_taxonomy import apply_known_amfi_aliases
from .mf_entry import ISIN_RE

# AMFI's NAVAll.txt uses these as section headers (each followed by
# "(fund_type - fund_category)"), not as an actual fund house name. Without
# excluding them, a section whose per-house name line is missing or
# differently formatted (seen for "Close Ended Schemes" and "Interval Fund
# Schemes") leaves the state-machine's `fund_house` tracking variable set to
# the section label itself, which then gets attributed to every scheme row
# that follows until the next real fund house name line.
SECTION_HEADER_FUND_HOUSE_LABELS = {'open ended schemes', 'close ended schemes', 'interval fund schemes'}


def _name_tokens(name):
    return set(re.findall(r'[a-z0-9]+', (name or '').lower()))


def name_has_new_info(old_name, new_name):
    '''
    Decide whether a freshly-parsed AMFI name should replace the name
    already stored for a scheme. AMFI's Aug 2026 NAVAll.txt format split
    plan/option out of the name into separate fields (see
    parse_scheme_name_nav_date); those fields come back blank for many
    legacy/closed schemes, so naively reconstructing the name from them
    would silently drop real detail that's still accurate (e.g. "Direct
    Plan - Growth" disappearing entirely). Comparing token sets instead of
    exact strings also avoids flagging pure reordering/case/punctuation
    differences (e.g. "Direct - Growth" vs "Direct Plan - Growth Option")
    as a change worth writing. Only treat it as an update when the new
    name contains a word the old one didn't.
    '''
    return not _name_tokens(new_name).issubset(_name_tokens(old_name))


PLAN_WORD_RE = re.compile(r'\bplan\b', re.IGNORECASE)
IDCW_BOILERPLATE_RE = re.compile(r'income\s+distribution\s+cum\s+capital\s+withdrawal', re.IGNORECASE)
IDCW_FILLER_WORDS_RE = re.compile(r'\b(of|options?|optio)\b', re.IGNORECASE)


def _simplify_plan(plan):
    '''"Direct Plan"/"Regular Plan" -> "Direct"/"Regular": the word "Plan" is
    redundant once it's a separate name segment on its own.'''
    return re.sub(r'\s+', ' ', PLAN_WORD_RE.sub('', plan)).strip()


def _simplify_idcw_option(option):
    '''
    Collapse AMFI's verbose "Income Distribution cum Capital Withdrawal"
    phrasing down to "IDCW", while preserving whatever else is in the
    option text (frequency like "Monthly", distribution type like "Payout"
    vs "Reinvestment") - those are still needed to tell apart otherwise
    identical scheme codes that only differ by option (e.g. code 108274's
    "Quarterly Payout" vs code 110282's "Monthly Payout" for the same fund
    and plan). Options that aren't an IDCW expansion (e.g. "GROWTH", "Bonus
    Option") are returned unchanged.
    '''
    if not IDCW_BOILERPLATE_RE.search(option):
        return option.strip()
    result = IDCW_BOILERPLATE_RE.sub('', option)
    result = IDCW_FILLER_WORDS_RE.sub('', result)
    result = result.replace('(', '').replace(')', '')
    result = re.sub(r'\s+', ' ', result).strip(' -&')
    if 'idcw' not in result.lower():
        result = (result + ' IDCW').strip()
    return result


def parse_fund_type_info(scheme_data):
    fund_house = scheme_data.strip()
    amfi_fund_type = ''
    amfi_fund_category = ''

    if '(' in scheme_data and ')' in scheme_data and 'Mutual Fund' not in scheme_data:
        opening_paren = scheme_data.find('(')
        closing_paren = scheme_data.rfind(')')
        if opening_paren != -1 and closing_paren != -1 and opening_paren < closing_paren:
            fund_house = scheme_data[:opening_paren].strip()
            fund_type_info = scheme_data[opening_paren + 1:closing_paren].strip()
            if '-' in fund_type_info:
                splits = fund_type_info.split('-', 1)
                amfi_fund_type = splits[0].strip() if splits else ''
                amfi_fund_category = splits[1].strip() if len(splits) > 1 else ''
                if 'hildren' in amfi_fund_category.lower():
                    amfi_fund_category = "Children's Fund"
            else:
                amfi_fund_type = fund_type_info.strip()
                amfi_fund_category = ''
    return fund_house, amfi_fund_type, amfi_fund_category


def parse_scheme_name_nav_date(scheme):
    '''
    Extract (name, nav, date) from a semicolon-split AMFI NAVAll.txt data
    row. AMFI's historical format is 6 fields - code;isin;isin2;name;nav;
    date - with the plan/option (e.g. "Direct Plan - Growth Option") baked
    into the name. As of Aug 2026 AMFI started emitting 8 fields instead,
    splitting plan and option into their own fields - code;isin;isin2;
    name;plan;option;nav;date - which silently shifted nav/date for every
    row under the old fixed-position parsing (nav became the literal text
    "Direct Plan", breaking float conversion, and date became the option
    text, breaking '%d-%b-%Y' parsing). Handle both shapes so a future
    reversion or partial rollout doesn't break either format.
    '''
    if len(scheme) >= 8:
        parts = [scheme[3].strip(), _simplify_plan(scheme[4]), _simplify_idcw_option(scheme[5])]
        name = ' - '.join(part for part in parts if part)
        return name, scheme[6], scheme[7]
    return scheme[3], scheme[4], scheme[5]


def get_all_schemes()->dict:
    try:
        mf = Mftool()
        url = mf._get_quote_url
        response = mf._session.get(url)
        data = response.text.split("\n")
    except Exception as e:
        print(f'ERROR: exception fetching amfi details using Mftool: {e}.  Trying alternate')
        data = get_schemes_alternate()
    scheme_info = {}
    fund_house = ""
    amfi_fund_type = ""
    amfi_fund_category = ""
    ignored_zero_nav = 0
    ignored_no_isin = 0
    count = 0
    month_ago = datetime.datetime.today() - datetime.timedelta(days=30)
    month_ago = month_ago.date()
    for scheme_data in data:
        if ";INF" in scheme_data:
            try:
                scheme = scheme_data.rstrip().split(";")
                name, nav, date = parse_scheme_name_nav_date(scheme)
                if get_float_or_zero_from_string(nav) > 0:
                    isin = scheme[1].strip() if ISIN_RE.match(scheme[1].strip()) else ''
                    isin2 = scheme[2].strip() if ISIN_RE.match(scheme[2].strip()) else ''
                    scheme_info[scheme[0]] = {'isin': isin,
                                            'isin2':isin2,
                                            'name':name,
                                            'nav':nav,
                                            'date':date,
                                            'amfi_fund_type':amfi_fund_type,
                                            'amfi_category':amfi_fund_category}
                    if fund_house != '' and fund_house.strip().lower() not in SECTION_HEADER_FUND_HOUSE_LABELS:
                        scheme_info[scheme[0]]['fund_house'] = fund_house
                    dt = get_date_or_none_from_string(date, '%d-%b-%Y')
                    if dt and dt < month_ago:
                        scheme_info[scheme[0]]['end_date'] = dt.strftime('%d-%m-%Y')
                    count += 1
            except Exception as e:
                print(f'ERROR: exception processing scheme data {scheme_data}: {e}')
                
        elif scheme_data.strip() != "":
            if ';' not in scheme_data:
                if '(' in scheme_data and ')' in scheme_data and 'Mutual Fund' not in scheme_data:
                    fund_house, amfi_fund_type, amfi_fund_category = parse_fund_type_info(scheme_data)
                    amfi_fund_type, amfi_fund_category = apply_known_amfi_aliases(amfi_fund_type, amfi_fund_category)
                else:
                    fund_house = scheme_data.strip()
    print(f'found {count} funds. ignored {ignored_zero_nav} zero nav funds and {ignored_no_isin} no isin funds')

    return scheme_info


def get_schemes_alternate():
    url = "https://portal.amfiindia.com/spages/NAVAll.txt"
    _session = requests.Session()
    _session.verify = False
    response = _session.get(url)
    data = response.text.split("\n")
    return data

def get_details_amfi(code):
        """
        gets the scheme info for a given scheme code
        :param code: scheme code
        :param as_json: default false
        :return: dict or None
        :raises: HTTPError, URLError
        """
        code = str(code)
        scheme_info = {}
        url = f"https://api.mfapi.in/mf/{code}"
        _session = requests.Session()
        _session.verify = False
        response = _session.get(url).json()
        # close the session after use
        _session.close()
        scheme_data = response['meta']
        scheme_info['fund_house'] = scheme_data['fund_house']
        splits = scheme_data['scheme_category'].split('-')
        fund_type = splits[0].strip() if splits else ''
        fund_category = splits[1].strip() if len(splits) > 1 else ''
        fund_type, fund_category = apply_known_amfi_aliases(fund_type, fund_category)
        scheme_info['amfi_fund_type'] = fund_type
        scheme_info['amfi_fund_category'] = fund_category
        scheme_info['scheme_code'] = scheme_data['scheme_code']
        scheme_info['name'] = scheme_data['scheme_name']
        last_day = response['data'][int(len(response['data']) -1)]
        scheme_info['scheme_start_date'] = last_day['date']
        first_date = get_date_or_none_from_string(response['data'][0]['date'], '%d-%m-%Y')
        month_ago = datetime.datetime.today() - datetime.timedelta(days=30)
        month_ago = month_ago.date()
        if first_date and first_date < month_ago:
            scheme_info['scheme_end_date'] = response['data'][0]['date']
        else:            
            scheme_info['scheme_end_date'] = ''
        return scheme_info


def check_amfi_entry_complete(entry):
    required_fields = ['name', 'fund_house', 'inception_date', 'amfi_fund_type', 'amfi_category']
    for field in required_fields:
        if not entry.get(field):
            #print(f'entry {entry} is missing required field {field}')
            return False
    if entry['isin'] == '' and entry['isin2'] == '':
        return False
    return True
