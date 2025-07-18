#l!/usr/binnv python3
# -*- coding:utf-8 -*-
import serial
import pycrc
import time
import json
import requests
import threading
from datetime import datetime
import os
import math
import subprocess
import copy

#variable used for defining index in sensor data buffer
#indexDataUpBuf = 0
NUM_SRVDATA_UPLOAD_CNT = 5

#-----------------------------------------Global Variablesclass---------------------------------------#

class globalVariables:
    curr_time = 0
    prev_time = 0
    totalDistanceCalc = 0.0
    count_response_1 = 0
    currCalcDistance = 0.0
    piSerialNumber = ""
    sensorDataUpBuf1 = [[0 for _ in range(10)] for _ in range(10)] #defining number of rows and columns 
    sensorDataUpBuf2 = [[0 for _ in range(10)] for _ in range(10)]
    currSpeedInKmPerHr = 0.0
    totalDigitalInPulseCounter = 0
    input_status = 0
    indexDataUpBuf = 0
    currInputVoltage = 0
    prevInputVoltage = 0

#-------------------------------------------end of Global ariable class -------------------------------#

#--------------------------------------logic to read Serial number of Raspberry pi--------------------#
try:
    result = subprocess.check_output(
        ['cat', '/sys/firmware/devicetree/base/serial-number'],
        encoding='utf-8'  # Decodes bytes to string
    ).strip('\x00\n')  # Remove null and newline characters if any
    globalVariables.piSerialNumber = result
    print("Serial Number:",globalVariables.piSerialNumber)

except subprocess.CalledProcessError as e:
    print("Command failed:", e)
except FileNotFoundError:
    print("File not found.")

#----------------------------------------end of Serial number reading----------------------------------#

# Constants
WHEEL_DIAMETER = 750  # in mm
PI = math.pi

#file to store previous time
TIME_FILE = "prev_time.txt"

def get_previous_time():
    if os.path.exists(TIME_FILE):
        with open(TIME_FILE, "r") as f:
            return float(f.read().strip())
    return None

def save_current_time(curr_time):
    with open(TIME_FILE, "w") as f:
        f.write(str(curr_time))

#-------------------------------------------------Speed and Distance calculation -------------------------#

def digitalInReadTimerHndlr():   
    # Example variables (these would typically be updated in a loop or interrupt handler)
    curr_time = time.time()
    prev_time = get_previous_time()

    if prev_time is not None:
        time_diff = curr_time - prev_time
        print(f"Time difference: {time_diff:.2f} seconds")
    else:
        print("No previous time stamp found")

    save_current_time(curr_time)
    currSpeedInMtrPerSec = 0.0
    #currSpeedInKmPerHr = 0.0
    timeDiffInSec = 0.0

    # Calculate speed and distance
    #timeDiffMilliSec = currentTimeMilliSec - previousTimeMilliSec
    if globalVariables.count_response_1 > 0:

        circDistancePerRev = PI * WHEEL_DIAMETER / 1000  # in meters
        if time_diff != 0:
            currSpeedInMtrPerSec = (globalVariables.count_response_1 * circDistancePerRev) / time_diff
        else:
            currSpeedInMtrPerSec = 0.0
        globalVariables.currSpeedInKmPerHr = (currSpeedInMtrPerSec * 18) / 5
        print(f"Calculated Speed in km/hr: {globalVariables.currSpeedInKmPerHr:.3f}")
        currSpeedInKmPerHrUpd = globalVariables.currSpeedInKmPerHr
        prev_time = curr_time
        globalVariables.count_response_1 = 0
        globalVariables.currCalcDistance = globalVariables.currSpeedInKmPerHr * time_diff
        globalVariables.currCalcDistance /= 3600  # Convert km/hr * sec to km
        globalVariables.totalDistanceCalc += globalVariables.currCalcDistance
        #currSpeedInKmPerHr = 0.0
    print(f"Calculated Distance in km: {globalVariables.currCalcDistance:.3f}")
    print(f"Total Distance in km: {globalVariables.totalDistanceCalc:.3f}")
    print(globalVariables.currSpeedInKmPerHr)
    threading.Timer(1.0, digitalInReadTimerHndlr).start()

#----------------------------------------------end of speed and distance calculation----------------------#
	
#----------------------------------------ConfigTree implementation------------------------------#
CONFIG_FILE = "config.json"

# Default config structure
default_config = {
    "system": {
        "run_counter": 0,
        "logging": {
            "level": "INFO"
        }
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return default_config.copy()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def increment_run_counter(config):
    config["system"]["run_counter"] += 1
    return config["system"]["run_counter"]

#--------------------------------------------------------------------------------------------------#

#URL of your HTTP server endpoint
SERVER_URL = "http://172.105.41.167/pvlabs/raw_data.php"  #endpoint of EVA kapila server

#-----------------------------------Raw Data packet construction and upload-------------------------------#

#TODO : Construction of rawdata packet same as EVA510, follwoing is the sample packet construction
def send_data():
    # Construct JSON data

    epoch_time = int(time.time())

    print(f"poch timestamp : {epoch_time}")

    data = {
        "device_id": "sensor_001",
        "timestamp": epoch_time,
        "temperature": 45,  # Simulated temperature
        "humidity": 39,  # Simulated humidity
        "status": "OK"
    }

    print("Uploading data:", json.dumps(data, indent=2))

    # Send HTTP POST request
    try:
        response = requests.post(SERVER_URL, json=data, timeout=5)
        if response.status_code == 200:
            print(" Upload successful")
        else:
            print(f" Failed with status {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f" Error uploading: {e}")

    # Schedule the next upload after 1 second
    threading.Timer(1.0, send_data).start()

#---------------------------------------------------------------------------------------------------------#

#-------------------------------UploadTaskHandler Implementation-----------------------------------------#

def dataUploadTaskHandler():
    indexDataUpBuf = 0

    epoch_time = int(time.time())

    print(f"poch timestamp : {epoch_time}")

    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][0] = epoch_time           #timestamp in utc
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][1] = 0
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][2] = globalVariables.input_status
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][3] = 0
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][4] = 0
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][5] = int(globalVariables.totalDistanceCalc * 100000)
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][6] = int(globalVariables.currSpeedInKmPerHr * 1000)
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][7] = 0
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][8] = 0
    globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf][9] = globalVariables.totalDigitalInPulseCounter

    print(globalVariables.sensorDataUpBuf1[globalVariables.indexDataUpBuf])

    if (globalVariables.indexDataUpBuf == (NUM_SRVDATA_UPLOAD_CNT - 1)):
        globalVariables.sensorDataUpBuf2 = copy.deepcopy(globalVariables.sensorDataUpBuf1)
        send_data()
        globalVariables.indexDataUpBuf = 0
    else:
        globalVariables.indexDataUpBuf += 1

    print(globalVariables.indexDataUpBuf)

    threading.Timer(1.0, dataUploadTaskHandler).start()



#----------------------------------------------------------------------------------------------------------#

def main():
	config = load_config()
	new_count = increment_run_counter(config)
	save_config(config)
	print(f"Script has been run {new_count} times.")

if __name__ == "__main__":
	main()

#-----------------------------------------------------------------------------------------------------------#

#---------------------------------------------------------------------------------------------------------#
#connecting to USB0 of raspberry pi with 115200 baudrate
s = serial.Serial("/dev/ttyUSB0",9600) 
cmd = [0, 0, 0, 0, 0, 0, 0, 0]
#count_response_1 = 0  # Counter for when response[3] == 1
#send_data()
dataUploadTaskHandler()
digitalInReadTimerHndlr()
currInputVolt = 0
prevInputVolt = 0
while True:
    cmd[0] = 0x01  #Device address
    cmd[1] = 0x02  #command
    cmd[2] = 0
    cmd[3] = 0
    cmd[4] = 0
    cmd[5] = 8
    crc = pycrc.ModbusCRC(cmd[0:6])
    cmd[6] = crc & 0xFF
    cmd[7] = crc >> 8
    s.write(cmd)
    time.sleep(0.04)
    response = list(s.read_all())
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if len(response) >= 4:
        globalVariables.input_status = response[3]
        print(f"Input status: {globalVariables.input_status}")
        globalVariables.currInputVoltage = globalVariables.input_status
        print(f"current Input status: {globalVariables.currInputVoltage}")
        print(f"previous Input status: {globalVariables.prevInputVoltage}")
        if ((globalVariables.currInputVoltage == 1) and (globalVariables.prevInputVoltage == 0)):
            globalVariables.count_response_1 += 1
            print(f"Response '1' count: {globalVariables.count_response_1}")
            globalVariables.totalDigitalInPulseCounter += 1
            #digitalInReadTimerHndlr()
        globalVariables.prevInputvoltage=globalVariables.currInputVoltage
        print(globalVariables.prevInputVoltage)
    else:
        print(f"[{current_time}] No or incomplete response")
        cmd[0] = 0x00  #Device address changing baudrate to 115200
        cmd[1] = 0x06  #command
        cmd[2] = 0x20
        cmd[3] = 0
        cmd[4] = 0
        cmd[5] = 0x01 # 01 for 9600
        crc = pycrc.ModbusCRC(cmd[0:6])
        cmd[6] = crc & 0xFF
        cmd[7] = crc >> 8
        s.write(cmd)
        time.sleep(0.05)
        response = list(s.read_all())
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if len(response) >= 4:
            print(f"[{current_time}] Write register status: {response[3]}")
        else:
            print(f"[{current_time}] Write command also failed or incomplete")
#        prevInputvolt = currInputVolt

#----------------------------------------------------------------------------------------------------------#
