#!/bin/sh
git -C $HOME/kegger/ pull

#
# Harness for the server
#
while(true)
do
    $HOME/kegger/server/server.py
    sleep 10
done
