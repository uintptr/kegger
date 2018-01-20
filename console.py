#!/usr/bin/env python
import sys
import curses
import time
import locale

VERSION_MAJ         = 1
VERSION_MIN         = 0

BAR_WIDTH           = 20

COLOR_BORDER        = 1
COLOR_TEXT_KEY      = 1
COLOR_TEXT_VALUE    = 2
COLOR_BAR_RED       = 3
COLOR_BAR_YELLOW    = 4
COLOR_BAR_GREEN     = 5

def display_product ( win ):

    (max_y, max_x ) = win.getmaxyx()

    ver_str = "Version {}.{}".format ( VERSION_MAJ, VERSION_MIN )

    middle  = max_x / 2 - len ( ver_str ) / 2

    win.attron  ( curses.color_pair(COLOR_TEXT_VALUE) )
    win.addstr  ( 0, middle, ver_str )
    win.attroff ( curses.color_pair(COLOR_TEXT_VALUE) )

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
    win.addstr  ( "C" )
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

def display_bar ( bar, level, name ):
    #
    # Invalid inputs
    #
    if ( 0 == level or level > 100 ):
        # Should we raise an exception ?
        return

    #
    # Select the color
    #
    if ( level >= 70 ):
        color = curses.color_pair(COLOR_BAR_GREEN )
    elif ( level >= 30 ):
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
    # Display all the bars
    #
    max_y -= 4
    max_x -= 2
    bar.attron  ( color )
    for i in range ( 0, level * max_y / 100 ):

        for j in range ( 0, BAR_WIDTH - 2 ):
            bar.addch ( max_y-i, max_x-j, curses.ACS_CKBOARD )
    bar.attroff ( color )

def alloc_bar ( win ):

    (max_y, max_x ) = win.getmaxyx()
    h = max_y - 10

    return curses.newwin ( h, BAR_WIDTH, 5, ( max_x / 2 ) - ( BAR_WIDTH/ 2 ) )

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
            win.erase()

            win.attron(curses.color_pair(COLOR_BORDER))
            win.border()
            win.attroff(curses.color_pair(COLOR_BORDER))
            bar = alloc_bar(win)

            bar.attron  ( curses.color_pair(COLOR_BORDER) )
            bar.border()
            win.attroff(curses.color_pair(COLOR_BORDER))

            display_product ( win )
            display_temperature(win, 21)
            display_humidity(win, 34)
            display_url(win)

            display_bar ( bar, level, "test" )

            level += 1

            if ( level > 100 ):
                level = 0

            curses.curs_set(0)

            win.refresh()
            bar.refresh()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception:
        curses.endwin()
        raise

    curses.endwin()

if __name__ == '__main__':
    sys.exit(main())
