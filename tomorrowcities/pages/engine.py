import solara
import time
import random
import json
import pandas as pd
import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
from typing import Tuple, Optional
import ipyleaflet
from ipyleaflet import AwesomeIcon, Marker
import numpy as np
import rasterio 
from rasterio.warp import calculate_default_transform, reproject, Resampling
import io
import xml
import logging, sys
#logging.basicConfig(stream=sys.stderr, level=logging.INFO)

from ..backend.engine import compute, compute_power_infra, calculate_metrics


layers = solara.reactive({
    'layers' : {
        'building': {
            'render_order': 50,
            'map_info_tooltip': 'Number of buildings',
            'data': solara.reactive(None),
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {'ds': 0, 'metric1': 0, 'metric2': 0, 'metric3': 0,'metric4': 0, 'metric5': 0,'metric6': 0,'metric7': 0},
            'attributes_required': set(['residents', 'fptarea', 'repvalue', 'nhouse', 'zoneid', 'expstr', 'bldid', 'geometry', 'specialfac']),
            'attributes': set(['residents', 'fptarea', 'repvalue', 'nhouse', 'zoneid', 'expstr', 'bldid', 'geometry', 'specialfac'])},
        'landuse': {
            'render_order': 20,
            'map_info_tooltip': 'Number of landuse zones',
            'data': solara.reactive(None),
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['geometry', 'zoneid', 'luf', 'population', 'densitycap', 'avgincome']),
            'attributes': set(['geometry', 'zoneid', 'luf', 'population', 'densitycap', 'floorarat', 'setback', 'avgincome'])},
        'household': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of households',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required':set(['hhid', 'nind', 'income', 'bldid', 'commfacid']),
            'attributes':set(['hhid', 'nind', 'income', 'bldid', 'commfacid'])},
        'individual': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of individuals',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['individ', 'hhid', 'gender', 'age', 'eduattstat', 'head', 'indivfacid']),
            'attributes': set(['individ', 'hhid', 'gender', 'age', 'eduattstat', 'head', 'indivfacid'])},
        'intensity': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of intensity measurements',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['geometry','im']),
            'attributes': set(['geometry','im'])},
        'fragility': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of records in fragility configuration',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['expstr','muds1_g','muds2_g','muds3_g','muds4_g','sigmads1','sigmads2','sigmads3','sigmads4']),
            'attributes': set(['expstr','muds1_g','muds2_g','muds3_g','muds4_g','sigmads1','sigmads2','sigmads3','sigmads4'])},
        'vulnerability': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of records in vulnerabilty configuration',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['expstr', 'hw0', 'hw0_5', 'hw1', 'hw1_5', 'hw2', 'hw3', 'hw4', 'hw5','hw6']),
            'attributes': set(['expstr', 'hw0', 'hw0_5', 'hw1', 'hw1_5', 'hw2', 'hw3', 'hw4', 'hw5','hw6'])},
        'gem_vulnerability': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of functions in gem vulnerabilty',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['id', 'assetCategory', 'lossCategory', 'description', 'vulnerabilityFunctions']),
            'attributes': set(['id', 'assetCategory', 'lossCategory', 'description', 'vulnerabilityFunctions']),
        },
        'power nodes': {
            'render_order': 90,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of electrical power nodes',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {'ds': 0, 'is_damaged': False, 'is_operational': True},
            'attributes_required': set(['geometry', 'node_id', 'pwr_plant', 'n_bldgs', 'eq_vuln']),
            'attributes': set(['geometry', 'fltytype', 'strctype', 'utilfcltyc', 'indpnode', 'guid', 
                         'node_id', 'x_coord', 'y_coord', 'pwr_plant', 'serv_area', 'n_bldgs', 
                         'income', 'eq_vuln'])},
        'power edges': {
            'render_order': 80,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of connections in power grid',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['geometry','from_node','to_node', 'edge_id']),
            'attributes': set(['from_node', 'direction', 'pipetype', 'edge_id', 'guid', 'capacity', 
                         'geometry', 'to_node', 'length'])},
        'power fragility': {
            'render_order': 0,
            'data': solara.reactive(None),
            'map_info_tooltip': 'Number of records in fragility configuration for power',
            'map_layer': solara.reactive(None),
            'force_render': solara.reactive(False),
            'visible': solara.reactive(False),
            'extra_cols': {},
            'attributes_required': set(['vuln_string', 'med_slight', 'med_moderate', 'med_extensive', 'med_complete', 
                         'beta_slight', 'beta_moderate', 'beta_extensive', 'beta_complete']),
            'attributes': set(['vuln_string', 'med_slight', 'med_moderate', 'med_extensive', 'med_complete', 
                         'beta_slight', 'beta_moderate', 'beta_extensive', 'beta_complete', 'description'])}
            },
    'center': solara.reactive((41.01,28.98)),
    'selected_layer' : solara.reactive(None),
    'render_count': solara.reactive(0),
    'bounds': solara.reactive(None),
    'policies': {
        '1': {'id':1, 'label': 'P1', 'description': 'Land and tenure security program', 'applied': solara.reactive(False)},
        '2': {'id':2, 'label': 'P2', 'description': 'State-led upgrading/retrofitting of low-income/informal housing', 'applied': solara.reactive(False)},
        '3': {'id':3, 'label': 'P3', 'description': 'Robust investment in WASH (water, sanitation and hygiene) and flood-control infrastructure', 'applied': solara.reactive(False)},
        '4': {'id':4, 'label': 'P4', 'description': 'Investments in road networks and public spaces through conventional paving', 'applied': solara.reactive(False)},
        '5': {'id':5, 'label': 'P5', 'description': 'Shelter Law - All low-income and informal settlements should have physical and free access to community centres and shelters', 'applied': solara.reactive(False)},
        '6': {'id':6, 'label': 'P6', 'description': 'Funding community-based networks in low-income areas (holistic approaches)', 'applied': solara.reactive(False)},
        '7': {'id':7, 'label': 'P7', 'description': 'Urban farming programs', 'applied': solara.reactive(False)},
        '8': {'id':8, 'label': 'P8', 'description': 'Emergency cash transfers to vulnerable households', 'applied': solara.reactive(False)},
        '9': {'id':9, 'label': 'P9', 'description': 'Waste collection and rivers cleaning program ', 'applied': solara.reactive(False)},
        '10': {'id':10, 'label': 'P10', 'description': 'Enforcement of environmental protection zones', 'applied': solara.reactive(False)},
    },
    'implementation_capacity_score': solara.reactive("high"),
    'map_info_button': solara.reactive("summary"),
    'map_info_detail': solara.reactive({}),
    'metrics': {
        "metric1": {"desc": "Number of workers unemployed", "value": 0, "max_value": 100},
        "metric2": {"desc": "Number of children with no access to education", "value": 0, "max_value": 100},
        "metric3": {"desc": "Number of households with no access to hospital", "value": 0, "max_value": 100},
        "metric4": {"desc": "Number of individuals with no access to hospital", "value": 0, "max_value": 100},
        "metric5": {"desc": "Number of households displaced", "value": 0, "max_value": 100},
        "metric6": {"desc": "Number of homeless individuals", "value": 0, "max_value": 100},
        "metric7": {"desc": "Population displacement", "value": 0, "max_value":100},}})


def building_colors(feature):
    ds_to_color = {0: 'lavender', 1:'violet',2:'fuchsia',3:'indigo',4:'darkslateblue',5:'black'}
    ds = feature['properties']['ds'] 
    return {'fillColor': 'black', 'color': 'red' if ds > 0 else 'blue' }

def building_click_handler(event=None, feature=None, id=None, properties=None):
    layers.value['map_info_detail'].set(properties)
    layers.value['map_info_button'].set("detail")  
    layers.value['map_info_force_render'].set(True)  

def landuse_click_handler(event=None, feature=None, id=None, properties=None):
    layers.value['map_info_detail'].set(properties)
    layers.value['map_info_button'].set("detail")  
    layers.value['map_info_force_render'].set(True)  

def landuse_colors(feature):
    print(feature)
    luf_type = feature['properties']['luf']
    if luf_type == 'RESIDENTIAL (HIGH DENSITY)':
        luf_color = {
        'color': 'black',
        'fillColor': '#A0522D', # sienna
        }    
    elif luf_type == 'HISTORICAL PRESERVATION AREA':
        luf_color = {
        'color': 'black',
        'fillColor': '#673147', # plum
        }    
    elif luf_type == 'RESIDENTIAL (MODERATE DENSITY)':
        luf_color = {
        'color': 'black',
        'fillColor': '#cd853f', # peru
        }   
    elif luf_type == 'COMMERCIAL AND RESIDENTIAL':
        luf_color = {
        'color': 'black',
        'fillColor': 'red',
        }   
    elif luf_type == 'CITY CENTER':
        luf_color = {
        'color': 'black',
        'fillColor': '#E6E6FA', # lavender
        }   
    elif luf_type == 'INDUSTRY':
        luf_color = {
        'color': 'black',
        'fillColor': 'grey',
        }   
    elif luf_type == 'RESIDENTIAL (LOW DENSITY)':
        luf_color= {
        'color': 'black',
        'fillColor': '#D2B48C', # tan
        }   
    elif luf_type == 'RESIDENTIAL (GATED NEIGHBORHOOD)':
        luf_color= {
        'color': 'black',
        'fillColor': 'orange',
        }   
    elif luf_type == 'AGRICULTURE':
        luf_color= {
        'color': 'black',
        'fillColor': 'yellow',
        }   
    elif luf_type == 'FOREST':
        luf_color= {
        'color': 'black',
        'fillColor': 'green',
        }   
    elif luf_type == 'VACANT ZONE':
        luf_color = {
        'color': 'black',
        'fillColor': '#90EE90', # lightgreen
        }   
    elif luf_type == 'RECREATION AREA':
        luf_color = {
        'color': 'black',
        'fillColor': '#32CD32', #lime
        }   
    else:
        luf_color = {
        'color': 'black',
        'fillColor': random.choice(['red', 'yellow', 'green', 'orange','blue']),
        } 
    return luf_color

def power_node_colors(feature):
    print(feature)
    ds_to_color = {0: 'lavender', 1:'violet',2:'fuchsia',3:'indigo',4:'darkslateblue',5:'black'}
    ds = random.randint(0,5) #feature['properties']['ds'] 
    return {'color': ds_to_color[ds], 'fillColor': ds_to_color[ds]}

def create_map_layer(df, name):
    if df is None:
        return None 
    if "geometry" not in list(df.columns):
        return None 
    
    if name not in layers.value['layers'].keys():
        return None
    
    existing_map_layer = layers.value['layers'][name]['map_layer'].value
    if existing_map_layer is not None and not layers.value['layers'][name]['force_render'].value:
        return existing_map_layer
    
    if name == "intensity":
        # Take the largest 500_000 values to display
        df_limited = df.sort_values(by='im',ascending=False).head(500_000)
        locs = np.array([df_limited.geometry.y.to_list(), df_limited.geometry.x.to_list(), df_limited.im.to_list()]).transpose().tolist()
        map_layer = ipyleaflet.Heatmap(locations=locs, radius = 10) 
    elif name == "landuse":
        map_layer = ipyleaflet.GeoJSON(data = json.loads(df.to_json()),
            style={'opacity': 1, 'dashArray': '9', 'fillOpacity': 0.5, 'weight': 1},
            hover_style={'color': 'white', 'dashArray': '0', 'fillOpacity': 0.5},
            style_callback=landuse_colors)
        map_layer.on_click(building_click_handler)   
    elif name == "building":
        map_layer = ipyleaflet.GeoJSON(data = json.loads(df.to_json()),
            style={'opacity': 1, 'dashArray': '9', 'fillOpacity': 0.5, 'weight': 1},
            hover_style={'color': 'white', 'dashArray': '0', 'fillOpacity': 0.5},
            style_callback=building_colors)
        map_layer.on_click(landuse_click_handler)
    
    elif name == "power nodes":
        markers = []
        for index, node in df.iterrows():
            x = node.geometry.x
            y = node.geometry.y
            marker_color = 'blue' if node['is_operational'] else 'red'
            icon_name = 'fa-industry' if node['pwr_plant'] == 1 else 'bolt'
            icon_color = 'black'
            marker = Marker(icon=AwesomeIcon(
                        name=icon_name,
                        marker_color=marker_color,
                        icon_color=icon_color,
                        spin=False
                    ),location=(y,x),title=f'{node["node_id"]}')

            markers.append(marker)
        map_layer= ipyleaflet.MarkerCluster(markers=markers,
                                                   disable_clustering_at_zoom=5)
        
        
    else:
        map_layer = ipyleaflet.GeoData(geo_dataframe = df)
    layers.value['layers'][name]['map_layer'].set(map_layer)
    layers.value['layers'][name]['force_render'].set(False)
    return map_layer

def fast_transform_xy(T,x,y):
    TI = rasterio.transform.IDENTITY.translation(0.5, 0.5)
    TI_mat = np.array([[TI[0],TI[1],TI[2]],[TI[3],TI[4],TI[5]]])
    T_mat = np.array([[T[0],T[1],T[2]],[T[3],T[4],T[5]]])
    n = len(x)
    first_input = np.ones((3,n))
    first_input[0,:] = x
    first_input[1,:] = y
    first_pass = np.dot(TI_mat, first_input)
    second_inp = np.concatenate([first_pass[[1]],first_pass[[0]],first_input[[2]]])    
    second_pass = np.dot(T_mat, second_inp)
    return second_pass[0], second_pass[1]

def read_tiff(file_bytes):
    byte_io = io.BytesIO(file_bytes)
    with rasterio.open(byte_io) as src:
        ims = src.read()
    
    current_crs = src.crs
    target_crs = 'EPSG:4326'
    transform, width, height = calculate_default_transform(current_crs, target_crs, src.width, src.height, *src.bounds)
    ims_transformed = np.zeros((height, width))

    print('start reproject ..........')
    reproject(
        source=ims[0],
        destination=ims_transformed,
        src_transform=src.transform,
        src_crs=current_crs,
        dst_transform=transform,
        dst_crs=target_crs,
        resampling=Resampling.nearest)


    lon_pos, lat_pos = np.meshgrid(range(width),range(height))
    print('start transform ..........')
    #lon, lat = rasterio.transform.xy(transform,lat_pos.flatten(),lon_pos.flatten())
    lon, lat = fast_transform_xy(transform,lat_pos.flatten(),lon_pos.flatten())
    print('start dataframe ..........')
    gdf = gpd.GeoDataFrame(ims_transformed.flatten(), 
            geometry = gpd.points_from_xy(lon, lat, crs="EPSG:4326"))
    gdf = gdf.rename(columns={0:'im'})
    # return only the non-zero intensity measures
    return gdf[gdf['im'] > 0]
    #return gdf.sort_values(by='im',ascending=False).head(10000)


def read_gem_xml(data: [bytes]):
    content_as_string = data.decode('utf-8')
    content_as_string = content_as_string.replace('\n','')
    dom = xml.dom.minidom.parseString(content_as_string)

    def getText(node):
        nodelist = node.childNodes
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

    d = dict()
    node = dom.getElementsByTagName('vulnerabilityModel')[0]
    for i in range(node.attributes.length):
        d[node.attributes.item(i).name] = node.attributes.item(i).value 

    d['description'] = getText(dom.getElementsByTagName('description')[0])


    d['vulnerabilityFunctions'] = []
    for node in dom.getElementsByTagName('vulnerabilityFunction'):
        v = dict()
        for i in range(node.attributes.length):
            v[node.attributes.item(i).name] = node.attributes.item(i).value 
        imls = node.getElementsByTagName('imls')[0]
        v['imt'] = imls.getAttribute('imt')
        v['imls'] = np.fromstring(getText(imls),dtype=float, sep=' ')
        v['meanLRs'] = np.fromstring(getText(node.getElementsByTagName('meanLRs')[0]),dtype=float, sep=' ')
        v['covLRs'] = np.fromstring(getText(node.getElementsByTagName('covLRs')[0]),dtype=float, sep=' ')
        d['vulnerabilityFunctions'].append(v)

    return d


@solara.component
def VulnerabilityFunctionDisplayer(vuln_func):
    vuln_func, _ = solara.use_state_or_update(vuln_func)

    x = vuln_func['imls']
    y = vuln_func['meanLRs']
    s = vuln_func['covLRs']
    xlabel = vuln_func['imt']
   
    options = { 
        'title': {
            'text': vuln_func['id'],
            'left': 'center'},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'cross'
            }
        },
        #'legend': {'data': ['Covariance','Mean']},
        'xAxis': {
            'axisTick': {
                'alignWithLabel': True
            },
            'data': list(x),
            'name': xlabel,
            'nameLocation': 'middle',
            'nameTextStyle': {'verticalAlign': 'top','padding': [10, 0, 0, 0]}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': "Covariance",
                'position': 'left',
                'alignTicks': True,
                'axisLine': {
                    'show': True,
                    'lineStyle': {'color': 'green'}}
            },
            {
                'type': 'value',
                'name': "Mean",
                'position': 'right',
                'alignTicks': True,
                'axisLine': {
                    'show': True,
                    'lineStyle': {'color': 'blue'}}
            },

        ],
        'series': [
            {
            'name': 'Mean',
            'data': list(y),
            'type': 'line',
            'yAxisIndex': 1
            },
            {
            'name': 'Covariance',
            'data': list(s),
            'type': 'line',
            'yAxisIndex': 0
            },
        ],
    }
    solara.FigureEcharts(option=options) 

@solara.component
def VulnerabiliyDisplayer(vuln_xml: dict):
    vuln_xml, set_vuln_xml = solara.use_state_or_update(vuln_xml)

    func_labels = [f'{v["imt"]}---{v["id"]}' for v in vuln_xml['vulnerabilityFunctions']]
    func_label, set_func_label  = solara.use_state_or_update(func_labels[0])

    with solara.GridFixed(columns=2):
        with solara.Column(gap="1px"):
            solara.Text('Description:',style={'fontWeight': 'bold'})
            with solara.Row(justify="left"):
                solara.Text(f'{vuln_xml["description"]}')   
            with solara.GridFixed(columns=2,row_gap="1px"):
                solara.Text('Asset Category:',style={'fontWeight': 'bold'})
                with solara.Row(justify="right"):
                    solara.Text(f'{vuln_xml["assetCategory"]}')
                solara.Text('Loss Category:',style={'fontWeight': 'bold'})
                with solara.Row(justify="right"):
                    solara.Text(f'{vuln_xml["lossCategory"]}')
                solara.Text('# of vulnerability functions:',style={'fontWeight': 'bold'})
                with solara.Row(justify="right"):
                    solara.Text(f'{len(vuln_xml["vulnerabilityFunctions"])}')      
            solara.Text('Select vulnerability function:',style={'fontWeight': 'bold'})
            solara.Select(label='',value=func_label, values=func_labels,
                        on_value=set_func_label)
        with solara.Column():
            VulnerabilityFunctionDisplayer(vuln_xml['vulnerabilityFunctions'][func_labels.index(func_label)])

@solara.component
def MetricWidget(name, description, value, max_value, render_count):
    value, set_value = solara.use_state_or_update(value)
    max_value, set_max_value = solara.use_state_or_update(max_value)
    options = { 
        "series": [ {
                "type": 'gauge',  
                "min": 0,
                "name": description,
                "max": max(1,max_value), # workaround when max_value = 0
                "startAngle": 180,
                "endAngle": 0,
                "progress": {"show": True, "width": 8},
                "pointer": { "show": False},
                "axisLine": {"lineStyle": {"width": 8}},
                "axisTick": {"show": False},
                "splitLine": {"show": False},            
                "axisLabel": {"show": False},
                "anchor": {"show": False},
                "title": {"show": False},
                "detail": {
                    "valueAnimation": True,
                    "offsetCenter": [0, '-15%'],
                    "fontSize": 14,
                    "color": 'inherit'},
                "title": {"fontSize": 12},
                "data": [{"value": value, "name": name}]}]}
    print(f'value/max_value {value}:{max_value}')
    

    with solara.Tooltip(description):
        with solara.Column():
            solara.FigureEcharts(option=options, attributes={ "style": "height: 100px; width: 100px" })


def import_data(fileinfo: solara.components.file_drop.FileInfo):
    data_array = fileinfo['data']
    extension = fileinfo['name'].split('.')[-1]
    if extension == 'xlsx':
        data = pd.read_excel(data_array)
    elif extension in ['tiff','tif']:
        data = read_tiff(data_array)
    elif extension.lower() in ['xml']:
        data = read_gem_xml(data_array)
    else:
        json_string = data_array.decode('utf-8')
        json_data = json.loads(json_string)
        if "features" in json_data.keys():
            data = gpd.GeoDataFrame.from_features(json_data['features'])
        else:
            data = pd.read_json(json_string)

    if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
        data.columns = data.columns.str.lower()
        attributes = set(data.columns)
    elif isinstance(data, dict):
        attributes = set(data.keys())
    else:
        return (None, None)


    # in the first pass, look for exact column match
    name = None
    for layer_name, layer in layers.value['layers'].items():
        if layer['attributes'] == attributes:
            name = layer_name
            break
    # if not, check only the required columns
    if name is None:
        for layer_name, layer in layers.value['layers'].items():
            if layer['attributes_required'].issubset(attributes):
                name = layer_name
                logging.debug('There are extra columns', attributes - layer['attributes_required'])
                break
    

    # Inject columns
    if name is not None and (isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame)):
        for col, val in layers.value['layers'][name]['extra_cols'].items():
            data[col] = val
    return (name, data)


@solara.component
def FileDropZone():
    total_progress, set_total_progress = solara.use_state(-1)
    fileinfo, set_fileinfo = solara.use_state(None)
    result, set_result = solara.use_state(solara.Result(True))

    def load():
        if fileinfo is not None:
            print('processing file')
            name, data = import_data(fileinfo)
            if name is not None and data is not None:
                if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
                    layers.value['layers'][name]['data'].set(data)
                    layers.value['selected_layer'].set(name)
                    layers.value['layers'][name]['visible'].set(True)
                    layers.value['layers'][name]['force_render'].set(True)
                    if  "geometry" in list(data.columns):
                        center = (data.geometry.centroid.y.mean(), data.geometry.centroid.x.mean())
                        layers.value['center'].set(center)
                elif isinstance(data, dict):
                    layers.value['layers'][name]['data'].set(data)
                    layers.value['selected_layer'].set(name)
                    layers.value['layers'][name]['visible'].set(True)
                    layers.value['layers'][name]['force_render'].set(True)
            else:
                return False
        return True
        
    def progress(x):
        set_total_progress(x)

    def on_file_deneme(f):
        set_fileinfo(f)
    
    result = solara.use_thread(load, dependencies=[fileinfo])

    solara.FileDrop(on_total_progress=progress,
                    on_file=on_file_deneme, 
                    lazy=False)
    if total_progress > -1 and total_progress < 100:
        solara.Text(f"Uploading {total_progress}%")
        solara.ProgressLinear(value=total_progress)
    else:
        if result.state == solara.ResultState.FINISHED:
            if result.value:
                solara.Text("Spacer", style={'visibility':'hidden'})
            else:
                solara.Text("Unrecognized file")
            solara.ProgressLinear(value=False)
        elif result.state == solara.ResultState.INITIAL:
            solara.Text("Spacer", style={'visibility':'hidden'})
            solara.ProgressLinear(value=False)
        elif result.state == solara.ResultState.ERROR:
            solara.Text(f'{result.error}')
            solara.ProgressLinear(value=False)
        else:
            solara.Text("Processing")
            solara.ProgressLinear(value=True)

@solara.component
def LayerDisplayer():
    print(f'{layers.value["bounds"].value}')
    nonempty_layers = {name: layer for name, layer in layers.value['layers'].items() if layer['data'].value is not None}
    nonempty_layer_names = list(nonempty_layers.keys())
    selected = layers.value['selected_layer'].value
    def set_selected(s):
        layers.value['selected_layer'].set(s)

    solara.ToggleButtonsSingle(value=selected, on_value=set_selected, 
                               values=nonempty_layer_names)
    if selected is None and len(nonempty_layer_names) > 0:
        set_selected(nonempty_layer_names[0])
    if selected is not None:
        data = nonempty_layers[selected]['data'].value
        if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
            if "geometry" in data.columns:
                ((ymin,xmin),(ymax,xmax)) = layers.value['bounds'].value
                df_filtered = data.cx[xmin:xmax,ymin:ymax].drop(columns='geometry')
                solara.DataFrame(df_filtered)
            else:
                solara.DataFrame(data)
            if selected == "building":
                file_object = data.to_json()
                with solara.FileDownload(file_object, "building_export.geojson", mime_type="application/geo+json"):
                    solara.Button("Download GeoJSON", icon_name="mdi-cloud-download-outline", color="primary")
        if selected == 'gem_vulnerability':
            VulnerabiliyDisplayer(data)

@solara.component
def MetricPanel():
    building = layers.value['layers']['building']['data'].value
    filtered_metrics = {name: 0 for name in layers.value['metrics'].keys()}
    if building is not None and layers.value['bounds'].value is not None:
        ((ymin,xmin),(ymax,xmax)) = layers.value['bounds'].value
        filtered = building.cx[xmin:xmax,ymin:ymax]
        for metric in filtered_metrics.keys():
            filtered_metrics[metric] = int(filtered.cx[xmin:xmax,ymin:ymax][metric].sum())
    
    with solara.Row():
        for name, metric in layers.value['metrics'].items():
            MetricWidget(name, metric['desc'], 
                         filtered_metrics[name], 
                         metric['max_value'],
                         layers.value['render_count'].value)
        with solara.Link("/docs/metrics"):
            solara.Button(icon_name="mdi-help-circle-outline", icon=True)
  

@solara.component
def LayerController():
    with solara.Row(gap="0px"):
        for layer_name, layer in layers.value['layers'].items():
            if layer['map_layer'].value is not None:
                solara.Checkbox(label=layer_name, 
                                value=layer['visible'])

                    
@solara.component
def MapViewer():
    print('rendering mapviewer')
    default_zoom = 14
    #default_center = (-1.3, 36.80)
    zoom, set_zoom = solara.use_state(default_zoom)
    #center, set_center = solara.use_state(default_center)

    base_map = ipyleaflet.basemaps["Esri"]["WorldImagery"]
    base_layer = ipyleaflet.TileLayer.element(url=base_map.build_url())
    map_layers = [base_layer]

    render_order = [l['render_order'] for _, l in layers.value['layers'].items()]
    for _, (layer_name, layer) in sorted(zip(render_order,layers.value['layers'].items())):
        df = layer['data'].value
        if isinstance(df, gpd.GeoDataFrame):
            # we have something to display on map
            if  "geometry" in list(df.columns) and layer['visible'].value:
                map_layer = create_map_layer(df, layer_name)
                if map_layer is not None:
                    map_layers.append(map_layer)

     
    ipyleaflet.Map.element(
        zoom=zoom,
        on_zoom=set_zoom,
        on_bounds=layers.value['bounds'].set,
        center=layers.value['center'].value,
        on_center=layers.value['center'].set,
        scroll_wheel_zoom=True,
        dragging=True,
        double_click_zoom=True,
        touch_zoom=True,
        box_zoom=True,
        keyboard=True if random.random() > 0.5 else False,
        layers=map_layers
        )
        
@solara.component
def ExecutePanel():
    infra, set_infra = solara.use_state(["building"])
    hazard, set_hazard = solara.use_state("flood")


    execute_counter, set_execute_counter = solara.use_state(0)
    execute_btn_disabled, set_execute_btn_disabled = solara.use_state(False)
    execute_error = solara.reactive("")

    def on_click():
        set_execute_counter(execute_counter + 1)
        execute_error.set("")

    def is_ready_to_run(infra, hazard):
        existing_layers = set([name for name, l in layers.value['layers'].items() if l['data'].value is not None])
        missing = []

        if hazard == "earthquake":
            if "power" in  infra:
                missing += list(set(["power edges","power nodes","intensity","power fragility"]) - existing_layers)
            if "building" in infra:
                missing += list(set(["landuse","building","household","individual","intensity","fragility"]) - existing_layers)
        elif hazard == "flood":
            if "power" in  infra:
                missing += list(set(["power edges","power nodes","intensity","power vulnerability"]) - existing_layers)
            if "building" in infra:
                missing += list(set(["landuse","building","household","individual","intensity","vulnerability"]) - existing_layers)
 
        if infra == []:
            missing += ['You should select power and/or building']
        return missing == [], missing
    


    def execute_engine():


        def execute_infra():
            nodes = layers.value['layers']['power nodes']['data'].value
            edges = layers.value['layers']['power edges']['data'].value
            intensity = layers.value['layers']['intensity']['data'].value
            power_fragility = layers.value['layers']['power fragility']['data'].value


            eq_ds, is_damaged, is_operational = compute_power_infra(nodes, 
                                    edges,
                                    intensity,
                                    power_fragility)
            
            #power_node_df =  dfs['Power Nodes'].copy()                         
            nodes['ds'] = list(eq_ds)
            nodes['is_damaged'] = list(is_damaged)
            nodes['is_operational'] = list(is_operational)
            return nodes

        def execute_building():
            landuse = layers.value['layers']['landuse']['data'].value
            buildings = layers.value['layers']['building']['data'].value
            household = layers.value['layers']['household']['data'].value
            individual = layers.value['layers']['individual']['data'].value
            intensity = layers.value['layers']['intensity']['data'].value

            fragility = layers.value['layers']['fragility']['data'].value
            vulnerability = layers.value['layers']['vulnerability']['data'].value

            policies = [p['id'] for id, p in layers.value['policies'].items() if p['applied'].value]

            print('policies',policies)
            df_bld_hazard = compute(
                landuse,
                buildings, 
                household, 
                individual,
                intensity,
                fragility if hazard == "earthquake" else vulnerability, 
                hazard,policies=policies)
            buildings['ds'] = list(df_bld_hazard['ds'])

            implementation_capacity_score = layers.value['implementation_capacity_score'].value
            if implementation_capacity_score == 'medium':
                capacity = 1.25
            elif implementation_capacity_score == 'low':
                capacity = 1.50
            else:
                capacity = 1
            computed_metrics, df_metrics = calculate_metrics(buildings, household, 
                                                             individual, hazard, policies=policies,capacity=capacity)
        
            print(computed_metrics)
            for metric in df_metrics.keys():
                buildings[metric] = list(df_metrics[metric][metric])
                layers.value['metrics'][metric]['value'] = computed_metrics[metric]['value']
                layers.value['metrics'][metric]['max_value'] = computed_metrics[metric]['max_value']
            
            return buildings

        if execute_counter > 0 :
            is_ready, missing = is_ready_to_run(infra, hazard)
            if not is_ready:
                raise Exception(f'Missing {missing}')
            
            if 'power' in infra:
                nodes = execute_infra()
                layers.value['layers']['power nodes']['data'].set(nodes)
            if 'building' in infra:
                buildings = execute_building()
                layers.value['layers']['building']['data'].set(buildings)

            # trigger render event
            layers.value['render_count'].set(layers.value['render_count'].value + 1)
            if 'power' in infra:
                layers.value['layers']['power nodes']['force_render'].set(True)
            if 'building' in infra:
                layers.value['layers']['building']['force_render'].set(True)

            

    # Execute the thread only when the depencency is changed
    result = solara.use_thread(execute_engine, dependencies=[execute_counter])

    with solara.GridFixed(columns=2):
        solara.Text("Infrastructure Type")
        with solara.Row(justify="right"):
            solara.ToggleButtonsMultiple(value=infra, on_value=set_infra, values=["building","power"])
        solara.Text("Hazard")
        with solara.Row(justify="right"):
            solara.ToggleButtonsSingle(value=hazard, on_value=set_hazard, values=["earthquake","flood"])
        with solara.Tooltip("Building-level metrics will be increased by 25% and 50% for medium and low"):
            solara.Text("Implementation Capacity Score")
        with solara.Row(justify="right"):
            solara.ToggleButtonsSingle(value=layers.value['implementation_capacity_score'].value, 
                                values=['low','medium','high'],
                                on_value=layers.value['implementation_capacity_score'].set)
    PolicyPanel()
    solara.ProgressLinear(value=False)
    solara.Button("Calculate", on_click=on_click, outlined=True,
                  disabled=execute_btn_disabled)
    # The statements in this block are passed several times during thread execution
    if result.error is not None:
        execute_error.set(execute_error.value + str(result.error))

    if execute_error.value != "":
        solara.Text(f'{execute_error}', style={"color":"red"})
    else:
        solara.Text("Spacer", style={"visibility": "hidden"})

    if result.state in [solara.ResultState.RUNNING, solara.ResultState.WAITING]:
        set_execute_btn_disabled(True)
        solara.ProgressLinear(value=True)
    else:
        set_execute_btn_disabled(False)
        solara.ProgressLinear(value=False)

@solara.component
def PolicyPanel():
    with solara.GridFixed(columns=6):
        for policy_key, policy in layers.value['policies'].items():
            with solara.Tooltip(tooltip=policy['description']):
                solara.Checkbox(label=policy['label'], 
                                value=policy['applied'])
        with solara.Link("/docs/policies"):
            solara.Button(icon_name="mdi-help-circle-outline", icon=True)


@solara.component
def MapInfo():
    print(f'{layers.value["bounds"].value}')

    print(layers.value['map_info_button'].value)

    with solara.Row(justify="center"):
        solara.ToggleButtonsSingle(value=layers.value['map_info_button'].value, 
                               on_value=layers.value['map_info_button'].set, 
                               values=["summary","detail"])

    if layers.value['map_info_button'].value == "summary":
        with solara.GridFixed(columns=2,row_gap="1px"):
            for layer_name,layer in layers.value['layers'].items():
                data = layer['data'].value
                with solara.Tooltip(layer['map_info_tooltip']):
                    solara.Text(f'{layer_name}')
                with solara.Row(justify="right"):
                    if data is None:
                        solara.Text('0')
                    else:
                        if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
                            solara.Text(f"{len(data)}")
                        elif isinstance(data, dict) and layer_name == 'gem_vulnerability':
                            solara.Text(f"{len(data['vulnerabilityFunctions'])}")
    else:
        with solara.GridFixed(columns=2,row_gap="1px"):
            for key, value in layers.value['map_info_detail'].value.items():
                if key == 'style':
                    continue
                solara.Text(f'{key}')
                with solara.Row(justify="right"):
                    strvalue = str(value)
                    if len(strvalue) > 10:
                        with solara.Tooltip(f'{value}'):
                            solara.Text(f'{strvalue[:10]}...')
                    else:
                        solara.Text(f'{value}')




@solara.component
def WebApp():

    with solara.Columns([30,70]):
        with solara.Column():
            solara.Markdown('[Download Sample Dataset](https://drive.google.com/file/d/1BGPZQ2IKJHY9ExOCCHcNNrCTioYZ8D1y/view?usp=sharing)')
            FileDropZone()
            ExecutePanel()
        with solara.Column():
            LayerController()
            with solara.Columns([80,20]):
                MapViewer()
                MapInfo()
            MetricPanel()
            
    LayerDisplayer()

@solara.component
def Page(name: Optional[str] = None, page: int = 0, page_size=100):
    css = """
    .v-input {
        height: 10px;
    }

    .v-btn-toggle:not(.v-btn-toggle--dense) .v-btn.v-btn.v-size--default {
        height: 24px;
        min-height: 0;
        min-width: 24px;
    }

    """
    solara.Style(value=css)
    solara.Title("TCDSE » Engine")

    WebApp()
