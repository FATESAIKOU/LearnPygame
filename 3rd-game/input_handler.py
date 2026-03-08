"""
input_handler.py - Non-blocking input handling for curses-based game.
"""

import curses


class InputHandler:
    """Handles keyboard input via curses."""

    # Action constants
    ACTION_LEFT = 'left'
    ACTION_RIGHT = 'right'
    ACTION_QUIT = 'quit'
    ACTION_PAUSE = 'pause'
    ACTION_CONFIRM = 'confirm'
    ACTION_NONE = None

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def get_action(self):
        """Read a single keypress and return the corresponding action."""
        try:
            key = self.stdscr.getch()
        except curses.error:
            return self.ACTION_NONE

        if key == -1:
            return self.ACTION_NONE
        elif key in (ord('a'), ord('A'), curses.KEY_LEFT):
            return self.ACTION_LEFT
        elif key in (ord('d'), ord('D'), curses.KEY_RIGHT):
            return self.ACTION_RIGHT
        elif key in (ord('q'), ord('Q'), 27):  # q or ESC
            return self.ACTION_QUIT
        elif key in (ord('p'), ord('P')):
            return self.ACTION_PAUSE
        elif key in (ord('\n'), ord('\r'), ord(' '), curses.KEY_ENTER):
            return self.ACTION_CONFIRM
        return self.ACTION_NONE

    def flush(self):
        """Clear input buffer."""
        self.stdscr.nodelay(True)
        try:
            while self.stdscr.getch() != -1:
                pass
        except curses.error:
            pass

    def wait_for_key(self):
        """Block until a key is pressed, return the action."""
        self.stdscr.nodelay(False)
        try:
            key = self.stdscr.getch()
        except curses.error:
            return self.ACTION_NONE
        finally:
            self.stdscr.nodelay(True)

        if key in (ord('q'), ord('Q'), 27):
            return self.ACTION_QUIT
        elif key in (ord('\n'), ord('\r'), ord(' '), curses.KEY_ENTER):
            return self.ACTION_CONFIRM
        elif key in (ord('p'), ord('P')):
            return self.ACTION_PAUSE
        return self.ACTION_CONFIRM
