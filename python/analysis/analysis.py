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

    return test_designation, dfTreatments


def filter_test_devicestatus(dfDeviceStatus, glucoseThreshold):
    # the first and last glucose should be glucoseThreshold or the times were not correct
    firstGlucose=dfDeviceStatus.iloc[0]['glucose']
    lastGlucose=dfDeviceStatus.iloc[-1]['glucose']
    if not (firstGlucose == glucoseThreshold and lastGlucose == glucoseThreshold):
        print("times are not correct - did not capture the whole test")
        print("First and Last Glucose:", firstGlucose, lastGlucose)
        exit(0)

    testDetails = {} # initialize an empty dictionary

    # auto detect if this is a high-glucose test or a low-glucose test.
    lowFrame=dfDeviceStatus[dfDeviceStatus['glucose'] < glucoseThreshold]
    highFrame=dfDeviceStatus[dfDeviceStatus['glucose'] > glucoseThreshold]

    if len(highFrame) < len(lowFrame):
        type = 'low'
        startTime = lowFrame.iloc[0]['time']
        endTime = lowFrame.iloc[-1]['time']
    elif len(highFrame) > len(lowFrame):
        type = 'high'
        startTime = highFrame.iloc[0]['time']
        endTime = highFrame.iloc[-1]['time']
    else:
        print('Could not detect if test type was low or high')
        exit(1)
    
    # limit dfDeviceStatus by time (allows a low event to exceed glucoseThreshold in middle)
    deltaToCheck = pd.to_timedelta(10.0, unit='sec')
    dfDeviceStatus=dfDeviceStatus[(dfDeviceStatus['time'] >= startTime-deltaToCheck) & \
                (dfDeviceStatus['time'] <= endTime+deltaToCheck)]
    testDetails={
                'type': type, 
                'startTime': startTime,
                'endTime': endTime,
                'startTimeString': startTime.strftime("%Y-%m-%d %H:%M"),
                'endTimeString': endTime.strftime("%Y-%m-%d %H:%M") 
                }

    return testDetails, dfDeviceStatus


def filter_test_treatments(dfTreatments, testDetails):
    # limit dfTreatments by time
    deltaToCheck = pd.to_timedelta(10.0, unit='sec')
    dfTreatments=dfTreatments[(dfTreatments['time'] >= (testDetails['startTime']-deltaToCheck)) & \
                 (dfTreatments['time'] <= (testDetails['endTime']+deltaToCheck))]

    # perform cumsum only after limiting time in dfTreatments
    dfTreatments['insulinCumsum'] = dfTreatments['insulin'].cumsum()
    #print(dfTreatments)

    return dfTreatments

