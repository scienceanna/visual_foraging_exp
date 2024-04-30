library(tidyverse)

source("functions/import_data.R")

# import data as a list of two dataframes.
# d$stim contains all the stimulis info
# d$found contains the behavioural data
d <- import_data("test")