from geopy import Point


class Base:

    def __init__(self, id: int, x: float, y: float):
        self.id = id
        self.location = Point(x, y)
