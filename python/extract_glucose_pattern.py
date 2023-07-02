# extract_glucose_pattern.py

# read in a devicestatus download file (from NS) and create a glucose pattern

#   function names use undercase separated by underscore: function_name
#   variable name use camel case: variableName


import sys
import numpy as np
import pandas as pd
from analysis.analysis import extract_devicestatus
from analysis.analysis import extract_treatments
from file_io.file_io import read_raw_nightscout
from util.report import report_test_results
from util.report import create_glucose_file
from util.plot import plot_single_test
from util.plot import plot_glucose
from util.util import print_dict


def help(reportFilename):
    print("Usage:")
    print("  python extract_glucose_pattern.py arg1")
    print("    arg1 - filename with nightscout download")
    print("    arg2 - (optional) output file for 5 minute glucose values")


def main():
    # 0 = none, 1 = a little verbose, 2 = very verbose
    verboseFlag=0 
    reportFlag = 0
    duration = 0 # plot all tests with fixed hour duration, 0 means auto-scale
    legendFlag = 1 # include legend

    testIO = {}
    numArgs = len(sys.argv)-1
    # if insufficient arguments, provide help
    if numArgs < 1:
        help()
        exit(1)
    else:
        devicestatusFilename = sys.argv[1]

    plotFilename = "plot_glucose.png"
    if numArgs == 2:
        reportFlag = 1
        reportFile = sys.argv[2]

    # begin filling in testIO here
    testIO = {
              "devicestatusFilename": devicestatusFilename,
              "plotname": plotFilename}

    if verboseFlag == 1:
        print_dict(testIO)

    content1 = read_raw_nightscout(devicestatusFilename)
    dfDeviceStatus = extract_devicestatus(content1)
    if verboseFlag == 2:
        print(" *** dfDeviceStatus:")
        print(dfDeviceStatus)

    startTime = dfDeviceStatus.iloc[0]['time']
    endTime = dfDeviceStatus.iloc[-1]['time']
    startTimeString=startTime.strftime("%Y-%m-%d %H:%M")
    endTimeString=endTime.strftime("%Y-%m-%d %H:%M")

    # add to testIO:
    testIO['startTimeString']=startTimeString
    testIO['endTimeString']=endTimeString
    print_dict(testIO)

    if verboseFlag == 2:
        print(startTimeString, endTimeString)
        print(" *** dfDeviceStatus:")
        print(dfDeviceStatus)

    
    # add to testIO:
    testIO['startTimeString']=startTimeString
    testIO['endTimeString']=endTimeString    
 
    # plot pandas dataframe containing Nightscout data
    plotLabel = f'glucose example {startTime}'
    legendFlag = 0
    plot_glucose(plotFilename, plotLabel, legendFlag, duration, startTime,
                     dfDeviceStatus)
    print(' *** plot created:     ', plotFilename)

    if reportFlag:
        numEntry = create_glucose_file(dfDeviceStatus, reportFile)
        print(f"File {reportFile} created with {numEntry} entries")

    print(' END of Analysis\n')


if __name__ == "__main__":
    main()

