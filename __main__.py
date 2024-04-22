import dash
from dash import dcc, html,dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import numpy as np
from collections import Counter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


df = pd.read_json('output/output.json').dropna(subset='awayScore')

df['homeScore'] = df['homeScore'].astype(float)

season = "2014-2015"
team = "STADE DE REIMS"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id = "dropdownSeason",
            options = [{'label' : season, 'value': season} for season in df['season'].unique()],
            value = df['season'].unique()[0]
        )),
        dbc.Col(dcc.Dropdown(id="dropdown_Team"))
    ]),
    dbc.Row([
        dbc.Col([dcc.Graph(id="graph1")],width=3),
        dbc.Col([dcc.Graph(id="graph2")],width=4),
        dbc.Col([dcc.Graph(id='graph3')],width=5)
    ]),
    dbc.Row([
        dbc.Col([dcc.Graph(id="graph4")],width=4),
        dbc.Col(dash_table.DataTable(id='table1',style_table={'overflowX': 'auto'}),width=4,style={'margin': 'auto'}),
        dbc.Col([dcc.Graph(id="graph5")],width=4)

    ])
    ])

@app.callback(
    [Output('dropdown_Team', 'options'),
    Output('dropdown_Team', 'value')],
    [Input('dropdownSeason', 'value')])

def getTeam(season) :
    filterData = df[df['season']==season]
    homeTeam = filterData['homeTeam'].unique()
    val = homeTeam[0]
    return [{"label" : team, "value":team} for team in homeTeam],val

@app.callback(
    [Output('graph1',"figure"),
     Output('graph2','figure'),
     Output('graph3','figure'),
     Output('graph4',"figure"),
     Output('table1','data'),
     Output("graph5","figure")
    ],
    [Input('dropdownSeason',"value"),
     Input('dropdown_Team','value')]
)
def dtm(season,team):
    
    dtm = df[(df['season']==season)]
    dtm = dtm[(dtm['homeTeam'] == team) | (dtm['awayTeam']==team)]
    dtm.loc[(dtm['homeTeam']==team) & (dtm['homeScore']>dtm['awayScore']),'vainqueur'] = 'win'
    dtm.loc[(dtm['homeTeam']==team) & (dtm['homeScore']<dtm['awayScore']),'vainqueur'] = 'lose'
    dtm.loc[(dtm['awayTeam']==team) & (dtm['homeScore']<dtm['awayScore']),'vainqueur'] = 'win'
    dtm.loc[(dtm['awayTeam']==team) & (dtm['homeScore']>dtm['awayScore']),'vainqueur'] = 'lose'
    dtm.loc[dtm['vainqueur'].isna(),'vainqueur'] = 'draw'
    
    pieData = dtm.groupby(['vainqueur'],as_index=False).count()
    pieData = pieData[['vainqueur','id']].rename(columns={'id':'value'})
    pieChart = px.pie(pieData,names='vainqueur',values='value').update_layout(showlegend=False,title_x=0.5).update_traces(textposition='inside', textinfo='percent+label')
    
    dtm.loc[dtm['homeTeam']==team,'domicile'] = 'Home'
    dtm.loc[dtm['homeTeam']!=team,'domicile'] = 'Away'
    barData = dtm.groupby(['vainqueur','domicile'],as_index=False).count()
    barData = barData[['vainqueur','domicile','id']]
    barChart = px.bar(barData,x='vainqueur',y='id',color="domicile").update_layout(showlegend=False,title_x=0.5)

    dtm.loc[(dtm['homeTeam']==team) & (dtm['homeScore']>5),'goal'] = "Over 5"
    dtm.loc[(dtm['homeTeam']==team) & (dtm['goal'].isna()),'goal'] = dtm['homeScore']
    dtm.loc[(dtm['awayTeam']==team) & (dtm['awayScore']>5),'goal'] = "Over 5"
    dtm.loc[(dtm['awayTeam']==team) & (dtm['goal'].isna()),'goal'] = dtm['awayScore']
    dtm['goal'] = dtm['goal'].astype(str)
    goalData = dtm.groupby(['goal'],as_index=False).count()
    goalChart = px.bar(goalData,x='goal',y='id')

    losingGame = dtm[dtm['vainqueur']=="lose"]
    loser = losingGame['homeTeam'].values.tolist() + losingGame['awayTeam'].values.tolist()
    loserDt= pd.DataFrame.from_dict(Counter(loser),orient="index").reset_index().rename(columns={'index':'names',0:'values'})
    loserDt = loserDt[loserDt['names']!=team].sort_values(by='values',ascending=False).head(5)
    loseChart = px.bar(loserDt,x='names',y='values')

    last5DaysResults = dtm.sort_values(by=['matchDay'],ascending=False).head(5)
    last5DaysResults['5 last Match'] = last5DaysResults['homeTeam'] + " " +last5DaysResults['homeScore'].astype(int).astype('str') + " - " + last5DaysResults['awayScore'].astype(int).astype('str') + " " +last5DaysResults['awayTeam']
    last5DaysResults = last5DaysResults[['5 last Match']]
    last5DaysResults
    tableRecom = last5DaysResults.to_dict('records')


    seasonDt = df[df['season']==season]
    seasonDt['points'] = seasonDt.apply(lambda row: 3 if row['homeScore'] > row['awayScore'] else (0 if row['homeScore'] < row['awayScore'] else 1), axis=1)
    team_stats = seasonDt.groupby('homeTeam').agg({
        'points': 'sum',
        'homeScore': 'sum',  # Buts marqués à domicile
        'awayScore': 'sum'   # Buts reçus à domicile
    }).rename(columns={'homeScore': 'goals_for', 'awayScore': 'goals_against'})
    scaler = StandardScaler()
    team_stats_scaled = scaler.fit_transform(team_stats)

    # Clustering K-means
    kmeans = KMeans(n_clusters=2, random_state=0)
    team_stats['cluster'] = kmeans.fit_predict(team_stats_scaled)
    team_stats['goal_difference'] = team_stats['goals_for'] - team_stats['goals_against']
    team_stats.reset_index(inplace=True)
    team_stats.loc[team_stats['homeTeam']==team,'cluster'] = 3
    ClusterTeams = px.scatter(team_stats, x='goals_for', y='goals_against', color='cluster',hover_name='homeTeam')
    # Ajustement du style des marqueurs
    ClusterTeams.update_layout(showlegend=False).update_traces(marker=dict(size=15, line=dict(width=2, color='DarkSlateGrey')))

    return pieChart,barChart,goalChart,loseChart,tableRecom,ClusterTeams



if __name__ == '__main__':
    app.run_server(debug=True)
