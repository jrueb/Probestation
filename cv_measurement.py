#!/usr/bin/env python

from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import logging
from measurement_window import MeasurementThread, MeasurementWindow
import keithley
import agilent
import sys

try:
    from PyQt5 import QtWidgets as QtW
    from PyQt5 import QtCore
except ImportError as e :
    from PyQt4 import QtGui as QtW
    from PyQt4 import QtCore

import os
import csv
import datetime
from time import sleep
from pyvisa.errors import VisaIOError, InvalidBinaryFormat
from io import open
from collections import OrderedDict

def getDateTimeFilename ( ) :
	s = datetime.datetime.now ( ) .isoformat ( )
	s = s.replace ( u":", u"_" )
	s = s.replace ( u".", u"_" )
	return s

class CvMeasurementThread ( MeasurementThread ) :
	def __init__ ( self, args ) :
		super ( CvMeasurementThread, self ) .__init__ ( args )

	def run ( self ) :
		args = self.args

		fname = getDateTimeFilename ( )
		output_csv = os.path.join ( str ( args.output_dir ), fname + u".csv" )
		logger = logging.getLogger ( u'myLogger' )
		logger.debug ( u' In cv_measurement.py:' )

		try :
			keith6517B = keithley.Keithley6517B ( args.devname_kei6517b )
			logger.info ( u"Voltage source device introduced itself as {}" .format ( keith6517B.identify ( ) ) )
			agilentE4980A = agilent.AgilentE4980A ( args.devname_agiE4980A )
			logger.info ( u"LCR meter introduced itself as {}" .format ( agilentE4980A.identify ( ) ) )
		except VisaIOError :
			errormsg = u"Could not open devices."
			self.error_signal.emit ( errormsg )
			logger.error ( errormsg )
			self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )
			return

		try :
			logger.info ( u"Starting measurement" )

			agilentE4980A.set_frequency ( args.frequency )
			agilentE4980A.set_voltage_level ( args.deltavolt )

			mode = 'w'
			if sys.version_info.major < 3:
				mode += 'b'

			with open ( output_csv, mode ) as f :
				header = OrderedDict ( [ ( 'kei6517b_srcvoltage', None ), ( 'agie4980a_capacitance', None ), ('agie4980a_conductance', None ) ] )
				writer = csv.DictWriter ( f, fieldnames = header, extrasaction = u"ignore" )
				writer.writeheader ( )

				for keivolt in keith6517B.voltage_series ( args.start, args.end, args.step ) :
					sleep ( args.sleep )
					if self._exiting :
						break

					line = agilentE4980A.get_reading ( )
					meas = agilent.parse_cgv ( line, u"agie4980a" )
					meas[u"kei6517b_srcvoltage"] = keivolt
					if ( not u"kei6517b_srcvoltage" in meas or not u"agie4980a_capacitance" in meas or not u"agie4980a_conductance" in meas or meas[u"kei6517b_srcvoltage"] is None or meas[u"agie4980a_capacitance"] is None or meas[u"agie4980a_conductance"] is None ) :
						raise IOError ( u"Got invalid reading from device" )

					print ( u"VSrc = {: 10.4g} V; C = {: 10.4g} F; G = {: 10.4g} S" .format ( meas[u"kei6517b_srcvoltage"], meas[u"agie4980a_capacitance"], meas[u"agie4980a_conductance"] ) )

					writer.writerow ( meas )
					self.measurement_ready.emit ( ( meas[u"kei6517b_srcvoltage"], 1 / meas[u"agie4980a_capacitance"] ** 2 ) )

					if self._exiting :
						break

		except IOError as e :
			errormsg = u"Error: {}" .format ( e )
			self.error_signal.emit ( errormsg )
			logger.error ( errormsg )
		except ( VisaIOError, InvalidBinaryFormat, ValueError ) :
			errormsg = u"Error during communication with devices."
			self.error_signal.emit ( errormsg )
			logger.error ( errormsg )
		finally :
			logger.info ( u"Stopping measurement" )
			try :
				keith6517B.stop_measurement ( )
			except ( VisaIOError, InvalidBinaryFormat, ValueError ) :
				logger.error ( u"Error during stopping. Trying to turn off output" )
				keith6517B.set_output_state ( False )

		self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )

class CvMeasurementWindow ( MeasurementWindow ) :
	def __init__ ( self, parent, args ) :
		thread = CvMeasurementThread ( args )
		super ( CvMeasurementWindow, self ) .__init__ ( parent, 1, args, thread )

		self._ylabel = [u"Capacitance${}^{-2}$ in $\\mathrm{F}^{-2}$", u"Conductance in $\\mathrm{S}$"]
		self.setWindowTitle ( u"CV measurement" )
