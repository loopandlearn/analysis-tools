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
    for line in linesRaw:
        try:
            json_dict = json.loads(line)
            if (jdx < 2 & verboseFlag):
                print('\n *** jdx = ', jdx)
                printDict(json_dict)
            loop_time.append(json_dict['loop']['timestamp'][0:-1]) # remove Z
            iob_time.append(json_dict['loop']['iob']['timestamp'])
            iob.append(json_dict['loop']['iob']['iob'])
            glucose_time.append(json_dict['loop']['predicted']['startDate'])
            glucose.append(json_dict['loop']['predicted']['values'][0])
            recommendedBolus.append(json_dict['loop']['recommendedBolus'])
            if verboseFlag:
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
    note_string = 'Note'
    lost_basal = -0.60/60 # units per minute
    jdx=0
    timestamp=[]
    insulin=[]
    for line in linesRaw:
        try:
            json_dict = json.loads(line)
            #if (verboseFlag & jdx < 2):
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
            if verboseFlag:
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
    # reindex the dataframe
    dfTreatments = dfTreatments.reset_index(drop=True)

    return test_designation, dfTreatments


def filter_test_devicestatus(dfDeviceStatus, glucoseThreshold):
    # All tests start and end with steady state values of glucoseThreshold
    #   All tests to date use glucoseThreshold of 110.
    # The test begins off when the glucose goes above glucoseThreshold (for high) or 
    # below glucoseThreshold (for low).
    # During the test (at least for low), the values might go both above and below glucoseThreshold
    #   So need to limit to be first reading after beginning not at glucoseThreshold
    #   And last reading from the end not at glucoseThreshold

    # the first and last glucose should be glucoseThreshold or the times were not correct
    firstGlucose=dfDeviceStatus.iloc[0]['glucose']
    lastGlucose=dfDeviceStatus.iloc[-1]['glucose']
    if not (firstGlucose == glucoseThreshold and lastGlucose == glucoseThreshold):
        print("times are not correct - did not capture the whole test")
        print("First and Last Glucose:", firstGlucose, lastGlucose)
        exit(0)

    testDetails = {} # initialize an empty dictionary

    # auto detect if this is a high-glucose test or a low-glucose test.
    lowFrameIndex=dfDeviceStatus.index[dfDeviceStatus['glucose'] < glucoseThreshold]
    highFrameIndex=dfDeviceStatus.index[dfDeviceStatus['glucose'] > glucoseThreshold]  

    if len(lowFrameIndex) == 0:
        type = 'high'
    elif len(highFrameIndex) == 0:
        type = 'low'
    elif lowFrameIndex[0] < highFrameIndex[0]:
        type = 'low'
    elif lowFrameIndex[0] > highFrameIndex[0]:
        type = 'high'
    else:
        print('Could not detect if test type was low or high')
        exit(1)
    
    if type == 'low':
        print(f"lowFrameIndex: {lowFrameIndex[0]} to {lowFrameIndex[-1]}")
        
    # limit dfDeviceStatus by time (allows a low event to exceed glucoseThreshold in middle)
    dfDeviceStatus = filter_on_glucose_devicestatus(dfDeviceStatus, glucoseThreshold, type)
    startTime = dfDeviceStatus.iloc[0]['time']
    endTime = dfDeviceStatus.iloc[-1]['time']
    testDetails={
                'type': type, 
                'startTime': startTime,
                'endTime': endTime,
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

    return dfDeviceStatus


def filter_test_treatments(dfTreatments, testDetails):
    # limit dfTreatments by time
    deltaToCheck = pd.to_timedelta(10.0, unit='sec')
    dfTreatments=dfTreatments[(dfTreatments['time'] >= (testDetails['startTime']-deltaToCheck)) & \
                 (dfTreatments['time'] <= (testDetails['endTime']+deltaToCheck))]

    # perform cumsum only after limiting time in dfTreatments
    dfTreatments['insulinCumsum'] = dfTreatments['insulin'].cumsum()
    #print(dfTreatments)

    return dfTreatments

