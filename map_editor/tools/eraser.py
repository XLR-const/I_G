"""Ластик — ставит '_' в клетку"""

class Eraser:
    """Инструмент 'Ластик'"""

    def __init__(self, editor):
        self.editor = editor

    def apply(self, x, y):
        """Стирает клетку (ставит '_')"""
        if not self.editor.grid:
            return

        if 0 <= y < len(self.editor.grid) and 0 <= x < len(self.editor.grid[0]):
            if self.editor.grid[y][x] != '_':
                self.editor.grid[y][x] = '_'
                self.editor._on_change()
                return True
        return False