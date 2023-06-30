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
from file_io.file_io import read_raw_nightscout
from file_io.file_io import read_test_list
from file_io.file_io import read_test_list_scale
from util.report import report_test_results
#from util.plot import plot_single_test
from util.plot import plot_initiate
from util.plot import plot_one
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

    [fig, axes] = plot_initiate()

    testIdx = 0

    for test in testList:
        # begin filling in testIO
        devicestatusFilename = test + "_devicestatus.txt"
        treatmentsFilename = test + "_treatments.txt"
        externalLabel = testLabel[testIdx]
        testIO = {
                "foldername": foldername,
                "devicestatusFilename": devicestatusFilename,
                "treatmentsFilename": treatmentsFilename,
                "externalLabel": externalLabel,
                "nightscoutNote": "",
                "plotname": plotname
                }

        if verboseFlag == 1:
            print_dict(testIO)

        scaleFactor = testScale[testIdx]
        devicestatusFilename = foldername + "/" + devicestatusFilename
        content1 = read_raw_nightscout(devicestatusFilename)
        dfDeviceStatus = extract_devicestatus(content1)

        # scale IOB and adjust label
        dfDeviceStatus['IOB'] = dfDeviceStatus['IOB'].mul(scaleFactor)
        testLabel[testIdx] = f'{testLabel[testIdx]} x {scaleFactor:4.2f}'

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

        resultsDict = report_test_results("", testIO, dfDeviceStatus, dfTreatments)
        if verboseFlag:
            print_dict(resultsDict)

        [fig, axes] = plot_one(fig, axes, testIdx, 
                               duration, startTime, dfDeviceStatus, dfTreatments)
        testIdx += 1

    # plot pandas dataframe containing Nightscout data
    # TODO: add indicators for time and value of max IOB, CumIns and indicate on plots
    titleString = f'Overlay {testIdx} Algorithm Experiments\nFor Same Input Glucose Pattern'
    titleString = f'{titleString}\n{plotSubtitle}'
    # do not include legends with more than 6 plots
    if testIdx > 6:
        legendFlag = 0

    [fig, axes] = plot_format(fig, axes, testLabel, titleString, legendFlag)
    plot_save(plotFilename, fig)
    print(' END of plot overlay test\n')


if __name__ == "__main__":
    main()

