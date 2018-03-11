#!/usr/bin/env python

import logging

class Scale():

    last_sample = 0

    def __init__(self, dout, pd_sck, calibration=None ):
        logging.debug("Loading HX711")
        pass

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
