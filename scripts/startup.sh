#!/bin/sh
git -C $HOME/kegger/ pull
$HOME/kegger/server/server.py
