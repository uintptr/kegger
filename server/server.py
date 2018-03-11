#!/usr/bin/env python

import time
import sys
import os
import threading
import logging
import argparse
import platform
import flask
import json

from flask import Flask, Response, redirect, render_template, request

#
# Assumption:
#
# If we're running on arm, it's probably a raspberry-pi
#
if ( 'arm' in platform.machine() ):
    import scale
else:
    import scale_dummy as scale

import userconfig

LOG_FILE    = "scale.log"
VERSION     = "0.1"

#
# Default values unless specified in the cmd line
#
DEF_SAMPLE_GRAN     = 300
DEF_LISTENING_PORT  = 5000

app = Flask(__name__)

def printkv(k,v):
    key = "{}:".format ( k )
    print "{0:<22} {1}".format ( key, v )

@app.route("/")
def http_index():
    return render_template("index.html")

@app.route("/reset")
def http_reset():
    uconf = flask.g["user_config"]
    s     = flask.g["scale"]

    s.reset()
    uconf.set_base_weight(0)
    uconf.set_current_weight(0)
    uconf.set_full_weight(0)
    return redirect("/", code=302)

@app.route("/newkeg")
def http_new_keg():

    scale = flask.g["scale"]
    uconf = flask.g["user_config"]

    full_weight = scale.sample()

    if ( full_weight > 0 ):
        uconf.set_full_weight ( full_weight )

    return redirect("/", code=302)

@app.route("/updateconfig", methods=['POST'])
def http_update_config():

    uconf = flask.g["user_config"]

    uconf.set_base_weight  ( float ( request.form["base_weight"] ) )
    uconf.set_empty_weight ( float ( request.form["empty_weight"]) )
    uconf.set_full_weight  ( float ( request.form["full_weight"] ) )
    uconf.set_beer_type    ( request.form["beer_type"] )
    uconf.set_beer_name    ( request.form["beer_name"] )

    return redirect("/", code=302)

@app.route("/update")
def http_update():

    root = os.path.dirname( sys.argv[0] )
    root = os.path.join ( root, "templates" )

    uconf = flask.g["user_config"]

    base        = uconf.get_base_weight()
    empty       = uconf.get_empty_weight()
    full        = uconf.get_full_weight()
    beer_type   = uconf.get_beer_type()
    beer_name   = uconf.get_beer_name()

    html_file = os.path.join ( root, "update.html" )
    html_data = None

    with open ( html_file ) as f:
        html_data = f.read()

        html_data = html_data.replace ( "__BASE_WEIGHT__", str(base) )
        html_data = html_data.replace ( "__EMPTY_WEIGHT__", str ( empty) )
        html_data = html_data.replace ( "__FULL_WEIGHT__", str ( full ) )

        html_data = html_data.replace ( "__BEER_TYPE__", beer_type )
        html_data = html_data.replace ( "__BEER_NAME__", beer_name )

    return Response ( html_data )

@app.route("/config")
def http_config():

    uconf = flask.g["user_config"]
    json_str = json.dumps ( uconf.get(), indent=4 )
    return Response(json_str, content_type="application/json; charset=utf-8" )

@app.route("/weight")
def http_weight():

    uconf  = flask.g["user_config"]

    weight = {}

    json_str = json.dumps ( weight, indent=4 )

    return Response(json_str, content_type="application/json; charset=utf-8" )

def sampler_thread_cb(quit_event, sample_granularity):

    next_sample = 0

    s = scale.Scale(2,3)

    flask.g["scale"] = s

    config = flask.g["user_config"]

    while ( False == quit_event.wait(1) ):

        if ( 0 == next_sample ):
            sample = s.sample()

            logging.debug("New Weight @ {}".format ( sample ) )

            config.set_current_weight( sample )

            next_sample = sample_granularity

        else:
            next_sample -= 1
            logging.debug("Sampling in {}".format ( next_sample ) )

        time.sleep ( 1 )

    s.cleanup()

    logging.debug ( "Sampling thread is returning..." )

def main():

    global g_done

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

    parser.add_argument("--sample-granularity",
                        type=int,
                        default=DEF_SAMPLE_GRAN,
    help="Weight sampling granularity. Default={}".format(DEF_SAMPLE_GRAN ) )

    args = parser.parse_args()

    flask.g = {}

    if ( True == args.verbose ):
        logging.basicConfig(level=logging.DEBUG )
    else:
        logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE )

    print "Scale Server v{0}:".format ( VERSION )
    printkv ( "Debug", args.debug )
    printkv ( "Verbose", args.verbose )
    printkv ( "Listening Port", args.port )
    printkv ( "Sampling Granularity", args.sample_granularity )
    print ""

    flask.g["user_config"] = userconfig.Config()

    logging.debug ( "Starting thread" )

    quit_event = threading.Event()

    st = threading.Thread(  target=sampler_thread_cb,
                            kwargs=
                            {
                                "quit_event"        : quit_event,
                                'sample_granularity': args.sample_granularity
                            } )

    st.start()


    try:
        app.run(host  = "0.0.0.0",
                port  = args.port,
                debug = args.debug )
    except KeyboardInterrupt:
        print "\rKeyboard interrupted. Quitting"

    logging.debug ( "Joining sampling thread" )

    quit_event.set()

    st.join()

    logging.debug ( "Sampling thread returned" )

if __name__ == '__main__':
    sys.exit(main())