#!/bin/sh
git -C $HOME/kegger/ pull
$HOME/kegger/server/server.py --sample-granularity 500
