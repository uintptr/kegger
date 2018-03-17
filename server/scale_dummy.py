#!/usr/bin/env python

import logging

class Scale():

    last_sample = 0
    CALIBRATION = -11600.00

    def __init__(self, dout, pd_sck, calibration=CALIBRATION ):
        logging.debug("Loading HX711")

        self.calibration = calibration
        logging.debug("Calibration: {}".format ( self.calibration ) )

    def cleanup(self):
        logging.debug("cleaning up")

    def last(self):
        return self.last_sample

    def reset(self):
        pass

    def sample(self):
        logging.debug("sampling")
        self.last_sample = 10

        return self.last_sample
