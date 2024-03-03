import numpy as np
import pandas as pd

import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm

# Plotting
import plotly.express as px

# Specify the coordinates (longitude, latitude) of origin and destination
# first parameter is latitude, second parameter is longitude

source = (40.42758062902799, -86.91323137300341) # WALC 
dest  = (40.42713523127093, -86.92142049541496)  # Windsor

start = "{},{}".format(source[1], source[0])
end = "{},{}".format(dest[1], dest[0])
# Service - 'route', mode of transportation - 'driving', without alternatives
url = 'http://router.project-osrm.org/route/v1/driving/{};{}?alternatives=true&annotations=nodes'.format(start, end)


headers = { 'Content-type': 'application/json'}
r = requests.get(url, headers = headers)
print("Calling API ...:", r.status_code) # Status Code 200 is success


routejson = r.json()
route_nodes = routejson['routes'][0]['legs'][0]['annotation']['nodes']
### keeping every third element in the node list to optimise time
route_list = []
for i in range(0, len(route_nodes)):
    if i % 2==1:
        route_list.append(route_nodes[i])

coordinates = []

for node in tqdm(route_list):
    try:
        url = 'https://api.openstreetmap.org/api/0.6/node/' + str(node)
        r = requests.get(url, headers = headers)
        myroot = ET.fromstring(r.text)
        for child in myroot:
            lat, long = child.attrib['lat'], child.attrib['lon']
        coordinates.append((lat, long))
    except:
        continue
print(coordinates[:10])
df_out = pd.DataFrame({'Node': np.arange(len(coordinates))})
df_out['coordinates'] = coordinates
df_out[['lat', 'long']] = pd.DataFrame(df_out['coordinates'].tolist())

# Converting Latitude and Longitude into float
df_out['lat'] = df_out['lat'].astype(float)
df_out['long'] = df_out['long'].astype(float)

# Plotting the coordinates on map
color_scale = [(0, 'red'), (1,'green')]
fig = px.line_mapbox(df_out, 
                        lat="lat", 
                        lon="long", 
                        zoom=8, 
                        height=600,
                        width=900)


fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()