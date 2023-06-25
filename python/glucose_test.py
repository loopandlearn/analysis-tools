# glucose_test.py
#   function names use undercase separated by underscore: function_name
#   variable name use camel case: variableName

# Set up a google sheet to autogenerate download commands based on time stamps
#   to create the devicestatus and treatments files
# Command line arguments (no flexibility - order is fixed)
# order of args: path timestamp-code [optional: externalLabel] [optional: summary.csv filename]

import sys
import numpy as np
import pandas as pd
from analysis.analysis import extract_devicestatus
from analysis.analysis import extract_treatments
from file_io.file_io import read_raw_nightscout
from util.report import report_test_results
from util.plot import plot_single_test
from util.util import print_dict


def help(reportFilename):
    print("Usage:")
    print("  python glucose_test.py arg1 arg2 [arg3] [arg4]")
    print("    arg1 - path for data I/O")
    print("    arg2 - timestamp identifier (used for I/O)")
    print("       input: arg2_devicestatus.txt, arg2_treatments.txt")
    print("       output: plot_arg2.png")
    print("    arg3 - optional label, otherwise uses note in treatments")
    print("    arg4 - optional output filename, otherwise uses", reportFilename)


def main():
    # 0 = none, 1 = a little verbose, 2 = very verbose
    verboseFlag=1 

    testDict = {}
    numArgs = len(sys.argv)-1
    reportFilename="glucose_impulse_response.csv"
    # if insufficient arguments, provide help
    if numArgs < 2:
        help(reportFilename)
        exit
    else:
        scriptname = sys.argv[0]
        foldername = sys.argv[1]
        timestamp_id = sys.argv[2]
    # optional arguments
    externalLabel=""
    
    if numArgs >= 3:
        externalLabel = sys.argv[3]
    if numArgs == 4:
        reportFilename = sys.argv[4]
    
    devicestatusFilename = timestamp_id + "_devicestatus.txt"
    treatmentsFilename = timestamp_id + "_treatments.txt"
    plotname = "plot_" + timestamp_id + ".png"
    plotFilename = foldername + "/" + plotname

    if verboseFlag == 2:
        print("scriptname:", scriptname)
        print("foldername:", foldername)
        print("devicestatusFilename:", devicestatusFilename)
        print("treatmentsFilename:", treatmentsFilename)
        print("externalLabel:", externalLabel)
        print("reportFilename:", reportFilename)

    devicestatusFilename = foldername + "/" + devicestatusFilename
    content1 = read_raw_nightscout(devicestatusFilename)
    dfDeviceStatus = extract_devicestatus(content1)
    if verboseFlag == 2:
        print(" *** dfDeviceStatus:")
        print(dfDeviceStatus)

    treatmentsFilename = foldername + "/" + treatmentsFilename
    content2 = read_raw_nightscout(treatmentsFilename)
    [nightscoutNote, dfTreatments] = extract_treatments(content2)

    # the first and last glucose should be 110 or the times were not correct
    firstGlucose=dfDeviceStatus.iloc[0]['glucose']
    lastGlucose=dfDeviceStatus.iloc[-1]['glucose']
    if not (firstGlucose == 110 and lastGlucose == 110):
        print("times are not correct - did not capture the whole test")
        print("First and Last Glucose:", firstGlucose, lastGlucose)
        exit(0)

    # use glucose values > 110 as markers for start and end of test.
    dfDeviceStatus=dfDeviceStatus[dfDeviceStatus['glucose'] > 110]
    startTime = dfDeviceStatus.iloc[0]['time']
    endTime = dfDeviceStatus.iloc[-1]['time']
    startTimeString=startTime.strftime("%Y-%m-%d %H:%M")
    endTimeString=endTime.strftime("%Y-%m-%d %H:%M")
    dfTreatments=dfTreatments[(dfTreatments['time'] > startTime) & \
                              (dfTreatments['time'] < endTime)]
    if verboseFlag == 2:
        print(startTimeString, endTimeString)
        print(" *** dfTreatments:")
        print(dfTreatments)
    dfTreatments['insulinCumsum'] = dfTreatments['insulin'].cumsum()
 
    # IOB stats
    maxIOB=dfDeviceStatus['IOB'].max()
    iobTimeDF=dfDeviceStatus[(dfDeviceStatus['IOB'] > (maxIOB-0.01))]
    iobTime=iobTimeDF.iloc[0]['time']
    iobDeltaTimeMinutes=round((iobTime - startTime).seconds/60.0)
    # cumulative insulin stats
    maxCumInsulin=dfTreatments['insulinCumsum'].max()
    ciTimeDF=dfTreatments[(dfTreatments['insulinCumsum'] > (maxCumInsulin-0.01))]
    ciTime=ciTimeDF.iloc[0]['time']
    ciDeltaTimeMinutes=round((ciTime - startTime).seconds/60.0)

    headerString = 'StartTime, MinutesToMaxIOB, MinutesToMaxCumInsulin, maxIOB, maxCumInsulin, ' + \
                       'ExternalLabel, NightscoutNote, Plotname'
    
    # set up a dictionary of the test results
    testDict = {'headerString': headerString,
                'startTimeString': startTimeString,
                'iobDeltaTimeMinutes': iobDeltaTimeMinutes,
                'ciDeltaTimeMinutes': ciDeltaTimeMinutes,
                'maxIOB': maxIOB,
                'maxCumInsulin': maxCumInsulin,
                'externalLabel': externalLabel,
                'nightscoutNote': nightscoutNote,
                'plotname': plotname }

    if verboseFlag == 1:
        print_dict(testDict)

    if len(externalLabel) > 5:
        plotLabel = externalLabel

    report_test_results(testDict, reportFilename)

    # plot pandas dataframe containing Nightscout data
    # always beginning of input filename (YYYY-MM-DDTHH for the output plot)
    # TODO: add indicators for time and value of max IOB, CumIns and indicate on plots
    # TODO: add ability to plot more than one test on a given figure
    plot_single_test(plotFilename, plotLabel, dfDeviceStatus, dfTreatments)
    print(' *** plot created:     ', plotFilename)


if __name__ == "__main__":
    main()

