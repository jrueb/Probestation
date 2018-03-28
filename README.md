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

## Software dependencies:
* python 3.4 or newer
* [pyvisa](https://github.com/pyvisa/pyvisa) together with a backend like NI-VISA
* PyQt5
* [numpy](http://www.numpy.org/)
* [matplotlib](https://matplotlib.org/) 2.2 or newer

