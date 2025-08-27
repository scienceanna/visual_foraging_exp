from block import *
from psychopy import visual, core, data, event, gui 
from other_stuff import *
from item import *
import numpy as np
import re

class Trial():
    def __init__(self, trial_n, cond, block, exp_settings):

        self.n = trial_n

        self.condition = cond 
        self.block = block

        self.n_rows = int(cond["n_row"].iloc[0])
        self.n_cols = int(cond["n_col"].iloc[0])

        # counter for how many attempts have been made for this trial
        self.attempts = 0
        # a flag to track if the trial needs repeated
        self.complete = False   

        # how many points have we scored this trial so far? 
        self.score = 0
        # how many targets have been clicked on so far (this trial)?
        self.n_found = 0
        # set up feedback
        self.feedback = visual.TextStim(exp_settings.win, text = self.score, pos = (int(exp_settings.scrn_width - exp_settings.width_border)/2 - 50, int(exp_settings.scrn_height - exp_settings.height_border)/2 - 50), units = 'pix')

        # end trial rules
        self.max_time = int(cond["max_time"].iloc[0])
        
        # log of selected items
        self.selected_items = [] 

    def check_and_fix_overlap(self):

        # For each pair of items, check that they do not overlap
        # If they do, adjust (jiggle!)

        rejiggle_sep_multipler = 1.5

        n_fixed = 0

        for ii in self.items:

            # check do not overlap with the line
            if self.condition["display_line"].iloc[0] != "off":
                x0 = ii.poly.pos[0]
                x1 = self.line.start[0]
                x2 = self.line.end[0]
                y0 = ii.poly.pos[1]
                y1 = self.line.start[1]
                y2 = self.line.end[1]

                qx, qy = closest_point_on_line(x1, y1, x2, y2, x0, y0)

                delta2 = ((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1))**2 / ((x2-x1)**2 + (y2-y1)**2)
                min_sep = 1.2*ii.poly.radius

                if (delta2 < (min_sep**2)):

                    # update the number of pairs required fixed
                    n_fixed = n_fixed + 1

                    # calculate how small the current sep delta is 
                    # relative to min allowed

                    delta_ratio = (rejiggle_sep_multipler + min_sep) / math.sqrt(max(delta2, 0.001))
                        
                    midpoint = [(ii.poly.pos[0] + qx)/2, (ii.poly.pos[1] + qy)/2]
                        
                    p1 = delta_ratio * (ii.poly.pos - midpoint) + midpoint
                        
                    ii.update_location(np.around(p1[0]), np.around(p1[1]))
        
            # check for all other items
            for jj in self.items:

                if (ii != jj):
                 
                    # use squared distances, as faster computationally 
                    delta2 = (ii.poly.pos[0] - jj.poly.pos[0])**2 + (ii.poly.pos[1] - jj.poly.pos[1])**2
                    min_sep = 1.1*(ii.poly.radius + jj.poly.radius)

                    if (delta2 < (min_sep**2)):

                        # update the number of pairs required fixed
                        n_fixed = n_fixed + 1

                        # calculate how small the current sep delta is 
                        # relative to min allowed
                        delta_ratio = (rejiggle_sep_multipler + min_sep) / math.sqrt(delta2)

                        #print("need to re-jiggle!", delta_ratio)
                        
                        midpoint = [(ii.poly.pos[0] + jj.poly.pos[0])/2, (ii.poly.pos[1] + jj.poly.pos[1])/2]
                        
                        p1 = delta_ratio * (ii.poly.pos - midpoint) + midpoint
                        p2 = - delta_ratio * (midpoint - jj.poly.pos) + midpoint

                        ii.update_location(np.around(p1[0]), np.around(p1[1]))
                        jj.update_location(np.around(p2[0]), np.around(p2[1]))

        return(n_fixed)

    def item_placements(self, experiment, cond):
        
        place_rule = str(cond["placement_rule"].iloc[0])

        if place_rule == "cardinal":
            grid = get_grid(self.n_rows, self.n_cols, 0, experiment)
            print("dims")
            print(self.n_rows)
            print(self.n_cols)

        if place_rule == "rotated":
            grid = get_grid(self.n_rows, self.n_cols, np.pi/4, experiment)

        if place_rule == "uniform":
            grid = uniform_random_placement(self.n_rows * self.n_cols, experiment) 

        if place_rule == "clump":
            grid = clumpy_placement(self.n_rows * self.n_cols, experiment)

        return(grid)

    def item_details(self, cond):

        # import from our csv
        proportions = cond["proportions"].iloc[0]
        proportions = np.array(proportions.split("-"), dtype = np.float32)
        
        class_type = cond["class_type"].iloc[0]
        class_type = np.array(class_type.split("-"), dtype = object)

        points = cond["points"].iloc[0]
        points = list(map(float, points.split("-")))

        colours = cond["colours"].iloc[0]
        colours = colours.split("-")

        shapes = cond["shapes"].iloc[0]
        shapes = shapes.split("-")

        # check proportions sum to 1
        proportions = proportions / sum(proportions)

        # calculate the number of items of each type
        n = list(map(int, np.round(self.n_items * proportions)))
        
        #if  n != self.n_items:
         #   print("mismatch number of items.")
     

        item_class = np.repeat(class_type, n, axis = 0)
        # randomly shuffle labels here
        item_class = np.random.permutation(item_class)

        return(item_class)

    def create_items(self, cond, es):

        # create our list of our items
        items = []

        # create items
        x, y, item_id = zip(*self.grid)
        xy_pos = zip(x,y,item_id, self.item_class)
        
        for x, y, item_id, item_class in xy_pos:

            # first, is the item a target?
            match = re.search("targ", item_class)

            if match == None:
                is_targ = 0
            else: 
                is_targ = 1

            # now create a new item
            new_item = Item(x, y, item_id, item_class, is_targ, cond, es)       

            items.append(new_item) 

        return(items)

    def update_score(self, cond, selected_item, es):
        self.feedback_type = cond["display_feedback"].iloc[0]
        self.score = self.score + selected_item.points
        
        if self.feedback_type == "trial_score":
            self.feedback.text = self.score
            self.feedback.autoDraw = True
        
        if (selected_item.is_target == True):
            self.n_found = self.n_found + 1
            
        if self.feedback_type == "trial_found": 
            self.feedback.text = self.n_found
            self.feedback.autoDraw = True

    def get_keypress(self):
        keys = event.getKeys()
        if keys:
            return keys[0]
        else:
            return None

    def shutdown(self, es):
        
        # if using eyetracking
        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        if es.track_eyes == "track":
            es.el_tracker.closeDataFile()
            local_edf = os.path.join(es.data_folder, es.edf_fname + '.EDF')
            es.el_tracker.receiveDataFile(es.edf_file, local_edf)
            es.el_tracker.close()

        es.dataFile.close()
        es.dataFileStim.close()
        print('The experiment was ended!')
        es.win.close()
        core.quit()

    def run(self, exp_settings):

        #############################################################
        # This is the important method where we actually run a trial!
        #############################################################
        self.attempts = self.attempts + 1

        # create the grid!
        self.grid = self.item_placements(exp_settings, self.condition)

        # how many lattice points (items) did we fit on the grid?
        # note: this may have changed from row*col due to rotation
        self.n_items = len(self.grid)
        print("n items = ")
        print(self.n_items)
        # now create the items that we need
        self.item_class = self.item_details(self.condition)
        # create all the items for this trial
        self.items = self.create_items(self.condition, exp_settings)

        # display background, if we have one
        img_stim = visual.ImageStim(
            win = exp_settings.win,
            image =  gen_1overf_noise(3, n = 512),  # Pass matrix directly
            size = (1, 1),  # Size in pixels
            pos = (0, 0))
        img_stim.autoDraw = True

        # do we want a line?
        if self.condition["display_line"].iloc[0] == "vert":
            self.line = visual.Line(exp_settings.win, 
                start =(0,-1), 
                end =(0,1), 
                units = 'height',
                lineWidth = 5, lineColor = "white")
            self.line.autoDraw = True

        elif self.condition["display_line"].iloc[0] == "horz":
            self.line = visual.Line(exp_settings.win, 
                start =(-1,0), 
                end =(1,0), 
                units = 'height',
                lineWidth = 5, lineColor = "white")
            self.line.autoDraw = True

        elif "circle" in self.condition["display_line"][0]:

            # extract radius
            number_str = ""

            for char in self.condition["display_line"][0]:
              if char.isdigit():
                number_str += char

            if number_str:
                self.radius = int(number_str)
                #print(self.radius)  # Output: 150

            self.line = visual.Circle(exp_settings.win, 
                radius = self.radius/100,
                lineWidth = 5, lineColor = "white",
                fillColor = "none");
            self.line.autoDraw = True
        
        # make sure items are not overlapping        
        #jiggle_ctr = 0
        #max_jiggle_attempts = 10
        #n_fixed = 10
        #while (n_fixed > 0) & (jiggle_ctr < max_jiggle_attempts): 
        #    jiggle_ctr = jiggle_ctr + 1
         #   n_fixed = self.check_and_fix_overlap()
        
        # now we want to save the item info (after everything is in correct place)
        for ii in self.items:
            exp_settings.dataFileStim.write(str(exp_settings.p_id) + "," + str(self.block) + "," + str(self.condition["label"].iloc[0]) + "," + str(self.n) + "," + str(self.attempts) + "," + str(ii.id) + "," + str(ii.item_class) + "," + str(ii.x) + "," + str(ii.y) + '\n')

        for ii in self.items:  
            ii.poly.autoDraw = True
        
        # are we eyetracking?
        if exp_settings.track_eyes == "track":
            print("start recording")
            exp_settings.el_tracker.sendMessage('CONDITION %s' % self.condition["label"].iloc[0])
            exp_settings.el_tracker.sendMessage('BLOCK %s' % self.block)
            exp_settings.el_tracker.sendMessage('TRIALID %d' % self.n)
            exp_settings.el_tracker.sendMessage('ATTEMPT %d' % self.attempts)
            exp_settings.el_tracker.startRecording(1, 1, 1, 1)

        # update the window
        exp_settings.win.flip()
        
        # save a frame, if wanted.
        if exp_settings.screenshot == "screenshot":
            self.imageName = str(exp_settings.p_id) + "_" + str(self.block) + "_" + str(self.condition["label"].iloc[0]) + "_" + str(self.n)
            exp_settings.win.getMovieFrame()
            exp_settings.win.saveMovieFrames(str(exp_settings.data_folder + self.imageName + '.png'))

        # loop while waiting for keypress/mouseclick/timeout
        clock = core.Clock()
        keep_going = True

        while keep_going:
            
            # can escape out and it will save
            key = self.get_keypress()
            if key is None:
                ... # No response
            elif key == 'escape':
                self.shutdown(exp_settings)
            
            # for each frame, check if an item has been clicked on
            for ii in self.items:
                if exp_settings.mouse.isPressedIn(ii.poly) and ii.poly.autoDraw == True:
                    # get time
                    current_time = np.around(clock.getTime(), 2)

                    # whatever was clicked, remove it from the display
                    ii.poly.autoDraw = False

                    if ii.is_target:

                        # we clicked on a target. Yay!
                        self.update_score(self.condition,ii,exp_settings)
                        
                    else: 
                        # we clicked on a distractor. Boo!
                        print("not a target")

                        if self.condition["distracter_click"][0] == "terminate":  
                            # end the trial, but do not recycle  
                            print("terminate the trial")                       
                            keep_going = False
                            self.complete = True  
                       
                        elif self.condition["distracter_click"][0] == "recycle":
                            # end the trial and then try it again
                            keep_going = False
                            self.complete = False   
                            # set score back to 0 for the next attempt 
                            self.score = 0 
                            # set found back to 0 for the next attempt
                            self.n_found = 0

                        elif self.condition["distracter_click"][0] == "as_target":
                            # in this case, treat distracters like a target
                            # presumably it has some negative point value
                            self.update_score(self.condition,ii,exp_settings)

                    # add info to log
                    # person, block, condition, trial, attempt, id, found, score, item_class, x, y, rt
                    exp_settings.dataFile.write(str(exp_settings.p_id) + "," + str(self.block) + "," + str(self.condition["label"].iloc[0]) + "," + str(self.n) + "," + str(self.attempts) + "," + str(ii.id) + "," + str(self.n_found) + "," + str(self.score) + "," + str(ii.item_class) + "," + str(ii.x) + "," + str(ii.y) + "," + str(current_time) + '\n')
                      
            
            # check if we have reached the max trial time
            if clock.getTime() > self.max_time:
                keep_going = False
                if self.condition["stopping_rule"].iloc[0] == "timer":
                    self.complete = True
                else:
                    self.complete = False

            # check if we have reached the point threshold!
            if self.condition["stopping_rule"].iloc[0] == "points":
                if self.score >= int(self.condition["point_threshold"].iloc[0]):
                    keep_going = False
                    self.complete = True

            # if we're doing exhaustive foraging, check
            if self.condition["stopping_rule"].iloc[0] == "exhaustive":
                # print("we have " + str(self.n_found) + " pokemon out of " + str(self.n_targ))
                if (self.n_found == self.n_targ):
                    # print("gotta collect them all!")
                    keep_going = False
                    self.complete = True

            exp_settings.win.flip()

        self.end_trial(exp_settings)
        
        return(self.final_found, self.final_score)

    def end_trial(self, es):
        
        self.feedback.autoDraw = False
        self.final_found = self.n_found
        self.final_score = self.score

        for ii in self.items:
            ii.poly.autoDraw = False

        if self.condition["display_line"].iloc[0] != "off":
           self.line.autoDraw = False
        
        # If eyetracking, stop it
        if es.track_eyes == "track":
            print("stopping recording now")
            es.el_tracker.stopRecording()

        # wipe screen
        self.items = [] 
        es.win.flip()
        core.wait(1)

