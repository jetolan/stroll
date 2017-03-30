# Filename: placesAPI.py
# Description: contains functions that have to do with the Google Places API
################################################################################

### Libraries
import requests
import pandas as pd
import re
import time

### Google Places API Key
KEY="AIzaSyBBD7_aZuBAuYQ2bwnNFiKJzrA1qCyuu8E"

# Function: getPlaces
# Usage: getPlaces(lat_coord,long_coord,radius)
# Description: Takes in a desired latitude & longitude coordinates and a desired
# radius (in meters) and outputs a pandas dataframe of up to 60 open places in
# the area within the radius. This is because Google API only lets you get up to
# 60 places maximum.
################################################################################
def getPlaces(latitude,longitude,radius):
	places=[] # declare places matrix variable
	## Changes latitude, longitude to string and make Google API URL
	location=str(latitude)+","+str(longitude) #lat+long
	radius=str(radius) #in meters
	url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+location+"&radius="+radius+"&key="+KEY+"&hasNextPage=true&nextPage()=true&opennow=true"
	## Loop over pages to get information about open places
	while True:
		## Parse JSON file
		r = requests.get(url=url)
		item = r.json()
		## For each item: extract name, location and whether the place is open
		for shop in item['results']:
			name=str(shop.get('name','N/A')) #get name
			# Get Location:
			if 'geometry' in shop:
				location_str=str(shop['geometry'].get('location','N/A')).split(',')
				if 'lat' in location_str[0]:
					lat=re.sub('[^\-0-9.]','', location_str[0])
					long=re.sub('[^\-0-9.]','', location_str[1])
				else:
					long=re.sub('[^\-0-9.]','', location_str[0])
					lat=re.sub('[^\-0-9.]','', location_str[1])
			else:
				long='N/A'
				lat='N/A'
			# Get if place is open
			if 'opening_hours' in shop:
				open=str(shop['opening_hours'].get('open_now','N/A'))
			else:
				open='N/A'
			places.append([name,long,lat,open]) #append all the above info into places matrix
		## If there is a next page, update the JSON URL and continue loop, otherwise leave loop (see [1] for more details)
		if 'next_page_token' in item.keys():
			url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+location+"&radius="+radius+"&key="+KEY+"&hasNextPage=true&nextPage()=true&opennow=true&pagetoken="+item['next_page_token']
			time.sleep(2) #Need to add time for the request to work (see [2])
		else:
			break
	## Change places matrix into pandas data frame with sensible column names
	df = pd.DataFrame(places,columns=["Name","Longitude","Latitude", "Open Now"])
	return(df)

# [1] When you ask for a JSON request for Google places, it returns 20 places
#     and a "next page token". So in order to see the next page you have to use 
#     the same URL but add a "pagetoken" parameter and use the next page token 
#     from the previous page. The 3rd page does not have a next page token since
#     the Google Places API will return a maximum of 60 items. 
# [2] http://stackoverflow.com/questions/14056488/google-places-api-next-page-token-error