'''

A collection of utils used for
Stroll prediction.

TODO:ADD DOCUMENTATION!!!!!

'''

import pandas as pd
import numpy as np
from dateutil import parser
from geopy.geocoders import Nominatim
from stroll.placesAPI import getPlaces


def read_crimes():
    df = pd.read_csv('data/SFPD_Incidents_-_from_1_January_2003.csv')

    df['lon']=df['X']
    df['lat']=df['Y']
    df.drop(['X','Y'], axis=1, inplace=True)
    return df
    


def find_meanlonlat():

    df = pd.read_csv('data/On-street_Parking_Supply.csv')

    linestring = df['Geom']

    # loop over segments, parsing the coordinate string
    fin = np.zeros((len(linestring), 2))
    for i in range(0, len(linestring)):
        fin[i, :] = parse_coordstring(linestring.iloc[i])

    # find the mean lat,lon and join to dataframe.
    # this is not accurate and should be improved!
    mean_latlon = {'lon': fin[:, 0], 'lat': fin[:, 1]}
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
    for i in range(0, lrhs.count(',')):
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


def limit_df(df, in_lat, in_lon):
    '''
    Given an input latitude and longitude, find
    a square grid of coordinates around it with id's

    The right thing to use for this is probably geoPandas

    Parameters:
    ------------
    df:DataFrame
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


    # limit the street centers to our area
    A = df['lon'] > minlon
    B = df['lon'] < maxlon
    C = df['lat'] > minlat
    D = df['lat'] < maxlat

    found_indices = A * B * C * D
    out_segments = df[found_indices]

    return out_segments
    
def create_segments(df, segments):
    '''
    Takes df of values (ie crimes) and bins into street blocks 
    in segments

    Parameters:
    ---------
    df: DataFrame
       Data to be binned
       Contains keys ['value', 'lon', 'lat']

    Outputs:
    --------
    segments: DataFrame
    '''

    #EACH SEGMENT SHOULD HAVE A UNIQUE ID AND THE OUTPUT FROM THIS FUNCTION
    #WILL CONTAIN UNIQUE IDS
    
    # now assign crimes to each of the blocks
    lats = np.array(segments.lat)
    lons = np.array(segments.lon)
    num = np.zeros(len(segments))
    for i in range(len(df)):
        lon = df['lon'].iloc[i]
        lat = df['lat'].iloc[i]
        dist = np.sqrt(np.square(float(lat) - lats) + np.square(float(lon) - lons))
        ind = np.argmin(dist)
        num[ind] += 1

    num = pd.DataFrame({"num": num})
    segments.reset_index(inplace=True)
    segments = segments.join(num)

    return segments

    #------------------------------#


def make_grid_of_scores(in_address):
    '''
    Parameters:
    ------------
    in_address: str
             Address, flexible formatting

    Returns:
    ------------
    df: pandas DataFrame


    '''
    # get the location (can be coordinates or street address)
    [out_lat, out_lon] = convert_address(in_address)

    #grab blocks & limit to desired area
    df=find_meanlonlat()
    segments= limit_df(df, out_lat, out_lon)

    #grab crimes and limit to desired area
    df=read_crimes()
    crimes=limit_df(df, out_lat, out_lon)

    #grab business and limit to radius
    radius=500
    businesses=getPlaces(out_lat, out_lon, radius)

    #now bin
    crime_segments=create_segments(crimes, segments)
    business_segments=create_segments(businesses,segments)
    
    # loop over segems, get scores
    # this loop is slow... vectorize?
    business_score = []
    crime_score = []
    for i in range(len(segments)):

        # this is the business score
        business_score.append(business_segments.num.iloc[i])
        # this is crime score
        crime_score.append(crime_segments.num.iloc[i])

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
        weight = weight**1

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
    #score = 1

    # add to score for crimes
    #score = score + crime_score

    # divide by business_score
    #score = score / business_score

    #score is just business score for now...
    score=business_score
    
    # we shouldn't have any scores <0
    score[np.where(score < 0)] = 0

    # get rid of nan
    score[np.isnan(score)] = 0

    return score


if __name__ == "__main__":

    in_address = '37.72, -122.37'
    out_segments, loc_out, coord_out = make_grid_of_scores(in_address)

    #in_lat = 37.72
    #in_lon = -122.37
    #out_segments,_,_ = make_grid_of_scores(in_address)
