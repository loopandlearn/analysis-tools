# analysis.py
# this contains functions to process data read from disk


import pandas as pd
import json
import matplotlib.pyplot as plt


def extract_devicestatus(content):

    dfDeviceStatus = pd.DataFrame({})

    # split by newline:
    linesRaw = content.splitlines()
 
    verboseFlag = 0
    if verboseFlag:
        print("\n>>>   call to extract_devicestatus")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])
        print("\nlinesRaw has ", len(linesRaw), " lines")

    # parse the devicedata output
    jdx=0
    loop_time=[]
    iob_time=[]
    iob=[]
    glucose_time=[]
    glucose=[]
    recommendedBolus=[]
    dataType="unknown"
    oldSavedTime="2001-10-14T17:50:03.921"
    for line in linesRaw:
        try:
            json_dict = json.loads(line)
            if 'loop' in json_dict:
                dataType="loop"
                loop_time.append(json_dict['loop']['timestamp'][0:-1]) # remove Z
                iob_time.append(json_dict['loop']['iob']['timestamp'])
                iob.append(json_dict['loop']['iob']['iob'])
                glucose_time.append(json_dict['loop']['predicted']['startDate'])
                glucose.append(json_dict['loop']['predicted']['values'][0])
                recommendedBolus.append(json_dict['loop']['recommendedBolus'])
            elif 'openaps' in json_dict:
                dataType="openaps"
                #openaps_data = json_dict['openaps']
                #suggested_data = json_dict['openaps']['suggested']
                # or enacted?
                getWhat = 'enacted' # this was actually implemented
                #getWhat = 'suggested'
                #savedTime = json_dict['openaps'][getWhat]['deliverAt']
                savedTime = json_dict['openaps'][getWhat]['timestamp']
                if oldSavedTime == savedTime:
                    #print("duplicate time stamp in device status")
                    continue
                oldSavedTime = savedTime
                loop_time.append(savedTime[0:-1])
                iob_time.append(savedTime)
                iob.append(json_dict['openaps'][getWhat]['IOB'])
                glucose_time.append(savedTime)
                glucose_value = json_dict['openaps'][getWhat]['bg']
                if glucose_value < 30:
                    glucose_value = glucose_value/0.0555 # convert to mg/dL
                glucose.append(glucose_value)
                recommendedBolus.append(json_dict['openaps'][getWhat]['insulinForManualBolus'])
            else:
                print("Neither 'loop' nor 'openaps' data found in JSON")
                continue
            if verboseFlag:
                if dataType == "loop" or dataType == "openaps":
                    print("\n *** type and index = ", dataType, jdx)
                    print(loop_time[jdx], glucose_time[jdx], iob_time[jdx], glucose[jdx],
                           iob[jdx], recommendedBolus[jdx])
                else:
                    print("did not find loop or openaps")
            jdx=jdx+1

        except Exception as e:
            if verboseFlag == 3:
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
    if verboseFlag:
        print(tmpDF)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(tmpDF['glucose_time'])
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # dfDeviceStatus = tmpDF.sort_values(by="time")
    dfDeviceStatus = tmpDF.sort_index(ascending=False)
    # reindex the dataframe
    dfDeviceStatus = dfDeviceStatus.reset_index(drop=True)

    return dfDeviceStatus


def extract_treatments(content):

    dfTreatments = pd.DataFrame({})

    # split by newline:
    linesRaw = content.splitlines()
 
    verboseFlag = 0
    if verboseFlag:
        print("\n>>>   call to extract_treatments")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])
        print("\nlinesRaw has ", len(linesRaw), " lines")

    # parse the devicedata output
    tb_string = 'Temp Basal'
    ab_string = 'Correction Bolus'
    smb_string = 'SMB'
    note_string = 'Note'
    # warning - tests require single basal rates of 0.6 U/hr
    lost_basal = -0.60/60 # units per minute
    jdx=0
    timestamp=[]
    insulin=[]
    insulinType=[]
    ns_notes=[]
    ns_notes_timestamp = []
    for line in linesRaw:
        try:
            json_dict = json.loads(line)
            eventType = json_dict['eventType']
            #print("eventType = ", eventType)
            if eventType == tb_string:
                duration = json_dict['duration']
                insulin.append(lost_basal*duration)
                insulinType.append(json_dict['insulinType'])
                if 'timestamp' in json_dict:
                    timestamp.append(json_dict['timestamp'])
                    #print("Temp Basal timestamp", json_dict['timestamp'])
                else:
                    timestamp.append(json_dict['created_at'])
                    #print("Temp Basal created_at", json_dict['created_at'])
            elif eventType == smb_string:
                insulin.append(json_dict['insulin'])
                insulinType.append(json_dict['insulinType'])
                timestamp.append(json_dict['created_at'])
                #print("SMB created_at", json_dict['created_at'])
            elif eventType == ab_string:
                insulinType.append(json_dict['insulinType'])
                insulin.append(json_dict['insulin'])
                timestamp.append(json_dict['timestamp'])
                #print("AB timestamp", json_dict['timestamp'])
            elif eventType == note_string:
                ns_notes.append(json_dict['notes'])
                ns_notes_timestamp.append(json_dict['created_at'])
                #print("note : ",json_dict['created_at'], json_dict['notes'])
            else:
                print(json_dict['created_at'], eventType)
            if verboseFlag:
                print("\n *** index = ", jdx)
                print(timestamp[jdx], insulin[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'timestamp': timestamp, 'insulin': insulin, 'insulinType': insulinType}
    tmpDF = pd.DataFrame(d)
    if verboseFlag:
        print(tmpDF)
    # split the time into a new column, use for plots
    time_array = pd.to_datetime(tmpDF['timestamp'],utc=True)
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # dfTreatments = tmpDF.sort_values(by="time")
    dfTreatments = tmpDF.sort_index(ascending=False)
    # reindex the dataframe
    dfTreatments = dfTreatments.reset_index(drop=True)

    return dfTreatments, ns_notes, ns_notes_timestamp


def filter_test_devicestatus(dfDeviceStatus, glucoseThreshold):
    # All tests start and end with steady state values of glucoseThreshold
    #   But because we now handle Trio data, which won't loop with flat glucose
    #   use a glucose range, keep steady state at 110, 109, 111 levels
    # Update this function to handle any glucose trace
    # The beginning and ending indices come from out-of-glucose-range values

    absDeltaAllowed = 2
    lowThreshold = glucoseThreshold - absDeltaAllowed
    highThreshold = glucoseThreshold + absDeltaAllowed
    extraRowsEndOfTest = 48 # add rows at end of tests

    # first find all indices within the glucoseThreshold band
    # indices = df.loc[(df['A'] >= 20) & (df['A'] <= 40)].index
    idxOutRange = dfDeviceStatus.loc[(dfDeviceStatus['glucose'] <= lowThreshold) |
                                     (dfDeviceStatus['glucose'] >= highThreshold)].index
    if len(idxOutRange) < 10:
        print("   ERROR ---- ")
        print(" Time range is not reasonable")
        print("   Total data set length ", len(dfDeviceStatus))
        print("   Number of rows where glucose is outside normal band ", len(idxOutRange))
        exit(1)
    # report information about the test
    idx0 = max(idxOutRange[0],0)
    idx1 = idxOutRange[-1]
    # for type: if all idxOutRange are high - it is high
    if min(dfDeviceStatus.iloc[idx0:idx1]['glucose']) > highThreshold:
        type = 'high'
    else:
        type = 'mixed'

    idx1 = min(idx1 + extraRowsEndOfTest,len(dfDeviceStatus)-1)
    print('\trowsAvail, rowsUsed, idx0, idx1, glucose: idx0, ixd1')
    print('\t{0:6d}, {1:10d}, {2:4d}, {3:4d}, {4:5d}, {5:5d}'.format(
          len(dfDeviceStatus), idx1-idx0+1, idx0, idx1,
          dfDeviceStatus.iloc[idx0]['glucose'], dfDeviceStatus.iloc[idx1]['glucose']))

    # configure testDetails dictionary
    testDetails = {} # initialize an empty dictionary
    startTime = dfDeviceStatus.iloc[idx0]['time']
    endTime = dfDeviceStatus.iloc[idx1]['time']
    duration = (endTime - startTime).total_seconds() / 3600.
    testDetails={
                'type': type, 
                'startTime': startTime,
                'endTime': endTime,
                'durationInHours': duration,
                'startTimeString': startTime.strftime("%Y-%m-%d %H:%M"),
                'endTimeString': endTime.strftime("%Y-%m-%d %H:%M") 
                }

    # limit dfDeviceStatus using idx0 and idx1 before return
    dfDeviceStatus=dfDeviceStatus[idx0:idx1]

    return testDetails, dfDeviceStatus


def filter_test_treatments(dfTreatments, testDetails):
    # limit dfTreatments by time
    deltaToCheck = pd.to_timedelta(10.0, unit='sec')
    dfTreatments=dfTreatments[(dfTreatments['time'] >= (testDetails['startTime']-deltaToCheck)) & \
                 (dfTreatments['time'] <= (testDetails['endTime']+deltaToCheck))]

    # perform cumsum only after limiting time in dfTreatments
    dfTreatments = dfTreatments.reset_index(drop=True)
    dfTreatments['insulinCumsum'] = dfTreatments['insulin'].cumsum()
    #print(dfTreatments)

    return dfTreatments

