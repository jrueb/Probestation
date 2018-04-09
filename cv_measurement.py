#!/usr/bin/env python3

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

class CvMeasurementThread(MeasurementThread):
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

            agilentE4980A.set_frequency(args.frequency)
            agilentE4980A.set_voltage_level(args.deltavolt)

            with open(output_csv, "w", newline="") as f:
                header = ["kei6517b_srcvoltage", "agie4980a_capacity", "agie4980a_conductance"]
                writer = csv.DictWriter(f, header, extrasaction="ignore")
                writer.writeheader()

                for keivolt in keith6517B.voltage_series(args.start, args.end, args.step):
                    sleep(args.sleep)
                    if self._exiting:
                        break

                    line = agilentE4980A.get_reading()
                    meas = agilent.parse_cgv(line, "agie4980a")
                    meas["kei6517b_srcvoltage"] = keivolt
                    if (not "kei6517b_srcvoltage" in meas
                            or not "agie4980a_capacity" in meas
                            or not "agie4980a_conductance" in meas
                            or meas["kei6517b_srcvoltage"] is None
                            or meas["agie4980a_capacity"] is None
                            or meas["agie4980a_conductance"] is None):
                        raise IOError("Got invalid reading from device")

                    print("VSrc = {: 10.4g} V; C = {: 10.4g} F; G = {: 10.4g} S".format(
                        meas["kei6517b_srcvoltage"],
                        meas["agie4980a_capacity"],
                        meas["agie4980a_conductance"]))

                    writer.writerow(meas)
                    self.measurement_ready.emit((meas["kei6517b_srcvoltage"], 1 / meas["agie4980a_capacity"] ** 2))

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

class CvMeasurementWindow(MeasurementWindow):
    def __init__(self, parent, args):
        thread = CvMeasurementThread(args)
        super().__init__(parent, 1, args, thread)

        self._ylabel = ["Capacitance${}^{-2}$ in $\\mathrm{F}^{-2}$", "Conductance in $\\mathrm{S}$"]
        self.setWindowTitle("CV measurement")
