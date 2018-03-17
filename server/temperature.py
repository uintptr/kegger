#!/usr/bin/env python

import sys
import time
import logging

import RPi.GPIO as GPIO

import dht11.dht11 as dht11


class Temperature():

    _dht_instance = None
    _last_result  = None

    def __init__(self, dpin ):
        # read data using pin 14

        #GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        logging.debug ( "DHT pin: {}".format ( dpin ) )

        self._dht_instance = dht11.DHT11(pin = dpin )

    def sample(self):

        logging.debug ( "Sampling temperature" )

        result = self._dht_instance.read()

        #
        # Only set it if it was successful. The sensor is a bit finicky
        #
        if ( 0 != result.temperature and 0 != result.humidity ):
            self._last_result = result
            logging.debug ( "Temp: {}".format ( result.temperature))

    def get_temperature(self):
        if ( None == self._last_result ):
            return 0
        return self._last_result.temperature

    def get_humidity(self):
        if ( None == self._last_result ):
            return 0
        return self._last_result.humidity
