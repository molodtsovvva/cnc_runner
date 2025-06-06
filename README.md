# cnc_runner
Terminal-ran CNC controller

To run the program, save the python file in the directory to which you cd'ed, and give it a name (e.g. cnc.py). Then, having installed python/python3, run the following:

> python3 cnc.py -p COM4 -b 115200 -m home

-p / --port : specify the port to which the CNC is connected <br />
-b / --baudrate : baud rate, defaults to 115200 <br />
-m / --mode : mode of operation: can either be **run** or **home** <br />
    **home** takes the machine to (0,0,0) (can be modified) and defines that point as the zero for future reference. <br />
    **run** starts at the initial position specified in the program and iterates over the coordinates of the square. the coordinates are recorded in the position.csv file that can be accessed in the program folder. <br />

The step size, number of steps, and the waiting time in between acquisitions can be changed INSIDE the program.

Recommended to first home the CNC, then run. The list of the positions the CNC iterated through can be found in positions.csv. 


If using the mac version, cnc2.py, do not specify the port in the call command. Example:
> python cnc2.py --mode run


Instead, specify the port inside the program itself. To see the list of available ports, run:
> ls /dev/tty.*




