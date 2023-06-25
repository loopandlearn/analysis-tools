# report.py
# functions for reporting results


import os
import pandas as pd
from util.util import print_dict


def report_test_results(testDict, reportFilename):
    print_dict(testDict)
    print(reportFilename)
    isItThere = os.path.isfile(reportFilename)
    # now open the file
    stream_out = open(reportFilename, mode='at')
    if not isItThere:
        # set up a table format order
        stream_out.write(testDict['headerString'])
        stream_out.write('\n')
    stream_out.write(f"{testDict['startTimeString']},")
    stream_out.write(f"{testDict['iobDeltaTimeMinutes']},")
    stream_out.write(f"{testDict['ciDeltaTimeMinutes']},")
    stream_out.write(f"{testDict['maxIOB']:6.2f},")
    stream_out.write(f"{testDict['maxCumInsulin']:6.2f},")
    stream_out.write(f"{testDict['externalLabel']},")
    stream_out.write(f"{testDict['nightscoutNote']},")
    stream_out.write(f"{testDict['plotname']}")
    stream_out.write('\n')
    stream_out.close()
    print('  Row appended to ', reportFilename)
