# plot.py
# plotting functions:
#   At one point, only labeled the x-axes for bottom plot of 3.
#   Modify that to plot the middle and bottom plots, 
#   can then clip the plot to show just IOB and have it be labeled properly


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def add_delta_time_column_in_hours(startTime, dataframe):
    # pandas does not handling plotting of deltatime in an transparent manner
    # must convert it to float for consistent plotting
    # the dataframes require the same startTime
    elapsedHoursArray=[]
    oneHrInSec = 3600.0
   
    for index, row in dataframe.iterrows():
        # change to time
        timeStamp = row['time']
        elapsedHours = (timeStamp-startTime).total_seconds()/oneHrInSec
        elapsedHoursArray.append(elapsedHours)

    dataframe['elapsedHours']=elapsedHoursArray
    return dataframe


def select_non_zero_diffs(dataframe, columnString, epsilon):
    # skip time stamps where the column of interest does not change
    # modify usage. Call it with 'elapsedHours' to remove rows that have
    # same glucose time as other rows to get only new data
    dataframe['deltaValue'] = dataframe[columnString].diff()
    dataframe=dataframe[dataframe['deltaValue'].abs() > epsilon]
    dataframe=dataframe.reset_index(drop=True)
    return dataframe


def plot_initiate(nrows, ncols):
    if nrows == 2:
        figSize = (5, 9)
    else:
        figSize =  (5, 10)
    fig, axes = plt.subplots(nrows, ncols, figsize=figSize)

    return fig, axes


def plot_one_test(fig, axes, idx, duration, startTime, dfDeviceStatus, dfTreatments, styleOffset):
    naxes=len(axes)

    colorList = ['black', 'magenta', 'cyan', 'green', 'purple', 
                 'darkgoldenrod', 'red', 'darkviolet', 'sandybrown', 'mediumslateblue']
    styleLineList = ['-', '--', '-.', ':']
    stylePointList = ['p', '*', 'x', '+', '.', 'd']
    # sometimes want to offset the colors to compare items
    styleIdx = idx+styleOffset
    color = colorList[styleIdx%len(colorList)]
    styleLine = styleLineList[styleIdx%len(styleLineList)]
    stylePoint = stylePointList[styleIdx%len(stylePointList)]
    xRange = [0, duration]
    if duration > 4.2:
        bottom_ticks = np.arange(0, duration, step=1)
    else:
        bottom_ticks = np.arange(0, duration, step=0.5)
    dfDeviceStatus = add_delta_time_column_in_hours(startTime, dfDeviceStatus)
    dfTreatments = add_delta_time_column_in_hours(startTime, dfTreatments)

    verboseFlag = 1
    if verboseFlag == 2:
        print(dfDeviceStatus.iloc[0:15])
        print(dfDeviceStatus.iloc[-15:-1])

    filterFlag = 1
    if filterFlag:
        epsilon = 0.06
        dfDeviceStatus = select_non_zero_diffs(dfDeviceStatus, 'elapsedHours', epsilon)

    initialIOB = dfDeviceStatus.iloc[0]['IOB']

    print('\tInitial IOB {0:.2f}, rows uniq elapsedHours {1:d}'.format(initialIOB, len(dfDeviceStatus)))

    if verboseFlag == 2:
        print("After filtering:")
        print(dfDeviceStatus.iloc[0:15])
        print(dfDeviceStatus.iloc[-15:-1])
        print(dfTreatments)

    # plot glucose each time to ensure alignment
    dfDeviceStatus.plot(x='elapsedHours', y='glucose', c=color, ax=axes[0],
                        linestyle=styleLine, marker=stylePoint, xlim=xRange, xticks=bottom_ticks)
    dfDeviceStatus.plot(x='elapsedHours', y='IOB', c=color, ax=axes[1],
                        linestyle=styleLine, marker=stylePoint, xlim=xRange, xticks=bottom_ticks)
    if naxes == 3:
        dfTreatments.plot(x='elapsedHours', y='insulinCumsum', c=color, ax=axes[2],
                        linestyle=styleLine, marker=stylePoint, linewidth=0.2,
                        xlim=xRange, xticks=bottom_ticks)
    plt.draw()
    plt.pause(0.001)

    return fig, axes


def plot_format(fig, axes, testDetails, testLabel, titleString, legendFlag):
    naxes = len(axes)
    axes[0].set_title(titleString)

    for x in axes:
        x.grid('on')
        x.set_xlabel("hours")
        x.xaxis.set_label_position('bottom')

    # set limits for BG (always in mg/dl)
    axes[0].set_ylabel("Glucose (mg/dL)")
    bg_ylim = axes[0].get_ylim()
    if testDetails['type'] == 'high':
        a = min(bg_ylim[0], 0)
        b = max(1.1*bg_ylim[1], 300)
    else:
        a = min(bg_ylim[0], 0)
        b = max(1.1*bg_ylim[1], 250)
    axes[0].set_ylim([a, b])

    # handle case where IOB is never zero for entire plot
    axes[1].set_ylabel("IOB (U)")
    iob_ylim = axes[1].get_ylim()
    if testDetails['type'] == 'high':
        a = min(1.1*iob_ylim[0], -1)
        b = max(1.1*iob_ylim[1], 10)
    else:
        a = min(1.1*iob_ylim[0], -2)
        b = max(1.1*iob_ylim[1], 2)
    axes[1].set_ylim([a, b])

    if naxes == 3:
        axes[2].set_ylabel("Sum Insulin (U)")
        insulinCumsum_ylim = axes[2].get_ylim()
        if testDetails['type'] == 'high':
            a = min(1.1*insulinCumsum_ylim[0], -1)
            b = max(1.1*insulinCumsum_ylim[1], 10)
        else:
            a = min(1.1*insulinCumsum_ylim[0], -2)
            b = max(1.1*insulinCumsum_ylim[1], 2)
        axes[2].set_ylim([a, b])
        axes[2].legend('')

    # anchorTuple = [1.10, 0.90]
    anchorTuple = [1.00, 1.10]
    # Only need one legend for the plot
    axes[0].legend('')
    if legendFlag == 1:
        axes[1].legend(testLabel, loc='right', bbox_to_anchor=anchorTuple, framealpha=1.0)
    else:
        axes[1].legend('')

    plt.draw()
    plt.pause(0.001)

    return fig, axes


def plot_save(outFile, fig):
    plt.draw()
    plt.pause(0.001)
    plt.pause(2)
    plt.savefig(outFile)
    plt.close(fig)
    return


def plot_single_test(outFile, label, testDetails, legendFlag, duration, startTime, dfDeviceStatus,
                     dfTreatments, styleOffset):
    nrows = 3
    ncols = 1
    [fig, axes] = plot_initiate(nrows, ncols)
    idx = 0
    titleString = (f'Analysis: {startTime.strftime("%Y-%m-%d %H:%M")}\n{label}\n')
    [fig, axes] = plot_one_test(fig, axes, idx, duration, startTime, dfDeviceStatus,
                                dfTreatments, styleOffset)
    [fig, axes] = plot_format(fig, axes, testDetails, "", titleString, legendFlag)
    plot_save(outFile, fig)
    return


def plot_glucose(outFile, label, legendFlag, duration, startTime, dfDeviceStatus):
    nrows = 2
    ncols = 1
    [fig, axes] = plot_initiate(nrows, ncols)
    oneHrInSec = 3600.0
    if duration == 0:
        duration= (dfDeviceStatus.iloc[-1]['time']- 
                   dfDeviceStatus.iloc[0]['time']).total_seconds()/oneHrInSec
    idx = 0
    titleString = (f'Analysis: {startTime.strftime("%Y-%m-%d %H:%M")}\n{label}')
    [fig, axes] = plot_one_glucose(fig, axes, idx, duration, startTime, dfDeviceStatus)
    axes[0].set_title(titleString)
    plot_save(outFile, fig)
    return


def plot_one_glucose(fig, axes, idx, duration, startTime, dfDeviceStatus):
    colorList = ['black', 'magenta', 'cyan', 'green', 'purple', 
                 'darkgoldenrod', 'red', 'darkviolet', 'sandybrown', 'mediumslateblue']
    styleList = ['-', '--', '-.', ':']
    color = colorList[idx%len(colorList)]
    style = styleList[idx%len(styleList)]
    xRange = [0, duration]
    if duration > 4.1:
        bottom_ticks = np.arange(0, duration, step=1)
    else:
        bottom_ticks = np.arange(0, duration, step=0.5)
    dfDeviceStatus = add_delta_time_column_in_hours(startTime, dfDeviceStatus)

    dfDeviceStatus.plot(x='elapsedHours', y='glucose', c=color, ax=axes[0],
                        style=style, xlim=xRange, xticks=bottom_ticks)
    dfDeviceStatus.plot(x='elapsedHours', y='IOB', c=color, ax=axes[1],
                        style=style, xlim=xRange, xticks=bottom_ticks)
    plt.draw()
    plt.pause(0.001)

    return fig, axes
