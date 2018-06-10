# Execute the 2nd line to run this script
# python temperature_correlation.py stations.json.gz city_data.csv output.svg

import sys
import pandas as pd
import difflib
import numpy as np
import gzip
import matplotlib.pyplot as plt

stations_filename = sys.argv[1]
city_data_filename = sys.argv[2]
output_name = sys.argv[3]
station_fh = gzip.open(stations_filename, 'rt', encoding='utf-8')
stations = pd.read_json(station_fh, lines=True)
city = pd.read_csv(city_data_filename)

# stations format (avg_tmax need to be divided by 10), 9149 rows 
"""
        avg_tmax  elevation  latitude  longitude  observations      station
0     102.016667      691.0   54.4500  -124.2833           300  CA001092970
1     139.309375      967.0   50.0333  -113.2167           320  CA003030529
"""
stations['avg_tmax'] /= 10


# city format (area needs to be divided by 10^6 bc m2 covert to km2)
"""
                name        population       area   latitude   longitude
0        Airdrie, Alberta         NaN          NaN  51.291700 -114.014000
1                  Brooks         NaN          NaN  50.564167 -111.898889
2                 Calgary   1096833.0  825290000.0  51.054444 -114.066944
side note:
a) There are many cities that are missing either their area or population: 
we can't calculate density for those, so they can be removed. 
Population density is population divided by area.
b) exclude cities with area greater than 10000 km².
"""
city['area'] /= 10**6
city = city[~np.isnan(city['population'])] # ~ is the NOT operator
city = city[~np.isnan(city['area'])]
city = city[city['area'] <= 10000]
city = city[~np.isnan(city['latitude'])]
city = city[~np.isnan(city['longitude'])]

def distance(city, stations):
    # calculates the distance between one city and every station
    lat1, lon1 = city.loc['latitude'], city.loc['longitude']
    lat2, lon2 = stations['latitude'].values, stations['longitude'].values
    p = 0.017453292519943295     #Pi/180
    a = 0.5 - np.cos((lat2 - lat1) * p)/2 + np.cos(lat1 * p) * np.cos(lat2 * p) * (1 - np.cos((lon2 - lon1) * p)) / 2
    return 12742 * np.arcsin(np.sqrt(a)) #2*R*asin...  distance in KM

def best_tmax(city, stations):
    # returns the best value you can find for 'avg_tmax' for that one city, from the list of all weather stations
    distance_to_stations = distance(city, stations)
    return stations.loc[np.argmin(distance_to_stations)]['avg_tmax']


city['temperature'] = city.apply(best_tmax, axis=1, stations=stations)
city['density'] = city['population'] / city['area']
city.to_csv('output2.csv')

# scatter plot, x - temperature, y - density
plt.scatter(city['temperature'], city['density'])
plt.title('Temperature vs Population Density')
plt.xlabel('Avg Max Temperature (\u00b0C)')
plt.ylabel('Population Density (people/km\u00b2)')
plt.savefig(output_name)