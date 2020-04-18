import os, sys
# Add pyvesc folder to path
sys.path.append(os.path.dirname("./pyvesc/"))

import pyvesc
from pyvesc.VESC.messages import GetValues
#from pyvesc import GetValues
#from pyvesc.VESC.messages import GetValues
#from pyvesc.protocol import encode_request, decode

import time, re, datetime
import serial, ports


def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)


# pass serial object?
def log_vesc(base_name="vesc_log", port="COM1", log_interval=100):

    # Prepare the log directory path
    log_dir = os.path.join(os.getcwd(), 'logs')
    
    # Create the log directory and don't throw an exception if it exists already
    os.makedirs(log_dir, exist_ok=True)
    
    # Check if the log directory exists now
    if os.path.isdir(log_dir) == False:
        print("Error: Unable to create log directory. Aborting.")
        return
    
    
    # Generate filename based on existing files in log dir
    
    new_log = 1
    reg_pattern = '_([0-9]+).csv'
    no_logs = True    
    
    # Create a list of items in log directory
    for root, dirs, files in os.walk(log_dir):
    
        # For each file
        for filename in files:
        
            # Is the file an existing log?
            if filename.find(base_name) != -1:
                # no_logs remains True only when no matches were found
                no_logs = False
                
                # Extract the log number from the filename
                reg_out = re.search(reg_pattern, filename)
                old_log = int(reg_out.group(1))
                
                if old_log > new_log:
                    new_log = old_log
    
        
    if no_logs:
        log_filename = base_name + "_1.csv"
        
    else:
        new_log += 1
        log_filename = base_name + "_" + str(new_log) + ".csv"
    
    # Add the full path to the filename 
    log_filename = os.path.join(log_dir, log_filename)
    
    print("New log will be " + log_filename)
    
    try:
        
        # Open serial port
        s1 = serial.Serial(port, baudrate=115200)
            
        # Open log file for writing
        log_file = open(log_filename, 'w')    
        
        input_buffer = bytearray()   
        
        # Start polling timer
        last_time = millis()
        start_time = last_time
        first_msg = True
        
        while True:
            
            loop_time = millis()
            
            # if polling timer expires reset the timer and poll the VESC
            if loop_time - last_time >= log_interval:
                last_time = loop_time


                # pyvesc creates frame to request sensor data
                send_packet = pyvesc.encode_request(GetValues)
                s1.write(send_packet)
                sent_time = millis()                
        
        
            # Check if serial buffer has data
            if s1.in_waiting > 0:
                input_buffer += s1.read(s1.in_waiting) # Grab the bytes waiting in the serial input
            
            
            # Enough data for vesc frame?
            if len(input_buffer) > 61:
                recv_msg, consumed = pyvesc.decode(input_buffer)
                input_buffer = input_buffer[consumed:]  # trim consumed bytes
                
                # Sort the sensor names
                sensor_keys = sorted(recv_msg.__dict__.keys())

                if first_msg == True:
                    first_msg = False

                    csv_names = "time (s), "

                    # Use the received sensor names for the CSV file's column names
                    for sensor in sensor_keys:
                        csv_names += sensor +", "

                    print("Logging values: " + csv_names + "\n")
                    log_file.write(csv_names + "\n")


                # Start the line with the time column value
                log_line = str((loop_time - start_time) / 1000) + ','

                # Fill out the time string
                sec, ms = divmod(loop_time - start_time, 1000)
                time_str = time.strftime("%Hh %Mm %S.", time.gmtime(sec))
                time_str += "{:03d}s".format(ms)                

                # Add each sensor value to the log line
                for sensor in sensor_keys:
                    log_line += str(recv_msg.__dict__[sensor]) + ','
          
                # Finish the line and write it    
                log_line += '\n'
                log_file.write(log_line)
                log_file.flush()

                print("Sensor data received at " + time_str)



    except (OSError, serial.SerialException, ValueError) as ex:    
        print("Error: " + str(ex))
        
        # Flush file buffer and close file
        log_file.flush()
        log_file.close() 
        
        # Close serial port
        s1.close()
        return
    
