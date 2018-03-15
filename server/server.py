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
from flask import Markup
from flask import flash

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

LOG_FILE    = "server.log"
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

def get_level ( config ):

    full = config["full_weight"]
    base = config["empty_weight"]
    cur  = config["current_weight"]

    if ( cur > full ):
        full = cur

    full -= base
    cur  -= base

    # Otherwise we'd divide by 0
    if ( 0 == full ):
        return 0

    level = 100 * ( cur / full )

    logging.debug("level @ {}".format ( level ) )

    #
    # the load cells are not super reliable
    #
    if ( level > 100 ):
        level = 100

    return abs ( int ( level ) )

@app.route("/")
def html_root():

    config = flask.g["user_config"].get()

    level = get_level ( config )

    if ( level >= 60 ):
        bar_type = 'success'
    elif ( level >= 20 ):
        bar_type = 'warning'
    else:
        bar_type = 'danger'

    return render_template( "index.html",
                            config=config,
                            bar_level=level,
                            bar_type=bar_type)

@app.route("/<path:path>")
def static_handler(path):
    return render_template(path)



@app.route("/api/reset")
def http_reset():
    uconf = flask.g["user_config"]

    if ( "scale" not in flask.g ):
        return

    s = flask.g["scale"]

    s.reset()
    uconf.set_base_weight(0)
    uconf.set_current_weight(0)
    uconf.set_full_weight(0)
    return redirect("/", code=302)

@app.route("/api/newkeg")
def http_new_keg():

    scale = flask.g["scale"]
    uconf = flask.g["user_config"]

    full_weight = scale.sample()

    if ( full_weight > 0 ):
        uconf.set_full_weight ( full_weight )

    return render_template( "newkeg_2.html",
                            beer_type=uconf.get_beer_type(),
                            beer_name=uconf.get_beer_name() )

@app.route("/formhandler", methods=['POST'])
def http_form_config():

    uconf = flask.g["user_config"]

    if ( "base_weight" in request.form ):
        uconf.set_base_weight  ( float ( request.form["base_weight"] ) )

    if ( "empty_weight" in request.form ):
        uconf.set_empty_weight ( float ( request.form["empty_weight"]) )

    if ( "full_weight" in request.form ):
        uconf.set_full_weight( float ( request.form["full_weight"] ) )

    if ( "beer_type" in request.form ):
        uconf.set_beer_type( request.form["beer_type"] )

    if ( "beer_name" in request.form ):
        uconf.set_beer_name( request.form["beer_name"] )

    return redirect("/", code=302)

@app.route("/config")
def http_config():

    uconf = flask.g["user_config"]

    return render_template( "config.html",
                            base_weight  = uconf.get_base_weight(),
                            empty_weight = uconf.get_empty_weight(),
                            full_weight  = uconf.get_full_weight(),
                            beer_type    = uconf.get_beer_type(),
                            beer_name    = uconf.get_beer_name() )
@app.route("/api/level")
def http_api_level():
    conf  = flask.g["user_config"].get()
    level = get_level( conf )

    level_conf = {}
    level_conf["beer_type" ] = conf["beer_type"]
    level_conf["beer_name" ] = conf["beer_name"]
    level_conf["beer_level"] = level

    return Response(json.dumps( level_conf, indent=4, sort_keys=True ),
                                content_type="application/json; charset=utf-8")

@app.route("/api/config")
def http_api_config():

    conf = flask.g["user_config"].get()

    return Response(json.dumps ( conf, indent=4, sort_keys=True ),
                    content_type="application/json; charset=utf-8" )

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

        time.sleep ( 1 )

    s.cleanup()

    logging.debug ( "Sampling thread is returning..." )

def main():

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
        log_file = "stdout"
    else:
        log_file = os.path.expanduser ( "~/{}".format ( LOG_FILE ) )
        logging.basicConfig(level=logging.DEBUG, filename=log_file)

    print "Scale Server v{0}:".format ( VERSION )
    printkv ( "Debug", args.debug )
    printkv ( "Verbose", args.verbose )
    printkv ( "Listening Port", args.port )
    printkv ( "Sampling Granularity", args.sample_granularity )
    printkv ( "Log File", log_file )

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
