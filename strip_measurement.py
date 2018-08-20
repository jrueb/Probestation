#!/usr/bin/env python

from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import logging
from measurement_window import MeasurementThread, MeasurementWindow
import keithley
import agilent
import sys
from math import fabs

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

class StripMeasurementThread ( MeasurementThread ) :
	def __init__ ( self, args ) :
		super ( StripMeasurementThread, self ) .__init__ ( args )

	def run ( self ) :
		args = self.args

		fname = getDateTimeFilename ( )
		output_csv = os.path.join ( str ( args.output_dir ), fname + u".csv" )
		logger = logging.getLogger ( u'myLogger' )
		logger.debug ( u' In strip_measurement.py:' )

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
			if args.resistance :
				logger.info ( u"Resistance!" )

			agilentE4980A.set_frequency ( args.frequency )
			agilentE4980A.set_voltage_level ( args.deltavolt )

			mode = 'w'
			if sys.version_info.major < 3:
				mode += 'b'

			with open ( output_csv, mode ) as f :
				if not args.resistance :
					header = OrderedDict ( [ ( 'kei6517b_srcvoltage', None ), ( 'agie4980a_capacitance', None ) ] )
				else :
					header = OrderedDict ( [ ( 'kei6517b_srcvoltage', None ), ( 'agie4980a_resistance', None ) ] )
				writer = csv.DictWriter ( f, header, extrasaction = "ignore" )
				writer.writeheader ( )

				for keivolt in keith6517B.voltage_series ( args.start, args.end, args.step ) :
					sleep ( args.sleep )
					if self._exiting :
						break

					if not args.resistance :
						line = agilentE4980A.get_reading ( )
						print ( "got", line )
						meas = agilent.parse_cgv ( line, "agie4980a" )
						meas["kei6517b_srcvoltage"] = keivolt
						if ( not "kei6517b_srcvoltage" in meas or not "agie4980a_capacitance" in meas or not "agie4980a_conductance" in meas or meas["kei6517b_srcvoltage"] is None or meas["agie4980a_capacitance"] is None or meas["agie4980a_conductance"] is None ) :
							raise IOError ( "Got invalid reading from device" )

						print ( "VSrc = {: 10.4g} V; C = {: 10.4g} F; G = {: 10.4g} S" .format ( meas["kei6517b_srcvoltage"], meas["agie4980a_capacitance"], meas["agie4980a_conductance"] ) )

					else :
						line = agilentE4980A.get_resistance ( )
						print ( "got", line )
						meas = agilent.parse_res ( line, "agie4980a" )
						meas["kei6517b_srcvoltage"] = keivolt
						if ( not "kei6517b_srcvoltage" in meas or not "agie4980a_resistance1" in meas or not "agie4980a_resistance2" in meas or meas["kei6517b_srcvoltage"] is None or meas["agie4980a_resistance1"] is None or meas["agie4980a_resistance2"] is None ) :
							raise IOError ( "Got invalid reading from device" )

						print ( "VSrc = {: 10.4g} V; R = {: 10.4g} O" .format( meas["kei6517b_srcvoltage"], ( ( fabs(meas["agie4980a_resistance1"] ) + fabs ( meas["agie4980a_resistance2"] ) ) / 2.0 ) ) )

					writer.writerow ( meas )
					if not args.resistance :
						self.measurement_ready.emit ( ( meas["kei6517b_srcvoltage"], meas["agie4980a_capacitance"] ) )
					else :
						self.measurement_ready.emit ( ( meas["kei6517b_srcvoltage"], ( ( fabs ( meas["agie4980a_resistance1"] ) + fabs ( meas["agie4980a_resistance2"] ) ) / 2.0 ) ) )

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

class StripMeasurementWindow ( MeasurementWindow ) :
	def __init__ ( self, parent, args ) :
		thread = StripMeasurementThread ( args )
		super ( StripMeasurementWindow, self ) .__init__ ( parent, 1, args, thread )

		if not args.resistance :
			self._ylabel = [u"Capacitance in $\\mathrm{F}$", u"Conductance in $\\mathrm{S}$"]
		else:
			self._ylabel = [u"Resistance in $\\mathrm{Ohm}$"]
		self.setWindowTitle ( u"Strip measurement" )
