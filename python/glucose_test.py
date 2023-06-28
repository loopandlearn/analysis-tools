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
    verboseFlag=0 
    duration = 5 # plot all tests with fixed hour duration
    legendFlag = 1 # include legend

    testIO = {}
    numArgs = len(sys.argv)-1
    reportFilename="glucose_impulse_response.csv"
    # if insufficient arguments, provide help
    if numArgs < 2:
        help(reportFilename)
        exit(1)
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

    # begin filling in testIO here
    testIO = {"scriptname": scriptname,
              "foldername": foldername,
              "devicestatusFilename": devicestatusFilename,
              "treatmentsFilename": treatmentsFilename,
              "externalLabel": externalLabel,
              "reportFilename": reportFilename,
              "plotname": plotname}

    if verboseFlag == 1:
        print_dict(testIO)

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

    # adjust time in case time stamps don't match exactly
    deltaToCheck = pd.to_timedelta(10.0, unit='sec')
    dfTreatments=dfTreatments[(dfTreatments['time'] >= (startTime-deltaToCheck)) & \
                              (dfTreatments['time'] <= (endTime+deltaToCheck))]
    # perform cumsum only after limiting time in dfTreatments
    dfTreatments['insulinCumsum'] = dfTreatments['insulin'].cumsum()

    # add to testIO:
    testIO['startTimeString']=startTimeString
    testIO['endTimeString']=endTimeString
    testIO['nightscoutNote']=nightscoutNote

    if verboseFlag == 2:
        print(startTimeString, endTimeString)
        print(" *** dfTreatments:")
        print(dfTreatments)

    
    # add to testIO:
    testIO['startTimeString']=startTimeString
    testIO['endTimeString']=endTimeString    
 

    if len(externalLabel) > 5:
        plotLabel = externalLabel

    resultsDict = report_test_results(reportFilename, testIO, dfDeviceStatus, dfTreatments)

    # plot pandas dataframe containing Nightscout data
    # always beginning of input filename (YYYY-MM-DDTHH for the output plot)
    # TODO: add indicators for time and value of max IOB, CumIns and indicate on plots
    # TODO: add ability to plot more than one test on a given figure
    plot_single_test(plotFilename, plotLabel, legendFlag, duration, startTime,
                     dfDeviceStatus, dfTreatments)
    print(' *** plot created:     ', plotFilename)
    print(' END of Analysis\n')


if __name__ == "__main__":
    main()

