#!/usr/bin/env python3

import logging
import visa
from sys import platform

class GPIBDetector(object):
    def __init__(self):
        logger = logging.getLogger('myLogger')
        logger.debug(' In gpib_detect.py:')
        logger.debug('  Checking platform...')
        if platform == "linux" or platform == "linux2" or platform == "darwin":
            self._rm = visa.ResourceManager('@py')
            logger.debug('   Found Linux or MacOS')
        elif platform == "win32" or platform == "cygwin":
            self._rm = visa.ResourceManager()
            logger.debug('   Found Windows')
        resources = self._rm.list_resources()
        self.identifiers = {}
        logger.debug('  Found resources: %s', resources)
        for res in resources:
            logger.debug('   Checking %s', res)
            if not ( res.startswith("ASRL/dev/tty") or res.startswith("GPIB") ):
                continue

            if res.startswith("ASRL/dev/tty"):
                logger.debug('    Probing serial %s', res)
                dev = self._rm.open_resource(res, baud_rate=19200, data_bits=8)
            if res.startswith("GPIB"):
                logger.debug('    Probing GPIB %s', res)
                dev = self._rm.open_resource(res)
            try:
                logger.debug('    Sending query: *IDN?')
                idn = dev.query("*IDN?")
                self.identifiers[res] = idn
                dev.close()
            except:
                continue

    def get_resname_for(self, search):
        for key, value in self.identifiers.items():
            if search in value:
                return key
        return None

if __name__ == "__main__":
    import pprint

    detector = GPIBDetector()

    pprint.pprint(detector.identifiers)
