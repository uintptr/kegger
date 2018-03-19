#!/usr/bin/env python

import logging

import RPi.GPIO as GPIO
from hx711py.hx711 import HX711

class Scale():

    hx = None
    calibration = None

    def __init__(self, dout, pd_sck, calibration ):

        logging.debug ( "loading HX711" )
        self.hx = HX711( dout, pd_sck )

        logging.debug ("init HX711")

        self.hx = HX711(2,3)
        self.hx.reset()
        self.hx.tare()

        logging.debug("HX711 is ready!")

        self.calibration = calibration

        logging.debug("Calibration: {}".format ( self.calibration ) )


    def reset(self):
        self.hx.reset()
        self.hx.tare()

    def cleanup(self):
        logging.debug ( "Cleaning up" )
        GPIO.cleanup()

    def sample(self):

        self.hx.power_up()

        val = self.hx.get_weight ( 20 )
        logging.debug ( "val: {}".format ( val ) )

        val /= self.calibration

        logging.debug ( "calibrated: {}".format ( val ) )

        self.hx.power_down()

        return val
