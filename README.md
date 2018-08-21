# Probe Station Manual and Software

Refer to `docs/manual.pdf` for detailed operation and usage instructions.


# Usage

Usage: `python gui.py [options] <default storage path>`

If no default storage path is specified, the current directory is used.

Options:
  `-h`, `--help`   show this help message and exit
  `-d`, `--debug`  debug flag, enables more verbose console output


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
cd 

# Installation on other PCs

The software has been tested to run on Ubuntu 18.04, Raspbian Strech, CERN CentOS 7 and Microsoft Windows 7.


## Ubuntu 18.04


### Normal Installation

On Ubuntu 18.04 you first have to install `git` and `pip` for python
```
sudo apt-get install git python3-pip
```
Upgrade `pip` to the latest version with
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


### Advanced Options

These commands should not be needed, but are listed here as reference.

- If you do not have `sudo` rights, append a `--user` to the `pip3` commands to install the python packages for your user only.

- To use `Python 2.7`, run `sudo apt-get install python-pip` to get pip2. Then install the python packages, substituting `pip2` for `pip3` and run the program with the command `python gui.py`.

- The program automatically defaults back to `Qt4` if `Qt5` can not be found. The `Qt4` packages can't be installed by `pip`, but have to be installed with `sudo apt-get install python-qt4` for `Python 2.7` and `sudo apt-get install python3-pyqt4` for `Python 3`.


## Raspbian Strech

Currently, `Qt5` is not available via the package manager, so the easiest way to run the software is with `Python 2` using `Qt 4`. You will need to install some packages:
```
sudo apt-get install git python-qt4
```
Upgrade `pip` to the latest version with
```
sudo pip install --upgrade pip
```
You can then install the required python packages
```
sudo pip install pyvisa pyvisa-py numpy matplotlib pyserial
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
python gui.py
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

On Microsoft Windows 7 you need a Python environment, such as [Miniconda](https://conda.io/miniconda.html).
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


## Ubuntu 18.04 and Raspbian Strech

On Ubuntu 18.04 and Raspbian Strech you need to install several `latex` packages via
```
sudo apt-get install texlive-latex-base texlive-science texlive-latex-extra
```
You can then build the documentation with the command
```
cd doc && pdflatex manual.tex
```


## CERN CentOS 7

On CERN CentOS 7 you will need to install several `latex` packages. Unfortunately, the easiest way is to install all available ones from a root terminal
```
yum install texlive-*
```
You then have to download some packages manually
```
cd doc
wget http://www.cs.cmu.edu/afs/cs/misc/tex/common/teTeX-1.0/lib/texmf/tex/latex/misc/SIunits.sty
wget http://www.cs.cmu.edu/afs/cs/misc/tex/common/teTeX-1.0/lib/texmf/tex/latex/misc/tocbibind.sty
wget http://www.cs.cmu.edu/afs/cs/misc/tex/common/teTeX-1.0/lib/texmf/tex/latex/misc/stdclsdv.sty
```
Before you can then build the documentation
```
pdflatex manual.tex
```

## Microsoft Windows 7

This is beyond the scope of this document, there are good step-by-step instructions on the internet.
