#!/usr/bin/env python

from __future__ import absolute_import
import logging

try:
	from PyQt5 import QtWidgets as QtW
	from PyQt5 import QtCore
except ImportError as e :
	from PyQt4 import QtGui as QtW
	from PyQt4 import QtCore

import os
from collections import namedtuple
from pyvisa.errors import VisaIOError

import gpib_detect
from iv_measurement import IvMeasurementWindow
from cv_measurement import CvMeasurementWindow
from strip_measurement import StripMeasurementWindow

def createSpin ( lower, upper, step, value, decimals, suffix, tooltip = u"" ) :
	spin = QtW.QDoubleSpinBox ( )
	spin.setRange ( lower, upper )
	spin.setSingleStep ( step )
	spin.setValue ( value )
	spin.setDecimals ( decimals )
	spin.setSuffix ( suffix )
	if tooltip :
		spin.setToolTip ( tooltip )
	return spin

class GeneralOptionsWidget ( QtW.QGroupBox ) :
	def __init__ ( self ) :
		super ( GeneralOptionsWidget, self ) .__init__ ( u"Device communication" )

		form = QtW.QFormLayout ( )
		self.setLayout ( form )

		self._serialenable_cb = QtW.QCheckBox ( )
		self._serialenable_cb.setChecked ( True )
		self._serialenable_cb.toggled.connect ( self._onSerialEnableToggled )
		form.addRow ( u"Enable serial device connection", self._serialenable_cb )
		
		self._envsensorsenable_cb = QtW.QCheckBox ( )
		self._envsensorsenable_cb.setChecked ( True )
		form.addRow ( u"  Enable enviroment sensors", self._envsensorsenable_cb )
		
	def _onSerialEnableToggled ( self, checked ):
		self._envsensorsenable_cb.setDisabled ( not checked )
		if not checked:
			self._envsensorsenable_cb.setChecked ( False )

	def getStatus ( self ) :
		enableserial = self._serialenable_cb.isChecked ( )
		enableenvsensors = self._envsensorsenable_cb.isChecked ( )
		return ( enableserial, enableenvsensors )

class VoltsrcGroupWidget ( QtW.QGroupBox ) :
	def __init__ ( self ) :
		super ( VoltsrcGroupWidget, self ) .__init__ ( u"Voltage source" )

		form = QtW.QFormLayout ( )
		self.setLayout ( form )

		self._start_spin = createSpin ( -1000, 1000, 0.01, 0, 2, u" V", u"Source voltage to start with" )
		self._end_spin = createSpin ( -1000, 1000, 0.01, -1, 2, u" V", u"Source voltage to end with" )
		self._step_spin = createSpin ( 0, 1000, 0.01, 0.1, 2, u" V", u"Source voltage difference between taking measurements" )
		self._sleep_spin = createSpin ( 0, 100, 1, 1, 1, u" s", u"Time to wait between setting the source voltage and taking the measurement" )
		self._compliance_spin = createSpin ( 0.1, 1000, 1, 10, 1, u" \u03BCA", u"If the compliance current is reached by one of the measured currents, the voltage source is immediately turned off." )

		form.addRow ( u"Start voltage", self._start_spin )
		form.addRow ( u"End voltage", self._end_spin )
		form.addRow ( u"Abs step", self._step_spin )
		form.addRow ( u"Wait time", self._sleep_spin )
		form.addRow ( u"Abs compliance current", self._compliance_spin )

	def getVoltages ( self ) :
		start = self._start_spin.value ( )
		end = self._end_spin.value ( )
		step = self._step_spin.value ( )
		sleeptime = self._sleep_spin.value ( )
		compcurrent = self._compliance_spin.value ( ) * 1e-6

		return ( start, end, step, sleeptime, compcurrent )

class GuardMeasWidget ( QtW.QGroupBox ) :
	def __init__ ( self ) :
		super ( GuardMeasWidget, self ) .__init__ ( u"Guard ring" )

		form = QtW.QFormLayout ( )
		self.setLayout ( form )

		self._guardring_cb = QtW.QCheckBox ( )

		form.addRow ( u"Enable guard ring measurement", self._guardring_cb )

	def getStatus ( self ) :
		guardring = self._guardring_cb.isChecked ( )
		return ( guardring )

class FreqGroupWidget ( QtW.QGroupBox ) :
	def __init__ ( self ) :
		super ( FreqGroupWidget, self ) .__init__ ( u"LCR parameters" )

		form = QtW.QFormLayout ( )
		self.setLayout ( form )

		self._freq_spin = createSpin ( 0.02, 2000, 0.5, 1, 2, u" kHz" )
		form.addRow ( u"Frequency", self._freq_spin )

		self._volt_spin = createSpin ( 0, 20, 0.5, 1, 2, u" V" )
		form.addRow ( u"AC Voltage level", self._volt_spin )

	def getSettings ( self ):
		freq = self._freq_spin.value ( ) * 1e3
		volt = self._volt_spin.value ( )

		return ( freq, volt )

class StripGroupWidget ( QtW.QGroupBox ) :
	def __init__ ( self ) :
		super ( StripGroupWidget, self ) .__init__ ( u"Strip Measurement" )

		form = QtW.QFormLayout ( )
		self.setLayout ( form )

		self._select_r = QtW.QComboBox ( )
		self._select_r.addItems ( ["Capacitance", "Resistance/Impedance"] )
		form.addRow ( u"Measurement Type", self._select_r )

	def getSettings ( self ):
		select = self._select_r.currentText ( )

		return ( select )

class DirectoryLayout ( QtW.QHBoxLayout ):
	def __init__ ( self, directory, parent_win ) :
		super ( DirectoryLayout, self ) .__init__ ( )

		self._parent_win = parent_win

		self._label = QtW.QLabel ( u"Output folder: " )
		self.addWidget ( self._label )
		self._edit = QtW.QLineEdit ( directory )
		self._edit.setReadOnly ( True )
		self.addWidget ( self._edit )
		self._browse = QtW.QPushButton ( u"Browse..." )
		self._browse.clicked.connect ( self._onBrowseClicked )
		self.addWidget ( self._browse )

	def _onBrowseClicked ( self ) :
		new_dir = QtCore.QDir.toNativeSeparators ( QtW.QFileDialog.getExistingDirectory ( self._parent_win, u"", self.getOutputDir ( ) ) )
		if new_dir :
			self._edit.setText ( new_dir )

	def getOutputDir ( self ) :
		return self._edit.text ( )

MeasurementArgs = namedtuple ( u"MeasurementArgs", [u"type",
													u"serialenable",
													u"devname_ardenv",
													u"devname_hv",
													u"devname_kei6485",
													u"devname_agiE4980A",
													u"start",
													u"end",
													u"step",
													u"compcurrent",
													u"guardring",
													u"resistance",
													u"frequency",
													u"deltavolt",
													u"sleep",
													u"output_dir"] )
													
class MeasurementSetttingsError ( RuntimeError ) :
	pass
													
class MeasurementTab ( QtW.QWidget ) :
	def __init__ ( self, parent_win, output_dir ) :
		super ( MeasurementTab, self ).__init__ ( )
		
		self._parent_win = parent_win
		
		self._vbox = QtW.QVBoxLayout ( )
		self.setLayout ( self._vbox )
		
		self._general = GeneralOptionsWidget ( )
		self._vbox.addWidget ( self._general )
		
		self._voltsrc = VoltsrcGroupWidget ( )
		self._vbox.addWidget ( self._voltsrc )
		
		self._vbox.addStretch ( 1 )
		
		self._bottombox = QtW.QVBoxLayout ( )
		self._vbox.addLayout ( self._bottombox )
		
		self._browse_layout = DirectoryLayout ( output_dir, self._parent_win )
		self._bottombox.addLayout ( self._browse_layout )
		
		hbox = QtW.QHBoxLayout ( )
		hbox.addStretch ( 1 )
		self._bottombox.addLayout ( hbox )
		self._start_button = QtW.QPushButton ( u"Start" )
		self._start_button.setToolTip ( u"Start the measurement" )
		self._start_button.resize ( self._start_button.sizeHint ( ) )
		self._start_button.clicked.connect ( self._onStartClicked )
		hbox.addWidget ( self._start_button )
		
	def _addToCenter ( self, obj ) :
		if isinstance ( obj, QtW.QWidget ) :
			self._vbox.insertWidget ( self._vbox.count ( ) - 2, obj )
		else:
			self._vbox.insertLayout ( self._vbox.count ( ) - 2, obj )
		
	def _addToBottom ( self, obj ) :
		if isinstance ( obj, QtW.QWidget ) :
			self._bottombox.insertWidget ( self._bottombox.count ( ) - 2, obj )
		else:
			self._bottombox.insertLayout ( self._bottombox.count ( ) - 2, obj )
			
	def _setupMeasurement ( self ) :
		start, end, step, sleeptime, compcurrent = self._voltsrc.getVoltages ( )
		if step <= 0 :
			raise MeasurementSetttingsError ( u"Abs step needs to be positive." )
		if abs ( start ) > 1000 or abs ( end ) > 1000 :
			raise MeasurementSetttingsError ( u"Voltage can't be larger than 1000 V." )
		if not 0 <= sleeptime :
			raise MeasurementSetttingsError ( u"Invalid sleep time." )
			
		serialenable, envsensorsenable = self._general.getStatus ( )
		
		if compcurrent <= 0 :
			raise MeasurementSetttingsError ( u"Compliance current needs to be positive." )
			
		output_dir = self._browse_layout.getOutputDir ( )
		if not os.path.isdir ( output_dir ) or not os.access ( output_dir, os.W_OK ) :
			raise MeasurementSetttingsError ( u"Invalid output directory." )
			
		try :
			detector = gpib_detect.GPIBDetector ( serialenable )
			if envsensorsenable:
				devname_ardenv = detector.get_resname_for ( u"Arduino Probestation Enviroment Sensoring" )
				if devname_ardenv is None:
					raise MeasurementSetttingsError ( u"Could not find an Arduino for enviroment sensoring" )
			else:
				devname_ardenv = None
			kei6517b_devname = detector.get_resname_for ( u"KEITHLEY INSTRUMENTS INC.,MODEL 6517B" )
			kei2410_devname = detector.get_resname_for ( u"KEITHLEY INSTRUMENTS INC.,MODEL 2410" )
			if kei6517b_devname is None :
				hvdev_devname = kei2410_devname
				logger.debug ( u"  Couldn't find Keithley 6517B, trying Keithley 2410 for HV." )
			if kei2410_devname is None :
				hvdev_devname = kei6517b_devname
				logger.debug ( u"  Couldn't find Keithley 2410, trying Keithley 6517B for HV." )
			if ( kei6517b_devname is not None and kei2410_devname is not None) :
				raise MeasurementSetttingsError ( u"I found both Keithley 6517B and Keithley 2410!<br><br>I don't know which to use!" )
			if ( kei6517b_devname is None and kei2410_devname is None ) :
				raise MeasurementSetttingsError ( u"Could not find Keithley 6517B or Keithley 2410." )
			else :
				kei6485_devname = None
		except VisaIOError :
			raise MeasurementSetttingsError ( u"Could not connect to GPIB/serial devices." )
				
		args = MeasurementArgs ( None, # type
								 serialenable, # serialenable
								 devname_ardenv, # devname_ardenv
								 hvdev_devname, # devname_hv
								 kei6485_devname, # devname_kei6485
								 None, # devname_agiE4980A
								 start, # start
								 end, # end
								 step, # step
								 compcurrent, # compcurrent
								 None, # guardring
								 None, # resistance
								 None, # frequency
								 None, # deltavolt
								 sleeptime, # sleep
								 output_dir ) # output_dir
			
		return args
		
	def _onStartClicked ( self, warning = None ) :
		if self._parent_win.measurementIsRunning ( ) :
			self._parent_win.showErrorDialog ( u"Measurement is currently running." )
			return

		check = QtW.QMessageBox.question ( self, u"Warning", warning, QtW.QMessageBox.Yes, QtW.QMessageBox.No )
		if check == QtW.QMessageBox.No :
			return
				
		try:
			args = self._setupMeasurement ( )
		except MeasurementSetttingsError as e:
			self._parent_win.showErrorDialog ( str ( e ) )
			return
		
		self._parent_win.startMeasurement ( args )

class IvTab ( MeasurementTab ) :
	def __init__ ( self, parent_win, output_dir ) :
		super ( IvTab, self ) .__init__ ( parent_win, output_dir )

		self._guard = GuardMeasWidget ( )
		self._addToCenter ( self._guard )
		
	def _setupMeasurement ( self ):
		args = super ( IvTab, self ) ._setupMeasurement ( ) ._asdict ( )
		args = dict ( args )
		
		guardring = self._guard.getStatus ( )
		
		kei6485_devname = None
		try:
			if guardring :
				kei6485_devname = detector.get_resname_for ( u"KEITHLEY INSTRUMENTS INC.,MODEL 6485" )
				if kei6485_devname is None :
					raise MeasurementSetttingsError ( u"Could not find Keithley 6485." )
		except VisaIOError:
			raise MeasurementSetttingsError ( u"Could not connect to GPIB/serial devices." )

		args["type"] = u"IV"
		args["guardring"] = guardring
		args["devname_kei6485"] = kei6485_devname
		
		return MeasurementArgs ( **args )
		

	def _onStartClicked ( self ) :
		super( IvTab, self ) ._onStartClicked ( u"Is the CV/IV box set to IV?" )

class CvTab ( MeasurementTab ) :
	def __init__ ( self, parent_win, output_dir ) :
		super ( CvTab, self ) .__init__ ( parent_win, output_dir )

		self._freqsettings = FreqGroupWidget ( )
		self._addToCenter ( self._freqsettings )
		
	def _setupMeasurement ( self ):
		args = super ( CvTab, self ) ._setupMeasurement ( ) ._asdict ( )
		args = dict ( args )
		
		freq, volt = self._freqsettings.getSettings ( )
		if not 20 <= freq <= 2e6 :
			raise MeasurementSetttingsError ( u"Frequency must be between 20 Hz and 2 MHz." )
		if not 0 <= volt <= 20 :
			raise MeasurementSetttingsError ( u"AC voltage must be between 0 V and 20 V." )
		
		agie4980a_devname = None
		try:
			agie4980a_devname = detector.get_resname_for ( u"Agilent Technologies,E4980A" )
			if agie4980a_devname is None :
				raise MeasurementSetttingsError ( u"Could not find Agilent E4980A." )
		except VisaIOError:
			raise MeasurementSetttingsError ( u"Could not connect to GPIB/serial devices." )

		args["type"] = u"CV"
		args["compcurrent"] *= 1000.0 # CV box adds 1KOhm -> compcurrent goes down...
		args["frequency"] = freq
		args["deltavolt"] = volt
		args["devname_agiE4980A"] = agie4980a_devname
		
		return MeasurementArgs ( **args )

	def _onStartClicked ( self ) :
		super( CvTab, self ) ._onStartClicked ( u"Is the CV/IV box set to both CV and External?" )

class StripTab ( MeasurementTab ) :
	def __init__ ( self, parent_win, output_dir ) :
		super ( StripTab, self ) .__init__ ( parent_win, output_dir )

		self._freqsettings = FreqGroupWidget ( )
		self._addToCenter ( self._freqsettings )
		
		self._stripsettings = StripGroupWidget ( )
		self._addToCenter ( self._stripsettings )
		
	def _setupMeasurement ( self ):
		args = super ( StripTab, self ) ._setupMeasurement ( ) ._asdict ( )
		args = dict ( args )
		
		freq, volt = self._freqsettings.getSettings ( )
		if not 20 <= freq <= 2e6 :
			raise MeasurementSetttingsError ( u"Frequency must be between 20 Hz and 2 MHz." )
		if not 0 <= volt <= 20 :
			raise MeasurementSetttingsError ( u"AC voltage must be between 0 V and 20 V." )
		
		if ( self._stripsettings.getSettings ( ) == u"Resistance/Impedance" ) :
			resistance = True
		else :
			resistance = False
		
		agie4980a_devname = None
		try:
			agie4980a_devname = detector.get_resname_for ( u"Agilent Technologies,E4980A" )
			if agie4980a_devname is None :
				raise MeasurementSetttingsError ( u"Could not find Agilent E4980A." )
		except VisaIOError:
			raise MeasurementSetttingsError ( u"Could not connect to GPIB/serial devices." )

		args["type"] = u"Strip"
		args["compcurrent"] *= 1000.0 # CV box adds 1KOhm -> compcurrent goes down...
		args["frequency"] = freq
		args["deltavolt"] = volt
		args["resistance"] = resistance
		args["devname_agiE4980A"] = agie4980a_devname
		
		return MeasurementArgs ( **args )

	def _onStartClicked ( self ) :
		super( StripTab, self ) ._onStartClicked ( u"Is the CV/IV box set to both IV and C<sub>int</sub>/R<sub>int</sub>?" )

class MainWindow ( QtW.QMainWindow ) :
	def __init__ ( self, output_dir ) :
		super ( MainWindow, self ) .__init__ ( )

		self.setWindowTitle ( u"Probe Station Software" )

		self._tabwidget = QtW.QTabWidget ( )
		self.setCentralWidget ( self._tabwidget )

		self._ivtab = IvTab ( self, output_dir )
		self._tabwidget.addTab ( self._ivtab, u"IV" )

		self._cvtab = CvTab ( self, output_dir )
		self._tabwidget.addTab ( self._cvtab, u"CV" )

		self._striptab = StripTab ( self, output_dir )
		self._tabwidget.addTab ( self._striptab, u"Strip" )

		self._mwin = None

	def measurementIsRunning ( self ) :
		return not self._mwin is None and self._mwin.isRunning ( )

	def startMeasurement ( self, args ) :
		if args.type == u"IV" :
			self._mwin = IvMeasurementWindow ( self, args )
		elif args.type == u"CV" :
			self._mwin = CvMeasurementWindow ( self, args )
		elif args.type == u"Strip" :
			self._mwin = StripMeasurementWindow ( self, args )
		else :
			raise NotImplementedError ( args.type )
		self._mwin.setWindowModality ( QtCore.Qt.WindowModal )
		self._mwin.set_absolute ( True )
		self._mwin.start ( )

	def showErrorDialog ( self, message ) :
		reply = QtW.QMessageBox.critical ( self, u"Error", message, QtW.QMessageBox.Ok, QtW.QMessageBox.Ok )

if __name__ == u"__main__" :
	import sys
	import optparse

	app = QtW.QApplication ( sys.argv )
	if len ( sys.argv ) > 1 and os.path.isdir ( sys.argv[1] ) :
		output_dir = sys.argv[1]
	else:
		output_dir = os.getcwd ( )

	usage = u"Usage: python %prog [options] <default storage path>"
	description = u"If no default storage path is specified, the current directory is used."
	parser = optparse.OptionParser ( usage = usage, description = description )
	parser.add_option ( u"-d", u"--debug", action = u"store_true", dest = u"debug", help = u"debug flag, enables more verbose console output" )
	options, args = parser.parse_args ( )
	logger = logging.getLogger ( u'probestation' )
	ch = logging.StreamHandler ( )
	logger.addHandler ( ch )
	logger.setLevel ( logging.INFO )
	ch.setLevel ( logging.INFO )
	if options.debug :
		logger.setLevel ( logging.DEBUG )
		ch.setLevel ( logging.DEBUG )
		logger.debug ( u"Running in DEBUG mode!" )
		logger.debug ( u" Output path is: %s", output_dir )

	win = MainWindow ( output_dir )
	win.show ( )
	sys.exit ( app.exec_ ( ) )
