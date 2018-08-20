#!/usr/bin/env python

from __future__ import with_statement
from __future__ import division
from __future__ import absolute_import
import logging
from measurement_window import MeasurementThread, MeasurementWindow
import keithley
import sys

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

class IvMeasurementThread ( MeasurementThread ) :
	def __init__ ( self, args ) :
		super ( IvMeasurementThread, self ) .__init__ ( args )

	def run ( self ) :
		args = self.args

		fname = getDateTimeFilename ( )
		output_csv = os.path.join ( str ( args.output_dir ), fname + u".csv" )
		logger = logging.getLogger ( u'myLogger' )
		logger.debug ( u' In iv_measurement.py:' )

		try :
			keith6517B = keithley.Keithley6517B ( args.devname_kei6517b )
			logger.info ( u"  Voltage source device introduced itself as {}" .format ( keith6517B.identify ( ) ) )
			if not args.devname_kei6485 is None and args.guardring :
				keith6485 = keithley.Keithley6485 ( args.devname_kei6485 )
				logger.info ( u"  Guard ring device introduced itself as {}" .format ( keith6485.identify ( ) ) )
			else :
				keith6485 = None
				logger.info ( u"  Running without guard ring measurement" )
		except VisaIOError :
			errormsg = u"Could not open devices."
			self.error_signal.emit ( errormsg )
			logger.error ( errormsg )
			self.finished.emit ( os.path.join ( str ( args.output_dir ), fname ) )
			return

		try :
			logger.info ( u"Starting measurement" )
			mode = 'w'
			if sys.version_info.major < 3:
				mode += 'b'

			with open ( output_csv, mode ) as f :
				if not keith6485 is None :
					header = OrderedDict ( [ ( 'kei6517b_srcvoltage', None ), ( 'kei6517b_current', None ), ( 'kei6485_current', None ) ] )
				else :
					header = OrderedDict ( [ ( 'kei6517b_current', None ), ( 'kei6517b_srcvoltage', None ) ] )
				writer = csv.DictWriter ( f, fieldnames = header, extrasaction = u"ignore" )
				writer.writeheader ( )

				for voltage in keith6517B.voltage_series ( args.start, args.end, args.step ) :
					sleep ( args.sleep )
					if self._exiting :
						break

					line = keith6517B.get_reading ( )
					meas = keithley.parse_iv ( line, u"kei6517b" )
					if ( not u"kei6517b_srcvoltage" in meas or not u"kei6517b_current" in meas or meas[u"kei6517b_srcvoltage"] is None or meas[u"kei6517b_current"] is None ) :
						raise IOError ( u"Got invalid response from Keithley 6517B" )
					if self._exiting :
						break

					if not keith6485 is None :
						gr_line = keith6485.get_reading ( )
						meas.update ( keithley.parse_iv ( gr_line, u"kei6485" ) )
						if ( not u"kei6485_current" in meas or meas[u"kei6485_current"] is None ) :
							raise IOError ( u"Got invalid response from Keithley 6485" )
						print ( u"VSrc = {: 10.4g} V; I = {: 10.4g} A; IGr = {: 10.4g} A" .format ( meas[u"kei6517b_srcvoltage"], meas[u"kei6517b_current"], meas[u"kei6485_current"] ) )
					else :
						meas[u"kei6485_current"] = 0
						print ( u"VSrc = {: 10.4g} V; I = {: 10.4g} A" .format ( meas[u"kei6517b_srcvoltage"], meas[u"kei6517b_current"] ) )

					if ( abs ( meas[u"kei6517b_current"] ) >= args.compcurrent or abs ( meas[u"kei6485_current"] ) >= args.compcurrent ) :
						self.error_signal.emit ( u"Compliance current reached" )
						print ( u"Compliance current reached" )
						#Instant turn off
						keith6517B.set_output_state ( False )
						self._exiting = True

					writer.writerow ( meas )
					if args.guardring :
						self.measurement_ready.emit ( ( meas[u"kei6517b_srcvoltage"], meas[u"kei6517b_current"], meas[u"kei6485_current"] ) )
					else :
						self.measurement_ready.emit ( ( meas[u"kei6517b_srcvoltage"], meas[u"kei6517b_current"] ) )
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
				logger.error ( u"Error during stopping. Trying turn off output" )
				keith6517B.set_output_state ( False )

		self.finished.emit ( os.path.join (  str ( args.output_dir ), fname ) )

class IvMeasurementWindow ( MeasurementWindow ) :
	def __init__ ( self, parent, args ) :
		thread = IvMeasurementThread ( args )
		super ( IvMeasurementWindow, self ) .__init__ ( parent, 2 if args.guardring else 1, args, thread )

		self._ylabel = [u"Pad current in A", u"GR current in A"]
		self.setWindowTitle ( u"IV measurement" )
		logger = logging.getLogger ( u'myLogger' )
