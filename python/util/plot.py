# plot.py
# plotting functions:
#  single test (now)
#  multiple tests (planned)


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


def plot_initiate():
    nrow = 3
    ncol = 1
    fig, axes = plt.subplots(nrow, ncol, figsize=(5, 7), sharex='col')
    return fig, axes


def plot_one(fig, axes, idx, duration, startTime, dfDeviceStatus, dfTreatments):
    colorList = ['black', 'magenta', 'cyan', 'green']
    styleList = ['-', '--', '-.', ':']
    color = colorList[nPlot%len(colorList)]
    style = styleList[nPlot%len(styleList)]
    xRange = [0, duration]
    bottom_ticks = np.arange(0, duration, step=1)
    dfDeviceStatus = add_delta_time_column_in_hours(startTime, dfDeviceStatus)
    dfTreatments = add_delta_time_column_in_hours(startTime, dfTreatments)

    # always plot glucose as black - plot each to ensure no outliers
    dfDeviceStatus.plot(x='elapsedHours', y='glucose', c='black', ax=axes[0],
                        style=style, xlim=xRange, xticks=bottom_ticks)
    dfDeviceStatus.plot(x='elapsedHours', y='IOB', c=color, ax=axes[1], 
                        style=style, xlim=xRange, xticks=bottom_ticks)
    dfTreatments.plot(x='elapsedHours', y='insulinCumsum', c=color, ax=axes[2], 
                      style=style, xlim=xRange, xticks=bottom_ticks)
    plt.draw()
    plt.pause(0.001)

    return fig, axes


def plot_format(fig, axes, testLabel, titleString):
    naxes = 3


    print()
    print("Plot Title:")
    print(" *** ", titleString)

    axes[0].set_title(titleString)

    for x in axes:
        x.grid('on')
        #x.legend(bbox_to_anchor=(1.11, 1.0), framealpha=1.0)

    idx = 0
    while idx < naxes:
        x_axis = axes[idx].axes.get_xaxis()
        x_label = x_axis.get_label()
        #x_axis.set_ticklabels([])
        idx += 1

    # set limits for BG (always in mg/dl)
    axes[0].set_ylabel("Glucose")
    axes[0].set_xlabel("hours")
    bg_ylim = axes[0].get_ylim()
    a = min(bg_ylim[0], 0)
    b = max(1.1*bg_ylim[1], 300)
    axes[0].set_ylim([a, b])

    # handle case where IOB is never zero for entire plot
    axes[1].set_ylabel("IOB")
    axes[1].set_xlabel("hours")
    iob_ylim = axes[1].get_ylim()
    a = min(1.1*iob_ylim[0], -1)
    b = max(1.1*iob_ylim[1], 10)
    axes[1].set_ylim([a, b])

    axes[2].set_ylabel("Sum Insulin")
    axes[2].set_xlabel("hours")
    insulinCumsum_ylim = axes[2].get_ylim()
    a = min(1.1*insulinCumsum_ylim[0], -1)
    b = max(1.1*insulinCumsum_ylim[1], 10)
    axes[2].set_ylim([a, b])

    idx = 1
    anchorTuple = [1.05, 1.0]
    # Only need one legend for the plot
    axes[0].legend('')
    axes[1].legend(testLabel, loc='right', bbox_to_anchor=anchorTuple, framealpha=1.0)
    axes[2].legend('')

    plt.draw()
    plt.pause(0.001)

    return fig, axes


def plot_save(outFile, fig):
    plt.draw()
    plt.pause(0.001)
    plt.pause(10)
    plt.savefig(outFile)
    plt.close(fig)
    return


def plot_single_test(outFile, label, duration, startTime, dfDeviceStatus, dfTreatments):
    [fig, axes] = plot_initiate()
    idx = 0
    titleString = (f'Analysis: {startTime.strftime("%Y-%m-%d %H:%M")}\n{label}')
    [fig, axes] = plot_one(fig, axes, idx, duration, startTime, dfDeviceStatus, dfTreatments)
    [fig, axes] = plot_format(fig, axes, "", titleString)
    plot_save(outFile, fig)
    return

