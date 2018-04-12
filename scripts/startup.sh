#!/bin/sh
git -C $HOME/kegger/ pull

#
# Harness for the server. Never seen it crash but it might happen
#
while(true)
do
    $HOME/kegger/server/server.py
    sleep 10
done
