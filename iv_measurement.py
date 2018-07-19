#!/usr/bin/env python3

import logging
from measurement_window import MeasurementThread, MeasurementWindow
import keithley

from PyQt5 import QtCore
import os
import csv
import datetime
from pyvisa.errors import VisaIOError, InvalidBinaryFormat
from time import sleep

def getDateTimeFilename ( ) :
	s = datetime.datetime.now ( ) .isoformat ( )
	s = s.replace ( ":", "_" )
	s = s.replace ( ".", "_" )
	return s

class IvMeasurementThread ( MeasurementThread ) :
	def __init__ ( self, args ) :
		super ( ) .__init__ ( args )

	def run ( self ) :
		args = self.args

		fname = getDateTimeFilename ( )
		output_csv = os.path.join ( args.output_dir, fname + ".csv" )
		logger = logging.getLogger ( 'myLogger' )
		logger.debug ( ' In iv_measurement.py:' )

		try :
			keith6517B = keithley.Keithley6517B ( args.devname_kei6517b )
			logger.info ( "  Voltage source device introduced itself as {}" .format ( keith6517B.identify ( ) ) )
			if not args.devname_kei6485 is None and args.guardring :
				keith6485 = keithley.Keithley6485 ( args.devname_kei6485 )
				logger.info ( "  Guard ring device introduced itself as {}" .format ( keith6485.identify ( ) ) )
			else :
				keith6485 = None
				logger.info ( "  Running without guard ring measurement" )
		except VisaIOError :
			errormsg = "Could not open devices."
			self.error_signal.emit ( errormsg )
			logger.error ( errormsg )
			self.finished.emit ( os.path.join ( args.output_dir, fname ) )
			return

		try :
			logger.info ( "Starting measurement" )

			with open ( output_csv, "w", newline = "" ) as f :
				if not keith6485 is None :
					header = ["kei6517b_srcvoltage", "kei6517b_current", "kei6485_current"]
				else :
					header = ["kei6517b_current", "kei6517b_srcvoltage"]
				writer = csv.DictWriter ( f, header, extrasaction = "ignore" )
				writer.writeheader ( )

				for voltage in keith6517B.voltage_series ( args.start, args.end, args.step ) :
					sleep ( args.sleep )
					if self._exiting :
						break

					line = keith6517B.get_reading ( )
					meas = keithley.parse_iv ( line, "kei6517b" )
					if ( not "kei6517b_srcvoltage" in meas or not "kei6517b_current" in meas or meas["kei6517b_srcvoltage"] is None or meas["kei6517b_current"] is None ) :
						raise IOError ( "Got invalid response from Keithley 6517B" )
					if self._exiting :
						break

					if not keith6485 is None :
						gr_line = keith6485.get_reading ( )
						meas.update ( keithley.parse_iv ( gr_line, "kei6485" ) )
						if ( not "kei6485_current" in meas or meas["kei6485_current"] is None ) :
							raise IOError ( "Got invalid response from Keithley 6485" )
						print ( "VSrc = {: 10.4g} V; I = {: 10.4g} A; IGr = {: 10.4g} A" .format ( meas["kei6517b_srcvoltage"], meas["kei6517b_current"], meas["kei6485_current"] ) )
					else :
						meas["kei6485_current"] = 0
						print ( "VSrc = {: 10.4g} V; I = {: 10.4g} A" .format ( meas["kei6517b_srcvoltage"], meas["kei6517b_current"] ) )

					if ( abs ( meas["kei6517b_current"] ) >= args.compcurrent or abs ( meas["kei6485_current"] ) >= args.compcurrent ) :
						self.error_signal.emit ( "Compliance current reached" )
						print ( "Compliance current reached" )
						#Instant turn off
						keith6517B.set_output_state ( False )
						self._exiting = True

					writer.writerow ( meas )
					if args.guardring :
						self.measurement_ready.emit ( ( meas["kei6517b_srcvoltage"], meas["kei6517b_current"], meas["kei6485_current"] ) )
					else :
						self.measurement_ready.emit ( ( meas["kei6517b_srcvoltage"], meas["kei6517b_current"] ) )
					if self._exiting :
						break

		except ( PermissionError, IOError ) as e :
			errormsg = "Error: {}" .format ( e )
			self.error_signal.emit ( errormsg )
			print ( errormsg )
		except ( VisaIOError, InvalidBinaryFormat, ValueError ) :
			errormsg = "Error during communication with devices."
			self.error_signal.emit ( errormsg )
			print ( errormsg )
		finally :
			print ( "Stopping measurement" )
			try :
				keith6517B.stop_measurement ( )
			except ( VisaIOError, InvalidBinaryFormat, ValueError ) :
				print ( "Error during stopping. Trying turn off output" )
				keith6517B.set_output_state ( False )

		self.finished.emit ( os.path.join ( args.output_dir, fname ) )

class IvMeasurementWindow ( MeasurementWindow ) :
	def __init__ ( self, parent, args ) :
		thread = IvMeasurementThread ( args )
		super ( ) .__init__ ( parent, 2 if args.guardring else 1, args, thread )

		self._ylabel = ["Pad current in A", "GR current in A"]
		self.setWindowTitle ( "IV measurement" )
		logger = logging.getLogger ( 'myLogger' )
