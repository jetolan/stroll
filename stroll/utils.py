'''

A collection of utils used for
Stroll prediction.

'''

import pandas as pd
import numpy as np
import datetime
from dateutil import parser
from geopy.geocoders import Nominatim


def read_crimes():
    df = pd.read_csv('data/SFPD_Incidents_-_from_1_January_2003.csv')

    return df


def find_meanlonlat():

    df = pd.read_csv('data/On-street_Parking_Supply.csv')

    linestring = df['Geom']

    # loop over segments, parsing the coordinate string
    fin = np.zeros((len(linestring), 2))
    for i in xrange(0, len(linestring)):
        fin[i, :] = parse_coordstring(linestring.iloc[i])

    # find the mean lat,lon and join to dataframe.
    # this is not accurate and should be improved!
    mean_latlon = {'meanlon': fin[:, 0], 'meanlat': fin[:, 1]}
    m_latlon = pd.DataFrame(mean_latlon)
    df = df.join(m_latlon)

    return df

#-----------------------------------------#


def parse_coordstring(str_in):

    # Remove the front and back of the string
    lhs, rhs = str_in.split("LINESTRING (", 2)
    lrhs, dum = rhs.split(")", 2)

    # Split up into pairs of coords
    pairs = lrhs.split(",", lrhs.count(','))

    # loop over string pairs
    array1 = np.zeros((2, lrhs.count(',')))
    for i in xrange(0, lrhs.count(',')):
        l_out = np.fromstring(pairs[i], dtype=float, sep=' ')
        array1[:, i] = np.transpose(l_out)

    ave_coord = np.mean(array1, 1)
    string_out = ave_coord

    return string_out


#-----------------------------------------#


def convert_address(address):
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    out_lat = location.latitude
    out_lon = location.longitude
    return out_lat, out_lon

#-----------------------------------------#


def grid_of_segments(in_lat, in_lon):
    '''
    Given an input latitude and longitude, find
    a square grid of coordinates around it with id's

    Parameters:
    ------------
    in_lat:float
    in_lon:float

    Returns:
    -----------
    out_segments: DataFrame
        Pandas DataFrame with one row per block

    '''
    # define our field of view
    # this is optimized for desktop wider screens
    field_of_view_lon = 0.008
    field_of_view_lat = 0.004
    minlat = in_lat - field_of_view_lat / 2
    maxlat = in_lat + field_of_view_lat / 2
    minlon = in_lon - field_of_view_lon / 2
    maxlon = in_lon + field_of_view_lon / 2

    # grab the coordinates
    df = find_meanlonlat()

    # limit the street centers to our area
    A = df['meanlon'] > minlon
    B = df['meanlon'] < maxlon
    C = df['meanlat'] > minlat
    D = df['meanlat'] < maxlat

    found_indices = A * B * C * D
    out_segments = df[found_indices]

    # limit crimes to fov too
    df = read_crimes()
    A = df['X'] > minlon
    B = df['X'] < maxlon
    C = df['Y'] > minlat
    D = df['Y'] > maxlat

    found_indices = A * B * C * D
    out_crimes = df[found_indices]

    # now assign crimes to each of the blocks
    lats = np.array(out_segments.meanlat)
    lons = np.array(out_segments.meanlon)
    num_crimes = np.zeros(len(out_segments))
    for i in range(len(out_crimes)):
        lon = out_crimes['X'].iloc[i]
        lat = out_crimes['Y'].iloc[i]
        dist = np.sqrt(np.square(lats - lats) + np.square(lon - lons))
        ind = np.argmin(dist)
        num_crimes[ind] += 1

    num_crimes = pd.DataFrame({"num_crimes": num_crimes})
    out_segments.reset_index(inplace=True)
    out_segments = out_segments.join(num_crimes)

    return out_segments

    #------------------------------#


def make_grid_of_scores(in_time, in_address):
    '''
    Parameters:
    ------------
    in_time: str
             Time, flexible formatting
    in_address: str
             Address, flexible formatting

    Returns:
    ------------
    df: pandas DataFrame


    '''
    # get the time parsed
    if in_time == "now" or in_time == "Now":
        ntime = datetime.datetime.now()
    else:
        ntime = parser.parse(in_time)

    # get the location (can be coordinates or street address)
    [out_lat, out_lon] = convert_address(in_address)

    # get grid of segments
    segments = grid_of_segments(out_lat, out_lon)

    # loop over segems, get scores
    # this loop is slow... vectorize?
    business_score = []
    crime_score = []
    for i in range(len(segments)):

        # this is the business scode (right now it is one)
        business_score.append(1)
        # this is crime score
        crime_score.append(segments.num_crimes.iloc[i])

    # calculate combined score... high number is less safe
    score = score_combine(business_score, crime_score)

    # take score and put in dataframe
    df_score = pd.DataFrame(score, columns=['score'])

    # join with grid of segments
    segments = segments.join(df_score)

    # drop parking_supply from segements
    segments = segments.drop('Parking Supply', axis=1)

    out_segments = segments.rename(
        columns={'meanlat': 'lat', 'meanlon': 'lon', 'score': 'weight'})

    out_segments = out_to_javascript(out_segments)

    loc_out = 'new google.maps.LatLng(' + \
        str(out_lat) + ',' + str(out_lon) + ')'

    coord_out = '{lat: ' + str(out_lat) + ',  lng: ' + str(out_lon) + '};'

    return out_segments, loc_out, coord_out


#-------------------------------------------------#
def out_to_javascript(out):
    out_str = "["
    for i in range(len(out)):

        # this is data we want
        lat = out.iloc[i].lat
        lon = out.iloc[i].lon
        weight = out.iloc[i].weight

        # may want to exponentially scale weight for visualization
        weight = weight**3

        # write strings for javascript
        out_str = out_str + '{location: new google.maps.LatLng(' + str(
            lat) + ',' + str(lon) + '), weight: ' + str(weight) + '}, '
    out_str = out_str + ']'
    return out_str

#-------------------------------------------------#


def score_combine(business_score, crime_score):
    # combines vectors of score types into one final score per segment
    # will add more input vectors

    # In case we aren't numpy arrays
    business_score = np.array(business_score)
    crime_score = np.array(crime_score)

    # Start with the score=1
    score = 1

    # add to score for crimes
    score = score + crime_score

    # divide by business_score
    score = score / business_score

    # we shouldn't have any scores <0
    score[np.where(score < 0)] = 0

    # get rid of nan
    score[np.isnan(score)] = 0

    return score


if __name__ == "__main__":

    in_time = 'Now'
    in_address = '37.72, -122.37'
    #out_segments, loc_out, coord_out = make_grid_of_scores(in_time, in_address)

    in_lat = 37.72
    in_lon = -122.37
    out_segments = grid_of_segments(in_lat, in_lon)
