#!/usr/bin/env python3

import visa
from sys import platform

class GPIBDetector(object):
    def __init__(self):
        if platform == "linux" or platform == "linux2" or platform == "darwin":
            self._rm = visa.ResourceManager('@py')
        elif platform == "win32" or platform == "cygwin":
            self._rm = visa.ResourceManager()
        resources = self._rm.list_resources()
        self.identifiers = {}
        #print ("Found:", resources)
        for res in resources:
            if not ( res.startswith("ASRL/dev/tty") or res.startswith("GPIB") ):
                continue

            if res.startswith("ASRL/dev/tty"):
                dev = self._rm.open_resource(res, baud_rate=19200, data_bits=8)
                #print ("Probing",res)
            if res.startswith("GPIB"):
                dev = self._rm.open_resource(res)
            try:
                idn = dev.query("*IDN?")
                self.identifiers[res] = idn
                #print(idn)
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
