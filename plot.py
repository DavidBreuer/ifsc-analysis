# %%# import

import os
import warnings

import itables
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import scipy as sp
import scipy.spatial

import plotly 
import plotly.io 
import plotly.subplots
import plotly.graph_objs as go
import plotly.express as px

# %% define

def replace_text(fin, fout, tinouts):
    with open(fin, 'r') as file :
        txt = file.read()
    for tin, tout in tinouts.items():
        txt = txt.replace(tin, tout)
    with open(fout, 'w', encoding="utf-8") as file:
        file.write(txt)
    return txt

def extract_html(html_in):
    tag0 = "<div>"
    tag1 = "</script>"
    html_out = html_in.split(tag0)[1].split(tag1)[0]+tag1
    return html_out

def nandist(veca, vecb):
    idn = (~np.isnan(veca)) & (~np.isnan(vecb))
    sim = np.nanmean(np.abs(veca[idn]-vecb[idn]))
    return sim

def month2number(mon):
    dct = {
            'jan': 1,
            'feb': 2,
            'mar': 3,
            'apr': 4,
            'may': 5,
            'jun': 6,
            'jul': 7,
            'aug': 8,
            'sep': 9, 
            'oct': 10,
            'nov': 11,
            'dec': 12
    }
    num = str(dct[mon.lower()]).zfill(2)
    return num

def results_2_podiums(fin, dca, base, scb):

    groups = fin[base + scb + ["Place"]].groupby(["Name", "Level"], sort=False)
    
    keys = groups.indices.keys()
    
    namez = np.unique(fin["Name"])
    lenn = len(namez)
    
    dct = {name: {} for name in namez}
        
    for name, level in keys:         
        # print(name, level)
        # info
        dct[name]["Name"] = name
        dct[name]["Active"] = dca.loc[name, "Active"]
        dct[name]["Gender"] = dca.loc[name, "Gender"]
        # comp
        group = groups.get_group((name, level))
        dct[name]["#" + level] = len(group)
        dct[name]["%" + level] = 100.0 * dct[name]["#" + level] / dct[name]["#Q"]            
        # podium
        if level == "F":
            dct[name]["#P"] = sum(group["Place"] < 4)
            dct[name]["%P"] = 100.0 * dct[name]["#P"] / dct[name]["#Q"]
            # medal
            for place in [3, 2, 1]:
                dct[name]["#" + str(place)] = sum(group["Place"] == place)
                dct[name]["%" + str(place)] = 100.0 * dct[name]["#" + str(place)] / dct[name]["#Q"]
    
    podiums = pd.DataFrame(dct).T.fillna(0)
    return podiums

def sub_2_graph(sub, scb, inciso=True, percentile=10):
    pivot = sub[["Unique", "Name"] + scb].pivot(index='Name', columns='Unique')
    pivot.replace(range(30), 1, inplace=True)  # 1 = reached in any number of attempts
    pivot.replace([np.inf], 0, inplace=True)  # 0 = not reached
    # print(pivot.min().min(), pivot.max().max())
    dist = sp.spatial.distance.pdist(pivot.values, nandist)
    dist = sp.spatial.distance.squareform(dist)
    np.fill_diagonal(dist, 1)
    dist = np.nan_to_num(dist, nan=1)
    graph = nx.from_numpy_array((dist < np.nanpercentile(dist, percentile))*dist)
    iso = list(nx.isolates(graph))
    if not inciso:
        graph.remove_nodes_from(iso)
    labels = {key: val for key, val in enumerate(pivot.index) if ((key not in iso) or inciso)}
    pos = nx.kamada_kawai_layout(graph)  # spring_layout planar_layout spiral_layout shell_layout kamada_kawai_layout fruchterman_reingold_layout
    # nx.draw_networkx(graph, pos, labels=labels)
    return graph, pos, labels, pivot


def networkx_2_plotly(graph, pos, pod, template, fwidth, fheight, vis=False):

    edge_x = []
    edge_y = []
    edge_trace = []
    for e0,e1,ew in graph.edges(data=True):
        x0, y0 = pos[e0]
        x1, y1 = pos[e1]
        edge_x = []
        edge_y = []
        edge_x.append(x0)
        edge_x.append(x1)
        # edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        # edge_y.append(None)
        width = (1.0-ew["weight"])
        
        n0 = pod.index[e0]
        n1 = pod.index[e1]        
        p0 = pod.pattern[e0]
        p1 = pod.pattern[e1]      
                
        text = "<b>Similarity: %.2f</b><br>%s %s<br>%s %s" % (width, p0, n0, p1, n1)
        
        edge_trace += [go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=4*width, color='#888'),
            mode='lines',
            visible=vis)]
        edge_trace += [go.Scatter(
            x=[0.5*(x0+x1)], 
            y=[0.5*(y0+y1)],
            mode='markers',
            customdata=[text],
            visible=vis,
            hovertemplate = '%{customdata}<extra></extra>',        
            marker=dict(
                opacity=0,
                color="lightgray"
                ))]
        
    # https://community.plotly.com/t/remove-trace-0-next-to-hover/33731
    node_trace = [go.Scatter(
        x=pod["x"], 
        y=pod["y"],
        mode='markers+text',
        visible=vis,
        text=pod["Name"],
        customdata=pod["t"],
        hovertemplate = '%{customdata}<extra></extra>',        
        # https://plotly.com/python/reference/layout/coloraxis/
        marker=dict(
            showscale=True,
            colorscale='Viridis',
            reversescale=True,
            color=pod["#P"],
            size=15,
            colorbar=dict(
                thickness=25,
                outlinewidth=0,
                title='#Podiums',
                #xanchor='left',
                #titleside='right'
            ),
            line_width=0))]
    
    data = edge_trace + node_trace
    fig = go.Figure(data=data,    
                    layout=go.Layout(
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        hoverlabel=dict(font=dict(family='monospace')),
                        template=template,
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    )
                    )
    
    fig.update_layout(template=template, width=fwidth, height=fheight)
    
    boo = [False]*len(data)
    
    return fig, boo, data


def plot_difficulty(colg, fin, names, scb, levels, template, fwidth, fheight):

    groups = fin[fin["Name"].isin(names)].groupby(["Level", colg])
    
    # idl = "F"
    # idc = "Boulder • Speed IFSC Climbing Worldcup (B,S) - Wujiang (CHN) 2019 WujiangWC 3 - 5 May"
    # idc = "GER"
    # idc = 2022
    # group = groups.get_group((idl, idc))
    
    tab = pd.DataFrame(np.nan, index=levels, columns=fin[colg].unique())
    for (idl, idc), group in groups:
        sub = group.loc[:, scb[::2]]    
        tot = np.nansum(~sub.isna())
        top = np.nansum(~sub.replace(np.inf, np.nan).isna())    
        tab.loc[idl, idc] = 100.0*top/tot
           
    if colg == "Comp":
        tab.index = ['(AVG = %.2f) ' % row.mean() + '% ' + idr for idr, row in tab.iterrows()]
        
    fig = px.imshow(tab,
                    template=template,
                    color_continuous_scale="Viridis",
                    labels={"x": colg,  "y": "Level", "color": "%Topped"},
                    width=fwidth, height=fheight
                    )
    
    fig.update_yaxes(
        tickmode="linear"
    )   
    
    if colg == "Comp":
        xline = [idi for idi, col in enumerate(tab.columns) if '2008' in col][0]-0.5
        fig.add_vline(x=xline)
        lenc = len(tab.columns)
        fig.update_xaxes(
            tickmode = 'array',
            tickvals = list(range(lenc)),
            ticktext = ['']*lenc
        )
        
    return fig


# %%# stop
