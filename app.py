import os
from flask import Flask, render_template, request, redirect

import numpy as np
import pandas as pd

import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm

from jinja2 import Template

# Plotting
import plotly.express as px

coord_dict = {'Meredith': [40.42638099306333, -86.92326699229753],
              'Meredith South': [40.42560040207003, -86.92337155604474],
              'Windsor': [40.426368102523114, -86.9210074161813],
              'Cary': [40.43198324155161, -86.91848293661857],
              'McCutcheon': [40.42485306592721, -86.9281869805071],
              'Tarkington': [40.43088959355467, -86.92072046666556]}

def create_route_map(sourceLat, sourceLong, destLat, destLong):
   source = (sourceLat, sourceLong) # Knoxville
   dest  = (destLat, destLong)  # New York City


   start = "{},{}".format(source[1], source[0])
   end = "{},{}".format(dest[1], dest[0])
   # Service - 'route', mode of transportation - 'driving', without alternatives
   url = 'http://router.project-osrm.org/route/v1/driving/{};{}?alternatives=false&annotations=nodes'.format(start, end)




   headers = { 'Content-type': 'application/json'}
   r = requests.get(url, headers = headers)
   print("Calling API ...:", r.status_code) # Status Code 200 is success




   routejson = r.json()
   route_nodes = routejson['routes'][0]['legs'][0]['annotation']['nodes']


   ### keeping every third element in the node list to optimise time
   route_list = []
   for i in range(0, len(route_nodes)):
       if i % 3==1:
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
   fig = px.scatter_mapbox(df_out,
                           lat="lat",
                           lon="long",
                           zoom=8,
                           height=600,
                           width=900)




   fig.update_layout(mapbox_style="open-street-map")
   fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
   return fig

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/showMap',methods=["POST", "GET"])
    def showMap():
        source = request.form['fname1']
        dest = request.form['fname2']

        for key in coord_dict.keys():
            if(key == source):
                sourceLat = coord_dict[key][0]
                sourceLong = coord_dict[key][1]
            if(key == dest):
                destLat = coord_dict[key][0]
                destLong = coord_dict[key][1]

        map = create_route_map(sourceLat, sourceLong, destLat, destLong)
        output_html_path="templates/map.html"
        input_template_path = "templates/template.html"

        plotly_jinja_data = {"fig":map.to_html(full_html=False)}
        #consider also defining the include_plotlyjs parameter to point to an external Plotly.js as described above

        with open(output_html_path, "w", encoding="utf-8") as output_file:
            with open(input_template_path) as template_file:
                j2_template = Template(template_file.read())
                output_file.write(j2_template.render(plotly_jinja_data))

        return render_template(output_html_path)

        #return render_template('map.html', map=map)

    return app