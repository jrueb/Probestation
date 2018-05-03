#!/usr/bin/env python3

import logging
import visa

class GPIBDetector(object):
    def __init__(self):
        logger = logging.getLogger('myLogger')
        logger.debug(' In gpib_detect.py:')
        self._rm1 = visa.ResourceManager('@py')
        resources = self._rm1.list_resources()
        try:
            self._rm2 = visa.ResourceManager()
            resources += self._rm2.list_resources()
        except:
            logger.debug('  Failed to open ni-visa')

        self.identifiers = {}
        logger.debug('  Found resources: %s', resources)
        for res in resources:
            logger.debug('   Checking %s', res)
            if not ( res.startswith("ASRL") or res.startswith("GPIB") ):
                continue

            if res.startswith("ASRL"):
                logger.debug('    Probing serial %s', res)
                dev = self._rm1.open_resource(res, baud_rate=19200, data_bits=8)
            if res.startswith("GPIB"):
                logger.debug('    Probing GPIB %s', res)
                dev = self._rm2.open_resource(res)
            try:
                logger.debug('    Sending query: *IDN?')
                idn = dev.query("*IDN?")
                logger.debug('    Recieved answer: %s', idn)
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
