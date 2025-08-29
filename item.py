import random
from psychopy import visual

class Item(): 
    def __init__(self, x, y, item_id, item_class, is_target, cond, exp_settings, colours, shapes, points):

        self.x = x
        self.y = y
        self.id = item_id
        self.item_class = item_class
        self.is_target = is_target 

        # work out what colour and shape the item should be
        # this depends on what condition we're in, and what 
        # item_class we have assigned
        self.colour = colours[item_class]
        self.shape = shapes[item_class]
        self.points = points[item_class]        
        # randomise orientation
        self.orient = random.randint(0,360)

        # now create our polygon
        self.poly = visual.Polygon(
            win = exp_settings.win, 
            units = 'pix', 
            edges = self.shape, 
            lineColor = None, 
            fillColor = self.colour, radius = 25, 
            ori = self.orient,
            pos = [self.x, self.y],
            autoDraw = False)

    def update_location(self, x, y):

        # this is called when we move the item, 
        # i.e., when making sure items do not overlap.
        self.x = x
        self.y = y
        self.poly.pos = [x, y]
