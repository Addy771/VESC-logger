# VESC Logger
# Connects to a VESC with USB and repeatedly logs VESC parameters


# Config
base_filename = "vesc_log"  # base name used for log files
poll_interval = 100         # How often to get VESC values in milliseconds
target_port = "COM3"       # Name of serial port that VESC will connect on


import serial
import logger
import time


# Create serial class
s1 = serial.Serial(timeout=0)

s1.baudrate = 115200
s1.port = target_port

while True:
    try:
        s1.open()
    except (OSError, serial.SerialException, ValueError):
        pass

    if s1.isOpen():
        print("\nPort available. Starting.")
        s1.close()
        logger.log_vesc(base_filename, target_port, poll_interval)
        
    else:
        print("Could not open port.")   

    time.sleep(1)
    
