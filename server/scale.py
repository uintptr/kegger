#!/usr/bin/env python

import logging

import RPi.GPIO as GPIO
from hx711py.hx711 import HX711

class Scale():

    CALIBRATION = -11600.00

    hx = None
    calibration = None
    last_sample = 0

    def __init__(self, dout, pd_sck, calibration=None ):

        logging.debug ( "loading HX711" )
        self.hx = HX711( dout, pd_sck )

        logging.debug ("init HX711")

        self.hx = HX711(2,3)
        self.hx.reset()
        self.hx.tare()

        logging.debug("HX711 is ready!")

        if ( None != calibration ):
            self.calibration = calibration
        else:
            self.calibration = self.CALIBRATION

    def cleanup(self):
        logging.debug ( "Cleaning up" )
        GPIO.cleanup()

    def last(self):
        return self.last_sample

    def reset(self):
        self.hx.reset()
        self.hx.tare()

    def sample(self):

        self.hx.power_up()

        val = self.hx.get_weight ( 20 )
        logging.debug ( "val: {}".format ( val ) )

        val /= self.calibration

        logging.debug ( "calibrated: {}".format ( val ) )


        self.hx.power_down()

        self.last_sample = val

        return val
