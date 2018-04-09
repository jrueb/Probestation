#!/usr/bin/env python3

import visa

class GPIBDetector(object):
    def __init__(self):
        self._rm = visa.ResourceManager()
        resources = self._rm.list_resources()
        self.identifiers = {}
        for res in resources:
            if not res.startswith("GPIB"):
                continue

            dev = self._rm.open_resource(res)
            idn = dev.query("*IDN?")
            self.identifiers[res] = idn
            dev.close()

    def get_resname_for(self, search):
        for key, value in self.identifiers.items():
            if search in value:
                return key
        return None

if __name__ == "__main__":
    import pprint

    detector = GPIBDetector()

    pprint.pprint(detector.identifiers)
