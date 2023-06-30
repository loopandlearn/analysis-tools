# report.py
# functions for reporting results


import os
import pandas as pd
from util.util import print_dict


def report_test_results(reportFilename, testIO, dfDeviceStatus, dfTreatments):

    # start time come from dfDeviceStatus
    startTime = dfDeviceStatus.iloc[0]['time']

    # IOB stats
    maxIOB=dfDeviceStatus['IOB'].max()
    startIOB=dfDeviceStatus.iloc[0]['IOB']
    adjMaxIOB=maxIOB-startIOB
    finalIOB=dfDeviceStatus.iloc[-1]['IOB']
    iobTimeDF=dfDeviceStatus[(dfDeviceStatus['IOB'] > (maxIOB-0.01))]
    iobTime=iobTimeDF.iloc[0]['time']
    iobDeltaTimeMinutes=round((iobTime - startTime).seconds/60.0)

    # cumulative insulin stats
    maxCumInsulin=dfTreatments['insulinCumsum'].max()
    finalCumInsulin=dfTreatments.iloc[-1]['insulinCumsum']
    ciTimeDF=dfTreatments[(dfTreatments['insulinCumsum'] > (maxCumInsulin-0.01))]
    ciTime=ciTimeDF.iloc[0]['time']
    ciDeltaTimeMinutes=round((ciTime - startTime).seconds/60.0)

    headerString = 'StartTime, MinutesToMaxIOB, MinutesToMaxCumInsulin, ' + \
                    'StartIOB, maxIOB, adjMaxIOB, finalIOB, ' + \
                    'maxCumInsulin, finalCumInsulin, ' + \
                    'ExternalLabel, NightscoutNote, Plotname'
    
    # set up a dictionary of the test results
    resultsDict = {'headerString': headerString,
                'startTimeString': testIO['startTimeString'],
                'iobDeltaTimeMinutes': iobDeltaTimeMinutes,
                'ciDeltaTimeMinutes': ciDeltaTimeMinutes,
                'startIOB': startIOB,
                'maxIOB': maxIOB,
                'adjMaxIOB': adjMaxIOB,
                'finalIOB': finalIOB,
                'maxCumInsulin': maxCumInsulin,
                'finalCumInsulin': finalCumInsulin,
                'externalLabel': testIO['externalLabel'],
                'nightscoutNote': testIO['nightscoutNote'],
                'plotname': testIO['plotname'] }

    if len(reportFilename) > 1:
        write_test_result(reportFilename, resultsDict)
        print('  Row appended to ', reportFilename)

    return resultsDict



def write_test_result(reportFilename, resultsDict):
    isItThere = os.path.isfile(reportFilename)
    # now open the file
    stream_out = open(reportFilename, mode='at')
    if not isItThere:
        # set up a table format order
        stream_out.write(resultsDict['headerString'])
        stream_out.write('\n')
    stream_out.write(f"{resultsDict['startTimeString']},")
    stream_out.write(f"{resultsDict['iobDeltaTimeMinutes']},")
    stream_out.write(f"{resultsDict['ciDeltaTimeMinutes']},")
    stream_out.write(f"{resultsDict['startIOB']:6.2f},")
    stream_out.write(f"{resultsDict['maxIOB']:6.2f},")
    stream_out.write(f"{resultsDict['adjMaxIOB']:6.2f},")
    stream_out.write(f"{resultsDict['finalIOB']:6.2f},")
    stream_out.write(f"{resultsDict['maxCumInsulin']:6.2f},")
    stream_out.write(f"{resultsDict['finalCumInsulin']:6.2f},")
    stream_out.write('"')
    stream_out.write(f"{resultsDict['externalLabel']}")
    stream_out.write('","')
    stream_out.write(f"{resultsDict['nightscoutNote']}")
    stream_out.write('",')
    stream_out.write(f"{resultsDict['plotname']}")
    stream_out.write('\n')
    stream_out.close()


def create_glucose_file(dataframe, reportFile):
    startTime = dataframe.iloc[0]['time']
    startGlucose = dataframe.iloc[0]['glucose']
    stream_out = open(reportFile, mode='wt')
    stream_out.write(f"{startGlucose}\n")
    cycleTime = 290 # sec between values
    haltAtGlucose = 120

    previousTime = startTime
    idx = 1
    for index, row in dataframe.iterrows():
        # change to time
        timeStamp = row['time']
        glucose = row['glucose']
        if glucose > haltAtGlucose:
            print(f"quit at {timeStamp} with glucose of {glucose}")
            break
        elapsedSec = (timeStamp-previousTime).total_seconds()
        if elapsedSec > cycleTime:
            stream_out.write(f"{glucose}\n")
            previousTime = timeStamp
            idx += 1

    stream_out.close()
    return idx