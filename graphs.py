#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 13:20:48 2024

@author: reitze
"""

"""
dependencies: Kaleido: sudo conda install -c conda-forge python-kaleido
or conda install -c conda-forge python-kaleido=0.1.0
Also statsmodels
"""
# Makes scatter displayed in streamlit
def scatter(dtaAgg, dtaselected, size, start, year, levels, highlight, legend, showlabel, showtrend, color_level, population=False, xrange = None, yrange=None):
    import pandas as pd
    import numpy as np
    import textwrap
    import plotly.express as px
    import plotly.io as pio
    from PIL import Image
    import json
    import scipy.optimize as opt
    pio.renderers.default='browser'

    metric = 'Average Annual log percentage change' #options are: 'Percentage change', 'Log percentage change', 'Average Annual Percentage change', 'Average Annual log percentage change'
    itl_string = ','.join(levels)
    figure_title = 'UK ' + itl_string + ' regions<br>' +\
                    '<sup>' + str(year) + ' Nominal smoothed GVA per hour, vs. ' + str(start) + '-' + \
                    str(year) + ' productivity change</sup>'

                    # '<sup><b>By ' + level.upper() + ' region</b></sup>'

         
    yaxistitle = str(start) + '-' + str(year) + ' ' + metric + ' in productivity'
    xaxistitle = str(year) + ' output per hour worked (£)'

    # averages = ['TLJ', 'UKX','UKXX']
    # avgcolors = ['purple', 'blue', 'green']
    averages = ['UKX']
    avgcolors = ['purple']
    with open("src/colormaps.json", "r") as file:
        colour_maps = json.load(file)

    # Access the individual dictionaries
    if color_level == 'MCA':
        colormap = colour_maps[3]
    else:
        colormap = colour_maps[int(color_level[3]) - 1]

    if showlabel:
        labels = 'name'
    else: labels = None

    if showtrend:
        trend = 'ols'
    else: trend = None

    dtaselected['Scaled Population'] = (10 + ((dtaselected['Population'] - dtaselected['Population'].min()) * (40 - 10)) / (dtaselected['Population'].max() - dtaselected['Population'].min())) * size
    #Style plot
    if population:#marker = dict(size =dtaselected['Scaled Population']*size)
        fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                    text=labels,
                    color = color_level.lower() + 'name',
                    color_discrete_map = colormap,
                    custom_data=['name', 'itl', 'GVA per hour', metric, 'Population', 'level'],
                    trendline = trend,
                    trendline_scope="overall",
                    trendline_color_override="red",
                    size='Scaled Population',
                    width=1000*size,
                    height=700*size,
                    )
        fig.update_traces(textposition='top center', textfont_size = 10*size)
    else:
        fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                    text=labels,
                    color = color_level.lower() + 'name',
                    color_discrete_map = colormap,
                    custom_data=['name', 'itl', 'GVA per hour', metric, 'level'],
                    trendline = trend,
                    trendline_scope="overall",
                    trendline_color_override="red",
                    width=1000*size,
                    height=700*size,
                    )
        fig.update_traces(marker = dict(size =10*size), textposition='top center', textfont_size = 10*size)
    # if showlabel:
    #     # Update label positions
    #     for i, row in dtaselected.reset_index().iterrows():
    #         fig.add_annotation(
    #             x=row['GVA per hour'] + row['x_offset'],
    #             y=row[metric] + row['y_offset'],
    #             text=row['name'],
    #             showarrow=False,
    #             font=dict(size=9)
    #         )
    #add the scatter point for the reference average, 1 for UK as whole one for UK excluding London:
    for i, v in enumerate(averages):
        avgUK = dtaAgg.loc[(slice(None), v, slice(None)),['GVA per hour', metric, 'Population']].reset_index()
        if population:
            ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                            # hover_name = 'name',
                            # text='name',
                            # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                            custom_data=['name', 'itl', 'GVA per hour', metric, 'Population', 'level'],
                            )
        else:
            ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                            # hover_name = 'name',
                            # text='name',
                            # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                            custom_data=['name', 'itl', 'GVA per hour', metric, 'level'],
                            )

        #styling for the UK average 'trace' or layer.
        ukavg.update_traces(marker=dict(
                                        size=2,
                                        # size=15,
                                        color=avgcolors[i],
                                        # line=dict(width=2, color = 'black')
                                        ),
                            textfont_size = 17,
                            # fillcolor = 'white',
                            # textfont_color = 'white',
                            textposition='top center')


        fig.add_trace(ukavg.data[0])

        #Add vertical and horizontal line through the UK average
        fig.add_hline(y=avgUK.loc[0, metric], line_width=1, line_dash="dash", line_color=avgcolors[i])
        fig.add_vline(x=avgUK.loc[0, 'GVA per hour'], line_width=1, line_dash="dash", line_color=avgcolors[i])


    if population:
        if xrange != None:
            sizeflag = (max(xrange) -min(xrange))/25
        else:
            sizeflag = (dtaselected['GVA per hour'].max() - dtaselected['GVA per hour'].min())/50 * size
    else:
        if xrange != None:
            sizeflag = (max(xrange) -min(xrange))/25
        else:
            sizeflag = (dtaselected['GVA per hour'].max() - dtaselected['GVA per hour'].min())/50 * size
    
    #Add image for the UK flag
    fig.add_layout_image(
        dict(
            source=Image.open("static/flag.png"),
            x=avgUK['GVA per hour'][0],
            y=avgUK[metric][0],
            sizex=sizeflag,
            sizey=sizeflag,
            layer = 'above',
            xref="x",
            yref="y",
            xanchor="center", yanchor="middle"
        )
    )


    '''Add scatter labels for selected regions'''
    if highlight != None:
        highlight = ['<br>'.join(textwrap.wrap(x, width = 15)) for x in highlight]
        dtaHighlight = pd.DataFrame()
        temp = dtaselected.loc[(dtaselected.index.get_level_values('level').isin(levels), slice(None), highlight),:].reset_index()
        dtaHighlight = pd.concat([dtaHighlight, temp], ignore_index=True)
        #Add names with arrow
        for i, v in dtaHighlight.iterrows():
            text = textwrap.wrap(v['name'], width = 20)
            text = '<br>'.join(text)
            fig.add_annotation({
                            'text': '<b>' + v['name'] + '</b>',
                            # 'text': text,
                            'x': v['GVA per hour'],
                            'y': v[metric],
                            'font': {'size': 10*size, 'color': 'black'},
                            'showarrow': True,
                            'arrowwidth': 1,
                            'arrowhead': 0,
                            'ay': -50, #This creates a different y-position of the text, so that when the graph is reduced in width the text won't overlap
                            # 'ax': prm['highlight'][v['itl']][1],

                            # textangle=0,
                            # xanchor='right',
                            # align:'left',
                            'bgcolor': 'rgba(237, 237, 237,0.0)',
                            'opacity': 1,
                            'xref': "x",
                            'yref': "y"
                        }
                        )


    #Plot formatting
    fig.update_layout(font = {'size': 18*size},
                      showlegend=legend,
                      legend_title = color_level + ' Region',
                      legend_title_font_size = 12*size,
                      legend_font_size = 12*size,
                      plot_bgcolor = 'rgba(237, 237, 237,0.5)',
                      #paper_bgcolor = 'white',
                      paper_bgcolor = 'rgba(0,0,0,0)',
                      title = {
                                'text': figure_title, #set main title
                                'x': 0.04,
                                'font_size': 15*size, #Title text size
                                },


                      margin = {
                          'l': 100*size,
                          'r': 100*size,
                          't': 100*size,
                          'b': 100*size,
                          },
                      )

    fig.layout.yaxis.tickformat =  '.1%'
    fig.update_xaxes(tickprefix='£')
    fig.update_yaxes(title = yaxistitle, tickfont=dict(size=12*size), title_font=dict(size=12*size))
    fig.update_xaxes(title = xaxistitle, tickfont=dict(size=12*size), title_font=dict(size=12*size))

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')

    if xrange != None: fig.update_xaxes(range=xrange)
    if yrange != None:
        yrange = [i/100 for i in yrange]

        fig.update_yaxes(range=yrange)

    #Define what information the tooltip shows
    if population:
        hovertemp="<br>".join([
                "<b> %{customdata[0]}</b>",
                "%{customdata[5]} code: %{customdata[1]}",
                str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
                "Productivity growth: %{customdata[3]:.2%}",
                "Working Population: %{customdata[4]}"
                ])
    else:
        hovertemp="<br>".join([
            "<b> %{customdata[0]}</b>",
            "%{customdata[4]} code: %{customdata[1]}",
            str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
            "Productivity growth: %{customdata[3]:.2%}",
            ])

    #Update the traces to inlcude the tootlip information
    fig.update_traces(hovertemplate=hovertemp)


    #Add annotations
    tsize = 12*size

    #Add annotation boxes to the plot
    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.99,
                                            y=0.03,
                                            showarrow=False,
                                            text="Losing ground",
                                            textangle=0,
                                            xanchor='right',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.99,
                                            y=0.97,
                                            showarrow=False,
                                            text="Steaming ahead",
                                            textangle=0,
                                            xanchor='right',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.01,
                                            y=0.97,
                                            showarrow=False,
                                            text="Catching up",
                                            textangle=0,
                                            xanchor='left',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.01,
                                            y=0.03,
                                            showarrow=False,
                                            text="Falling behind",
                                            textangle=0,
                                            xanchor='left',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    note = '<i>TPI visualisation, based on ONS Subregional Productivity June 2024 release</i>'

    #Add note
    fig.add_annotation(
                    {
                        'text': note,
                        'font': {'size': tsize},
                        'x': -0.1,
                        'y': -0.23,
                        'xanchor': 'left',
                        'yanchor': 'bottom',
                        'align': 'left',
                        'textangle': 0,
                        # 'bgcolor': 'white',
                        # 'opacity': 1,
                        'xref':"paper",
                        'yref': "paper",
                        'showarrow': False,
                    }
                )
    return fig
