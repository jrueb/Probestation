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

class StripMeasurementThread ( MeasurementThread ) :
	def __init__ ( self, args ) :
		super ( StripMeasurementThread, self ) .__init__ ( args )

	def run ( self ) :
		args = self.args

		fname = getDateTimeFilename ( )
		output_csv = os.path.join ( str ( args.output_dir ), fname + u".csv" )
		logger = logging.getLogger ( u'probestation.strip_measurement.StripMeasurementThread' )
		logger.debug ( u" In strip_measurement.py:" )

		try :
			if args.devname_ardenv:
				if not self._init_envsensor ( ):
					errormsg = u"Could not open envirovment sensor device."
					self.error_signal.emit ( errormsg )
					logger.error ( errormsg )
					self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )
				logger.info ( u"  Envirovment sensor device introduced itself as {}" .format ( self._envsensor.identify ( ) ) )
			
			input_hv = keithley.KeithleyMeter ( args.devname_hv, args.serialenable )
			if input_hv.identify ( ) .startswith ( u"KEITHLEY INSTRUMENTS INC.,MODEL 6517B" ) :
				keith_hv = keithley.Keithley6517B ( args.devname_hv, args.serialenable )
			elif input_hv.identify ( ) .startswith ( u"KEITHLEY INSTRUMENTS INC.,MODEL 2410" ) :
				keith_hv = keithley.Keithley2410 ( args.devname_hv, args.serialenable )
			else :
				errormsg = u"Could not open devices."
				self.error_signal.emit ( errormsg )
				logger.error ( errormsg )
				self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )
				return
			logger.info ( u"  Voltage source device introduced itself as {}" .format ( keith_hv.identify ( ) ) )
			agilentE4980A = agilent.AgilentE4980A ( args.devname_agiE4980A, args.serialenable )
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

			keith_hv.set_compliance ( args.compcurrent )

			with open ( output_csv, mode ) as f :
				if not args.resistance :
					header = OrderedDict ( [ ( 'keihv_srcvoltage', None ), ( 'agie4980a_capacitance', None ), ( 'keihv_current', None ) ] )
				else :
					header = OrderedDict ( [ ( 'keihv_srcvoltage', None ), ( 'agie4980a_resistance', None ), ( 'agie4980a_impedance', None ), ( 'keihv_current', None ) ] )
				writer = csv.DictWriter ( f, header, extrasaction = "ignore" )
				writer.writeheader ( )

				for keivolt in keith_hv.voltage_series ( args.start, args.end, args.step ) :
					sleep ( args.sleep )
					if self._exiting :
						break

					if args.devname_ardenv:
						env = self._measure_enviroment ( )
					if not args.resistance :
						line = agilentE4980A.get_reading ( )
						meas = agilent.parse_cgv ( line, "agie4980a" )
						meas["keihv_srcvoltage"] = keivolt
						if ( not "keihv_srcvoltage" in meas or not "agie4980a_capacitance" in meas or not "agie4980a_conductance" in meas or meas["keihv_srcvoltage"] is None or meas["agie4980a_capacitance"] is None or meas["agie4980a_conductance"] is None ) :
							raise IOError ( "Got invalid reading from device" )
						compline = keith_hv.get_reading ( )
						meas.update ( keith_hv.parse_iv ( compline, u"keihv" ) )

						print ( "VSrc = {: 10.4g} V; C = {: 10.4g} F; G = {: 10.4g} S" .format ( meas["keihv_srcvoltage"], meas["agie4980a_capacitance"], meas["agie4980a_conductance"] ) )

					else :
						line = agilentE4980A.get_resistance ( )
						meas = agilent.parse_res ( line, "agie4980a" )
						meas["keihv_srcvoltage"] = keivolt
						if ( not "keihv_srcvoltage" in meas or not "agie4980a_resistance" in meas or not "agie4980a_impedance" in meas or meas["keihv_srcvoltage"] is None or meas["agie4980a_resistance"] is None or meas["agie4980a_impedance"] is None ) :
							raise IOError ( "Got invalid reading from device" )
						compline = keith_hv.get_reading ( )
						meas.update ( keith_hv.parse_iv ( compline, u"keihv" ) )

						print ( "VSrc = {: 10.4g} V; R = {: 10.4g} O" .format( meas["keihv_srcvoltage"], meas["agie4980a_resistance"], meas["agie4980a_impedance"] ) )

					if ( abs ( meas[u"keihv_current"] ) >= args.compcurrent ) :
						self.error_signal.emit ( u"Compliance current reached" )
						print ( u"Compliance current reached" )
						#Instant turn off
						keith_hv.set_output_state ( False )
						self._exiting = True

					writer.writerow ( meas )
					if not args.resistance :
						self.measurement_ready.emit ( ( meas["keihv_srcvoltage"], meas["agie4980a_capacitance"] ) )
					else :
						self.measurement_ready.emit ( ( meas["keihv_srcvoltage"], meas["agie4980a_resistance"], meas["agie4980a_impedance"] ) )

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
				keith_hv.stop_measurement ( )
			except ( VisaIOError, InvalidBinaryFormat, ValueError ) :
				logger.error ( u"Error during stopping. Trying to turn off output" )
				keith_hv.set_output_state ( False )

		self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )

class StripMeasurementWindow ( MeasurementWindow ) :
	def __init__ ( self, parent, args ) :
		thread = StripMeasurementThread ( args )
		super ( StripMeasurementWindow, self ) .__init__ ( parent, 2 if args.resistance else 1, args, thread )

		if not args.resistance :
			self._ylabel = [u"Capacitance in $\\mathrm{F}$", u"Conductance in $\\mathrm{S}$"]
		else:
			self._ylabel = [u"Resistance in $\\mathrm{Ohm}$", u"Impedance in $\\mathrm{Ohm}$"]
		self.setWindowTitle ( u"Strip measurement" )
