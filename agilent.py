#!/usr/bin/env python

from __future__ import absolute_import
import logging
import visa

class AgilentMeter ( object ) :
	def __init__ ( self, resource_name, useserial ) :
		logger = logging.getLogger ( u'myLogger' )
		try :
			rm1 = visa.ResourceManager ( )
			resources = rm1.list_resources ( )
		except :
			logger.debug ( u"  Failed to open ni-visa" )
		try :
			if useserial :
				rm2 = visa.ResourceManager ( u'@py' )
				resources += rm2.list_resources ( )
		except :
			logger.debug ( u"  Failed to open py-visa" )
		if not resource_name in resources :
			self._connected = False
			raise ValueError ( u"Resource not found {}" .format ( resource_name ) )
		if resource_name.startswith ( u"ASRL" ) and useserial :
			logger.debug ( u"  Opening {} with py-visa." .format ( resource_name ) )
			self._res = rm2.open_resource ( resource_name, baud_rate = 19200, data_bits = 8, timeout = 5000 )
		else :
			logger.debug ( u"  Opening {} with ni-visa." .format ( resource_name ) )
			self._res = rm1.open_resource ( resource_name )
		self._connected = True

		self._write ( u"*RST; *CLS" )
		self._write ( u":FORMAT:ASCII:LONG ON" )

	def identify ( self ) :
		return self._query ( u"*IDN?" ) .strip ( )

	def _write ( self, cmd ) :
		self._res.write ( cmd )

	def _query ( self, cmd ) :
		return self._res.query ( cmd )

class AgilentE4980A ( AgilentMeter ) :
	def __init__ ( self, resource_name, useserial ) :
		super (AgilentE4980A, self ) .__init__ ( resource_name, useserial )

		# might need something else for resistance
		self._write ( u":FUNCTION:IMPEDANCE CPG" )
		self._write ( u":APER MED,5" )

	def get_VDC ( self ) :
		return self._query ( u":FETCH:SMONITOR:VDC?" )

	def get_voltage_level ( self ) :
		return self._query ( u":VOLTAGE?" )

	def set_voltage_level ( self, volts ) :
		if not 0 <= volts <= 20 :
			raise ValueError ( u"Voltage level out of range [0;20]: {}" .format ( volts ) )

		self._write ( u":VOLTAGE {}" .format ( volts ) )

	def get_frequency ( self ) :
		return self._query ( u":FREQUENCY?" )

	def set_frequency ( self, freq ) :
		if not 20 <= freq <= 2e6 :
			raise ValueError ( u"Frequency out of range [0;2e6]: {}" .format ( freq ) )

		self._write ( u":FREQUENCY {}" .format ( freq ) )

	def get_reading ( self ) :
		return self._query ( u"FETCH?" ) .strip ( )

	def get_resistance ( self ) :
		self._write ( u":FUNCTION:IMPEDANCE RX" )
		resi = self._query ( u":FETCH:IMPEDANCE:CORRECTED?" )
		return resi

def parse_cgv ( line, devname ) :
	line = line.split ( u"," )
	ret = {}
	ret[u"{}_capacitance" .format ( devname ) ] = float ( line[0] )
	ret[u"{}_conductance" .format ( devname ) ] = float ( line[1] )
	return ret

def parse_res ( line, devname ) :
	line = line.split ( u"," )
	ret = {}
	ret[u"{}_resistance" .format ( devname ) ] = float ( line[0] )
	ret[u"{}_impedance" .format ( devname ) ] = float ( line[1] )
	return ret

if __name__ == u"__main__" :
	a = AgilentE4980A ( u"GPIB0::20::INSTR", False )
