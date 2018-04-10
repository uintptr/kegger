#!/usr/bin/env python

import time
import sys
import os
import logging
import argparse
import flask
import serial

from threading import Lock

from flask import Flask, redirect, render_template, request
from flask import jsonify
from flask import send_from_directory

import userconfig

LOG_FILE            = "server.log"
VERSION             = "0.1"
CONFIG_FILE_NAME    = "config.json"

#
# Default values unless specified in the cmd line
#
DEF_SAMPLE_GRAN             = 300
DEF_LISTENING_PORT          = 5000
DEF_SAMPLING_TIMEOUT_SEC    = 30

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
        while ( timeout > time.time() ):

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

def sample(timeout=DEF_SAMPLING_TIMEOUT_SEC):

    temp     = 0
    humidity = 0
    weight   = 0

    #
    # Serialize the use of the serial port
    #
    g_mutex.acquire()

    try:
        (temp,humidity,weight) = sample_locked(timeout)
    finally:
        g_mutex.release()

    return (temp,humidity,weight)

def update_config(config):

    (temp,humidity,weight) = sample()

    if ( 0 != temp and 0 != humidity and 0 != weight ):
        config.set_weight(weight)
        config.set_temperature(temp)
        config.set_humidity(humidity)

def get_level ( config ):

    full  = config.get_full_weight()
    empty = config.get_keg_weight()
    cur   = config.get_weight()

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

@app.route('/favicon.ico')
def favicon():

    file_path = os.path.join(app.root_path, "templates")

    return send_from_directory( file_path,
                               'favicon.ico',
                                mimetype='image/vnd.microsoft.icon')

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
                            config=config.dup(),
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
                                empty_weight = config.get_keg_weight(),
                                calibration  = config.get_calibration(),
                                beer_type    = config.get_beer_type(),
                                beer_name    = config.get_beer_name() )
    return render_template(path)

@app.route("/api/reset")
def http_reset():
    config = flask.g["user_config"]

    config.set_base_weight(0)
    config.set_weight(0)
    config.set_full_weight(0)

    #
    # Leave the scale time to adjust
    #
    time.sleep(5)

    (temp,humidity,weight) = sample()

    if ( 0 != temp and 0 != humidity and 0 != weight ):
        config.set_temperature(temp)
        config.set_humidity(humidity)
        config.set_base_weight(weight)

    return redirect("/newkeg_2.html", code=302 )

@app.route("/api/newkeg")
def http_new_keg():

    config = flask.g["user_config"]

    #
    # Leave the scale time to adjust
    #
    time.sleep(5)

    (temp,humidity,weight) = sample()

    if ( 0 != temp and 0 != humidity and 0 != weight ):
        config.set_temperature(temp)
        config.set_humidity(humidity)
        config.set_full_weight(weight)
        config.set_weight(weight)

    return render_template( "newkeg_3.html",
                            beer_type=config.get_beer_type(),
                            beer_name=config.get_beer_name() )

@app.route("/formhandler", methods=['POST'])
def http_form_config():

    config = flask.g["user_config"]

    if ( "empty_weight" in request.form ):
        config.set_keg_weight ( float ( request.form["empty_weight"]) )

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

    update_config(config)

    level = get_level( config )

    level_conf = {}
    level_conf["beer_type" ]  = config.get_beer_type()
    level_conf["beer_name" ]  = config.get_beer_name()
    level_conf["beer_level"]  = level
    level_conf["temperature"] = config.get_temperature()
    level_conf["humidity"]    = config.get_humidity()

    return jsonify(level_conf )

@app.route("/api/config")
def http_api_config():
    return jsonify(flask.g["user_config"].dup())

@app.route("/api/weight")
def http_api_weight():

    config = flask.g["user_config"]
    update_config( config )

    weight = {}
    weight["weight"] = config.get_weight()

    return jsonify(weight)

def main():

    global g_mutex

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

    try:
        app.run(host  = "0.0.0.0",
                port  = args.port,
                debug = args.debug )
    except KeyboardInterrupt:
        print "\rKeyboard interrupted. Quitting"


    logging.debug ( "Joining sampling thread" )
    logging.debug ( "Sampling thread returned" )

if __name__ == '__main__':
    sys.exit(main())
