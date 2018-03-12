#!/usr/bin/env python

import sys
import json
import requests
import time

#
# Trying to fix the load cell creep problem. Need to sample
# overnight
#

def get_config ( server ):

    response = None

    url = "{}/{}".format ( server, "api/config" )
    response = requests.get ( url )

    config = json.loads ( response.content )

    return config["current_weight"]

def main():

    try:
        with open ( "samples.log", "w+" ) as f:
            while ( True ):
                weight = get_config ( "http://127.0.0.1:5000" )
                f.write ("{}\n".format ( weight ) )
                f.flush ()
                time.sleep(120)
    except KeyboardInterrupt:
        pass

    print "Returning"
if __name__ == '__main__':
    sys.exit(main())
