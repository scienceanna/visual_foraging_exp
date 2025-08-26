# import some libraries from PsychoPy
from psychopy.event import Mouse
from psychopy.hardware import keyboard
import pandas as pd
import random
import os.path
from block import *


class Experiment():
    def __init__(self, exp_name):
        
        # First, set up experiment
        print("*** Setting up experiment ***")
        
        # Create output folders
        self.exp_name = exp_name
        self.exp_folder = "exp_config/" + exp_name + "/"
        self.data_folder = "data/" + exp_name + "/"
        
        # does the data folder already exist?
        isExist = os.path.exists(self.data_folder)
        if not isExist:
               os.makedirs(self.data_folder)
               print("A new data directory has been created")

        # Ask for person demograpics (pop-up window)
        self.person = self.collect_person_info() 
        self.p_id = self.person.pop("Participant number")
        self.age = self.person.pop("Age")
        self.gender = self.person.pop("Gender")

        # Setting up experimental files
        self.date = data.getDateStr()
        self.fileName = str(self.p_id) + "_" + str(self.age) + "_" + str(self.gender) + "_" + self.date
        
        # this tracks the behaviour. I.e., the items that were selected
        # this corresponds to d$found in the FoMo import code
        self.dataFile = open(self.data_folder + self.fileName+'_found.csv', 'w') 
        self.dataFile.write('person,block,condition,trial,attempt,id,found,score,item_class,x,y,rt\n') 
        
        # this stores information on the stimulus (including items that were never selected)
        # this corresponds to d$stim in the FoMo import code
        self.dataFileStim = open(self.data_folder + self.fileName+'_stim.csv', 'w')
        self.dataFileStim.write('person,block,condition,trial,attempt,id,item_class,x,y\n') # this is d$stim
        
        # import exp config - this is saved in a csv
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
        
        # import conditions - this is saved in a csv file
        self.conditions = self.get_conditions()
        
        # read in blocks, and pblocks (pblocks may be empty)
        self.blocks = self.get_blocks(False)
        if os.path.isfile(self.exp_folder+"pblocks.csv"):
            self.pblocks = self.get_blocks(practice = True)

        # set up eye tracking, if using
        if self.track_eyes == "track":
            print("we are going to eyetrack")
            from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
            import pylink as pl
            # connect to eyelink host pc
            self.el_tracker = pl.EyeLink("100.1.1.1")
            # open edf data file - need to decide what we should call edf files
            self.edf_fname = self.p_id
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
        
        if dictDlg.OK:  # or if ok_data is not None
            return(info)
        else:
            print('user cancelled')
            core.quit()
        
    def import_exp_config(self):

            # read in config file
            exp_config = pd.read_csv(self.exp_folder+"exp_config.csv")
            # save config file to person folder
            exp_config.to_csv(self.data_folder + self.fileName + '_exp_config.csv')
            exp_config = exp_config.set_index("attribute").T # transpose

            self.scrn_height = int(exp_config["scrn_height"].iloc[0])
            self.scrn_width = int(exp_config["scrn_width"].iloc[0])

            self.height_border = int(exp_config["height_border"].iloc[0])
            self.width_border = int(exp_config["width_border"].iloc[0])
            
            self.jiggle = int(exp_config["jiggle"].iloc[0])

            self.intro_expt = exp_config["intro_expt"].iloc[0]
            self.outro_expt = exp_config["outro_expt"].iloc[0]

            self.block_style = exp_config["block_style"].iloc[0]
            self.global_practice = exp_config["global_practice"].iloc[0]

            self.track_eyes = exp_config["track_eyes"].iloc[0]
            self.screenshot = exp_config["screenshot"].iloc[0]

    def run(self):

        # this is where we run the experiment!
        # in short, we run each block, one at a time

        print("*** running experiment with", len(self.blocks), " blocks ***")

        for block in self.blocks:

            # calibrate eye tracker, if doing eye tracking
            if self.track_eyes == "track":

                self.el_tracker.doTrackerSetup()
                # make sure mouse is visible
                self.win.mouseVisible = True

            print("about to run block " + block.label)
            # run the block    
            block.run(self)
        
        # Experiment is now complete:
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
        
        # display outro text
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
            block = Block(block_file["label"].iloc[blk], block_file["conditions"].iloc[blk], block_file["n_trials_per_cond"].iloc[blk], block_file["group"].iloc[blk], block_file["intro_text"].iloc[blk], block_file["outro_text"].iloc[blk], block_file["practice"].iloc[blk], self)
            
            if self.block_style == "counter_balanced":
                if block_file["group"].iloc[blk] == "1":
                    blocks_one.append(block)
                elif block_file["group"].iloc[blk] == "2":
                    blocks_two.append(block)
                else:
                    blocks.append(block)
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
                if int(self.p_id) % 2 == 0:
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
        