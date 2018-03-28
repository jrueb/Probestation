# Probestation

A simple GUI to control and read out the meters at the probestation.
Currently works with:
* Keithley 6517B
* Keithley 6485
* Agilent E4980A

## Start
To start the program simply run the gui.py by executing
```
python3.4 gui.py
```
or depending on your python installation
```
python gui.py
```

## Usage
This program supports voltage-current (IV tab) and voltage-capacitance measurements (CV tab).

### IV measurement
To perform an IV measurement, the Keithley 6517B is needed.
First set the desired source voltage range using the start voltage, end voltage and abs step controlls of this program. The measurement will be performed by linearly increasing or decreasing by the step size from the start voltage to the end voltage.
To not damage any components a compliance current is set. When one of the current measurements reaches the set compliace current, the voltage source is immediately turned off.
If the Keithley 6485 is properly connected, its current measurement can be enabled by clicking the guarding measurement checkbox.
A time to wait between each time the voltage is set and taking a measurement can be set using the "Wait time" control.
Finally an output folder can be chosen, where the CVS and SVG with the measurement data will be saved.

### CV measurement
To perform an CV measurement, the Keithley 6517B and the Agilent E4980A are needed.
Like in the IV measurement set the desired voltage range by using the corresponding controls. Please note that there is no compliance current in the CV case, so the user has to make sure the requested range doesn't damage the components.
The frequency and the amplitude of the voltage level used in the CV measurement can be change using the frequency setting controls.
Finally wait time and output folder can be set as done in the IV measurement.

## Software dependencies:
* python 3.4 or newer
* [pyvisa](https://github.com/pyvisa/pyvisa) together with a backend like NI-VISA
* PyQt5
* [numpy](http://www.numpy.org/)
* [matplotlib](https://matplotlib.org/) 2.2 or newer

