# Probe Station Manual and Software

Refer to docs/manual.pdf for detailed instructions.

# Usage

Usage: `gui.py [options]`

Options:
  `-h` or `--help`   show this help message and exit
  `-d` or `--debug`  Debug flag



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

On Ubuntu 18.04 you first have to install `git` and `pip` for `python3`
```
sudo apt-get install git python3-pip
```
Then upgrade `pip` to the latest version
```
sudo pip3 install --upgrade pip
```
You can then install the required python packages
```
sudo pip3 install pyvisa pyvisa-py numpy matplotlib pyserial pyqt5
```
For a serial connection, your user account has to be added to the `dialout` group
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

On CERN CentOS 7 you also first have to install `git` and `python3`. Open a root terminal and run
```
yum install centos-release-scl
```
to enable software collections and then run:
```
yum install rh-python35 git
```
Then you can load the `python3` environment
```
source /opt/rh/rh-python35/enable
```
and upgrade `pip` to the latest version
```
pip3 install --upgrade pip
```
You can then install the required python packages
```
pip3 install pyvisa pyvisa-py numpy matplotlib pyserial pyqt5
```
For a serial connection, your user account has to be added to the `dialout` group
```
usermod -a -G dialout <yourusername>
```
You can now close the root terminal. Then download the repository with
```
git clone https://github.com/thomaseichhorn/probestation.git /where/you/want/to/install
```
After logging off and logging in again to refresh the user permissions, load the `python3` environment again
```
source /opt/rh/rh-python35/enable
```
You should be able to run the software from the directory you specified before with the command
```
python3 gui.py
```

## Microsoft Windows 7

On Microsoft Windows 7 you need a Python 3.x environment, such as [Miniconda](https://conda.io/miniconda.html).
If you have a DESY Windows installation, use DSM to install `Anaconda` (Software Categories -> Programming).
With the `Anaconda prompt` (or from the Windows command line) you can install the needed python packages with the command
```
conda install -c conda-forge pyvisa pyvisa-py numpy matplotlib pyserial pyqt
```
Otherwise you can select these packages with the Anaconda Navigator.
Assuming you downloaded the software to `C:\some\directory`, you can then run the software with
```
python C:\some\directory\gui.py
```
from the `Anaconda prompt` or from the Windows command line.

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
