import dash
from dash import dcc
import dash_daq as daq
from dash import html
from dash import dash_table
import dash_bootstrap_components as dbc

# Tab styles for ascending in hierarchy

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#6E6E6E',
    'color': 'white',
    'padding': '6px'
}

tab_selected_style_sub_main = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#424242',
    'color': 'white',
    'padding': '6px'
}

tab_selected_style_main = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#1F1F1F',
    'color': 'white',
    'padding': '6px'
}

def app_layout():
    return html.Div(children=[

    html.Div(className='row', children=[
        html.Div(className='two columns', children=[
            html.H1(children='  LabEmbryoCam', style={'display': 'inline-block', 'height': '20px'}),
            html.Img(src='./assets/img/embryophenomicslogo.png', style={'display': 'inline-block', 'height': '60px'}),
        ]),
        html.Div(className='eight columns', children=[
            html.Br(), # forces columns to be created
            html.Div(children=[
                html.Div(children=[
                    html.H6('Current timepoint:'),
                    html.Br(),
                    html.H6('Current embryo:')
                ], style={'width': '20%', 'display': 'table-cell'}),
                html.Div(children=[
                    dbc.Progress(id="timepoint-pg", style={'height': '20px'}),
                    html.Br(),
                    html.Br(),
                    dbc.Progress(id="embryo-pg", style={'height': '20px'})
                ], style={'width': '80%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),
        ]),
        html.Div(className='two columns', children=[
            html.Br(),
            html.Button('Shutdown', 'close-app'),
            html.Div(id='close-app-div')
        ])
    ]),

    html.Br(),

    html.Div(className='row', children=[
                dcc.Tabs(id='hardware-tabs', children=[

                    dcc.Tab(label='Camera', style=tab_style, selected_style=tab_selected_style_sub_main, children=[

                        html.Div(id='loaded-data-callback'),
                        html.Div(id='hiddenFPSdata'),
                        html.Div(id='fullROIData'),
                        html.Div(id='config-save-callback'),
                        html.Div(id='connect-cam-callback'),

                        html.Div(className='row', children=[

                            html.Div(className='three columns', children=[

                                html.Br(),

                                html.H5('Acquisition', style={'display': 'inline-block'}),

                                html.Br(),

                                html.Label(children='Number of positions'),
                                dcc.RadioItems(
                                    id='acquisition-number',
                                    options=[
                                        {'label': 'Single', 'value': 'Single'},
                                        {'label': 'Multiple', 'value': 'Multiple'}],
                                    value='Single',
                                    labelStyle={'display': 'inline-block'}),

                                html.Br(),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label(children='Number of time-points')
                                    ], style={'width': '70%', 'display': 'table-cell'}),
                                    html.Div(children=[
                                        daq.NumericInput(id='total-time-points', min=1, max=100000, value=1, size=100)
                                    ], style={'width': '30%', 'display': 'table-cell'}),
                                ], style={'width': '100%', 'display': 'table'}),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label(children='Acquisition interval (mins)')
                                    ], style={'width': '70%', 'display': 'table-cell'}),
                                    html.Div(children=[
                                        daq.NumericInput(id='acq-length', min=0, max=100000, value=1, size=100)
                                    ], style={'width': '30%', 'display': 'table-cell'}),
                                ], style={'width': '100%', 'display': 'table'}),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label(children='Acquisition length (secs)')
                                    ], style={'width': '70%', 'display': 'table-cell'}),
                                    html.Div(children=[
                                        daq.NumericInput(id='each-time-limit', min=1, max=100000, value=1, size=100)
                                    ], style={'width': '30%', 'display': 'table-cell'}),
                                ], style={'width': '100%', 'display': 'table'}),

                                html.Br(),

                                dcc.Input(
                                    id='acquire-path-input', 
                                    type='text',
                                    placeholder='Specify a path to save frames...',),
                                html.Div(id='acquire-outpath-check'),

                                html.Br(),

                                html.Label('Progress updates'),
                                dcc.Input(
                                    id='email-username',
                                    type='text',
                                    placeholder='Specify an email username...'),
                                dcc.Input(
                                    id='email-password',
                                    type='password',
                                    placeholder='Specify an email password...'),
                                html.Br(),
                                html.Button('Login', 'email-login'),
                                html.Div(id='login-callback'),

                                html.Br(),
                                html.Br(),

                                html.Button('Start acquisition', id='acquire-button'),
                                html.Div(id='hiddenAcquire'),
                                html.Button('Cancel acquisition', id='cancel-acquire-button'),

                            ]),

                            html.Div(className='two columns', children=[

                                html.Br(),

                                html.Label('Preset configuration files'),
                                html.Div(children=[
                                    html.Div(children=[
                                        dcc.Upload(
                                            id='load-config-button', 
                                            multiple=False,
                                            children=html.Button('Load'))
                                    ], style={'width': '10%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        html.Button('Save', id='save-config-button')
                                    ], style={'width': '10%', 'display': 'table-cell'}),

                                    html.Div(children=[], style={'width': '15%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        dcc.Input(
                                            id='config-name-input',
                                            type='text',
                                            placeholder='Please name a config file...')
                                    ], style={'width': '65%', 'display': 'table-cell'}),
                                ], 
                                style={'width': '100%', 'display': 'table'}),

                                html.Br(),

                                html.H5('Light brightness', style={'display': 'inline-block'}),

                                html.Br(),

                                dcc.Slider(
                                    id='hardware-brightness',
                                    min=0,
                                    max=100,
                                    value=0,
                                    tooltip={'always_visible': True, 'placement': 'bottom'},
                                    persistence=True),
                                html.Div(id='hardware-brightness-callback'),

                                html.Br(),

                                html.H5('Camera settings', style={'display': 'inline-block'}),

                                html.Br(),

                                html.Div(id='brightness-control', children=[

                                    html.Label(children='Exposure'),
                                    daq.NumericInput(id='exposure', min=0, max=999999, value=0, size=200, disabled=True, persistence=True),

                                    html.Br(),

                                    html.Label(children='Contrast'),                                        
                                    daq.NumericInput(id='contrast', min=0, max=999999, value=0, size=200, disabled=True, persistence=True),

                                ]),

                                html.Br(),

                                html.Div(id='fps-control', children=[

                                    html.Label(children='Frame-rate'),
                                    daq.NumericInput(id='fps', min=0, max=999999, value=0, size=200, disabled=True, persistence=True),
                                ]),

                                html.Br(),

                                html.Label(children='Resolution'),
                                dcc.Dropdown(
                                    id='resolution-preset',
                                    placeholder='Please select a resolution...',
                                    options=[
                                        dict(label='640x480', value=640),
                                        dict(label='1280x720', value=1280),
                                        dict(label='1920x1080', value=1920),
                                        dict(label='256x256', value=256),
                                        dict(label='512x512', value=512),
                                        dict(label='1024x1024', value=1024),
                                        dict(label='2048x2048', value=2048)],
                                    disabled=False,
                                    persistence=True,
                                    persistence_type='session'),

                                html.Br(),

                                html.Button('Update settings', id='update-camera-settings'),
                                html.Div(id='hidden-update-callback'),

                            ]),

                            html.Div(className='one column', children=[]),

                            html.Div(className='five columns', children=[

                                html.Br(),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Button('Snap', id='test-frame-button')
                                    ], style={'width': '25%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        html.Button('Start/Stop Stream', id='camera-live-stream'),
                                    ], style={'width': '75%', 'display': 'table-cell'})
                                ], style={'width': '100%', 'display': 'table'}),

                                html.Br(),

                                # html.Div(id='still-image', children=[]),

                                # html.Hr(),

                                html.Div(children=[], id='camera-state-live-view'),
                                html.Div(children=[], id='camera-state-snapshot'),

                                html.Img(src="/video_feed")

                            ]),
                        ]),
                    ]),

                    dcc.Tab(label='XYZ', style=tab_style, selected_style=tab_selected_style_sub_main, children=[
                        html.Div(className='row', children=[
                            html.Div(className='three columns', children=[

                                html.Br(),

                                html.Button('Set Origin', id='home-xy-button'),
                                html.Div(id='xyz-homing-callback'),

                                html.Br(),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label('Manual controls')
                                    ], style={'width': '50%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        daq.BooleanSwitch(
                                            id='manual-controls',
                                            on=False)
                                    ], style={'width': '50%', 'display': 'table-cell'})
                                ], style={'width': '100%', 'display': 'table'}),
                                html.Div(id='manual-controls-callback'),

                                html.Br(),

                            ]),

                            html.Div(className='three columns', children=[

                                html.Br(),
                                html.Br(),
                                html.Br(), # Extra spacing to line up with above inputs

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Button('Generate xy', id='generate-xy-button', disabled=True)
                                    ], style={'width': '40%', 'display': 'table-cell'}),
                                    html.Div(children=[
                                        dcc.Dropdown(
                                            id='plate-size',
                                            placeholder='Please select a plate size...',
                                            options=[
                                                dict(label='24 wells', value=24),
                                                dict(label='48 wells', value=48),
                                                dict(label='96 wells', value=96),
                                                dict(label='384 wells', value=384)],
                                            disabled=True)
                                    ], style={'width': '60%', 'display': 'table-cell'})
                                ], style={'width': '100%', 'display': 'table'}),
                                html.P('Note that you need position A1 to generate positions.'),

                                html.Div(id='generate-xy-callback'),
                                html.Div(id='load-xy-callback'),

                                html.Br(),

                                html.H5('Position List', style={'display': 'inline-block'}),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Button('Current', id='grab-xy'),
                                        html.Div(id='grab-xy-callback')
                                    ], style={'width': '40', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        html.Br()
                                    ], style={'width': '20', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        html.Button('Replace', id='replace-xy-button'),
                                        html.Div(id='replace-xy-callback')
                                    ], style={'width': '40%', 'display': 'table-cell'}),

                                    html.Div(children=[], style={'width': '80%', 'display': 'table-cell'}),

                                ], style={'width': '100%', 'display': 'table'}),

                                html.Br(),

                                html.Div(id='remove-xy-callback'),
                                dash_table.DataTable(
                                    id='xy_coords',
                                    columns=[
                                        dict(name='X', id='x'), 
                                        dict(name='Y', id='y'), 
                                        dict(name='Z', id='z'),
                                        dict(name='Label', id='label')],
                                    style_cell={'textAlign': 'left'},
                                    style_cell_conditional=[{'if': {'column_id': col},'width': '25%'} for col in ['x','y','z']],
                                    fixed_rows={'headers': True},
                                    style_table={'height': 500},
                                    row_deletable=True,
                                    row_selectable='single',
                                    editable=True,
                                    page_size=500
                                )
                            ]),

                            html.Div(className='four columns', children=[

                                html.Br(),

                                html.Br(),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label('Activate graph')
                                    ], style={'width': '50%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        daq.BooleanSwitch(
                                            id='activate-graph-switch',
                                            on=False)
                                    ], style={'width': '50%', 'display': 'table-cell'})
                                ], style={'width': '100%', 'display': 'table'}),

                                html.Br(),

                                html.Div(id='coord-graph-div', children=[]),
                                html.Div(id='graph-xy-move'),

                                html.Br(),
                                html.Br(),

                                html.Div(children=[
                                    html.Div(children=[
                                        html.Label('Dimensions')
                                    ], style={'width': '50%', 'display': 'table-cell'}),

                                    html.Div(children=[
                                        daq.ToggleSwitch(
                                            id='dimensions-switch',
                                            value=False,
                                            label=['2D', '3D'])
                                    ], style={'width': '50%', 'display': 'table-cell'})
                                ], style={'width': '100%', 'display': 'table'}),

                            ]),
                        ])
                    ])
                ])
            ])
        ])
