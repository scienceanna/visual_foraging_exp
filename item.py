import random
from psychopy import visual


class Item(): 
    def __init__(self, x, y, item_id, item_class, is_target, cond, exp_settings):

        self.x = x
        self.y = y
        self.id = item_id
        self.item_class = item_class
        self.is_target = is_target 

        # work out what colour and shape the item should be
        # this depends on what condition we're in, and what 
        # item_class we have assigned
        self.colour = self.get_col_from_class(cond)
        self.shape = self.get_shape_from_class(cond)
        self.points = self.get_points_from_class(cond)
        
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

        self.x = x
        self.y = y
        self.poly.pos = [x, y]

    def get_col_from_class(self, cond):

        if self.item_class == "targ_class1":
            colour = cond["targ1_col"].iloc[0]
        elif self.item_class == "targ_class2":
            colour = cond["targ2_col"].iloc[0]
        elif self.item_class == "dist_class1":
            colour = cond["dist1_col"].iloc[0]
        elif self.item_class == "dist_class2":
            colour = cond["dist2_col"].iloc[0]

        return(colour)

    def get_shape_from_class(self, cond):
        
        if self.item_class == "targ_class1":
            edges = int(cond["targ1_shape"].iloc[0])
        elif self.item_class == "targ_class2":
            edges = int(cond["targ2_shape"].iloc[0])
        elif self.item_class == "dist_class1":
            edges = int(cond["dist1_shape"].iloc[0])
        elif self.item_class == "dist_class2":
            edges = int(cond["dist2_shape"].iloc[0])
            
        return(edges)
    
    def get_points_from_class(self, cond):
        
        if self.item_class == "targ_class1":
            points = int(cond["targ1_points"].iloc[0])
        elif self.item_class == "targ_class2":
            points = int(cond["targ2_points"].iloc[0])
        elif self.item_class == "dist_class1":
            points = int(cond["dist1_points"].iloc[0])
        elif self.item_class == "dist_class2":
            points = int(cond["dist2_points"].iloc[0])
            
        return(points)