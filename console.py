#!/usr/bin/env python

import sys
import curses
import time
import locale

VERSION_MAJ = 1
VERSION_MIN = 0

COLOR_BORDER        = 1
COLOR_TEXT_KEY      = 1
COLOR_TEXT_VALUE    = 2
COLOR_BAR_RED       = 3
COLOR_BAR_YELLOW    = 4
COLOR_BAR_GREEN     = 5

def display_bar ( level ):
    pass

def display_version ( win ):

    ver_str = "Version {}.{}".format ( VERSION_MAJ, VERSION_MIN )

    (max_y, max_x ) = win.getmaxyx()

    win.addstr ( max_y - 2, max_x - ( len ( ver_str ) + 2 ) , ver_str )

def display_temperature( win, temp ):

    (max_y, max_x ) = win.getmaxyx()

    win.move ( max_y - 3, 2 )

    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( "Temperature: " )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( str ( temp ) )
    win.addch   (curses.ACS_DEGREE )
    win.addstr  ( "C" )
    win.attroff( curses.color_pair(COLOR_TEXT_VALUE) )

def display_humidity ( win, hum ):

    (max_y, max_x ) = win.getmaxyx()

    win.move ( max_y - 2, 2 )

    win.attron  ( curses.color_pair(COLOR_TEXT_KEY) )
    win.addstr  ( "Humidity:    " )
    win.attroff ( curses.color_pair(COLOR_TEXT_KEY) )

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( "{}%".format ( hum ) )
    win.attroff( curses.color_pair(COLOR_TEXT_VALUE) )

def display_bar ( bar, level, name ):
    #
    # Not valid
    #
    if ( 0 == level or level > 100 ):
        return

    if ( level >= 70 ):
        color = curses.color_pair(COLOR_BAR_GREEN )
    elif ( level >= 30 ):
        color = curses.color_pair(COLOR_BAR_YELLOW )
    else:
        color = curses.color_pair(COLOR_BAR_RED)

    (max_y, max_x ) = bar.getmaxyx()


    bar.attron  ( curses.color_pair(COLOR_BORDER) )
    bar.addch   ( max_y - 3, 0, curses.ACS_LTEE )
    bar.addch   ( max_y - 3, 1, curses.ACS_HLINE )
    bar.addch   ( max_y - 3, 2, curses.ACS_HLINE )
    bar.addch   ( max_y - 3, 3, curses.ACS_HLINE )
    bar.addch   ( max_y - 3, 4, curses.ACS_HLINE )
    bar.addch   ( max_y - 3, 5, curses.ACS_HLINE )
    bar.addch   ( max_y - 3, 6, curses.ACS_RTEE )
    bar.attroff ( curses.color_pair(COLOR_BORDER) )

    bar.attron  ( curses.color_pair(COLOR_TEXT_VALUE ) )
    bar.addstr  ( max_y - 2, 2, "{}%".format ( level ) )
    bar.attroff ( curses.color_pair(COLOR_TEXT_VALUE ) )

    max_y -= 4
    max_x -= 2

    for i in range ( 0, level * max_y / 100 ):
        bar.attron  ( color )
        bar.addch ( max_y-i, max_x, curses.ACS_CKBOARD, curses.A_REVERSE )
        bar.addch ( max_y-i, max_x-1, curses.ACS_CKBOARD, curses.A_REVERSE )
        bar.addch ( max_y-i, max_x-2, curses.ACS_CKBOARD, curses.A_REVERSE )
        bar.addch ( max_y-i, max_x-3, curses.ACS_CKBOARD, curses.A_REVERSE )
        bar.addch ( max_y-i, max_x-4, curses.ACS_CKBOARD, curses.A_REVERSE )
        bar.attroff ( color )


    #for i in range ( 0, level ):
    #    bar.addch ( curses.ACS_CKBOARD )

def alloc_bar ( win ):

    (max_y, max_x ) = win.getmaxyx()

    h = max_y - 20

    return curses.newwin ( h, 7 , 10, max_x / 2 )

def main():

    level = 0

    locale.setlocale(locale.LC_ALL, '')
    win = curses.initscr()

    curses.start_color()
    curses.init_pair(COLOR_BORDER,     curses.COLOR_CYAN,   curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT_VALUE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_RED,    curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_BAR_GREEN,  curses.COLOR_GREEN,  curses.COLOR_BLACK)

    try:
        while ( True ):
            #
            # Always first
            #
            win.clear()

            win.attron(curses.color_pair(COLOR_BORDER))
            win.border()
            win.attroff(curses.color_pair(COLOR_BORDER))
            bar = alloc_bar(win)

            bar.attron  ( curses.color_pair(COLOR_BORDER) )
            bar.border()
            win.attroff(curses.color_pair(COLOR_BORDER))

            display_temperature(win, 21)
            display_humidity(win, 34)
            display_version(win)

            display_bar ( bar, level, "test" )

            level += 1

            if ( level > 100 ):
                level = 0

            curses.curs_set(0)

            win.refresh()
            bar.refresh()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    except Exception:
        curses.endwin()
        raise

    curses.endwin()

if __name__ == '__main__':
    sys.exit(main())
