# util.py
# generic and useful functions


def print_dict(thisDict):
    if len(thisDict) == 0:
        return
    for keys, values in thisDict.items():
        print('  {} =   {}'.format(keys, values))
    print('\n')
