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
    test_designation = "Not Provided"

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
    for line in linesRaw:
        try:
            json_dict = json.loads(line)
            eventType = json_dict['eventType']
            #print("eventType = ", eventType)
            if eventType == tb_string:
                duration = json_dict['duration']
                insulin.append(lost_basal*duration)
                if 'timestamp' in json_dict:
                    timestamp.append(json_dict['timestamp'])
                    #print("Temp Basal timestamp", json_dict['timestamp'])
                else:
                    timestamp.append(json_dict['created_at'])
                    #print("Temp Basal created_at", json_dict['created_at'])
            elif eventType == smb_string:
                insulin.append(json_dict['insulin'])
                timestamp.append(json_dict['created_at'])
                #print("SMB created_at", json_dict['created_at'])
            elif eventType == ab_string:
                insulin.append(json_dict['insulin'])
                timestamp.append(json_dict['timestamp'])
                #print("AB timestamp", json_dict['timestamp'])
            elif eventType == note_string:
                test_designation=json_dict['notes']
                print("note : ",json_dict['created_at'], json_dict['notes'])
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

    d = {'timestamp': timestamp, 'insulin': insulin}
    tmpDF = pd.DataFrame(d)
    print(tmpDF)
    # split the time into a new column, use for plots
    time_array = pd.to_datetime(tmpDF['timestamp'],utc=True)
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # dfTreatments = tmpDF.sort_values(by="time")
    dfTreatments = tmpDF.sort_index(ascending=False)
    # reindex the dataframe
    dfTreatments = dfTreatments.reset_index(drop=True)

    return test_designation, dfTreatments


def filter_test_devicestatus(dfDeviceStatus, glucoseThreshold):
    # All tests start and end with steady state values of glucoseThreshold
    #   All tests to date use glucoseThreshold of 110
    #   But because we now handle Trio data, which won't loop with flat glucose
    #   We need to be more careful with the level changes
    # The test begins off when the glucose goes above glucoseThreshold (for high) or 
    # below glucoseThreshold (for low) by more than the indicated absDeltaAllowed.
    # During the test (at least for low), the values might go both above and below glucoseThreshold
    #   So need to limit to be first reading after beginning not at glucoseThreshold
    #   And last reading from the end not at glucoseThreshold
    # Because we want these to work with Trio - which will not loop with flat glucose
    # use a value that is within 1 mg/dL of glucoseThreshold.

    filterDataFlag = 1
    absDeltaAllowed = 3
    lowThreshold = glucoseThreshold - absDeltaAllowed
    highThreshold = glucoseThreshold + absDeltaAllowed

    # the first and last glucose should be glucoseThreshold or the times were not correct
    if len(dfDeviceStatus) == 0:
        print(f"Error - there is no data - check inputs")
        exit(1)

    firstGlucose=dfDeviceStatus.iloc[0]['glucose']
    lastGlucose=dfDeviceStatus.iloc[-1]['glucose']
    if not (abs(firstGlucose - glucoseThreshold) <= absDeltaAllowed and
            abs(lastGlucose - glucoseThreshold) <= absDeltaAllowed):
        print("   WARNING ---- ")
        print("times are not correct - did not capture the whole test")
        print("First and Last Glucose:", firstGlucose, lastGlucose)
        print("   WARNING ---- ")
        print("All data in the device files will be used")
        filterDataFlag = 0
        print("   WARNING ---- ")
        #exit(0)

    testDetails = {} # initialize an empty dictionary

    # auto detect if this is a high-glucose test or a low-glucose test.
    lowFrameIndex=dfDeviceStatus.index[dfDeviceStatus['glucose'] < lowThreshold ]
    highFrameIndex=dfDeviceStatus.index[dfDeviceStatus['glucose'] > highThreshold]  

    if len(lowFrameIndex) == 0:
        type = 'high'
        useThreshold = highThreshold
    elif len(highFrameIndex) == 0:
        type = 'low'
        useThreshold = lowThreshold
    elif lowFrameIndex[0] < highFrameIndex[0]:
        print('Decided test is low')
        type = 'low'
        useThreshold = lowThreshold
    elif lowFrameIndex[0] > highFrameIndex[0]:
        print('Decided test is high')
        type = 'high'
        useThreshold = highThreshold
    else:
        print('Could not detect if test type was low or high')
        exit(1)
    
    #if type == 'low':
    #    print(f"lowFrameIndex: {lowFrameIndex[0]} to {lowFrameIndex[-1]}")
        
    # limit dfDeviceStatus by time (allows a low event to exceed glucoseThreshold in middle)
    if filterDataFlag == 1:
        dfDeviceStatus = filter_on_glucose_devicestatus(dfDeviceStatus, useThreshold, type)
    startTime = dfDeviceStatus.iloc[0]['time']
    endTime = dfDeviceStatus.iloc[-1]['time']
    duration = (endTime - startTime).total_seconds() / 3600.
    testDetails={
                'type': type, 
                'startTime': startTime,
                'endTime': endTime,
                'durationInHours': duration,
                'startTimeString': startTime.strftime("%Y-%m-%d %H:%M"),
                'endTimeString': endTime.strftime("%Y-%m-%d %H:%M") 
                }

    return testDetails, dfDeviceStatus


def filter_on_glucose_devicestatus(dfDeviceStatus, glucoseThreshold, type):
    # We want to limit the dfDeviceStatus frame
    #   First row that is above or below glucoseThreshold
    #   Last row this is above or below glucoseThreshold
    #   Allow intermediate values to be any glucose level.
    if type == 'low':
        indexNotAtGlucoseThreshold = dfDeviceStatus.index[dfDeviceStatus['glucose'] < glucoseThreshold]
    else:
        indexNotAtGlucoseThreshold = dfDeviceStatus.index[dfDeviceStatus['glucose'] > glucoseThreshold]

    idx0 = indexNotAtGlucoseThreshold[0]
    idx1 = indexNotAtGlucoseThreshold[-1]
    print(f"first and last index are {idx0} and {idx1} out of {len(dfDeviceStatus)}")
    dfDeviceStatus=dfDeviceStatus.loc[idx0:idx1]
    if len(dfDeviceStatus) == 0:
        print(f"Error - dfDeviceStatus is empty after filtering")
        exit(1)

    dfDeviceStatus = dfDeviceStatus.reset_index(drop=True)
    return dfDeviceStatus


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

