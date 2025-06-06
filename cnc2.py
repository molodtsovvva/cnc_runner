import csv
import sys
import re
import time
import argparse
from serial import Serial
from serial.tools import list_ports
from tqdm import tqdm
from contextlib import closing
import subprocess

# TODO: arg parse for port and baudrate - done
# TODO: arg parse for X/Y coordinates and to select initial home machine,  just unlock, or none (if machine is already unlocked) - done(?)


# Starting position for acqusition
x_start = 30
y_start = 30
z= 0



#specify the step in mm:
step_size = 5
#specify the number of steps:
step_number = 8
#specify the waiting time between steps in sec:
wait_time = 10
# name of the other python program to call for acquisition
prog_name = "test2.py"
prog_name = f'echo'
prog_args = ['echo', './nHCAL_DAQ']



# Code to Move the Machine across the square array
run_code = [

    "$X",
    "$#",
    "G21                    ; Millimeters",
    "G54                    ; Activate work coordinate system G54 (default, but safe to specify)",
    "$#"
   
]

# Output CSV filename
output_file = "positions2.csv"

# Collect positions
positions = []


for j in range(step_number):
    #y = y_start + j * step_size
    y = j * step_size
    for i in range(step_number):
        #x = x_start + i * step_size
        x = i * step_size
        positions.append((x, y))
        run_code.append(f'G00 X{x} Y{y} F1000 ; Move to (X={x}, Y={y})')
        run_code.append(f'DAQ X{x} Y{y} ; Trigger acquisition')
        run_code.append(f'G4 P{wait_time} ; Wait {wait_time}s')
        
   

# Write to CSV
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['X (mm)', 'Y (mm)'])  # Header
    writer.writerows(positions)




# Code to Home the Machine (and rezero)
send_home = [

    "$H                   ; Home machine (if supported)",
    "$#                   ; Print offsets"
    "G90                  ; Use absolute positioning",
    "G21                    ; Millimeters",
    "G17 ; Select XY plane",
    "G10 L20 P1 X0 Y0       ; Set current position as 0,0 for work coordinate system G54",
    "$#                     ; Print offsets, verify G54",
    f'G00 X{x} Y{y} F1000 ; Move to (X={x}, Y={y})',
    ]





#codes=send_home

parser = argparse.ArgumentParser(
        prog="pyGcodeSender",
        description="A python script to run the CNC."
    )

#parser.add_argument("-p", "--port", help="serial port", metavar="port name")
parser.add_argument("-m", "--mode", help="mode of operation: home/run", metavar="mode of operation")
parser.add_argument("-b", "--baudrate", default=115200, type=int, help="baud rate, default 115200", metavar="baud rate")

args = parser.parse_args()



# Start of the program.
print('='*130)
print("Welcome to use this simple python script to send gcode file using serial.")
print()

# Check settings before continue.
print("Current setting:")
print(f"\tMode of Operation: {args.mode}")
#print(f"\tPort name: {port}")
print(f"\tBaud rate: {args.baudrate}")
print()
while(1):
    command = input("Would you like to continue with these settings?[y/n]")
    if command.strip().lower() == 'y':
        break
    elif command.strip().lower() =='n':
        sys.exit()
    else:
        print("Oooops! Please input yes or no.")
        continue





if args.mode == "run":
    print("Run Mode!")
    codes = run_code
elif args.mode == "home":
    print("Home Mode!")
    codes = send_home
else:
    print("Oooops! Please input run or home.")
    sys.exit()



print("Codes to be sent:")
for code in codes:
    print(f"  {code}")

def send_and_wait_ok(ser, line, timeout=15):
    ser.write((line.strip() + '\n').encode())
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = ser.readline().decode('ascii', errors='ignore').strip()
        if resp:
            print(f"<- {resp}")
            if resp.lower().startswith('ok'):
                return True
    raise RuntimeError(f"No OK received for: {line}")

if __name__ == '__main__':
    
    # port = 'COM4' # port = '/dev/tty.usbmodem11101'  # pick one from the list
    port = '/dev/tty.usbmodem2101'  # pick one from the list


    try:
        with closing(Serial(port, baudrate=115200, timeout=0.1)) as s:
            # wake/reset & consume banner
            s.write(b"\r\n\r\n")
            time.sleep(2)
            while True:
                line = s.readline().decode('ascii', errors='ignore').strip()
                if not line:
                    break
                print(f"<- {line}")

            for code in tqdm(codes, unit=" cmd", ncols=100):
                if not code.strip() or code.strip().startswith(';'):
                    continue
                # Checks if triggered
                if code.strip().startswith('DAQ'):
                    print("The line contains the DAQ symbol.!!")
#                    GET X AND Y from string, pass to program args
#                    exec(open(prog_name).read())

                    match = re.search(r'X(\d+)\s+Y(\d+)', code)
                    if match:
                        x = int(match.group(1))
                        y = int(match.group(2))
                        print(f"X: {x}, Y: {y}")
                    else:
                        print("No match found.")


                    prog_args = ["echo", "./runMyDaq", f'{wait_time}', f'{x}', f'{y}']
                    result = subprocess.run(prog_args, capture_output=True, text=True)

                    # Access the output and return code
                    print(result.stdout)  # Print standard output
                    print(result.returncode)  # Print return code (0 means success)
                    continue
                #
                tqdm.write(f">> {code}")
                send_and_wait_ok(s, code, 3*wait_time)
                #

            

        print("\nAll codes have been sent successfully. 🎉")
        if args.mode == "run":
            print(f"Saved {len(positions)} positions to {output_file}")

    except Exception as e:
        print("Serial error:", e) 
