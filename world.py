class World:
    def __init__(self, map_data):
        self.map = map_data
        self.width = len(map_data[0])
        self.height = len(map_data)
    
    def is_wall(self, x, y):
        """Проверяет, является ли клетка стеной"""
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.map[iy][ix] == 1
        return True  # за границами карты тоже стена