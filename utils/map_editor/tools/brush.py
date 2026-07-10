"""Кисть — ставит выбранный объект в клетку"""

class Brush:
    """Инструмент 'Кисть'"""

    def __init__(self, editor):
        self.editor = editor

    def apply(self, x, y):
        """Ставит выбранный объект в клетку (x, y)"""
        if not self.editor.grid:
            return

        if 0 <= y < len(self.editor.grid) and 0 <= x < len(self.editor.grid[0]):
            symbol = self.editor.selected_symbol
            if self.editor.grid[y][x] != symbol:
                self.editor.grid[y][x] = symbol
                self.editor._on_change()
                return True
        return False