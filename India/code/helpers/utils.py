import datetime

def get_float_or_zero_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float. returning 0')
    return 0

# default format expected of kind 2020-06-01
def get_date_or_none_from_string(input, format='%Y-%m-%d', printout=True):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format).date()
            return res
        except Exception as e:
            if printout:
                print('error converting ', input, ' to date. returning none' + str(e))
    return None

