# glucose_test.py
# code is all in this file

# Set up a google sheet to autogenerate download commands based on time stamps
#   to create the devicestatus and treatments files
# Command line arguments (no flexibility - order is fixed)
# order of args: devicestatus treatments [optional: external_label] [optional: summary.csv filename]

import sys
import re
import tempfile
import numpy as np
import os
import pandas as pd
import json
import matplotlib.pyplot as plt


# only function used from OmniLoopMessageParser - just copy it here
def printDict(thisDict):
    if len(thisDict) == 0:
        return
    for keys, values in thisDict.items():
        print('  {} =   {}'.format(keys, values))
    print('\n')


def read_raw_nightscout(filename):
    noisy = 0
    if noisy:
        print("filename in read_json_file = ", filename)
    fp = open(filename, "r", encoding='UTF8')
    raw_content = fp.read()
    fp.close()
    # this next bit could be done with jq as part of the shell script
    # but is NOT done so now - change if decide to modify that
    # remove the beginning and ending []
    content = raw_content[1:-2]
    # break into separate json lines
    content = content.replace(',{"_id', '\n{"_id')
    return content
    

def extract_devicestatus(content):

    dfDeviceStatus = pd.DataFrame({})

    # split by newline:
    lines_raw = content.splitlines()
 
    noisy = 0
    if noisy:
        print("\n>>>   call to extract_devicestatus")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])
        print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    jdx=0
    loop_time=[]
    iob_time=[]
    iob=[]
    glucose_time=[]
    glucose=[]
    recommendedBolus=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            if (jdx < 2 & noisy):
                print('\n *** jdx = ', jdx)
                printDict(json_dict)
            loop_time.append(json_dict['loop']['timestamp'][0:-1]) # remove Z
            iob_time.append(json_dict['loop']['iob']['timestamp'])
            iob.append(json_dict['loop']['iob']['iob'])
            glucose_time.append(json_dict['loop']['predicted']['startDate'])
            glucose.append(json_dict['loop']['predicted']['values'][0])
            recommendedBolus.append(json_dict['loop']['recommendedBolus'])
            if noisy:
                print("\n *** jdx = ", jdx)
                print(loop_time[jdx], glucose_time[jdx], iob_time[jdx], glucose[jdx], iob[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'loop_time': loop_time, 'iob_time': iob_time, 
         'glucose_time': glucose_time,
        'IOB': iob, 'glucose': glucose, 'recommendedBolus': recommendedBolus}
    tmpDF = pd.DataFrame(d)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(tmpDF['glucose_time'])
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # dfDeviceStatus = tmpDF.sort_values(by="time")
    dfDeviceStatus = tmpDF.sort_index(ascending=False)

    return dfDeviceStatus


def extract_treatments(content):

    dfTreatments = pd.DataFrame({})
    test_designation = "Not Provided"

    # split by newline:
    lines_raw = content.splitlines()
 
    noisy = 0
    if noisy:
        print("\n>>>   call to extract_treatments")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])
        print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    tb_string = 'Temp Basal'
    ab_string = 'Correction Bolus'
    note_string = 'Note'
    lost_basal = -0.60/60 # units per minute
    jdx=0
    timestamp=[]
    insulin=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            #if (noisy & jdx < 2):
            #    print('\n *** jdx = ', jdx)
            #    printDict(json_dict)
            
            # check eventType
            eventType = json_dict['eventType']
            if eventType == tb_string:
                duration = json_dict['duration']
                insulin.append(lost_basal*duration)
                timestamp.append(json_dict['timestamp'])
            elif eventType == ab_string:
                insulin.append(json_dict['insulin'])
                timestamp.append(json_dict['timestamp'])
            elif eventType == note_string:
                test_designation=json_dict['notes']
                print(json_dict['created_at'], json_dict['notes'])
            else:
                print(json_dict['created_at'], eventType)
            if noisy:
                print("\n *** jdx = ", jdx)
                print(timestamp[jdx], insulin[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'timestamp': timestamp, 'insulin': insulin}
    tmpDF = pd.DataFrame(d)
    # split the time into a new column, use for plots
    time_array = pd.to_datetime(tmpDF['timestamp'],utc=True)
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # dfTreatments = tmpDF.sort_values(by="time")
    dfTreatments = tmpDF.sort_index(ascending=False)

    return test_designation, dfTreatments

def generatePlot(outFile, label, dfDeviceStatus, dfTreatments):
    nrow = 3
    ncol = 1
    naxes = 3
    day_in_sec = 24*60*60
    one_hr_in_sec = day_in_sec/24
    #xRange = [0, day_in_sec+1]
    #bottom_ticks = np.arange(0, day_in_sec+1, step=two_hr_in_sec)
    mkSize = 10

    fig, axes = plt.subplots(nrow, ncol, figsize=(5, 7))
    start_time = dfDeviceStatus.iloc[0]['time']
    end_time = dfDeviceStatus.iloc[-1]['time']
    xRange = [start_time, end_time]
    #elapsed_time = end_time - start_time
    #bottom_ticks = np.arange(0, 21600, step=one_hr_in_sec)

    plot_start_time = f"{start_time}"
    print("start and end ", start_time, ", ", end_time)
    plot_start_time = plot_start_time[0:-6]

    title_string = (f'Analysis: {plot_start_time}\n{label}')

    print()
    print("Plot Title:")
    print(" *** ", title_string)

    axes[0].set_title(title_string)

    #dfDeviceStatus.plot(x='time', y='glucose', c='green', ax=axes[0], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    #dfDeviceStatus.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    dfDeviceStatus.plot(x='time', y='glucose', c='green', ax=axes[0], style='-',
            xlim=xRange)
    dfDeviceStatus.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
            xlim=xRange)
    dfTreatments.plot(x='time', y='insulin_cumsum', c='black', ax=axes[2], style='-',
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
    insulin_cumsum_ylim = axes[2].get_ylim()
    a = min(1.1*insulin_cumsum_ylim[0], -1)
    b = max(1.1*insulin_cumsum_ylim[1], 10)
    axes[2].set_ylim([a, b])

    plt.draw()
    plt.pause(0.001)
    plt.pause(5)
    # for use in interactive screen: plt.draw();plt.pause(0.001)
    plt.savefig(outFile)
    plt.close(fig)


def help(reportfile):
    print("Usage:")
    print("  python glucose_test.py arg1 arg2 [arg3] [arg4]")
    print("    arg1 - path for data I/O")
    print("    arg2 - timestamp identifier (used for I/O)")
    print("       input: arg2_devicestatus.txt, arg2_treatments.txt")
    print("       output: plot_arg2.png")
    print("    arg3 - optional label, otherwise uses note in treatments")
    print("    arg4 - optional output filename, otherwise uses", reportfile)

def main():
    noisy=1
    number_of_args = len(sys.argv)-1
    print("number_of_args = ", number_of_args)
    reportfile="glucose_impulse_response.csv"
    # if insufficient arguments, provide help
    if number_of_args < 2:
        help(reportfile)
        exit
    else:
        script_name = sys.argv[0]
        foldername = sys.argv[1]
        timestamp_id = sys.argv[2]
    # optional arguments
    external_label=""
    
    if number_of_args >= 3:
        external_label = sys.argv[3]
    if number_of_args == 4:
        reportfile = sys.argv[4]
    
    devicestatus_filename = timestamp_id + "_devicestatus.txt"
    treatments_filename = timestamp_id + "_treatments.txt"
    plot_filename = "plot_" + timestamp_id + ".png"

    if noisy:
        print("Script name:", script_name)
        print("foldername:", foldername)
        print("devicestatus_filename:", devicestatus_filename)
        print("treatments_filename:", treatments_filename)
        print("external_label:", external_label)
        print("reportfile:", reportfile)

    devicestatus_filename = foldername + "/" + devicestatus_filename
    content1 = read_raw_nightscout(devicestatus_filename)
    dfDeviceStatus = extract_devicestatus(content1)
    if noisy:
        print(" *** dfDeviceStatus:")
        print(dfDeviceStatus)

    treatments_filename = foldername + "/" + treatments_filename
    content2 = read_raw_nightscout(treatments_filename)
    [test_designation, dfTreatments] = extract_treatments(content2)

    # use glucose values > 100 as markers for start and end of test.
    # print("Looking for the correct indices")
    dfDeviceStatus=dfDeviceStatus[dfDeviceStatus['glucose'] > 110]
    # print(dfDeviceStatus)
    begin_time = dfDeviceStatus.iloc[0]['time']
    end_time = dfDeviceStatus.iloc[-1]['time']
    print(begin_time, end_time)
    dfTreatments=dfTreatments[(dfTreatments['time'] > begin_time) & \
                              (dfTreatments['time'] < end_time)]
    if noisy:
        print(" *** dfTreatments:")
        print(dfTreatments)
    dfTreatments['insulin_cumsum'] = dfTreatments['insulin'].cumsum()

    # plot pandas dataframe containing Nightscout data
    # always beginning of input filename (YYYY-MM-DDTHH for the output plot)
    this_plotname = foldername + "/" + plot_filename
    #label="Enter status for RC/IRC AB: Constant/GBAF"
    if len(external_label) > 5:
        test_designation = external_label
    generatePlot(this_plotname, test_designation, dfDeviceStatus, dfTreatments)
    print(' *** plot created:     ', this_plotname)
    maxIOB=dfDeviceStatus['IOB'].max()
    maxCumInsulin=dfTreatments['insulin_cumsum'].max()
    iobTimeDF=dfDeviceStatus[(dfDeviceStatus['IOB'] > (maxIOB-0.01))]
    iobTime=iobTimeDF.iloc[0]['time']
    iobDeltaTime=iobTime - begin_time
    ciTimeDF=dfTreatments[(dfTreatments['insulin_cumsum'] > (maxCumInsulin-0.01))]
    ciTime=ciTimeDF.iloc[0]['time']
    ciDeltaTime=ciTime - begin_time
    print(f'{begin_time}, {iobDeltaTime}, {ciDeltaTime}, {maxIOB:6.2f}, {maxCumInsulin:6.2f}, "{test_designation}"')

    reportfile="glucose_impulse_response.csv"
    isItThere = os.path.isfile(reportfile)
    # now open the file
    stream_out = open(reportfile, mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'StartTime, TimeToMaxIOB, TimeToMaxCumInsulin, maxIOB, maxCumInsulin, ' + \
                       'NightscoutNote'
        stream_out.write(headerString)
        stream_out.write('\n')
    stream_out.write(f"{begin_time},")
    stream_out.write(f"{iobDeltaTime},")
    stream_out.write(f"{ciDeltaTime},")
    stream_out.write(f"{maxIOB:6.2f},")
    stream_out.write(f"{maxCumInsulin:6.2f},")
    stream_out.write(f'"{test_designation}",')
    stream_out.write('\n')
    stream_out.close()
    print('  Row appended to ', reportfile)


if __name__ == "__main__":
    main()

