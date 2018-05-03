#!/usr/bin/env python3

import logging
import visa

class AgilentMeter(object):
    def __init__(self, resource_name):
        logger = logging.getLogger('myLogger')
        rm1 = visa.ResourceManager('@py')
        resources = rm1.list_resources()
        try:
            rm2 = visa.ResourceManager()
            resources += self._rm2.list_resources()
        except:
            logger.debug('  Failed to open ni-visa')
        if not resource_name in resources:
            self._connected = False
            raise ValueError("Resource not found {}".format(resource_name))
        if resource_name.startswith("ASRL"):
            self._res = rm1.open_resource(resource_name, baud_rate=19200, data_bits=8)
        else:
            self._res = rm2.open_resource(resource_name)
        self._connected = True

        self._write("*RST; *CLS")
        self._write(":FORMAT:ASCII:LONG ON")

    def identify(self):
        return self._query("*IDN?").strip()

    def _write(self, cmd):
        self._res.write(cmd)

    def _query(self, cmd):
        return self._res.query(cmd)

class AgilentE4980A(AgilentMeter):
    def __init__(self, resource_name):
        super().__init__(resource_name)

        self._write(":FUNCTION:IMPEDANCE CPG")
        self._write(":APER MED,5")

    def get_VDC(self):
        return self._query(":FETCH:SMONITOR:VDC?")

    def get_voltage_level(self):
        return self._query(":VOLTAGE?")

    def set_voltage_level(self, volts):
        if not 0 <= volts <= 20:
            raise ValueError("Voltage level out of range [0;20]: {}".format(volts))

        self._write(":VOLTAGE {}".format(volts))

    def get_frequency(self):
        return self._query(":FREQUENCY?")

    def set_frequency(self, freq):
        if not 20 <= freq <= 2e6:
            raise ValueError("Frequency out of range [0;2e6]: {}".format(freq))

        self._write(":FREQUENCY {}".format(freq))

    def get_reading(self):
        return self._query("FETCH?").strip()

def parse_cgv(line, devname):
    line = line.split(",")
    ret = {}

    ret["{}_capacity".format(devname)] = float(line[0])
    ret["{}_conductance".format(devname)] = float(line[1])

    return ret

if __name__ == "__main__":
    a = AgilentE4980A("GPIB0::20::INSTR")
