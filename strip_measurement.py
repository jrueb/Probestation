#!/usr/bin/env python3

import logging
from measurement_window import MeasurementThread, MeasurementWindow
import keithley
import agilent

from PyQt5 import QtCore
import os
import csv
import datetime
from time import sleep
from pyvisa.errors import VisaIOError, InvalidBinaryFormat

def getDateTimeFilename():
    s = datetime.datetime.now().isoformat()
    s = s.replace(":", "_")
    s = s.replace(".", "_")
    return s

class StripMeasurementThread(MeasurementThread):
    def __init__(self, args):
        super().__init__(args)

    def run(self):
        args = self.args

        fname = getDateTimeFilename()
        output_csv = os.path.join(args.output_dir, fname + ".csv")

        try:
            keith6517B = keithley.Keithley6517B(args.devname_kei6517b)
            print("Voltage source device introduced itself as {}".format(keith6517B.identify()))
            agilentE4980A = agilent.AgilentE4980A(args.devname_agiE4980A)
            print("LCR meter introduced itself as {}".format(agilentE4980A.identify()))
        except VisaIOError:
            errormsg = "Could not open devices."
            self.error_signal.emit(errormsg)
            print(errormsg)
            self.finished.emit(os.path.join(args.output_dir, fname))
            return

        try:
            print("Starting measurement")
            if args.resistance:
                print ("Resistance!")

            agilentE4980A.set_frequency(args.frequency)
            agilentE4980A.set_voltage_level(args.deltavolt)

            with open(output_csv, "w", newline="") as f:
                header = ["kei6517b_srcvoltage", "agie4980a_capacitance", "agie4980a_conductance"]
                writer = csv.DictWriter(f, header, extrasaction="ignore")
                writer.writeheader()

                for keivolt in keith6517B.voltage_series(args.start, args.end, args.step):
                    sleep(args.sleep)
                    if self._exiting:
                        break

                    line = agilentE4980A.get_reading()
                    if not args.resistance:
                        meas = agilent.parse_cgv(line, "agie4980a")
                        meas["kei6517b_srcvoltage"] = keivolt
                        if (not "kei6517b_srcvoltage" in meas
                                or not "agie4980a_capacitance" in meas
                                or not "agie4980a_conductance" in meas
                                or meas["kei6517b_srcvoltage"] is None
                                or meas["agie4980a_capacitance"] is None
                                or meas["agie4980a_conductance"] is None):
                            raise IOError("Got invalid reading from device")

                        print("VSrc = {: 10.4g} V; C = {: 10.4g} F; G = {: 10.4g} S".format(
                            meas["kei6517b_srcvoltage"],
                            meas["agie4980a_capacitance"],
                            meas["agie4980a_conductance"]))

                    else:
                        meas = agilent.get_resistance()
                        meas["kei6517b_srcvoltage"] = keivolt
                        if (not "kei6517b_srcvoltage" in meas
                                or not "agie4980a_resistance" in meas
                                or meas["kei6517b_srcvoltage"] is None
                                or meas["agie4980a_resistance"] is None):
                            raise IOError("Got invalid reading from device")

                        print("VSrc = {: 10.4g} V; R = {: 10.4g} O".format(
                            meas["kei6517b_srcvoltage"],
                            meas["agie4980a_resistance"]))

                    writer.writerow(meas)
                    if not args.resistance:
                        self.measurement_ready.emit(meas["kei6517b_srcvoltage"], meas["agie4980a_capacitance"])
                    else:
                        self.measurement_ready.emit(meas["kei6517b_srcvoltage"], meas["agie4980a_resistance"])

                    if self._exiting:
                        break

        except (PermissionError, IOError) as e:
            errormsg = "Error: {}".format(e)
            self.error_signal.emit(errormsg)
            print(errormsg)
        except (VisaIOError, InvalidBinaryFormat, ValueError):
            errormsg = "Error during communication with devices."
            self.error_signal.emit(errormsg)
            print(errormsg)
        finally:
            print("Stopping measurement")
            try:
                keith6517B.stop_measurement()
            except (VisaIOError, InvalidBinaryFormat, ValueError):
                print("Error during stopping. Trying turn off output")
                keith6517B.set_output_state(False)

        self.finished.emit(os.path.join(args.output_dir, fname))

class StripMeasurementWindow(MeasurementWindow):
    def __init__(self, parent, args):
        thread = StripMeasurementThread(args)
        super().__init__(parent, 1, args, thread)

        if not args.resistance:
            self._ylabel = ["Capacitance in $\\mathrm{F}$", "Conductance in $\\mathrm{S}$"]
        else:
            self._ylabel = ["Resistance in $\\mathrm{Ohm}$"]
        self.setWindowTitle("Strip measurement")
