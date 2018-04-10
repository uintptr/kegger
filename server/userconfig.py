#!/usr/bin/env python

import os
import json

class Config():


    CALIBRATION = -11600.00

    _config = None
    _config_file_Path = None

    def __init__(self, config_file_path ):

        if ( True == os.path.isfile ( config_file_path  ) ):
            with open ( config_file_path, "r" ) as f:
                self._config = json.load ( f )

        else:
            self._config = {}
            #
            # https://en.wikipedia.org/wiki/Keg#Sixth_barrel
            #
            self._config["keg_weight"]      = 14
            self._config["full_weight" ]    = 0
            self._config["weight" ]         = 0
            self._config["beer_name"   ]    = "Guinness"
            self._config["beer_type"   ]    = "Stout"
            self._config["calibration" ]    = self.CALIBRATION

        self._config_file_Path = config_file_path

    def _sync (self):
        with open ( self._config_file_Path, "w+" ) as f:
            json.dump ( self._config, f, indent=4 )

    """
    ""
    "" Beer Info
    ""
    """
    def set_beer_type(self, beer_type ):
        self._config["beer_type"] = beer_type
        self._sync()

    def get_beer_type(self):
        if ( "beer_type" not in self._config ):
            self.set_beer_type("")
        return self._config["beer_type"]

    def set_beer_name(self, beer_name ):
        self._config["beer_name"] = beer_name
        self._sync()

    def get_beer_name(self):
        if ( "beer_name" not in self._config ):
            self.set_beer_name("")
        return self._config["beer_name"]

    """
    ""
    "" WEIGHT
    ""
    """
    def set_keg_weight(self, weight):
        #
        # Already set in pounds, no need to calibrate
        #
        self._config["keg_weight"] = weight
        self._sync()

    def get_keg_weight(self):
        if ( "keg_weight" not in self._config ):
            self.set_keg_weight(0)
        return self._config["keg_weight"]

    def set_full_weight(self, weight):

        weight -= self.get_base_weight()
        weight /= self.get_calibration()

        self._config["full_weight" ] = weight
        self._sync()

    def get_full_weight(self):
        if ( "full_weight" not in self._config ):
            return 0
        return self._config["full_weight" ]

    def set_calibration(self,calibration):
        self._config["calibration"] = calibration
        self._sync()

    def get_calibration(self):
        if ( "calibration" not in self._config ):
            self.set_calibration(0)
        return self._config["calibration"]

    def set_base_weight (self, weight):
        self._config["base_weight"] = weight
        self._sync()

    def get_base_weight (self):
        if ( "base_weight" not in self._config ):
            self.set_base_weight(0)
        return self._config["base_weight"]

    def set_weight(self, weight):

        weight -= self.get_base_weight()
        weight /= self.get_calibration()

        self._config["weight"] = weight
        self._sync()

    def get_weight(self):
        if ( "weight" not in self._config ):
            self.set_weight(0)
        return self._config["weight"]


    """
    ""
    "" TEMPERATURE
    ""
    """
    def get_temperature(self):

        if ( "temperature" not in self._config ):
            self.set_temperature(0)
        return self._config["temperature"]

    def set_temperature(self,temperature):
        self._config["temperature"] = temperature
        self._sync()

    """
    ""
    "" HUMIDITY
    ""
    """
    def get_humidity(self):
        if ( "humidity" not in self._config ):
            self.set_humidity(0)
        return self._config["humidity"]

    def set_humidity(self,humidity):
        self._config["humidity"] = humidity
        self._sync()

    def dup (self):
        #
        # Return a copy
        #
        return dict ( self._config )

