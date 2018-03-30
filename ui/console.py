#!/usr/bin/env python

import sys
import os
import curses
import time
import locale
import logging
import tempfile
import argparse
import json
import requests

VERSION_MAJ         = 1
VERSION_MIN         = 0

BAR_WIDTH           = 15

REFRESH_DELAY_SEC   = 5

COLOR_BORDER        = 1
COLOR_TEXT_KEY      = 1
COLOR_TEXT_VALUE    = 2
COLOR_BAR_RED       = 3
COLOR_BAR_YELLOW    = 4
COLOR_BAR_GREEN     = 5

DEFAULT_SERVER      = "http://127.0.0.1:5000"


def display_product ( win ):

    (max_y, max_x ) = win.getmaxyx()

    ver_str = "Kegger Console {}.{}".format ( VERSION_MAJ, VERSION_MIN )

    middle  = max_x / 2 - ( len ( ver_str ) + 2 ) / 2

    win.move ( 0, middle )

    win.attron  ( curses.color_pair(COLOR_BORDER) )
    win.addch   ( curses.ACS_RTEE )
    win.attroff ( curses.color_pair(COLOR_BORDER) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attron  ( curses.A_BOLD )

    win.addstr  ( ver_str )

    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attroff ( curses.A_BOLD )

    win.attron  ( curses.color_pair(COLOR_BORDER) )
    win.addch   ( curses.ACS_LTEE )
    win.attroff ( curses.color_pair(COLOR_BORDER) )

def display_url ( win ):

    ver_str  = "github.com/uintptr/kegger"

    (max_y, max_x ) = win.getmaxyx()

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( max_y - 2, max_x - ( len ( ver_str ) + 2 ) , ver_str )
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )

def display_temperature( win, temp ):

    (max_y, max_x ) = win.getmaxyx()

    win.move ( max_y - 3, 2 )

    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( "Temperature: " )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( str ( temp ) )
    win.addch   (curses.ACS_DEGREE )
    win.addstr  ( "C / {}F".format ( ( temp * 1.8 ) + 32 ) )
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )

def display_humidity ( win, hum ):

    (max_y, max_x ) = win.getmaxyx()

    win.move ( max_y - 2, 2 )

    #
    # Spaces to lign it up with the temperature
    #
    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( "Humidity:    " )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( "{}%".format ( hum ) )
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )

def display_bar_info ( win, bar, name, type_str ):
    corner_x = bar.getbegyx()[1] + 0
    corner_y = bar.getmaxyx()[0] + 1

    #
    # Name
    #
    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( corner_y, corner_x, "Name:" )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attron  ( curses.A_BOLD )
    win.addstr  ( corner_y, corner_x + 6, name )
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attroff ( curses.A_BOLD )

    #
    # Type
    #
    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( corner_y + 1, corner_x, "Type:" )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attron  ( curses.A_BOLD )
    win.addstr  ( corner_y + 1, corner_x + 6, type_str)
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.attroff ( curses.A_BOLD )


def display_bar ( bar, level ):
    #
    # Invalid inputs
    #
    if ( level > 100 or level < 0 ):
        # Should we raise an exception ?
        return

    #
    # Select the color
    #
    if ( level >= 60 ):
        color = curses.color_pair(COLOR_BAR_GREEN )
    elif ( level >= 20 ):
        color = curses.color_pair(COLOR_BAR_YELLOW )
    else:
        color = curses.color_pair(COLOR_BAR_RED)

    (max_y, max_x ) = bar.getmaxyx()

    #
    # Little rectangle at the bottom of the bar to display the percentage
    # in decimal
    #
    bar.attron  ( curses.color_pair(COLOR_BORDER) )
    bar.addch   ( max_y - 3, 0, curses.ACS_LTEE )
    for i in range ( 1, BAR_WIDTH - 1):
        bar.addch   ( max_y - 3, i, curses.ACS_HLINE )
    bar.addch   (  max_y - 3, BAR_WIDTH -1, curses.ACS_RTEE )
    bar.attroff ( curses.color_pair(COLOR_BORDER) )

    #
    # Display the percentage
    #
    bar.attron  ( curses.color_pair(COLOR_TEXT_VALUE ) )
    level_str   = "{}%".format ( level )
    text_middle = ( BAR_WIDTH / 2 ) - len ( level_str ) / 2
    bar.addstr  ( max_y - 2, text_middle, level_str )
    bar.attroff ( curses.color_pair(COLOR_TEXT_VALUE ) )

    #
    # Display the bars
    #
    max_y -= 4
    max_x -= 2
    bar.attron  ( color )
    bar.attron  ( curses.A_BOLD )

    for i in range ( 0, ( level * max_y ) / 100 ):

        for j in range ( 0, BAR_WIDTH - 2 ):
            bar.addch ( max_y-i, max_x-j, curses.ACS_CKBOARD )

    bar.attroff ( curses.A_BOLD )
    bar.attroff ( color )

def alloc_bar ( win ):

    (max_y, max_x ) = win.getmaxyx()
    h = max_y - 6

    return curses.newwin ( h, BAR_WIDTH, 1, ( max_x / 2 ) - ( BAR_WIDTH/ 2 ) )

def init_logging ():

    log_file = os.path.join ( tempfile.gettempdir(), "kegger_console.log" )
    logging.basicConfig(filename=log_file,
                        filemode="a",
                        level=logging.DEBUG )

def parse_config ( file_path ):

    config_info = {}

    logging.debug ( "reading config file @ {}".format ( file_path ) )

    with open ( file_path, "r" ) as f:
        config_info = json.load ( f )

    return config_info


def get_level ( server ):

    response = None

    while ( None == response ):
        url = "{}/{}".format ( server, "api/level" )

        try:
            response = requests.get ( url )
        except requests.exceptions.ConnectionError:
            pass

        if ( None == response ):
            time.sleep ( 1 )

    return json.loads ( response.content )

def main():

    init_logging()

    parser = argparse.ArgumentParser()

    parser.add_argument("-s",
                        "--server",
                        help="Server. Default=".format ( DEFAULT_SERVER ),
                        default=DEFAULT_SERVER,
                        type=str )

    parser.add_argument("-u",
                        "--update-frequency",
                        help="How often to update the UI",
                        default=300,
                        type=int )

    args = parser.parse_args()

    #config = get_level ( args.server )
    #print config
    #return 0

    locale.setlocale(locale.LC_ALL, '')
    win = curses.initscr()

    curses.start_color()

    #
    # init the colors so we don't have to use literals throughout the code
    #
    curses.init_pair(COLOR_BORDER,     curses.COLOR_CYAN,   curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT_VALUE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_RED,    curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_GREEN,  curses.COLOR_GREEN,  curses.COLOR_BLACK)

    #
    # This'll force getting a sample in before everything
    #
    next_update = 0

    try:
        while ( True ):

            #
            # Only read the config when it changes
            #
            if ( next_update <= 0 ):
                config = get_level ( args.server )
                next_update = args.update_frequency

            #
            # Always first
            #
            win.erase()

            win.attron(curses.color_pair(COLOR_BORDER))
            win.border()
            win.attroff(curses.color_pair(COLOR_BORDER))

            bar = alloc_bar(win)

            bar.attron  ( curses.color_pair(COLOR_BORDER) )
            bar.border()
            win.attroff(curses.color_pair(COLOR_BORDER))

            display_product ( win )
            display_temperature(win, config["temperature"] )
            display_humidity(win, config["humidity"] )
            display_url(win)

            display_bar ( bar,  config["beer_level"] )

            display_bar_info (  win,
                                bar,
                                config["beer_name"],
                                config["beer_type"] )

            curses.curs_set(0)

            win.refresh()
            bar.refresh()

            #
            # We should relay on externals events. Only redisplay
            # if something's changed ( temp / level / humidity / ... )
            #
            time.sleep( REFRESH_DELAY_SEC )
            next_update -= REFRESH_DELAY_SEC

    except KeyboardInterrupt:
        #
        # CTRL+C'ed.
        #
        # We leavin'
        #
        pass

    curses.endwin()

if __name__ == '__main__':
    sys.exit(main())
