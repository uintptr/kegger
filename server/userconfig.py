#!/usr/bin/env python

import sys
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
            self._config["empty_weight"] = 14
            self._config["base_weight" ] = 0
            self._config["full_weight" ] = 0
            self._config["current_weight" ] = 0
            self._config["beer_name"   ] = "Guinness"
            self._config["beer_type"   ] = "Stout"
            self._config["calibration" ] = self.CALIBRATION

        self._config_file_Path = config_file_path

        if ( "current_weight" in self._config ):
            self._config["base_weight" ]    = self._config["current_weight" ]
            self._config["current_weight" ] = 0

    def _sync (self):
        with open ( self._config_file_Path, "w+" ) as f:
            json.dump ( self._config, f, indent=4 )

    def set_empty_weight(self, weight ):
        self._config["empty_weight"] = weight
        self._sync()


    def set_base_weight ( self, weight ):
        self._config["base_weight"] = weight
        self._sync()

    def set_current_weight(self, weight):

        if ( "base_weight" in self._config ):
            weight += self._config["base_weight"]

        self._config["current_weight"] = weight
        self._sync()

    def get_base_weight(self):
        return self._config["base_weight" ]

    def get_current_weight(self):
        return self._config["current_weight" ]

    def get_empty_weight(self):
        return self._config["empty_weight"]

    def get_beer_type(self):
        if ( "beer_type" not in self._config ):
            return ""
        return self._config["beer_type"]

    def set_beer_type(self, beer_type ):
        self._config["beer_type"] = beer_type
        self._sync()

    def get_beer_name(self):
        if ( "beer_name" not in self._config ):
            return ""
        return self._config["beer_name"]

    def set_beer_name(self, beer_name ):
        self._config["beer_name"] = beer_name
        self._sync()

    def get_full_weight(self):
        if ( "full_weight" not in self._config ):
            return 0
        return self._config["full_weight" ]

    def set_full_weight(self, weight):
        self._config["full_weight" ] = weight
        self._sync()

    def get_calibration(self):

        if ( "calibration" not in self._config ):
            self._config["calibration"] = self.CALIBRATION

        return self._config["calibration"]

    def set_calibration(self,calibration):
        self._config["calibration"] = calibration
        self._sync()

    def get (self):
        #
        # Return a copy
        #
        return dict ( self._config )

