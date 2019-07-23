#!/usr/bin/env python3

from __future__ import absolute_import

try:
    from PyQt5 import QtCore
except ImportError as e :
    from PyQt4 import QtCore

def run_async ( func, callback = None, error_callback = None, *args, **kwargs ):
	# QRunnable does not inherit QObject, but signals need QObject,
	# thus we need an extra class.
	class WorkerSignals ( QtCore.QObject ) :
		finished = QtCore.pyqtSignal ( object )
		error = QtCore.pyqtSignal ( Exception )
	
	class Worker ( QtCore.QRunnable ) :
		def __init__ ( self, func, *args, **kwargs ) :
			super ( Worker, self ) .__init__ ( )
			self.func = func
			self.args = args
			self.kwargs = kwargs
			self.signals = WorkerSignals ( )
			
		@QtCore.pyqtSlot()
		def run ( self ) :
			try :
				result = self.func ( *self.args, **self.kwargs )
			except Exception as e :
				self.signals.error.emit ( e )
			else:
				self.signals.finished.emit ( result )

	worker = Worker ( func, *args, **kwargs )
	if callback :
		worker.signals.finished.connect ( callback )
	if error_callback :
		worker.signals.error.connect ( error_callback )
	QtCore.QThreadPool.globalInstance ( ) .start ( worker )
