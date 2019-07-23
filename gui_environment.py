#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging

try:
	from PyQt5 import QtWidgets as QtW
	from PyQt5 import QtCore
except ImportError as e :
	from PyQt4 import QtGui as QtW
	from PyQt4 import QtCore

import gpib_detect
import arduinoenv
from probestation_utils import run_async
from pyvisa.errors import VisaIOError
import sys
import argparse
import threading

class SensorLabels ( object ) :
	def __init__ ( self ) :
		self.temp = QtW.QLabel ( )
		self.dewpoint = QtW.QLabel ( )
		self.humidity = QtW.QLabel ( )
		self.pressure = QtW.QLabel ( )
		
	def set ( self, temp = "", dewpoint = "", humidity = "", pressure = "" ) :
		self.temp.setText ( "{} °C".format ( temp ) )
		self.dewpoint.setText ( "{:.2f} °C".format ( dewpoint ) )
		self.humidity.setText ( "{} %".format ( humidity ) )
		self.pressure.setText ( "{:.0f} Pa".format ( pressure ) )

class MainWindow ( QtW.QMainWindow ) :
	def __init__ ( self, leftis76 ) :
		super ( MainWindow, self ) .__init__ ( )
		
		self._leftis76 = leftis76
		
		self.setWindowTitle ( "Probe Station Environment" )
		
		self._statuslabel = QtW.QLabel ( "Connecting..." )
		self._statuslabel.setAlignment ( QtCore.Qt.AlignCenter )
		self.setCentralWidget ( self._statuslabel )
		
		self._mainwidget = QtW.QWidget ( )
		grid = QtW.QGridLayout ( )
		self._mainwidget.setLayout ( grid )
		
		grid.addWidget ( QtW.QLabel ( "Left sensor" ) , 0, 1 )
		grid.addWidget ( QtW.QLabel ( "Right sensor" ) , 0, 2 )
		grid.addWidget ( QtW.QLabel ( "Temperature:" ) , 1, 0 )
		grid.addWidget ( QtW.QLabel ( "Dew point:" ) , 2, 0 )
		grid.addWidget ( QtW.QLabel ( "Humidity:" ) , 3, 0 )
		grid.addWidget ( QtW.QLabel ( "Pressure:" ) , 4, 0 )
		
		self._left = SensorLabels ( )
		grid.addWidget ( self._left.temp, 1, 1 )
		grid.addWidget ( self._left.dewpoint, 2, 1 )
		grid.addWidget ( self._left.humidity, 3, 1 )
		grid.addWidget ( self._left.pressure, 4, 1 )
		
		self._right = SensorLabels ( )
		grid.addWidget ( self._right.temp, 1, 2 )
		grid.addWidget ( self._right.dewpoint, 2, 2 )
		grid.addWidget ( self._right.humidity, 3, 2 )
		grid.addWidget ( self._right.pressure, 4, 2 )
		
		self._not_communicating = threading.Event ( )
		self._not_communicating.set ( )
		self._updating = threading.Event ( )
		
		run_async ( self._init, callback = self._init_finish, error_callback = self._init_error )
		
	def closeEvent ( self, event ) :
		self._not_communicating.wait ( )
		event.accept ( )
		
	def _init ( self ) :
		self._not_communicating.clear ( )
		try :
			self._detector = gpib_detect.GPIBDetector ( True )
			self._devname = self._detector.get_resname_for ( "Arduino Probestation Environment Sensoring" )
			if self._devname is None :
				raise RuntimeError ( )
			self._dev = arduinoenv.ArduinoEnvSensor ( self._devname )
			error = self._dev.get_error ( )
			if error is not None :
				raise RuntimeError ( error )
		finally :
			self._not_communicating.set ( )
			
	def _init_finish ( self ) :
		self._timer = QtCore.QTimer ( self )
		self._timer.timeout.connect ( self._update )
		self._timer.start ( 1000 )
		self.setCentralWidget ( self._mainwidget )
		
	def _init_error ( self, e ) :
		if isinstance ( e, ( VisaIOError, RuntimeError ) ) :
			message = "Could not connect to environment arduino.<br> It might be in use by another process or needs to be restarted."
			QtW.QMessageBox.critical ( self, u"Error", message, QtW.QMessageBox.Ok, QtW.QMessageBox.Ok )
			self.close ( )
		else :
			raise e
		
	def _update ( self ) :
		if self._updating.is_set ( ) :
			return
		self._updating.set ( )
		
		run_async ( self._get_reading, callback = self._got_reading )
		
	def _get_reading ( self ) :
		self._not_communicating.clear ( )
		try :
			read = self._dev.get_reading ( )
		finally :
			self._not_communicating.set ( )
		return read
		
	def _got_reading ( self, read ) :
		read1 = ",".join ( read.split ( "," ) [:4] )
		read2 = ",".join ( read.split ( "," ) [4:] )
		r = self._dev.parse_tphr ( read1, "s1" if self._leftis76 else "s2" )
		r.update ( self._dev.parse_tphr ( read2, "s2" if self._leftis76 else "s1" ) )
		
		if None not in [r["s1_temperature"], r["s1_humidity"]] :
			r["s1_dewpoint"] = self._dev.get_dewpoint (
						r["s1_temperature"],
						r["s1_humidity"] )
		if None not in [r["s2_temperature"], r["s2_humidity"]] :
			r["s2_dewpoint"] = self._dev.get_dewpoint (
						r["s2_temperature"],
						r["s2_humidity"] )
		
		self._left.set ( r["s1_temperature"],
							  r["s1_dewpoint"],
							  r["s1_humidity"],
							  r["s1_pressure"] )
		self._right.set ( r["s2_temperature"],
							  r["s2_dewpoint"],
							  r["s2_humidity"],
							  r["s2_pressure"] )
							  
		self._updating.clear ( )
		

if __name__ == "__main__" :
	parser = argparse.ArgumentParser ( )
	parser.add_argument ( "--leftis76", action = "store_true", help = "If present, the sensor with address 0x76 will be shown as \"left sensor\"." )
	args = parser.parse_args ( )
	
	app = QtW.QApplication ( sys.argv )
	win = MainWindow ( args.leftis76 )
	win.show ( )
	sys.exit ( app.exec_ ( ) )
