# Probe Station Manual and Software

Refer to docs/manual.pdf for detailed instructions.

# DESY FH E-Lab Probe Station PC

To run the probe station software, click on the Probestation link.
This executes the command:
```
C:\Programfiles\Anaconda3\python.exe gui.py D:\Measurements
```
running in the folder:
```
D:\Probestation
```
This should start the software.

# Installation on other PCs

The software has been tested to run on Ubuntu 18.04, CERN CentOS 7 and Microsoft Windows 7.

## Ubuntu 18.04

On Ubuntu 18.04 you first have to install git and pip for python 3
```
sudo apt-get install git python3-pip
```
Then upgrade pip to the latest version
```
sudo pip3 install --upgrade pip
```
You can then install the required python packages
```
sudo pip3 install pyvisa pyvisa-py numpy matplotlib pyserial pyqt5
```
For a serial connection, your user account has to be added to the dialout group
```
sudo usermod -a -G dialout $USER
```
Then download the repository with
```
git clone https://github.com/thomaseichhorn/probestation.git /where/you/want/to/install
```
After logging off and logging in again to refresh the user permissions, you should be able to run the software from the directory you specified before with the command
```
python3 gui.py
```

## CERN CentOS 7

On CERN CentOS 7 you also first have to install git and python 3. Open a root terminal and run
```
yum install centos-release-scl
```
to enable software collections and then run:
```
yum install rh-python35 git
```
Then you can load the python 3.5 environment
```
source /opt/rh/rh-python35/enable
```
and upgrade pip to the latest version
```
pip3 install --upgrade pip
```
You can then install the required python packages
```
pip3 install pyvisa pyvisa-py numpy matplotlib pyserial pyqt5
```
For a serial connection, your user account has to be added to the dialout group
```
usermod -a -G dialout <yourusername>
```
You can now close the root terminal. Then download the repository with
```
git clone https://github.com/thomaseichhorn/probestation.git /where/you/want/to/install
```
After logging off and logging in again to refresh the user permissions, load the python 3.5 environment again
```
source /opt/rh/rh-python35/enable
```
You should be able to run the software from the directory you specified before with the command
```
python3 gui.py
```

## Microsoft Windows

to be updated:

* python 3.4 or newer
* [pyvisa](https://github.com/pyvisa/pyvisa) together with a backend like NI-VISA
* PyQt5
* [numpy](http://www.numpy.org/)
* [matplotlib](https://matplotlib.org/) 2.2 or newer

# Recompiling the User Manual

To recompile the user manual, you need a working latex installation with some additional packages.

## Ubuntu 18.04

On Ubuntu 18.04 you need to install several latex packages via
```
sudo apt-get install texlive-latex-base texlive-science texlive-latex-extra
```
You can then build the documentation with the command
```
cd doc && pdflatex manual.tex
```

## CERN CentOS 7

to be updated:
