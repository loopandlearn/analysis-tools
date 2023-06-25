# plot.py
# plotting functions:
#  single test (now)
#  multiple tests (planned)


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_single_test(outFile, label, dfDeviceStatus, dfTreatments):
    nrow = 3
    ncol = 1
    naxes = 3
    day_in_sec = 24*60*60
    one_hr_in_sec = day_in_sec/24
    #xRange = [0, day_in_sec+1]
    #bottom_ticks = np.arange(0, day_in_sec+1, step=two_hr_in_sec)
    mkSize = 10

    fig, axes = plt.subplots(nrow, ncol, figsize=(5, 7))
    startTime = dfDeviceStatus.iloc[0]['time']
    endTime = dfDeviceStatus.iloc[-1]['time']
    xRange = [startTime, endTime]
    duration = (endTime - startTime).seconds
    #bottom_ticks = np.arange(0, duration, step=600)
    #dfDeviceStatus['deltaTime']=pd.to_timedelta(dfDeviceStatus['time']-startTime)
    #dfTreatments['deltaTime']=pd.to_timedelta(dfTreatments['time']-startTime)
    #print(dfTreatments['deltaTime'])

    titleString = (f'Analysis: {startTime.strftime("%Y-%m-%d %H:%M")}\n{label}')

    print()
    print("Plot Title:")
    print(" *** ", titleString)

    axes[0].set_title(titleString)

    #dfDeviceStatus.plot(x='time', y='glucose', c='green', ax=axes[0], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    #dfDeviceStatus.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    dfDeviceStatus.plot(x='time', y='glucose', c='green', ax=axes[0], style='-', 
                        xlim=xRange)
    dfDeviceStatus.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
                        xlim=xRange)
    dfTreatments.plot(x='time', y='insulinCumsum', c='black', ax=axes[2], style='-',
                      xlim=xRange)

    for x in axes:
        x.grid('on')
        x.legend(bbox_to_anchor=(1.11, 1.0), framealpha=1.0)

    idx = 0
    while idx < naxes:
        x_axis = axes[idx].axes.get_xaxis()
        # x_label = x_axis.get_label()
        x_axis.set_ticklabels([])
        idx += 1

    # set limits for BG (always in mg/dl)
    axes[0].set_ylabel("glucose")
    bg_ylim = axes[0].get_ylim()
    a = min(bg_ylim[0], 0)
    b = max(1.1*bg_ylim[1], 300)
    axes[0].set_ylim([a, b])

    # handle case where IOB is never zero for entire plot
    axes[1].set_ylabel("IOB")
    iob_ylim = axes[1].get_ylim()
    a = min(1.1*iob_ylim[0], -1)
    b = max(1.1*iob_ylim[1], 10)
    axes[1].set_ylim([a, b])

    axes[2].set_ylabel("Sum Insulin")
    insulinCumsum_ylim = axes[2].get_ylim()
    a = min(1.1*insulinCumsum_ylim[0], -1)
    b = max(1.1*insulinCumsum_ylim[1], 10)
    axes[2].set_ylim([a, b])

    plt.draw()
    plt.pause(0.001)
    plt.pause(5)
    # for use in interactive screen: plt.draw();plt.pause(0.001)
    plt.savefig(outFile)
    plt.close(fig)
