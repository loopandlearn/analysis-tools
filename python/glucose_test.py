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
from analysis.analysis import filter_test_devicestatus
from analysis.analysis import filter_test_treatments
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
    # modify this if test is longer than fixed hour duration, e.g., very bad night
    legendFlag = 1 # include legend

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

    devicestatusFilename = foldername + "/" + devicestatusFilename
    content1 = read_raw_nightscout(devicestatusFilename)
    dfDeviceStatus = extract_devicestatus(content1)
    if verboseFlag == 2:
        print(" *** dfDeviceStatus:")
        print(dfDeviceStatus)

    treatmentsFilename = foldername + "/" + treatmentsFilename
    content2 = read_raw_nightscout(treatmentsFilename)
    [nightscoutNote, dfTreatments] = extract_treatments(content2)

    # auto detect if this is a high-glucose test or a low-glucose test.
    [testDetails, dfDeviceStatus] = filter_test_devicestatus(dfDeviceStatus, 110)
    dfTreatments = filter_test_treatments(dfTreatments, testDetails)

    print_dict(testDetails)
    # combine testDetails with older concept of TestIO
    testDetails['nightscoutNote']=nightscoutNote
    testDetails['externalLabel']=externalLabel
    testDetails['plotname']=plotname
    print_dict(testDetails)

    if len(externalLabel) > 5:
        plotLabel = externalLabel
    
    if testDetails['durationInHours'] > duration:
        duration = testDetails['durationInHours']

    resultsDict = report_test_results(reportFilename, testDetails, dfDeviceStatus, dfTreatments)

    # plot pandas dataframe containing Nightscout data
    # always beginning of input filename (YYYY-MM-DDTHH for the output plot)
    # TODO: add indicators for time and value of max IOB, CumIns and indicate on plots
    # TODO: add ability to plot more than one test on a given figure
    plot_single_test(plotFilename, plotLabel, testDetails, legendFlag, duration, testDetails['startTime'],
                     dfDeviceStatus, dfTreatments)
    print(' *** plot created:     ', plotFilename)
    print(' END of Analysis\n')


if __name__ == "__main__":
    main()

