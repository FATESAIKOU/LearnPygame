"""
input_handler.py - 非阻塞鍵盤輸入處理（基於 curses）
"""

import curses


class InputHandler:
    def __init__(self, win):
        """
        win: curses window 物件，需已設定 nodelay(True)
        """
        self.win = win
        self.win.nodelay(True)
        self.win.keypad(True)

    def get_input(self) -> set:
        """
        回傳當前幀按下的鍵集合（字串集合）
        支援: 'left', 'right', 'q', 'p', 'r', 'enter'
        """
        pressed = set()
        try:
            key = self.win.getch()
            while key != -1:
                if key in (ord('a'), curses.KEY_LEFT):
                    pressed.add('left')
                elif key in (ord('d'), curses.KEY_RIGHT):
                    pressed.add('right')
                elif key == ord('q'):
                    pressed.add('q')
                elif key == ord('p'):
                    pressed.add('p')
                elif key in (ord('r'), ord('R')):
                    pressed.add('r')
                elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                    pressed.add('enter')
                key = self.win.getch()
        except Exception:
            pass
        return pressed
