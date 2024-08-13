from dash import dcc
import plotly.graph_objects as go
from dash import html
from plotly.subplots import make_subplots
import dash
import dash_daq as daq
import glob
from dataclasses import dataclass

import base64
import cv2
from io import BytesIO

def interactiveImage(id, img):
    '''    
    Create an interactive plotly graph from an image. 

    Parameters
    ----------
    id : str
        Identification string of graph component to use in other app callbacks (if any).
    img : ndarray
        An image array.

    Returns
    -------
        image_graph : dash_core_components.Graph
            Interactive graph component containing the given image.

    '''
    _, img_np = cv2.imencode('.jpg', img)
    byteStr = img_np.tobytes()

    encodedImg = base64.b64encode(byteStr)
    height, width = img.shape[0], img.shape[1]

    source = 'data:image/png;base64,{}'.format(encodedImg.decode())

    return dcc.Graph(
        id=id,
        figure={
            'data': [],
            'layout': {
                'margin': go.layout.Margin(l=0, b=0, t=0, r=0),
                'xaxis': {
                    'range': (0, 512),
                    'showgrid': False,
                    'zeroline': False,
                    'visible': True,
                    'scaleanchor': 'y',
                    'scaleratio': 1
                },
                'yaxis': {
                    'range': (0, 512),
                    'showgrid': False,
                    'zeroline': False,
                    'visible': True
                },
                'images': [{
                    'xref': 'x',
                    'yref': 'y',
                    'x': 0,
                    'y': 0,
                    'yanchor': 'bottom',
                    'sizing': 'stretch',
                    'sizex': width,
                    'sizey': height,
                    'layer': 'below',
                    'source': source,
                }],
            }
        },
        config={
            'modeBarButtonsToRemove': [
                'sendDataToCloud',
                'autoScale2d',
                'toggleSpikelines',
                'hoverClosestCartesian',
                'hoverCompareCartesian',
                'zoom2d'
            ],
            'displaylogo': False
        }
    )

def blank():
    '''Convenience function to return a blank image. '''
    filename = './assets/img/blankImg.png'
    img = cv2.imread(filename)

    return html.Div(children=[
        interactiveImage(
            id='still-image-graph', 
            img=img)
        ])


@dataclass
class Feature:
    __slots__ = ['current', 'min', 'max']
    current: float or int
    min: float or int
    max: float or int

def render_brightness_ui(data):
    '''
    Convenience function for rendering the brightness control ui in the camera tab.

    Parameters
    ----------
    data : dict
        Dict of dataclasses, containing various information about camera features.

    Returns
    --------
    div : dash_html_components.Div
        Div object containing the ui elements for controlling camera brightness settings.

    '''
    def numeric(exposure, contrast,  disabled):
        return html.Div(children=[
            html.Label(children="Exposure:"),
            daq.NumericInput(
                id="exposure",
                min=0,
                max=999999,
                value=exposure,
                disabled=disabled,
                size=200),

            html.Br(),

            html.Label(children="Contrast:"),
            daq.NumericInput(
                id="contrast",
                min=0,
                max=999999,
                value=contrast,
                disabled=disabled,
                size=200)
            ])
            

    if data is None:
        return numeric(0, 0, True)
    else:
        return numeric(data['exposure'], data['contrast'], False)

def render_roi_ui(data):
    '''
    Convenience function for rendering the roi ui in the camera tab.

    Parameters
    ----------
    selected_data : dict
        Data returned from a dash graph object.
    loaded_data : dict
        Data returned from loading a configuration file.

    Returns
    -------


    - selected_data: Dictionary. Data returned from a dash graph object.
    - loaded_data: Nested list. Data returned from loading a configuration file.

    Returns:
    - html.Div object containing the ui elements for controlling camera roi settings.

    '''

    def _render_roi_ui(width, height, disabled):
    
        return html.Div(children=[

            html.Label(children='Width'),
            daq.NumericInput(id='width', min=0, max=9999, value=width, size=200, disabled=disabled),

            html.Br(),

            html.Label(children='Height'),
            daq.NumericInput(id='height', min=0, max=9999, value=height, size=200, disabled=disabled)

        ])

    if data is None:
        return _render_roi_ui(0, 0, True)
    else:
        return _render_roi_ui(
            width=int(data['width']),
            height=int(data['height']),
            disabled=False)

def render_fps_ui(data):

    '''

    Convenience function for rendering the fps control ui in the camera tab.

    Arguments:
    - data: Dict. Dict of dataclasses, containing various information about camera features.

    Returns:
    - html.Div object containing the ui elements for controlling camera fps.

    '''

    def numeric(fps, disabled):
        return html.Div(children=[
            html.Label(children="Frame-rate"),
            daq.NumericInput(
                id="fps",
                min=0,
                max=9999,
                value=fps,
                disabled=disabled,
                size=200)
        ])

    if data is None:
        return numeric(0, True)
    else:
        return numeric(data['framerate'], False)


def graph(ID, fig, resolution=(800, 600)):

    '''

    Convenience function to reduce verbosity in graph method calls in app callbacks.
    This function renders a graph to a specific layout, with changes to the default 
    characteristics of plotly graphs.

    Arguments:
    - ID: Character string. id of graph component to be used in other callbacks (if any).
    - fig: Figure object. A plotly figure object. 
    - resolutions: Tuple. Size of graph to be rendered (units are pixels). Default is (800, 600).

    Returns:
    - A dcc.Graph() object to supplying to a container in your main app.

    '''

    width, height = resolution

    fig['layout']['margin'] = go.layout.Margin(l=0, b=0, t=0, r=0)

    fig.update_layout(
        legend=dict(
            traceorder='normal',
            font=dict(
                size=15,
                color='black'
            )
        )
    )

    return dcc.Graph(
        id=ID, 
        figure=fig, 
        config={
            'modeBarButtonsToRemove': [
                'sendDataToCloud',
                'autoScale2d',
                'toggleSpikelines',
                'hoverClosestCartesian',
                'hoverCompareCartesian',
                'zoom2d'
            ],
            'displaylogo': False
        },
        style=dict(width=width, height=height)
        )