# This is highest level function for stroll
#
# Inputs: are string of time and string of location
#
# Outputs: a data frame of parking coordinates and parking score
#         data is also written to scores_temp.csv
#
# This function relies on having postgres database up and running
# and will need to have the username & pswd changed in parking_utils
#
#
#
#
#------------------------#
# all functions are contained here:
from stroll import utils


# where are we
in_address = "Elixir, San Francisco CA"
#in_address="37.760605, -122.432334"

# when are we
in_time = "2016 June 21 4pm"
# in_time="Now"

# make a grid of scores around this location
out_segments, loc_out, coord_out = utils.make_grid_of_scores(
    in_time, in_address)
