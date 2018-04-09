# Probe Station
Probe Station Manual and Software

Refer to docs/manual.pdf for detailed instructions.


## DESY FH E-Lab Probe Station PC
To run the probe station software, click on the Probestation link.
This executes the command:

C:\Programfiles\Anaconda3\python.exe gui.py D:\Measurements

running in the folder:

D:\Probestation

This should start the software.

## Software Dependencies
* python 3.4 or newer
* [pyvisa](https://github.com/pyvisa/pyvisa) together with a backend like NI-VISA
* PyQt5
* [numpy](http://www.numpy.org/)
* [matplotlib](https://matplotlib.org/) 2.2 or newer

## Start
To start the program simply run the gui.py by executing
```
python3.4 gui.py
```
or depending on your python installation
```
python gui.py
```