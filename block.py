import random
from trial import *

class Block():
    def __init__(self, label, condition_labels, n_trials_per_cond, group, intro_text, outro_text, practice, es):
        
        self.label = label
        self.intro_text = intro_text
        self.outro_text = outro_text
        self.block_found = 0
        self.block_score = 0
        self.practice = practice
        
        n_trials_per_cond = int(n_trials_per_cond)

        # we need to split up conditions (each block may contain multiple!)
        self.condition_labels = condition_labels.split("-")
        
        # now, we need to go get the conditions that match the condition labels
        self.conditions = es.conditions[es.conditions["label"].isin(self.condition_labels)]

        # if we feed multiple conditions into a block, do 
        # we always want to randomise the trial order? At the moment, this is what is happening

        # make a load of trials
        self.trials = []

        for cidx in range(0, len(self.conditions)):
            for trl in range(0, n_trials_per_cond):
                self.trials.append(Trial(trl, self.conditions.iloc[[cidx]], self.label, es))

        print("created " + str(len(self.trials)) + " trials!")

        # shuffle trials
        random.shuffle(self.trials)

    def run(self, es):

        # before we run check is there is an associated practice block
        if self.practice != "none":
            # find the practice block with matching label!
            for pblk in es.pblocks:
                if pblk.label == self.practice:
                    pblk.run(es)

        self.display_intro_block(es)

        for trial in self.trials:

            while trial.complete == False: 
                # fixation cross
                es.fixation.draw()
                es.win.flip()
                # Press before beginning (or do we want a specific wait time?)
                event.waitKeys(keyList=['space'])
                final_found, final_score = trial.run(es)
                self.block_found = self.block_found + final_found
                self.block_score = self.block_score + final_score

                if trial.attempts > 5:
                    # this person is a muppet, let's move on
                    trial.complete = True

        self.display_outro_block(es)

    def display_intro_block(self, es):

        intro_text = visual.TextStim(es.win, self.intro_text, units = 'pix', height = 32)
        intro_text.draw()

        es.win.flip()
        event.waitKeys(keyList=['space'])
        es.win.flip()

    def display_outro_block(self, es):

        outro_text = visual.TextStim(es.win, self.outro_text, units = 'pix', height = 32)
        outro_text.draw()
        
        if es.conditions["display_feedback"].iloc[0] == 'block_found':
            outro_text_2 = visual.TextStim(es.win, 'In this block, you found ' + str(self.block_found) + ' stimuli.', pos = (0,-150), units = 'pix', height = 50)
            outro_text_2.draw()
            
        if es.conditions["display_feedback"].iloc[0] == 'block_score':
            outro_text_2 = visual.TextStim(es.win, 'In this block, you scored ' + str(self.block_score) + ' points.', pos = (0,-150), units = 'pix', height = 50)
            outro_text_2.draw()
            

        es.win.flip()
        event.waitKeys(keyList=['space'])
        es.win.flip()

class Item(): 
    def __init__(self, x, y, item_id, item_class, is_target, cond, exp_settings):

        self.x = x
        self.y = y
        self.id = item_id
        self.item_class = item_class
        self.is_target = is_target 

        # now work out what colour and shape the item should be
        self.colour = self.get_col_from_class(cond)
        self.shape = self.get_shape_from_class(cond)
        self.points = self.get_points_from_class(cond)
        
        # randomise orientation
        self.orient = random.randint(0,360)

        # now create polygon
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