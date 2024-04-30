import_data <- function(exp_name) {
  
  found_spec <- cols(
    person = col_character(),
    block = col_character(),
    condition = col_character(),
    trial = col_double(),
    attempt = col_double(),
    id = col_double(),
    found = col_double(),
    score = col_double(),
    item_class = col_character(),
    x = col_double(),
    y = col_double(),
    rt = col_double())
  
  stim_spec <- cols(
    person = col_character(),
    block = col_character(),
    condition = col_character(),
    trial = col_double(),
    attempt = col_double(),
    id = col_double(),
    item_class = col_character(),
    x = col_double(),
    y = col_double()
  )
  
  # should read in all csvs
  exp_folder <- paste0("../data/", exp_name)
  p_files <- dir(exp_folder)
  
  # we only want the *_stim and *_found files
  stim_files <- p_files[str_detect(p_files, "stim")]
  found_files <- p_files[str_detect(p_files, "found")]
 
  # read in all the data files
  d_found <- read_in_files(found_files, found_spec)
  d_stim <- read_in_files(stim_files, stim_spec)
  
  d_found  %>%
    select( person = "person", condition, trial = "trial",  
           id = "id", found = "found", item_class = "item_class",
           x = "x", y = "y")  -> d_found
  
  d_stim  %>%
    select(person = "person", condition, trial = "trial",  
           id = "id", item_class = "item_class",
           x = "x", y = "y") -> d_stim
  

  return(list(stim = d_stim,
              found = d_found))
}

fix_person_and_trial <- function(d) {
  
  # first arrange data so it has all of person 1, then person 2, etc
  d %>% arrange(person, condition, trial) -> d
  
  # make sure the person index goes from 1 to N with no missing people
  d$person <- as_factor(d$person)
  levels(d$person) <- 1:length(levels(d$person))
  d$person <- as.numeric(d$person)
  
  # make sure trial number is unique over people and conditions
  # save the old trial info in trial_p
  d %>% mutate(
    trial_p = trial,
    trial = paste(as.numeric(person), as.numeric(condition), trial),
    trial = as_factor(trial),
    trial = as.numeric(trial)) -> d
  
  return(d)
  
}

read_in_files <- function(my_files, spec) {
  
  ##############################
  # first, read in all files
  ##############################
  
  d_out <- tibble()
  
  for (pp in 1:length(my_files)) {
    
    d <- read_csv(paste0(exp_folder, "/", my_files[pp]), col_types = spec)
    
    d_out <- bind_rows(d_out, d)
    
  }
  
  ##############################
  # now tidy up before we output
  ##############################
 
  d_out %>% 
    mutate(
      # recode person to be a number
      person = parse_number(person), 
      # start trial counter at 1 rather than 0
      trial = trial + 1,
      # item_class & condition to factors
      item_class =factor(item_class),
      condition = as.factor(condition)) %>% 
    # take only the highest number attempt 
    # (this needs checking with a dataset with some mistakes)
    group_by(person, condition, trial) %>%
    filter(attempt == max(attempt)) -> d_out
  
  # make sure person IDs run 1, 2, .... N with no missing IDs
  # make sure trial number is unique
  d_out <- fix_person_and_trial(d_out)
  
}
