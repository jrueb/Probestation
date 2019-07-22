#!/usr/bin/env python

from __future__ import absolute_import
import visa
import pyvisa.errors
from serial.serialutil import SerialException
import logging
from multiprocessing.pool import ThreadPool

class GPIBDetector ( object ) :				
	def __init__ ( self, useserial ) :
		self.logger = logging.getLogger ( u'probestation.gpib_detect.GPIBDetector' )
		self.pool = ThreadPool ( processes=10 )
		self.useserial = useserial
		self.identifiers = { }

		try :
			rm = visa.ResourceManager ( )
		except pyvisa.errors.Error :
			self.logger.debug ( u"Failed to open ni-visa" )
		else :
			self.logger.debug ( u"Probing ni-visa devices..." )
			self._probe_rm ( rm, False )
		if useserial :
			try :
				rm = visa.ResourceManager ( "@py" )
			except pyvisa.errors.Error :
				self.logger.debug ( u"Failed to open pyvisa" )
			else :
				self.logger.debug ( u"Probing pyvisa devices..." )
				self._probe_rm ( rm, True )
		
	def _probe_rm(self, rm, isserial) :
		pool_results = []
		for res in rm.list_resources ( ) :
			if isserial and not res.startswith ( u"ASRL" ) :
				continue
			if not isserial and not res.startswith ( u"GPIB" ) :
				continue
				
			result = self.pool.apply_async ( self._obtain_idn, ( rm, res, isserial ) )
			pool_results.append ( result )
			
		for pool_result in pool_results :
			try :
				res, idn = pool_result.get ( )
			except ( pyvisa.errors.Error, SerialException ) :
				if isserial :
					self.logger.debug ( u"Could not open serial connection to %s", res )
				else :
					self.logger.debug ( u"Could not open GPIB connection to %s", res )
			else:
				if idn:
					self.identifiers[res] = idn
		
	def _obtain_idn ( self, rm, res, isserial ) :
		if isserial :
			self.logger.debug ( u"Opening serial connection to %s", res )
			# 5000 msecs needed to catch slow devices...
			dev = rm.open_resource ( res, baud_rate = 19200, data_bits = 8, timeout = 5000 )
		else :
			self.logger.debug ( u"Opening GPIB connection to %s", res )
			dev = rm.open_resource ( res )
		idn = dev.query ( u"*IDN?" )
		if idn :
			self.logger.debug ( u"Got device identification: %s", idn )
		else :
			self.logger.debug ( u"Got no device identification" )
		dev.close ( )
		return res, idn
		

	def get_resname_for ( self, search ) :
		for key, value in self.identifiers.items ( ) :
			if search in value :
				return key
		return None

if __name__ == u"__main__" :
	import pprint
	import sys

	logging.basicConfig ( stream=sys.stdout, level=logging.DEBUG )
	detector = GPIBDetector ( True )

	pprint.pprint ( detector.identifiers )
