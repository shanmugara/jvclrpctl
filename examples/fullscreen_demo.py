"""
Fullscreen Message Demo - Display centered text with colored backgrounds
Perfect for Raspberry Pi 3 with 3.5" TFT screen
"""

import os
import sys
import time


# ============================================================================
# Method 1: Simple ANSI Escape Codes (No dependencies)
# ============================================================================
def fullscreen_ansi(text, bg_color='green', fg_color='white', duration=2):
    """Display fullscreen message using ANSI escape codes"""
    
    # ANSI color codes
    bg_colors = {
        'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
        'blue': 44, 'magenta': 45, 'cyan': 46, 'white': 47
    }
    fg_colors = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37
    }
    
    # Clear screen
    os.system('clear')
    
    # Get terminal size
    try:
        rows, cols = os.popen('stty size', 'r').read().split()
        rows, cols = int(rows), int(cols)
    except:
        rows, cols = 24, 80  # Default fallback
    
    # Set colors and fill screen
    bg = bg_colors.get(bg_color, 42)
    fg = fg_colors.get(fg_color, 37)
    
    print(f"\033[{bg};{fg}m", end='')
    
    # Fill entire screen with colored background
    for i in range(rows):
        print(' ' * cols)
    
    # Move cursor to center and print text
    center_row = rows // 2
    center_col = (cols - len(text)) // 2
    print(f"\033[{center_row};{center_col}H\033[1m{text}\033[0m", end='', flush=True)
    
    time.sleep(duration)
    
    # Reset
    print("\033[0m")
    os.system('clear')


# ============================================================================
# Method 2: curses (Built-in, no installation needed)
# ============================================================================
def fullscreen_curses(text, bg_color_num=2, fg_color_num=0, duration=2):
    """Display fullscreen message using curses library"""
    import curses
    
    def show(stdscr):
        # Initialize colors
        curses.start_color()
        curses.init_pair(1, fg_color_num, bg_color_num)
        
        # Clear and set background
        stdscr.clear()
        stdscr.bkgd(' ', curses.color_pair(1))
        
        # Get screen dimensions
        height, width = stdscr.getmaxyx()
        
        # Calculate center position
        x = width // 2 - len(text) // 2
        y = height // 2
        
        # Display centered text
        stdscr.addstr(y, x, text, curses.color_pair(1) | curses.A_BOLD)
        stdscr.refresh()
        
        # Wait
        stdscr.timeout(duration * 1000)
        stdscr.getch()
    
    curses.wrapper(show)


# ============================================================================
# Method 3: Rich (Requires installation: pip install rich)
# ============================================================================
def fullscreen_rich(text, bg_color='green', fg_color='white', duration=2):
    """Display fullscreen message using Rich library"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.align import Align
        from rich.text import Text
        
        console = Console()
        console.clear()
        
        # Create large centered text
        big_text = Text(text, style=f"bold {fg_color}")
        
        # Create panel with colored background
        panel = Panel(
            Align.center(big_text, vertical="middle"),
            style=f"bold on {bg_color}",
            border_style=f"{bg_color}",
            expand=True,
            height=console.height
        )
        
        console.print(panel)
        time.sleep(duration)
        console.clear()
        
    except ImportError:
        print("Rich library not installed. Run: pip install rich")


# ============================================================================
# Method 4: Combined with pyfiglet for LARGE text
# ============================================================================
def fullscreen_figlet(text, bg_color='green', fg_color='white', duration=2):
    """Display fullscreen message with ASCII art text"""
    try:
        from pyfiglet import figlet_format
        
        # Generate large text
        large_text = figlet_format(text, font='banner')
        lines = large_text.split('\n')
        
        # ANSI color codes
        bg_colors = {
            'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
            'blue': 44, 'magenta': 45, 'cyan': 46, 'white': 47
        }
        fg_colors = {
            'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
            'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37
        }
        
        os.system('clear')
        
        # Get terminal size
        try:
            rows, cols = os.popen('stty size', 'r').read().split()
            rows, cols = int(rows), int(cols)
        except:
            rows, cols = 24, 80
        
        bg = bg_colors.get(bg_color, 42)
        fg = fg_colors.get(fg_color, 37)
        
        # Fill screen with background color
        print(f"\033[{bg};{fg}m", end='')
        for i in range(rows):
            print(' ' * cols)
        
        # Calculate starting row to center vertically
        start_row = (rows - len(lines)) // 2
        
        # Print each line centered
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                center_col = max(0, (cols - len(line)) // 2)
                print(f"\033[{start_row + i};{center_col}H\033[1m{line}\033[0m", end='')
        
        print(flush=True)
        time.sleep(duration)
        
        # Reset
        print("\033[0m")
        os.system('clear')
        
    except ImportError:
        print("pyfiglet not installed. Run: pip install pyfiglet")


# ============================================================================
# Demo Runner
# ============================================================================
def run_demos():
    """Run all fullscreen demos"""
    
    print("Fullscreen Message Demo")
    print("=" * 50)
    print("\nThis demo shows 4 different methods to display")
    print("fullscreen messages with colored backgrounds.")
    print("\nPress Ctrl+C to exit at any time.")
    print("=" * 50)
    
    input("\nPress Enter to start...")
    
    try:
        # Demo 1: ANSI (Green background)
        print("\n1. ANSI Escape Codes - HDR (Green)")
        time.sleep(1)
        fullscreen_ansi("HDR MODE", bg_color='green', fg_color='white', duration=2)
        
        # Demo 2: ANSI (Red background)
        print("\n2. ANSI Escape Codes - SDR (Blue)")
        time.sleep(1)
        fullscreen_ansi("SDR MODE", bg_color='blue', fg_color='white', duration=2)
        
        # Demo 3: curses (Green)
        print("\n3. Curses Library - OK (Green)")
        time.sleep(1)
        # curses colors: 0=black, 1=red, 2=green, 3=yellow, 4=blue, 5=magenta, 6=cyan, 7=white
        fullscreen_curses("✓ OK", bg_color_num=2, fg_color_num=7, duration=2)
        
        # Demo 4: Rich (if available)
        print("\n4. Rich Library - STATUS (Cyan)")
        time.sleep(1)
        fullscreen_rich("READY", bg_color='cyan', fg_color='black', duration=2)
        
        # Demo 5: pyfiglet + ANSI (Large text)
        print("\n5. PyFiglet + ANSI - Large HDR (Green)")
        time.sleep(1)
        fullscreen_figlet("HDR", bg_color='green', fg_color='white', duration=3)
        
        print("\n6. PyFiglet + ANSI - Large SDR (Blue)")
        time.sleep(1)
        fullscreen_figlet("SDR", bg_color='blue', fg_color='white', duration=3)
        
        print("\n" + "=" * 50)
        print("Demo complete!")
        print("\nRecommended for Pi3 TFT screen:")
        print("  - Method 1 (ANSI) - Lightweight, no dependencies")
        print("  - Method 2 (curses) - Built-in, reliable")
        print("  - Method 5 (pyfiglet+ANSI) - Best readability")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        os.system('clear')


if __name__ == "__main__":
    run_demos()
