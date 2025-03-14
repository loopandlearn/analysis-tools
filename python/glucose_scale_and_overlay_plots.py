# glucose_scale_and_overlay_plots.py
# copy from glucose_test_overlay_plots and allow a scale factor
#   to do a quick and dirty ISF vs IRC plot for Pete
#
#   Purpose: accept input text file of tests to overlay on a common plot
#            overlayID is used to automatically create the input filename
#                      and output plot name
#            plotSubtitle   if supplied, added to chart title
#            legendOff  if any arg is provided, no legends are plotted

#   function names use undercase separated by underscore: function_name
#   variable name use camel case: variableName

import sys
import numpy as np
import pandas as pd
from analysis.analysis import extract_devicestatus
from analysis.analysis import extract_treatments
from analysis.analysis import filter_test_devicestatus
from analysis.analysis import filter_test_treatments
from file_io.file_io import read_raw_nightscout
from file_io.file_io import read_test_list
from file_io.file_io import read_test_list_scale
from util.report import report_test_results
#from util.plot import plot_single_test
from util.plot import plot_initiate
from util.plot import plot_one_test
from util.plot import plot_format
from util.plot import plot_save
from util.util import print_dict


def help():
    print("Usage:")
    print("  python glucose_test_overlay_plots.py arg1 arg2 arg3")
    print("    arg1 - path for data I/O")
    print("    arg2 - overlayID - see below")
    print("    arg3 - plotSubtitle - if provided and not empty string")
    print("    arg4 - legendFlag - if provided, legends are not shown\n")
    print("           legends are not shown if > 5 test are overlaid\n")
    print(" input_for_arg2.txt : text file with list of identifiers")
    print("       each identifier is used to read in data and overlay on a single plot")
    print(" plot_overlay_arg2.png : output filename")
    print(" scale factor (as if ISF is changed)\n\n")


def main():
    # 0 = none, 1 = a little verbose, 2 = very verbose
    verboseFlag=0
    duration = 5 # plot all tests with fixed hour duration

    testIO = {}
    numArgs = len(sys.argv)-1
    # if insufficient arguments, provide help
    if numArgs < 2:
        help()
        exit(0)

    # assign required arguments
    foldername = sys.argv[1]
    overlayID = sys.argv[2]

    # default values for optional arguments
    plotSubtitle = ""
    legendFlag = 1
    if numArgs >= 3:
        plotSubtitle = sys.argv[3]
    
    if numArgs == 4:
        legendFlag = 0
        print("changed legendFlag to ", legendFlag)

    inputname = f'input_for_{overlayID}.txt'
    plotname = f'plot_overlay_{overlayID}.png'
    
    plotFilename = foldername + "/" + plotname
    inputFilename = foldername + "/" + inputname
    [testList, testLabel, testScale] = read_test_list_scale(inputFilename)
    if len(testList) < 1:
        print("no tests listed in ", inputFilename)
        exit(1)

    # configure plot bases on input arguments
    nrows = 3
    ncols = 1
    [fig, axes] = plot_initiate(nrows, ncols)

    testIdx = 0

    for test in testList:
        # begin filling in testIO
        devicestatusFilename = test + "_devicestatus.json"
        treatmentsFilename = test + "_treatments.json"
        externalLabel = testLabel[testIdx]
        testIO = {
                "foldername": foldername,
                "devicestatusFilename": devicestatusFilename,
                "treatmentsFilename": treatmentsFilename,
                "externalLabel": externalLabel,
                "nightscoutNote": "",
                "plotname": plotname
                }

        scaleFactor = testScale[testIdx]
        devicestatusFilename = foldername + "/" + devicestatusFilename
        content1 = read_raw_nightscout(devicestatusFilename)
        dfDeviceStatus = extract_devicestatus(content1)

        # scale IOB and adjust label
        dfDeviceStatus['IOB'] = dfDeviceStatus['IOB'].mul(scaleFactor)
        testLabel[testIdx] = f'{testLabel[testIdx]} x {scaleFactor:4.2f}'

        treatmentsFilename = foldername + "/" + treatmentsFilename
        content2 = read_raw_nightscout(treatmentsFilename)
        [nightscoutNote, dfTreatments] = extract_treatments(content2)

        # select the range of rows to use for the test analysis
        [testDetails, dfDeviceStatus] = filter_test_devicestatus(dfDeviceStatus, 110)
        dfTreatments = filter_test_treatments(dfTreatments, testDetails)

        # add to testIO:
        testIO['startTimeString']=testDetails['startTimeString']
        testIO['endTimeString']=testDetails['endTimeString']
        testIO['nightscoutNote']=nightscoutNote

        resultsDict = report_test_results("", testIO, dfDeviceStatus, dfTreatments)
        if verboseFlag:
            print_dict(resultsDict)

        [fig, axes] = plot_one_test(fig, axes, testIdx,  duration,
                               testDetails['startTime'], dfDeviceStatus, dfTreatments)
        testIdx += 1

    # plot pandas dataframe containing Nightscout data
    # TODO: add indicators for time and value of max IOB, CumIns and indicate on plots
    titleString = f'Overlay {testIdx} Algorithm Experiments\nFor Same Input Glucose Pattern'
    titleString = f'{titleString}\n{plotSubtitle}'
    # do not include legends with more than 6 plots
    if testIdx > 6:
        legendFlag = 0

    [fig, axes] = plot_format(fig, axes, testDetails, testLabel, titleString, legendFlag)
    plot_save(plotFilename, fig)
    print(' END of plot overlay test\n')


if __name__ == "__main__":
    main()

