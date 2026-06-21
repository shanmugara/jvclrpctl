import curses
import time

def banner(stdscr, messages):
    h, w = stdscr.getmaxyx()
    
    longest = max(messages, key=len)
    width = min(len(longest) + 4, w - 2)
    height = len(messages) + 3

    win = curses.newwin(height, width, 0, (w - width) // 2)
    win.box()
   
    curses.start_color()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)

    win.bkgd(' ', curses.color_pair(1))

    for i, message in enumerate(messages): 
      win.addstr(i+1, 2, message)

    win.refresh()
    time.sleep(3)

    win.clear()
    win.refresh()

def run(messages):
   curses.wrapper(lambda stdscr: banner(stdscr, messages))
