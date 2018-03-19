#!/usr/bin/env python

import sys
import json
import requests
import time
import argparse

#
# Trying to fix the load cell creep problem. Need to sample
# overnight
#

DEFAULT_SERVER = "http://127.0.0.1:5000"

def get_config ( server ):

    response = None

    url = "{}/{}".format ( server, "api/weight" )
    response = requests.get ( url )

    config = json.loads ( response.content )

    return config["weight"]

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-s",
                        "--server",
                        help="Server. Default=".format ( DEFAULT_SERVER ),
                        default=DEFAULT_SERVER,
                        type=str )

    parser.add_argument("-u",
                        "--update-frequency",
                        help="How often to update the UI",
                        default=120,
                        type=int )

    args = parser.parse_args()

    try:
        with open ( "samples.log", "w+" ) as f:
            while ( True ):
                weight = get_config ( args.server )
                f.write ("{}\n".format ( weight ) )
                f.flush ()
                time.sleep(args.update_frequency)
    except KeyboardInterrupt:
        pass

    print "Returning"
if __name__ == '__main__':
    sys.exit(main())
