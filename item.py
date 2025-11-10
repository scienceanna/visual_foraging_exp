import random
from psychopy import visual

class Item(): 
    def __init__(self, x, y, item_id, item_class, is_target, cond, exp_settings, colours, shapes, points, offset):

        self.x = x
        self.y = y
        self.id = item_id
        self.item_class = item_class
        self.is_target = is_target
        self.offset = offset

        # work out what colour and shape the item should be
        # this depends on what condition we're in, and what 
        # item_class we have assigned
        self.colour = colours[item_class]
        self.shape = shapes[item_class]
        self.points = points[item_class]
        
        # randomise orientation
        if self.shape  in ["T", "L"]:
            orient_options = ['0', '90', '180', '270'] 
            self.orient = random.choice(orient_options)
        else:
            self.orient = random.randint(0,360)
        
    
        # check if we are using a distribution of colours
        if self.colour == "randomGrey":
            grey = random.uniform(0.15,0.85)
            self.colour = [grey, grey, grey]

        self.display = False

        # now create our polygon(s)
        scale_size = exp_settings.win.size[1]/25
        # if shape is a T or L :
        
        if self.shape  in ["T", "L"]:
            self.poly = [None, None]

            if self.shape == "T":
                offset = 0
            else:
                offset = offset * (scale_size/2 - 2.5)
                #print(offset)

            self.poly = self.create_T_or_L(self.x, self.y, self.orient, exp_settings, offset, scale_size)

        else: 
            self.poly = visual.Polygon(
                win = exp_settings.win, 
                units = 'pix', 
                edges = self.shape, 
                lineColor = None, 
                fillColor = self.colour, 
                radius = exp_settings.win.size[1]/50,
                ori = self.orient,
                pos = [self.x, self.y],
                autoDraw = False)
                
    def create_T_or_L(self, x, y, orient, exp_settings, offset, scale_size):

        self.poly = [None, None]

        # draw stem
        if orient in ["0", "180"]:         
            self.poly[0] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (10, scale_size),
                lineColor = None, 
                fillColor = self.colour,                
                pos = [self.x, self.y],
                ori = self.orient,
                autoDraw = False)              
        else:   
            self.poly[0] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (10, scale_size),
                lineColor = None, 
                fillColor = self.colour,                
                pos = [self.x, self.y],
                ori = self.orient,
                autoDraw = False)    
            
        # draw crossbar
        if orient == "0": 
            self.poly[1] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (scale_size, 10),
                lineColor = None, 
                fillColor = self.colour,                
                pos = [self.x + scale_size/2, self.y + offset],
                ori = self.orient,
                autoDraw = False)
        elif orient == "180":
            self.poly[1] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (scale_size, 10),
                lineColor = None, 
                fillColor = self.colour,               
                pos = [self.x - scale_size/2, self.y - offset],
                ori = self.orient,
                autoDraw = False)
        elif orient == "90":
            self.poly[1] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (scale_size, 10),
                lineColor = None, 
                fillColor = self.colour,               
                pos = [self.x + offset, self.y + scale_size/2],
                ori = self.orient,
                autoDraw = False)
        elif orient == "270":
            self.poly[1] = visual.Rect(
                win = exp_settings.win, 
                units = 'pix', 
                size = (scale_size, 10),
                lineColor = None, 
                fillColor = self.colour,               
                pos = [self.x - offset, self.y - scale_size/2],
                ori = self.orient,
                autoDraw = False)         
      
        return self.poly
            
    def update_autoDraw(self, ad):
        # turn autoDraw on or off for the item
        self.display = ad

        if isinstance(self.poly, list):
            for p in self.poly:
                p.autoDraw = ad
        else:
            self.poly.autoDraw = ad 

    def check_mouse_click(self, mouse):
        # check if the mouse has clicked on this item
        if isinstance(self.poly, list):
            for p in self.poly:
                if mouse.isPressedIn(p) and self.display == True:
                    return True
            return False
        else:
            if mouse.isPressedIn(self.poly) and self.display == True:
                return True
            else:
                return False

    def update_location(self, x, y):

        # this is called when we move the item, 
        # i.e., when making sure items do not overlap.
        self.x = x
        self.y = y
        self.poly.pos = [x, y]
