from psychopy import visual, core, data, event, gui # import some libraries from PsychoPy
from psychopy.event import Mouse
from psychopy.hardware import keyboard
import numpy as np
import re
import pandas as pd
import math
import random
import os.path


class Experiment():
    def __init__(self, exp_name):
        
        print("*** Setting up experiment ***")
        
        self.exp_name = exp_name
        self.exp_folder = "exp_config/" + exp_name + "/"
        self.data_folder = "data/" + exp_name + "/"
        
        # does the data folder already exist?
        isExist = os.path.exists(self.data_folder)
        if not isExist:
               os.makedirs(self.data_folder)
               print("A new data directory has been created")

        self.person = self.collect_person_info()
        
        self.p_id = self.person.pop("Participant number|0")
        self.age = self.person.pop("Age|1")
        self.gender = self.person.pop("Gender|2")

        # Setting up experimental file
        self.date = data.getDateStr()
        self.fileName = str(self.p_id) + "_" + str(self.age) + "_" + str(self.gender) + "_" + self.date
        self.dataFile = open(self.data_folder + self.fileName+'_found.csv', 'w') 
        self.dataFile.write('person,block,condition,trial,attempt,id,found,score,item_class,x,y,rt\n') # this is d$found
        
        # setting up stim file
        self.dataFileStim = open(self.data_folder + self.fileName+'_stim.csv', 'w')
        self.dataFileStim.write('person,block,condition,trial,attempt,id,item_class,x,y\n') # this is d$stim
        
        # import exp config
        self.import_exp_config()
            
        # create screen, mouse and keyboard
        self.win = visual.Window([self.scrn_width,self.scrn_height], screen = 1, fullscr = True)
        self.mouse = Mouse()
        self.k1 = keyboard.Keyboard()
        
        # pre-draw fixation cross
        self.fixation = visual.ShapeStim(self.win, 
            vertices=((0, -0.05), (0, 0.05), (0,0), (-0.05,0), (0.05, 0)),
            lineWidth=5,
            units = 'height',
            closeShape=False,
            lineColor="white")
        
        # import conditions
        self.conditions = self.get_conditions()
        
        # read in blocks, and pblocks (pblocks may be empty)
        self.blocks = self.get_blocks(False)
        if os.path.isfile(self.exp_folder+"pblocks.csv"):
            self.pblocks = self.get_blocks(practice = True)
        print("imported blocks and pblocks")

        # set up eye tracking, if using
        if self.track_eyes == "track":
            print("we are going to eyetrack")
            from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
            import pylink as pl
            # connect to eyelink host pc
            self.el_tracker = pl.EyeLink("100.1.1.1")
            # open edf data file - need to decide what we should call edf files
            self.edf_fname = self.person[0]
            self.edf_file = self.edf_fname + ".edf"
            self.el_tracker.openDataFile(self.edf_file)
            # Send over a command to let the tracker know the correct screen resolution
            scn_coords = "screen_pixel_coords = 0 0 %d %d" % (self.scrn_width - 1, self.scrn_height - 1)
            self.el_tracker.sendCommand(scn_coords)
            # configure a graphics environment (genv) for tracker calibration
            genv = EyeLinkCoreGraphicsPsychoPy(self.el_tracker, self.win)
            # request pylink to use the PsychoPy window we opened above for calibration
            pl.openGraphicsEx(genv)
            # get reference to currently active Eyelink connection
            self.el_tracker = pl.getEYELINK()
            # clear screen
            self.win.fillColor = genv.getBackgroundColor()
            self.win.flip()
            # do tracker set up?
            self.el_tracker.doTrackerSetup()

        # display intro 
        self.display_intro_exp()
        
    def collect_person_info(self):
        # get some basic experimental info
        info = {'Participant number':'1', 'Age':99, 'Gender': 'f'}
        
        dictDlg = gui.DlgFromDict(dictionary=info,
        title='Foraging experiment', order = ['Participant number', 'Age', 'Gender'])
        
        #ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
        if dictDlg.OK:  # or if ok_data is not None
            return(info)
        else:
            print('user cancelled')
            core.quit()
        
    def import_exp_config(self):
            # read in config file
            exp_config = pd.read_csv(self.exp_folder+"exp_config.csv")
            # save config file
            exp_config.to_csv(self.data_folder + self.fileName + '_exp_config.csv')
            exp_config = exp_config.set_index("attribute").T # transpose

            self.scrn_height = int(exp_config["scrn_height"][0])
            self.scrn_width = int(exp_config["scrn_width"][0])

            self.height_border = int(exp_config["height_border"][0])
            self.width_border = int(exp_config["width_border"][0])
            
            self.jiggle = int(exp_config["jiggle"][0])

            self.intro_expt = exp_config["intro_expt"][0]
            self.outro_expt = exp_config["outro_expt"][0]

            self.block_style = exp_config["block_style"][0]
            self.global_practice = exp_config["global_practice"][0]

            self.track_eyes = exp_config["track_eyes"][0]
            self.screenshot = exp_config["screenshot"][0]

    def run(self):

        print("*** running experiment with", len(self.blocks), " blocks ***")

        for block in self.blocks:
            print("about to run block " + block.label)
            # calibrate eye tracker, if doing eye tracking
            if self.track_eyes == "track":
                self.el_tracker.doTrackerSetup()
            # run the block    
            block.run(self)
        
        # if using eyetracking
        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        if self.track_eyes == "track":
            self.el_tracker.closeDataFile()
            local_edf = os.path.join(self.data_folder, self.edf_fname + '.EDF')
            self.el_tracker.receiveDataFile(self.edf_file, local_edf)
            self.el_tracker.close()
            
        # close data file after running all blocks/trials
        self.dataFile.close()
        self.dataFileStim.close()
        
        # display outro
        self.display_outro_exp()

    def get_conditions(self):

        # read in condition definitions from csv file
        cond_file = pd.read_csv(self.exp_folder+"conditions.csv")
        # save conditions file
        cond_file.to_csv(self.data_folder + self.fileName + '_conditions.csv')
        conditions = cond_file.set_index("attribute").T
        
        print("----- found", len(conditions.index), " conditions")
        return(conditions)

    def get_blocks(self, practice, default_n_trials = 2): 

        if practice == True:
            if os.path.isfile(self.exp_folder+"pblocks.csv"):
                block_file = pd.read_csv(self.exp_folder+"pblocks.csv")
                # save block file
                block_file.to_csv(self.data_folder + self.fileName + '_pblocks.csv')
        else:
            block_file = pd.read_csv(self.exp_folder+"blocks.csv")
            # save block file
            block_file.to_csv(self.data_folder + self.fileName + '_blocks.csv')

        block_file = block_file.set_index("attribute").T

        n_blocks = len(block_file)
        blocks = []
        blocks_one = []
        blocks_two = []

        for blk in range(n_blocks):
            block = Block(block_file["label"][blk], block_file["conditions"][blk], block_file["n_trials_per_cond"][blk], block_file["group"][blk], block_file["intro_text"][blk], block_file["outro_text"][blk], block_file["practice"][blk], self)
            
            if self.block_style == "counter_balanced":
                if block_file["group"][blk] == "1":
                    blocks_one.append(block)
                elif block_file["group"][blk] == "2":
                    blocks_two.append(block)
                else:
                    blocks.append(block)

        if practice==False:
            if self.block_style == "randomised":
                random.shuffle(blocks)

                if self.global_practice != "none":
                    blocks.sort(key=lambda blk: blk.label != self.global_practice)         

            elif self.block_style == "counter_balanced":
                random.shuffle(blocks_one)
                random.shuffle(blocks_two)
            # if even participant number, group 2 first. Otherwise, group 1 first.            
                if int(self.p_id[0]) % 2 == 0:
                    blocks = blocks + blocks_one + blocks_two
                else:
                    blocks = blocks + blocks_two + blocks_one
                

                
        return(blocks)
        
    def display_intro_exp(self):
        intro_text_expt = visual.TextStim(self.win, self.intro_expt, units = 'pix', height = 32)
        intro_text_expt.draw()

        self.win.flip()
        event.waitKeys(keyList=['space'])
        self.win.flip()
    
    def display_outro_exp(self):
        outro_text_expt = visual.TextStim(self.win, self.outro_expt, units = 'pix', height = 32)
        outro_text_expt.draw()
        
        self.win.flip()
        event.waitKeys(keyList=['space'])
        self.win.flip()
        
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
        
        if es.conditions["display_feedback"][0] == 'block_found':
            outro_text_2 = visual.TextStim(es.win, 'In this block, you found ' + str(self.block_found) + ' stimuli.', pos = (0,-150), units = 'pix', height = 50)
            outro_text_2.draw()
            
        if es.conditions["display_feedback"][0] == 'block_score':
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
            colour = cond["targ1_col"][0]
        elif self.item_class == "targ_class2":
            colour = cond["targ2_col"][0]
        elif self.item_class == "dist_class1":
            colour = cond["dist1_col"][0]
        elif self.item_class == "dist_class2":
            colour = cond["dist2_col"][0]

        return(colour)

    def get_shape_from_class(self, cond):
        
        if self.item_class == "targ_class1":
            edges = int(cond["targ1_shape"][0])
        elif self.item_class == "targ_class2":
            edges = int(cond["targ2_shape"][0])
        elif self.item_class == "dist_class1":
            edges = int(cond["dist1_shape"][0])
        elif self.item_class == "dist_class2":
            edges = int(cond["dist2_shape"][0])
            
        return(edges)
    
    def get_points_from_class(self, cond):
        
        if self.item_class == "targ_class1":
            points = int(cond["targ1_points"][0])
        elif self.item_class == "targ_class2":
            points = int(cond["targ2_points"][0])
        elif self.item_class == "dist_class1":
            points = int(cond["dist1_points"][0])
        elif self.item_class == "dist_class2":
            points = int(cond["dist2_points"][0])
            
        return(points)

class Trial():
    def __init__(self, trial_n, cond, block, exp_settings):

        self.n = trial_n

        self.condition = cond 
        self.block = block

        self.n_rows = int(cond["n_row"][0])
        self.n_cols = int(cond["n_col"][0])

        # counter for how many attempts have been made for this trial
        self.attempts = 0
        # a flag to track if the trial needs repeated
        self.complete = False   

        # how many points have we scored this trial so far? 
        self.score = 0
        # how many targets have been clicked on so far (this trial)?
        self.n_found = 0
        # set up feedback
        self.feedback = visual.TextStim(exp_settings.win, text = self.score, pos = (int(exp_settings.scrn_width)/2 - 50, int(exp_settings.scrn_height)/2 - 50), units = 'pix')

        # end trial rules
        self.max_time = int(cond["max_time"][0])
        
        # log of selected items
        self.selected_items = [] 

    def check_and_fix_overlap(self):

        rejiggle_sep_multipler = 1.5
        # for each pair of items, check that they do not overlap
        # if they do, adjust

        n_fixed = 0

        for ii in self.items:

            # check do not overlap with the line
            if self.condition["display_line"][0] != "off":
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
        
        place_rule = str(cond["placement_rule"][0])

        if place_rule == "cardinal":
            grid = get_grid(self.n_rows, self.n_cols, 0, experiment)

        if place_rule == "rotated":
            grid = get_grid(self.n_rows, self.n_cols, np.pi/4, experiment)

        if place_rule == "uniform":
            grid = uniform_random_placement(self.n_rows * self.n_cols, experiment) 

        if place_rule == "clump":
            grid = clumpy_placement(self.n_rows * self.n_cols, experiment)

        return(grid)

    def item_details(self, cond):

        # note, just now we will hardcode 2 classes for targ/dists
        self.n_targ = round(float(cond["prop_target"][0]) * self.n_items)
        n_dist = self.n_items - self.n_targ

        # calcualte number of targets of each type
        targ_class1 = round(self.n_targ * float(cond["prop_targ1"][0]))
        targ_class2 = self.n_targ - targ_class1

        # calcualte number of distracters of each type
        dist_class1 = round(n_dist * float(cond["prop_dist1"][0]))
        dist_class2 = n_dist - dist_class1

        item_class = np.array(["targ_class1", "targ_class2", "dist_class1", "dist_class2"])
        item_class = np.repeat(item_class, [targ_class1, targ_class2, dist_class1, dist_class2], axis = 0)

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
        self.feedback_type = cond["display_feedback"][0]
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
        # now create the items that we need
        self.item_class = self.item_details(self.condition)
        # create all the items for this trial
        self.items = self.create_items(self.condition, exp_settings)

        # do we want a line?
        if self.condition["display_line"][0] == "vert":
            self.line = visual.Line(exp_settings.win, 
                start =(0,-1), 
                end =(0,1), 
                units = 'height',
                lineWidth = 5, lineColor = "white")
            self.line.autoDraw = True
        elif self.condition["display_line"][0] == "horz":
            self.line = visual.Line(exp_settings.win, 
                start =(-1,0), 
                end =(1,0), 
                units = 'height',
                lineWidth = 5, lineColor = "white")
            self.line.autoDraw = True
        
        # make sure items are not overlapping        
        jiggle_ctr = 0
        max_jiggle_attempts = 10
        n_fixed = 10
        while (n_fixed > 0) & (jiggle_ctr < max_jiggle_attempts): 
            jiggle_ctr = jiggle_ctr + 1
            n_fixed = self.check_and_fix_overlap()
        
        # now we want to save the item info (after everything is in correct place)
        for ii in self.items:
            exp_settings.dataFileStim.write(str(exp_settings.p_id) + "," + str(self.block) + "," + str(self.condition["label"][0]) + "," + str(self.n) + "," + str(self.attempts) + "," + str(ii.id) + "," + str(ii.item_class) + "," + str(ii.x) + "," + str(ii.y) + '\n')

        for ii in self.items:  
            ii.poly.autoDraw = True
        
        # are we eyetracking?
        if exp_settings.track_eyes == "track":
            print("start recording")
            exp_settings.el_tracker.sendMessage('CONDITION %s' % self.condition["label"][0])
            exp_settings.el_tracker.sendMessage('BLOCK %s' % self.block)
            exp_settings.el_tracker.sendMessage('TRIALID %d' % self.n)
            exp_settings.el_tracker.sendMessage('ATTEMPT %d' % self.attempts)
            
            exp_settings.el_tracker.startRecording(1, 1, 1, 1)

        # update the window
        exp_settings.win.flip()
        
        # save a frame, if wanted.
        if exp_settings.screenshot == "screenshot":
            self.imageName = str(exp_settings.p_id) + "_" + str(self.block) + "_" + str(self.condition["label"][0]) + "_" + str(self.n)
            exp_settings.win.getMovieFrame()
            exp_settings.win.saveMovieFrames(str(exp_settings.data_folder + self.imageName + '.png'))

        clock = core.Clock()

        keep_going = True

        while keep_going:
            
            # can escape out and it will save
            key = self.get_keypress()
            if key is None:
                ...# No response
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
                    exp_settings.dataFile.write(str(exp_settings.p_id) + "," + str(self.block) + "," + str(self.condition["label"][0]) + "," + str(self.n) + "," + str(self.attempts) + "," + str(ii.id) + "," + str(self.n_found) + "," + str(self.score) + "," + str(ii.item_class) + "," + str(ii.x) + "," + str(ii.y) + "," + str(current_time) + '\n')
                      
            
            # check if we have reached the max trial time
            if clock.getTime() > self.max_time:
                keep_going = False
                self.score = 0
                if self.condition["stopping_rule"][0] == "timer":
                    self.complete = True
                else:
                    self.complete = False

            # check if we have reached the point threshold!
            if self.condition["stopping_rule"][0] == "points":
                if self.score >= int(self.condition["point_threshold"][0]):
                    keep_going = False
                    self.complete = True

            # if we're doing exhaustive foraging, check
            if self.condition["stopping_rule"][0] == "exhaustive":
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

        if self.condition["display_line"][0] != "off":
           self.line.autoDraw = False
        
        # If eyetracking, stop it
        if es.track_eyes == "track":
            print("stopping recording now")
            es.el_tracker.stopRecording()

        # wipe screen
        self.items = [] 
        es.win.flip()
        core.wait(1)

def clumpy_placement(n_items, es):
 
    # first get the underlying density map
    ht = gen_1overf_noise(3)

    n_placed = 0
    x = []
    y = []

    while n_placed < n_items:

        # sample a potential position
        xp = int(np.around(np.random.uniform(0, 255, 1)))
        yp = int(np.around(np.random.uniform(0, 255, 1)))

        # keep if with probability determined by ht
        if np.random.binomial(size=1, n=1, p = ht[xp, yp]) == 1:
            x.append(xp/255 * (es.scrn_width - 2*es.width_border ) - es.scrn_width/2 + es.width_border)
            y.append(yp/255 * (es.scrn_height - 2*es.height_border) - es.scrn_height/2 + es.height_border)
            n_placed = n_placed + 1

    item_id = range(1, n_items+1)

    return(list(zip(x, y, item_id)))

def gen_1overf_noise(beta, filter_freq = -0.1, n = 256):

    # Generate indices
    nq = n // 2
    V = -np.tile(np.arange(-nq, nq).reshape(-1, 1), (1, 2 * nq))
    U = np.tile(np.arange(-nq, nq), (2 * nq, 1))
    f = np.sqrt(U**2 + V**2)

    # Generate random phase and magnitude
    theta = np.random.rand(n, n) * 2 * np.pi
    mag = np.power(f, -beta)
    lpf = 1-np.exp(-filter_freq*f)
   
    mag = np.fft.ifftshift(lpf*mag)
    mag[0, 0] = 0  # Zero d.c.

    # Convert to cartesian coordinates
    x, y = np.cos(theta) * mag, np.sin(theta) * mag
    F = x + 1j * y

    # Perform Inverse FFT
    ht = np.fft.ifft2(F).real

    # Adjust to [0, 1]
    ht = ht - np.min(ht)
    ht = ht / np.max(ht)

    return(ht)

def get_grid(rows, cols, theta, es):

    # some parameters
    jiggle_param = es.jiggle # how much random jitter should we add

    xmin = es.width_border
    xmax = es.scrn_width - es.width_border
    ymin = es.height_border
    ymax = es.scrn_height - es.height_border

    # create one-dimensional arrays for x and y
    # generate twice as many as required so 
    # we will fill the search space with items
    # even after rotation
    x = np.linspace(-1, 2, 3*cols) 
    y = np.linspace(-1, 2, 3*rows)

    # create the mesh based on these arrays
    x, y = np.meshgrid(x, y)

    # convert into 1D vector
    x = x.reshape((np.prod(x.shape),))
    y = y.reshape((np.prod(y.shape),))

 

    # scale to correct size
    x = (es.scrn_width  - 2*es.width_border)  * x + es.width_border
    y = (es.scrn_height - 2*es.height_border) * y + es.height_border
  
    idx = (x > es.width_border) * (x < es.scrn_width - es.width_border) * (y > es.height_border) * (y < es.scrn_height - es.height_border) 
    x = x[idx]
    y = y[idx]


    # translate so that (0, 0) is the centre of the screen
    x = x - es.scrn_width/2
    y = y - es.scrn_height/2

    # rotate lattice
    xr = np.cos(theta) * x - np.sin(theta) * y
    yr = np.sin(theta) * x + np.cos(theta) * y

    x = xr
    y = yr 
    
    #idx = ((x)**2 + (y)**2) < 500**2
 

    # apply random jiggle and round
    x = np.around(x + jiggle_param * np.random.randn(len(x)))
    y = np.around(y + jiggle_param * np.random.randn(len(y)))

    item_id = range(1, rows*cols+1)

    return(list(zip(x, y, item_id)))

def uniform_random_placement(n_items, es):

    xmin = es.width_border
    xmax = es.scrn_width - es.width_border
    ymin = es.height_border
    ymax = es.scrn_height - es.height_border

    x = np.around(np.random.uniform(xmin, xmax, n_items)) - es.scrn_width/2
    y = np.around(np.random.uniform(ymin, ymax, n_items)) - es.scrn_height/2
    
    item_id = range(1, n_items+1)

    return(list(zip(x, y, item_id)))

def closest_point_on_line(ax, ay, bx, by, px, py):
    """
    Calculate the closest point on a line defined by points A(ax, ay) and B(bx, by)
    to a point P(px, py).

    :param ax: x-coordinate of point A
    :param ay: y-coordinate of point A
    :param bx: x-coordinate of point B
    :param by: y-coordinate of point B
    :param px: x-coordinate of point P
    :param py: y-coordinate of point P
    :return: (qx, qy) coordinates of the closest point Q on the line to point P
    """

    # Vector AB
    abx, aby = bx - ax, by - ay

    # Vector AP
    apx, apy = px - ax, py - ay

    # Calculating the dot products
    ab_dot_ab = abx * abx + aby * aby
    ap_dot_ab = apx * abx + apy * aby

    # Calculating the ratio
    t = ap_dot_ab / ab_dot_ab

    # Finding the closest point Q
    qx = ax + t * abx
    qy = ay + t * aby

    return qx, qy
