#!/usr/bin/env python3

from PyQt5 import QtWidgets as QtW
from PyQt5 import QtCore

import os
from collections import namedtuple
from pyvisa.errors import VisaIOError

import gpib_detect
from iv_measurement import IvMeasurementWindow
from cv_measurement import CvMeasurementWindow

def createSpin(lower, upper, step, value, decimals, suffix, tooltip=""):
    spin = QtW.QDoubleSpinBox()
    spin.setRange(lower, upper)
    spin.setSingleStep(step)
    spin.setValue(value)
    spin.setDecimals(decimals)
    spin.setSuffix(suffix)
    if tooltip:
        spin.setToolTip(tooltip)
    return spin

class VoltsrcGroupWidget(QtW.QGroupBox):
    def __init__(self):
        super().__init__("Voltage source")
        
        form = QtW.QFormLayout()
        self.setLayout(form)
        
        self._start_spin = createSpin(-1000, 1000, 0.01, 0, 2, " V",
            "Source voltage to start with")
        self._end_spin = createSpin(-1000, 1000, 0.01, -1, 2, " V",
            "Source voltage to end with")
        self._step_spin = createSpin(0, 1000, 0.01, 0.1, 2, " V",
            "Source voltage difference between taking measurements")
        
        form.addRow("Start voltage", self._start_spin)
        form.addRow("End voltage", self._end_spin)
        form.addRow("Abs step", self._step_spin)
        
    def getVoltages(self):
        start = self._start_spin.value()
        end = self._end_spin.value()
        step = self._step_spin.value()
        
        return (start, end, step)
        
class FreqGroupWidget(QtW.QGroupBox):
    def __init__(self):
        super().__init__("Frequency parameters")
        
        form = QtW.QFormLayout()
        self.setLayout(form)
        
        self._freq_spin = createSpin(0.02, 2000, 0.5, 1, 2, " kHz")
        form.addRow("Frequency", self._freq_spin)
        
        self._volt_spin = createSpin(0, 20, 0.5, 1, 4, " V")
        form.addRow("Voltage level", self._volt_spin)
        
    def getSettings(self):
        freq = self._freq_spin.value() * 1e3
        volt = self._volt_spin.value()
        
        return (freq, volt)
        
class DirectoryLayout(QtW.QHBoxLayout):
    def __init__(self, directory, parent_win):
        super().__init__()
        
        self._parent_win = parent_win
        
        self._label = QtW.QLabel("Output folder: ")
        self.addWidget(self._label)
        self._edit = QtW.QLineEdit(directory)
        self._edit.setReadOnly(True)
        self.addWidget(self._edit)
        self._browse = QtW.QPushButton("Browse...")
        self._browse.clicked.connect(self._onBrowseClicked)
        self.addWidget(self._browse)
        
    def _onBrowseClicked(self):
        new_dir = QtCore.QDir.toNativeSeparators(
            QtW.QFileDialog.getExistingDirectory(
                self._parent_win, "", self.getOutputDir()))
        if new_dir:
            self._edit.setText(new_dir)
            
    def getOutputDir(self):
        return self._edit.text()
        
MeasurementArgs = namedtuple("MeasurementArgs", [
        "type",
        "devname_kei6517b",
        "devname_kei6485",
        "devname_agiE4980A",
        "start",
        "end",
        "step",
        "compcurrent",
        "guardring",
        "frequency",
        "deltavolt",
        "sleep",
        "output_dir"])
        
class IvTab(QtW.QWidget):
    def __init__(self, parent_win, output_dir):
        super().__init__()
        
        self._parent_win = parent_win
        
        vbox = QtW.QVBoxLayout()
        self.setLayout(vbox)
        
        self._voltsrc = VoltsrcGroupWidget()
        vbox.addWidget(self._voltsrc)
        
        hbox = QtW.QHBoxLayout()
        vbox.addLayout(hbox)
        compliance_label = QtW.QLabel("Abs compliance current: ")
        hbox.addWidget(compliance_label)
        self._compliance_spin = createSpin(0.1, 1000, 1, 10, 1, " µA",
            "When the compliance current is reached by one of the measured currents, the voltage source is immediately turned off.")
        hbox.addWidget(self._compliance_spin)
        
        hbox = QtW.QHBoxLayout()
        vbox.addLayout(hbox)
        self._guardring_cb = QtW.QCheckBox("Enable guardring measurement")
        hbox.addWidget(self._guardring_cb)
        
        hbox = QtW.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtW.QLabel("Wait time"))
        self._sleep_spin = createSpin(0, 100, 1, 1, 1, " s", 
            "Time to wait between setting the source voltage and taking the measurement")
        hbox.addWidget(self._sleep_spin)
        
        vbox.addStretch(1)
        
        self._browse_layout = DirectoryLayout(output_dir, self._parent_win)
        vbox.addLayout(self._browse_layout)
        
        hbox = QtW.QHBoxLayout()
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        self._start_button = QtW.QPushButton("Start")
        self._start_button.setToolTip("Start the measurement")
        self._start_button.resize(self._start_button.sizeHint())
        self._start_button.clicked.connect(self._onStartClicked)
        hbox.addWidget(self._start_button)
            
    def _onStartClicked(self):
        if self._parent_win.measurementIsRunning():
            self._parent_win.showErrorDialog("Measurement is currently running.")
            return
    
        start, end, step = self._voltsrc.getVoltages()
        if step <= 0:
            self._parent_win.showErrorDialog("Abs step needs to be positive.")
            return
        if abs(start) > 1000 or abs(end) > 1000:
            self._parent_win.showErrorDialog("Voltage can't be larger than 1000 V.")
            return
            
        guardring = self._guardring_cb.isChecked()
            
        compcurrent = self.getComplianceCurrent()
        if compcurrent <= 0:
            self._parent_win.showErrorDialog("Compliance current needs to be positive.")
            return
            
        sleeptime = self._sleep_spin.value()
        if not 0 <= sleeptime:
            self._parent_win.showErrorDialog("Invalid sleep time.")
            return
            
        output_dir = self._browse_layout.getOutputDir()
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self._parent_win.showErrorDialog("Invalid output directory.")
            return
            
        try:
            detector = gpib_detect.GPIBDetector()
            kei6517b_devname = detector.get_resname_for("KEITHLEY INSTRUMENTS INC.,MODEL 6517B")
            if kei6517b_devname is None:
                self._parent_win.showErrorDialog("Could not find Keithley 6517B.")
                return
            if guardring:
                kei6485_devname = detector.get_resname_for("KEITHLEY INSTRUMENTS INC.,MODEL 6485")
                if kei6485_devname is None:
                    self._parent_win.showErrorDialog("Could not find Keithley 6485.")
                    return
            else:
                kei6485_devname = None
        except VisaIOError:
            self._parent_win.showErrorDialog("Could not connect to GPIB devices.")
            return
            
        args = MeasurementArgs(
            "IV",
            kei6517b_devname,
            kei6485_devname,
            None,
            start,
            end,
            step,
            compcurrent,
            guardring,
            None,
            None,
            sleeptime,
            output_dir)
        self._parent_win.startMeasurement(args)
        
    def getComplianceCurrent(self):
        return self._compliance_spin.value() * 1e-6
        
class CvTab(QtW.QWidget):
    def __init__(self, parent_win, output_dir):
        super().__init__()
        
        self._parent_win = parent_win
        
        vbox = QtW.QVBoxLayout()
        self.setLayout(vbox)
        
        self._voltsrc = VoltsrcGroupWidget()
        vbox.addWidget(self._voltsrc)
        
        self._freqsettings = FreqGroupWidget()
        vbox.addWidget(self._freqsettings)
        
        hbox = QtW.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtW.QLabel("Wait time "))
        self._sleep_spin = createSpin(0, 100, 1, 1, 1, " s")
        self._sleep_spin.setToolTip("Time to wait between setting the source voltage and taking the measurement")
        hbox.addWidget(self._sleep_spin)
        
        vbox.addStretch(1)
		
        self._browse_layout = DirectoryLayout(output_dir, self._parent_win)
        vbox.addLayout(self._browse_layout)
        
        hbox = QtW.QHBoxLayout()
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        self._start_button = QtW.QPushButton("Start")
        self._start_button.setToolTip("Start the measurement")
        self._start_button.resize(self._start_button.sizeHint())
        self._start_button.clicked.connect(self._onStartClicked)
        hbox.addWidget(self._start_button)
        
    def _onStartClicked(self):
        if self._parent_win.measurementIsRunning():
            self._parent_win.showErrorDialog("Measurement is currently running.")
            return
            
        start, end, step = self._voltsrc.getVoltages()
        if step <= 0:
            self._parent_win.showErrorDialog("Abs step needs to be positive.")
            return
            
        freq, volt = self._freqsettings.getSettings()
        if not 20 <= freq <= 2e6:
            self._parent_win.showErrorDialog("Frequency must be between 20 Hz and 2 MHz.")
            return
        if not 0 <= volt <= 20:
            self._parent_win.showErrorDialog("Frequency voltage must to be between 0 and 20 V.")
            return
            
        sleeptime = self._sleep_spin.value()
        if not 0 <= sleeptime:
            self._parent_win.showErrorDialog("Invalid sleep time.")
            return
            
        output_dir = self._browse_layout.getOutputDir()
        if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
            self._parent_win.showErrorDialog("Invalid output directory.")
            return
            
        try:
            detector = gpib_detect.GPIBDetector()
            kei6517b_devname = detector.get_resname_for("KEITHLEY INSTRUMENTS INC.,MODEL 6517B")
            if kei6517b_devname is None:
                self._parent_win.showErrorDialog("Could not find Keithley 6517B.")
                return
            agie4980a_devname = detector.get_resname_for("Agilent Technologies,E4980A")
            if agie4980a_devname is None:
                self._parent_win.showErrorDialog("Could not find Agilent E4980A.")
                return
        except VisaIOError:
            self._parent_win.showErrorDialog("Could not connect to GPIB devices.")
            return
            
        args = MeasurementArgs(
            "CV",
            kei6517b_devname,
            None,
            agie4980a_devname,
            start,
            end,
            step,
            None,
            None,
            freq,
            volt,
            sleeptime,
            output_dir)
        self._parent_win.startMeasurement(args)
        

class MainWindow(QtW.QMainWindow):
    def __init__(self, output_dir):
        super().__init__()
        
        #self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle("Probestation measurement")
        
        self._tabwidget = QtW.QTabWidget()
        self.setCentralWidget(self._tabwidget)
        
        self._ivtab = IvTab(self, output_dir)
        self._tabwidget.addTab(self._ivtab, "IV")
        
        self._cvtab = CvTab(self, output_dir)
        self._tabwidget.addTab(self._cvtab, "CV")
            
        self._mwin = None

    def measurementIsRunning(self):
        return not self._mwin is None and self._mwin.isRunning()
        
    def startMeasurement(self, args):
        if args.type == "IV":
            self._mwin = IvMeasurementWindow(self, args)
        elif args.type == "CV":
            self._mwin = CvMeasurementWindow(self, args)
        else:
            raise NotImplementedError(args.type)
        self._mwin.setWindowModality(QtCore.Qt.WindowModal)
        self._mwin.set_absolute(True)
        self._mwin.start()
            
    def showErrorDialog(self, message):
        reply = QtW.QMessageBox.critical(self, "Error",
            message, QtW.QMessageBox.Ok, QtW.QMessageBox.Ok)
        
        
if __name__ == "__main__":
    import sys
    
    app = QtW.QApplication(sys.argv)
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        output_dir = sys.argv[1]
    else:
        output_dir = os.getcwd()
    win = MainWindow(output_dir)
    win.show()
    sys.exit(app.exec_())
