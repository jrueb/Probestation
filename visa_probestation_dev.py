#!/usr/bin/env python3

import visa
import logging

class VisaProbestationDev ( object ) :
	def __init__ ( self, resource_name, useserial, baud_rate = 19200, data_bits = 8 ) :
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
			self._res = rm2.open_resource ( resource_name, baud_rate = baud_rate, data_bits = data_bits, timeout = 5000 )
		else :
			logger.debug ( u"  Opening {} with ni-visa." .format ( resource_name ) )
			self._res = rm1.open_resource ( resource_name )
		self._connected = True

	def _write ( self, cmd ) :
		self._res.write ( cmd )

	def _query ( self, cmd ) :
		return self._res.query ( cmd )
        
	def _query_ascii_values ( self, cmd ) :
		return self._res.query_ascii_values ( cmd )
        
	def _read ( self ) :
		return self._res.read ( )
