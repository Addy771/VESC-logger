import pyvesc
#from pyvesc import GetValues
import serial, os, time, re, datetime
import ports


def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)


# pass serial object?
def log_vesc(port="COM1"):

    base_name = "vesc_log"  # base name used for log files
    log_interval = 100  # How often to get VESC values in milliseconds
       
    # Prepare the log directory path
    log_dir = "/boot/vesc_logs"
    #log_dir = os.path.join(os.getcwd(), 'logs')    # The log directory will be added to the current working directory    
    
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
        
        # Write the column headers for the CSV format
        log_file.write("time (s), temp_fet (C), temp_motor (C), current_motor (A), current_in (A), avg_id (A), avg_iq (A), duty_now, rpm, v_in (V), amp_hours, amp_hours_charged, watt_hours, watt_hours_charged, tachometer, tachometer_abs, mc_fault_code, unknown\n")
        
        input_buffer = bytearray()   
        
        # Start polling timer
        last_time = millis()
        start_time = last_time
        
        # Loop forever
        while True:
            
            # Record the current time
            loop_time = millis()
            
            # If polling timer expires reset the timer and poll the VESC
            if loop_time - last_time >= log_interval:
                last_time = loop_time
                print("Elapsed: " + str((loop_time - start_time) / 1000) + '\r')

                # pyvesc creates frame to request sensor data
                send_packet = pyvesc.encode_request(pyvesc.GetValues)
                
                # Write frame
                s1.write(send_packet)
                sent_time = millis()
        
            # check if serial buffer has data
            if s1.in_waiting > 0:
                input_buffer += s1.read(s1.in_waiting) # Grab the bytes waiting in the serial input

            # If there is enough data for VESC frame
            if len(input_buffer) > 61:
                recv_msg, consumed = pyvesc.decode(input_buffer)
                input_buffer = input_buffer[consumed:]  # trim consumed bytes
                
                """ 
                # print values for debug
                print("Received packet after " + str(millis() - sent_time) + "ms\n")
                
                for sensor, value in recv_msg.__dict__.items():
                    print("S: " + str(sensor) + "   V:" + str(value))
                
                print("\nEND PACKET\n\n")
                """
                
                # Start the line with the time column value
                log_line = str((loop_time - start_time) / 1000) + ','                
                
                # Add each sensor value to the log line
                log_line += str(recv_msg.temp_fet) + ','
                log_line += str(recv_msg.temp_motor) + ','
                log_line += str(recv_msg.current_motor) + ','
                log_line += str(recv_msg.current_in) + ','
                log_line += str(recv_msg.avg_id) + ','
                log_line += str(recv_msg.avg_iq) + ','
                log_line += str(recv_msg.duty_now) + ','
                log_line += str(recv_msg.rpm) + ','
                log_line += str(recv_msg.v_in) + ','
                log_line += str(recv_msg.amp_hours) + ','
                log_line += str(recv_msg.amp_hours_charged) + ','
                log_line += str(recv_msg.watt_hours) + ','
                log_line += str(recv_msg.watt_hours_charged) + ','
                log_line += str(recv_msg.tachometer) + ','
                log_line += str(recv_msg.tachometer_abs) + ','
                log_line += str(recv_msg.mc_fault_code) + ','
                log_line += str(recv_msg.unknown)                
                
                # Finish the line and write it    
                log_line += '\n'
                log_file.write(log_line)
                log_file.flush()


    except (OSError, serial.SerialException, ValueError) as ex:    
        print("Error: " + str(ex))
        
    # Flush file buffer and close file
    log_file.flush()
    log_file.close() 
    
    # Close serial port
    s1.close()
    return
    

def main():

    # Create serial class
    s1 = serial.Serial(timeout=0)
    
    test_port = "/dev/ttyACM0"


    s1.baudrate = 115200
    s1.port = test_port
 
    while True:
        try:
            s1.open()
        except (OSError, serial.SerialException, ValueError):
            pass
    
        if s1.isOpen():
            print("\nPort available. Starting.")
            s1.close()
            log_vesc(test_port)
            
        else:
            print("Could not open port.")   

        time.sleep(1)
    
    
    
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        raise
