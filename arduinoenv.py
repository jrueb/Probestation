#!/usr/bin/env python
# -*- coding: utf-8 -*-

from visa_probestation_dev import VisaProbestationDev
from math import log

class ArduinoEnvSensor ( VisaProbestationDev ) :
	def __init__ ( self, resource_name ) :
		super ( ArduinoEnvSensor, self ) .__init__ ( resource_name, True )
		
		self._res.encoding = "utf-8"
		
	def identify ( self ) :
		return self._query ( u"*IDN?" ) .strip ( )
		
	def get_reading ( self, sensor = None ) :
		if sensor is None:
			return self._query ( "measureall" ) .strip ( )
		elif sensor == 0x76:
			return self._query ( "measure76" ) .strip ( )
		elif sensor == 0x77:
			return self._query ( "measure77" ) .strip ( )
		else:
			raise ValueError ( "sensor must be either None, 0x76 or 0x77." )
			
	@staticmethod
	def parse_tphr ( line, devname ) :
		for field in line.split ( "," ) :
			field = field.strip ( )
			temperature = pressure = humidity = resistance = None
			
			if field[-2:] == "°C":
				temperature = float ( field[:-2] )
			elif field[-2:] == "Pa":
				pressure = float ( field[:-2] )
			elif field[-1:] == "%":
				humidity = float ( field[:-1] )
			elif field[-2:] == "kΩ":
				resistance = float ( field[:-2] )
				
		return { "{}_temperature".format ( devname ) : temperature,
				 "{}_pressure" .format ( devname ) : pressure,
				 "{}_humidity" .format ( devname ) : humidity,
				 "{}_resistance" .format ( devname ) : resistance }

	@staticmethod
	def get_dewpoint (t, rh):
		"""
		t Temperature in degrees Celcius
		rh Relative humidity in percent
		"""
		a = 6.1121    
		b = 17.62
		c = 243.12
		
		logphi = log(rh) - log(100)
		return c * ((b * t) / (c + t) + logphi) / ((b * c) / (c + t) - logphi)
