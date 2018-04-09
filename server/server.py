#!/usr/bin/env python

import time
import sys
import os
import logging
import argparse
import platform
import flask
import json

from threading import Lock

from flask import Flask, Response, redirect, render_template, request
from flask import Markup
from flask import flash
from flask import jsonify

import userconfig

LOG_FILE            = "server.log"
VERSION             = "0.1"
CONFIG_FILE_NAME    = "config.json"

#
# Default values unless specified in the cmd line
#
DEF_SAMPLE_GRAN     = 300
DEF_LISTENING_PORT  = 5000

app = Flask(__name__)

def printkv(k,v):
    key = "{}:".format ( k )
    print "{0:<22} {1}".format ( key, v )

def sample_locked(timeout):

    sp       = None
    timeout += time.time()
    temp     = 0
    humidity = 0
    weight   = 0

    try:
        sp = serial.Serial ( "/dev/ttyUSB0", 9600 )

        #
        # The loop breaks after a timeout or a
        #
        while ( timeout > time.time() )

            line = sp.readline()

            if ( None != line ):

                line = line.strip("\r\n")

                print line

                #
                # When the line starts with D, we treat it as a debug line
                #
                if ( False == line.startswith("D") ):
                    (temp,humidity,weight) = line.split(",")
                    temp        = float(temp)
                    humidity    = float(humidity)
                    weight      = float(weight)
                    break
    except KeyboardInterrupt:
        temp = humidity = weight = 0
    except serial.SerialException:
        temp = humidity = weight = 0
    finally:
        if ( None != sp ):
            sp.close()

    return (temp,humidity,weight)

def sample(timeout=SAMPLING_TIMEOUT)

    temp     = 0
    humidity = 0
    weight   = 0

    #
    # Serialize the use of the serial port
    #
    g_mutex.acquire()

    try:
        (temp,humidity,weight) = sample_locked()
    finally:
        g_mutex.release()

    return (temp,humidity,weight)

def sample_weight()

    temp        = 0
    humidity    = 0
    weight      = 0

    (temp,humidity,weight) = sample()

    return weight

def update_weight(config):

    weight = scale_weight_locked()
    config.set_current_weight(weight)
    return config.get_current_weight()

def get_level ( config ):

    full  = config.get_full_weight()
    empty = config.get_empty_weight()
    cur   = config.get_current_weight()

    logging.debug("full:  {}".format ( full  ) )
    logging.debug("empty: {}".format ( empty ) )
    logging.debug("curr:  {}".format ( cur   ) )

    if ( cur > full ):
        full = cur

    full -= empty
    cur  -= empty

    # Otherwise we'd divide by 0
    if ( 0 == full ):
        logging.debug("divide by 0 exception" )
        return 0

    logging.debug("{}/{}={}".format ( cur, full, cur / full ) )

    level = 100 * ( cur / full )

    logging.debug("level @ {}".format ( level ) )

    #
    # the load cells are not super reliable
    #
    if ( level > 100 ):
        level = 100

    return abs ( int ( level ) )

#
# For the index.html
#
@app.route("/")
def html_root():

    config = flask.g["user_config"]

    level = get_level ( config )

    if ( level >= 60 ):
        bar_type = 'success'
    elif ( level >= 20 ):
        bar_type = 'warning'
    else:
        bar_type = 'danger'

    return render_template( "index.html",
                            config=config.get(),
                            bar_level=level,
                            bar_type=bar_type)

#
# All other html files
#
@app.route("/<path:path>")
def static_handler(path):

    config = flask.g["user_config"]

    if ( path == "config.html" ):
        return render_template( "config.html",
                                base_weight  = config.get_base_weight(),
                                empty_weight = config.get_empty_weight(),
                                full_weight  = config.get_full_weight(),
                                calibration  = config.get_calibration(),
                                beer_type    = config.get_beer_type(),
                                beer_name    = config.get_beer_name() )
    return render_template(path)

@app.route("/api/reset")
def http_reset():
    config = flask.g["user_config"]

    config.set_base_weight(0)
    config.set_current_weight(0)
    config.set_full_weight(0)

    scale_reset_locked()

    return redirect("/newkeg_2.html", code=302 )

@app.route("/api/newkeg")
def http_new_keg():

    conf = flask.g["user_config"]

    full_weight = scale_weight_locked()

    if ( full_weight > 0 ):
        conf.set_full_weight    ( full_weight )
        conf.set_current_weight ( full_weight )

    return render_template( "newkeg_3.html",
                            beer_type=conf.get_beer_type(),
                            beer_name=conf.get_beer_name() )

@app.route("/formhandler", methods=['POST'])
def http_form_config():

    config = flask.g["user_config"]

    if ( "base_weight" in request.form ):
        config.set_base_weight  ( float ( request.form["base_weight"] ) )

    if ( "empty_weight" in request.form ):
        config.set_empty_weight ( float ( request.form["empty_weight"]) )

    if ( "full_weight" in request.form ):
        config.set_full_weight( float ( request.form["full_weight"] ) )

    if ( "calibration" in request.form ):
        config.set_calibration ( float ( request.form ["calibration"] ) )

    if ( "beer_type" in request.form ):
        config.set_beer_type( request.form["beer_type"] )

    if ( "beer_name" in request.form ):
        config.set_beer_name( request.form["beer_name"] )

    return redirect("/", code=302)

@app.route("/api/level")
def http_api_level():
    config = flask.g["user_config"]

    global g_temp

    update_weight(config)

    temperature_sample_locked()

    level = get_level( config )
    temp  = g_temp.get_temperature()
    humidity = g_temp.get_humidity()

    level_conf = {}
    level_conf["beer_type" ]  = config.get_beer_type()
    level_conf["beer_name" ]  = config.get_beer_name()
    level_conf["beer_level"]  = level
    level_conf["temperature"] = temp
    level_conf["humidity"]    = humidity

    return jsonify(level_conf )

@app.route("/api/config")
def http_api_config():
    return jsonify(flask.g["user_config"].get())

@app.route("/api/weight")
def http_api_weight():

    conf  = flask.g["user_config"]
    weight = {}
    weight["weight"] = update_weight( conf )

    return jsonify(weight)

def main():

    global g_mutex
    global g_scale
    global g_temp

    parser = argparse.ArgumentParser()

    parser.add_argument("-d",
                        "--debug",
                        action="store_true",
                        help="Debug mode" )

    parser.add_argument("--verbose",
                        "-v",
                        action="store_true",
                        help="Verbose")

    parser.add_argument("--port",
                        "-p",
                        type=int,
                        default=DEF_LISTENING_PORT,
    help="Listening port. Default={}".format(DEF_LISTENING_PORT) )

    parser.add_argument("-c",
                        "--config-file",
                        type=str,
                        help="/path/to/config.json" )

    args = parser.parse_args()

    flask.g = {}

    if ( True == args.verbose ):
        logging.basicConfig(level=logging.DEBUG )
        log_file = "stdout"
    else:
        log_file = os.path.expanduser ( "~/{}".format ( LOG_FILE ) )
        logging.basicConfig(level=logging.DEBUG, filename=log_file)

    if ( None == args.config_file ):
        config_file_path = os.path.dirname ( sys.argv[0] )
        config_file_path = os.path.join ( config_file_path, CONFIG_FILE_NAME )
        config_file_path = os.path.abspath ( config_file_path )

    print "Scale Server v{0}:".format ( VERSION )

    printkv ( "Config File", config_file_path )
    printkv ( "Debug", args.debug )
    printkv ( "Verbose", args.verbose )
    printkv ( "Listening Port", args.port )
    printkv ( "Log File", log_file )

    config = userconfig.Config( config_file_path )

    flask.g["user_config"] = config

    g_mutex = Lock()
    g_scale = scale.Scale(2,3, config.get_calibration() )
    g_temp  = temperature.Temperature ( 17 )

    try:
        app.run(host  = "0.0.0.0",
                port  = args.port,
                debug = args.debug )
    except KeyboardInterrupt:
        print "\rKeyboard interrupted. Quitting"

    g_scale.cleanup()

    logging.debug ( "Joining sampling thread" )
    logging.debug ( "Sampling thread returned" )

if __name__ == '__main__':
    sys.exit(main())
