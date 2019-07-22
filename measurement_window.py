#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from PyQt5 import QtWidgets as QtW
    from PyQt5 import QtCore
    from matplotlib.backends.backend_qt5agg import ( FigureCanvas, NavigationToolbar2QT as NavigationToolbar )
except ImportError as e :
    from PyQt4 import QtGui as QtW
    from PyQt4 import QtCore
    from matplotlib.backends.backend_qt4agg import ( FigureCanvas, NavigationToolbar2QT as NavigationToolbar )

from matplotlib.figure import Figure
import numpy as np
import logging
import arduinoenv

class MeasurementThread ( QtCore.QThread ) :
	error_signal = QtCore.pyqtSignal ( str )
	measurement_ready = QtCore.pyqtSignal ( tuple )
	envmeasurement_ready = QtCore.pyqtSignal ( tuple )
	finished = QtCore.pyqtSignal ( str )

	def __init__ ( self, args ) :
		super ( MeasurementThread, self ) .__init__ ( )
		self.args = args
		self._exiting = False
		self._logger = logging.getLogger("probestation.measurement_window.MeasurementThread")

	def __del__ ( self ) :
		self.quit_and_wait ( )

	def quit_and_wait ( self ) :
		self._exiting = True
		self.wait ( )
		if self._envsensor:
			self._envsensor.close ( )
		
	def _init_envsensor ( self ):
		self._envsensor = arduinoenv.ArduinoEnvSensor ( self.args.devname_ardenv )
		idn = self._envsensor.identify ( )
		if not idn.startswith ( u"Arduino Probestation Environment Sensoring" ) :
			return False
		self._logger.info ( u"Environment sensor device introduced itself as {}" .format ( self._envsensor.identify ( ) ) )
		
		return True
		
	def _measure_environment ( self ):
		# Query both sensors
		reading = self._envsensor.get_reading ( )
		read1 = ",".join(reading.split(",")[:4])
		read2 = ",".join(reading.split(",")[4:])
		
		reading = self._envsensor.parse_tphr(read1, "envsensor1")
		reading.update(self._envsensor.parse_tphr(read2, "envsensor2"))
		
		reading["envsensor1_dewpoint"] = None
		reading["envsensor2_dewpoint"] = None
		if None not in [reading["envsensor1_temperature"], reading["envsensor1_humidity"]] :
			reading["envsensor1_dewpoint"] = self._envsensor.get_dewpoint (
						reading["envsensor1_temperature"],
						reading["envsensor1_humidity"] )
		if None not in [reading["envsensor2_temperature"], reading["envsensor2_humidity"]] :
			reading["envsensor2_dewpoint"] = self._envsensor.get_dewpoint (
						reading["envsensor2_temperature"],
						reading["envsensor2_humidity"] )
		
		self.envmeasurement_ready.emit ( ( reading["envsensor1_temperature"],
										   reading["envsensor1_dewpoint"],
										   reading["envsensor2_temperature"],
										   reading["envsensor2_dewpoint"] ) )
		
		return reading

class MeasurementWindow ( QtW.QWidget ) :
	def __init__ ( self, parent, num_plots, args, thread ) :
		super ( MeasurementWindow, self ) .__init__ ( parent )
		self.setWindowFlags ( QtCore.Qt.Window )
		self.resize ( 500, 500 )
		self._center ( )

		self._num_plots = num_plots
		self._ax = []
		self._args = args
		self._x = []
		self._y = [[] for i in range ( num_plots )]
		self._xlabel = "Source voltage in V"
		self._ylabel = [""] * num_plots
		self._should_abs = False

		layout = QtW.QVBoxLayout ( self )

		self._figure = Figure ( figsize = ( 5, 3 ) )
		dynamic_canvas = FigureCanvas ( self._figure )
		policy = QtW.QSizePolicy ( QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Expanding )
		dynamic_canvas.setSizePolicy ( policy )
		layout.addWidget ( NavigationToolbar ( dynamic_canvas, self ) )
		layout.addWidget ( dynamic_canvas )
		
		self._env_label = QtW.QLabel ( )
		layout.addWidget ( self._env_label )
		if args.devname_ardenv is None:
			self._env_label.hide ( )

		hbox = QtW.QHBoxLayout ( )
		layout.addLayout ( hbox )

		self._abs_cb = QtW.QCheckBox ( "Plot absolute values" )
		self._abs_cb.setChecked ( self._should_abs )
		self._abs_cb.toggled.connect ( self._on_abs_toggled )
		hbox.addWidget ( self._abs_cb )

		hbox.addStretch ( 1 )

		self._stop_button = QtW.QPushButton ( "Stop" )
		self._stop_button.clicked.connect ( self._stop_clicked )
		hbox.addWidget ( self._stop_button )

		for i in range ( self._num_plots ) :
			if i == 0 :
				self._ax.append ( dynamic_canvas.figure.add_subplot ( 100 * self._num_plots + 10 + ( i + 1 ) ) )
			else :
				self._ax.append ( dynamic_canvas.figure.add_subplot ( 100 * self._num_plots + 10 + ( i + 1 ), sharex = self._ax[0] ) )

		self._thread = thread
		self._thread.error_signal.connect ( self.showErrorDialog )
		self._thread.measurement_ready.connect ( self.add_point )
		self._thread.finished.connect ( self._measurementFinished )
		self._thread.envmeasurement_ready.connect ( self._on_env_measured )

		self._figure.subplots_adjust ( left = 0.15, right = 0.99, top = 0.95, hspace = 0.4 )
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		self.update ( )

	def _center ( self ) :
		qr = self.frameGeometry ( )
		cp = QtW.QDesktopWidget ( ) .availableGeometry ( ) .center ( )
		qr.moveCenter ( cp )
		self.move ( qr.topLeft ( ) )

	def _stop_clicked ( self ) :
		self._thread.quit_and_wait ( )
		
	def _on_env_measured ( self, measurement ):
		self._env_label.setText ( "T1 = {:.1f} °C, Dewpoint1 = {:.1f} °C, T2 = {:.1f} °C, Dewpoint2 = {:.1f} °C".format(*measurement) )

	def add_point ( self, point ) :
		self._x.append ( point[0] )
		for i, ax in enumerate ( self._ax ) :
			self._y[i].append ( point[i + 1] )
		self.update ( )

	def set_absolute ( self, should_abs ) :
		self._should_abs = should_abs
		self._abs_cb.setChecked ( should_abs )
		self.update ( )

	def update ( self ) :
		for i, ax in enumerate ( self._ax ) :
			ax.clear ( )
			ax.set_xlabel ( self._xlabel + ( " (Abs)" if self._should_abs else "" ) )
			ax.set_ylabel ( self._ylabel[i] + ( " (Abs)" if self._should_abs else "" ) )
			ax.ticklabel_format ( style = "sci", axis = "y", scilimits = ( 0, 0 ), useMathText = True )
			ax.grid ( )
			if self._should_abs :
				ax.plot ( np.abs ( self._x ), np.abs ( self._y[i] ) )
			else :
				ax.plot ( self._x, self._y[i] )
			ax.autoscale_view ( )
		self._figure.canvas.draw ( )

	def savefig ( self, fname ) :
		self._figure.savefig ( fname )

	def isRunning ( self ) :
		return self._thread and self._thread.isRunning ( )

	def _measurementFinished ( self, name ) :
		try :
			#Other formats like .pdf are also supported
			self.savefig ( str ( name ) + ".svg" )
		except IOError as e :
			pass

	def _on_abs_toggled ( self ) :
		self._should_abs = self._abs_cb.isChecked ( )
		self.update ( )

	def start ( self ) :
		self.show ( )
		self._thread.start ( )

	def closeEvent ( self, event ) :
		if self._thread.isRunning ( ) :
			self._thread.quit_and_wait ( )
		self._thread = None # Delete thread to free devices
		event.accept ( )

	def showErrorDialog ( self, message ) :
		reply = QtW.QMessageBox.critical ( self, "Error", message, QtW.QMessageBox.Ok, QtW.QMessageBox.Ok )
