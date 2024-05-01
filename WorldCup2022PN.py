from statsbombpy import sb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch

comp = sb.competitions()
mat = sb.matches(competition_id = 43, season_id = 106)
def get_user_input():
    home_team = input("Enter the home team name: ")
    away_team = input("Enter the away team name: ")
    return home_team, away_team

def find_match_id(home_team, away_team, df_matches):
    # Strip whitespace and match case sensitivity
    df_matches['home_team'] = df_matches['home_team'].str.strip()
    df_matches['away_team'] = df_matches['away_team'].str.strip()
    home_team = home_team.strip()
    away_team = away_team.strip()
    
    # Debug output
    print(f"Searching for match: {home_team} vs {away_team}")
    
    match = df_matches[(df_matches['home_team'].str.lower() == home_team.lower()) & 
                       (df_matches['away_team'].str.lower() == away_team.lower())]
    if not match.empty:
        match_id = match.iloc[0]['match_id']
        print(f"Match found: ID {match_id}")
        return match_id
    else:
        print("Match not found. Please check the team names and try again.")
        return None


def generate_pass_network(match_id, home_team, away_team):
    events = sb.events(match_id)
    tactics = events[events['tactics'].notnull()]
    tactics = tactics[['tactics', 'team', 'type']]
    tactics = tactics[tactics['type'] == 'Starting XI']
    tactics_1 = tactics[tactics['team'] == home_team]
    tactics_2 = tactics[tactics['team'] == away_team]
    # Use .iloc to access the first row
    dict_1 = tactics_1.iloc[0]['tactics']['lineup'] if not tactics_1.empty else None
    dict_2 = tactics_2.iloc[0]['tactics']['lineup'] if not tactics_2.empty else None

    if dict_1 is not None and dict_2 is not None:
        lineup_1 = pd.DataFrame.from_dict(dict_1)
        lineup_2 = pd.DataFrame.from_dict(dict_2)
    else:
        print(f"Could not find starting lineup for one or both of the teams: {home_team}, {away_team}")


    players_1 = {}
    for i in range(len(lineup_1)):
        key = lineup_1.player[i]['name']
        val = lineup_1.jersey_number[i]
        players_1[key] = str(val)
    players_2 = {}
    for i in range(len(lineup_2)):
        key = lineup_2.player[i]['name']
        val = lineup_2.jersey_number[i]
        players_2[key] = str(val)
    
    print(players_1)
    print(players_2)
    
    events_pass = events[['minute', 'second', 'team', 'type', 'location', 'pass_end_location', 'pass_outcome', 'player']]
    pass_events_1 = events_pass[events_pass['team'] == home_team]
    pass_events_2 = events_pass[events_pass['team'] == away_team]
    pn_events_1 = pass_events_1[pass_events_1['type'] == 'Pass']
    pn_events_2 = pass_events_2[pass_events_2['type'] == 'Pass']
    
    pn_events_1['pass_maker'] = pn_events_1['player']
    pn_events_1['pass_receiver'] = pn_events_1['player'].shift(-1) 
    pn_events_2['pass_maker'] = pn_events_2['player']
    pn_events_2['pass_receiver'] = pn_events_2['player'].shift(-1) 


    pn_events_1 = pn_events_1[pn_events_1['pass_outcome'].isnull() == True].reset_index()
    pn_events_2 = pn_events_2[pn_events_2['pass_outcome'].isnull() == True].reset_index()

    sub_1 = pass_events_1[pass_events_1['type'] == 'Substitution']
    sub_2 = pass_events_2[pass_events_2['type'] == 'Substitution']

    sub_1_minute = np.min(sub_1['minute'])
    sub_1_minute_data = sub_1[sub_1['minute'] == sub_1_minute]
    sub_1_second = np.min(sub_1_minute_data['second'])

    sub_2_minute = np.min(sub_2['minute'])
    sub_2_minute_data = sub_2[sub_2['minute'] == sub_2_minute]
    sub_2_second = np.min(sub_2_minute_data['second'])

    print('Testing Testing Testing',sub_1_minute)

    pn_events_1 = pn_events_1[(pn_events_1['minute'] < sub_1_minute)]
    pn_events_2 = pn_events_2[(pn_events_2['minute'] < sub_2_minute)]

    Loc = pn_events_1['location']
    Loc = pd.DataFrame(Loc.to_list(), columns=['pass_maker_x', 'pass_maker_y'])

    Loc_end = pn_events_1['pass_end_location']
    Loc_end = pd.DataFrame(Loc_end.to_list(), columns=['pass_receiver_x', 'pass_receiver_y'])

    pn_events_1['pass_maker_x'] = Loc['pass_maker_x']
    pn_events_1['pass_maker_y'] = Loc['pass_maker_y']
    pn_events_1['pass_receiver_x'] = Loc_end['pass_receiver_x']
    pn_events_1['pass_receiver_y'] = Loc_end['pass_receiver_y']

    pn_events_1 = pn_events_1[['minute', 'second', 'team', 'type', 'pass_outcome',
                               'player', 'pass_maker', 'pass_receiver', 'pass_maker_x',
                               'pass_maker_y', 'pass_receiver_y', 'pass_receiver_x']]
    
    Loc = pn_events_2['location']
    Loc = pd.DataFrame(Loc.to_list(), columns=['pass_maker_x', 'pass_maker_y'])

    Loc_end = pn_events_2['pass_end_location']
    Loc_end = pd.DataFrame(Loc_end.to_list(), columns=['pass_receiver_x', 'pass_receiver_y'])

    pn_events_2['pass_maker_x'] = Loc['pass_maker_x']
    pn_events_2['pass_maker_y'] = Loc['pass_maker_y']
    pn_events_2['pass_receiver_x'] = Loc_end['pass_receiver_x']
    pn_events_2['pass_receiver_y'] = Loc_end['pass_receiver_y']

    pn_events_2 = pn_events_2[['minute', 'second', 'team', 'type', 'pass_outcome',
                               'player', 'pass_maker', 'pass_receiver', 'pass_maker_x',
                               'pass_maker_y', 'pass_receiver_y', 'pass_receiver_x']]
    
    pn_events_1.reset_index(inplace=True)
    pn_events_2.reset_index(inplace=True)

    average_loc_1 = pn_events_1.groupby('pass_maker').agg({'pass_maker_x':['mean'],
                                                           'pass_maker_y':['mean','count']})
    average_loc_2 = pn_events_2.groupby('pass_maker').agg({'pass_maker_x':['mean'],
                                                           'pass_maker_y':['mean','count']})
    
    average_loc_1.columns = ['pass_maker_x', 'pass_maker_y', 'count']
    average_loc_2.columns = ['pass_maker_x', 'pass_maker_y', 'count']

    #pass_1 = pn_events_1.groupby(['pass_maker', 'pass_receiver']).index.count().reset_index(drop=True)
    #pass_2 = pn_events_2.groupby(['pass_maker', 'pass_receiver']).index.count().reset_index(drop=True)

    pass_1 = pn_events_1.groupby(['pass_maker', 'pass_receiver']).index.count().reset_index()
    pass_2 = pn_events_2.groupby(['pass_maker', 'pass_receiver']).index.count().reset_index()

    #print(pass_1)
    #print(pass_2)




    pass_1.rename(columns = {'index': 'number_of_passes'}, inplace = True)
    pass_2.rename(columns = {'index': 'number_of_passes'}, inplace = True)

    pass_1 = pass_1.merge(average_loc_1, left_on = 'pass_maker', right_index = True)
    pass_2 = pass_2.merge(average_loc_2, left_on = 'pass_maker', right_index = True)

    pass_1 = pass_1.merge(average_loc_1, left_on = 'pass_receiver', right_index = True, suffixes = ['', '_receipt'])
    pass_1.rename(columns = {'pass_maker_x_receipt': 'pass_receiver_x',
                           'pass_maker_y_receipt': 'pass_receiver_y',
                           'count_receipt': 'number_of_passes_received'}, inplace = True)
    #pass_1 = pass_1[pass_1['pass_maker'] != pass_1['pass_receiver']].reset_index()

    pass_2 = pass_2.merge(average_loc_2, left_on = 'pass_receiver', right_index = True, suffixes = ['', '_receipt'])
    pass_2.rename(columns = {'pass_maker_x_receipt': 'pass_receiver_x',
                           'pass_maker_y_receipt': 'pass_receiver_y',
                           'count_receipt': 'number_of_passes_received'}, inplace = True)
    #pass_2 = pass_2[pass_2['pass_maker'] != pass_2['pass_receiver']].reset_index()

    pass_1 = pass_1.dropna(subset=['pass_maker_x', 'pass_maker_y', 'pass_receiver_x', 'pass_receiver_y'])
    pass_2 = pass_2.dropna(subset=['pass_maker_x', 'pass_maker_y', 'pass_receiver_x', 'pass_receiver_y'])

    print(average_loc_1)



    #Home
    pitch = pitch = Pitch(pitch_color = 'grass', line_color = 'white', stripe = True,
                        goal_type = 'box', label = False,
                      axis = True, tick = False)
    fig, ax = pitch.draw()
    arrows = pitch.arrows(pass_1.pass_maker_x, pass_1.pass_maker_y,
                      pass_1.pass_receiver_x, pass_1.pass_receiver_y, lw = 5,
                      color = 'white', zorder = 1, ax = ax)
    nodes = pitch.scatter(average_loc_1.pass_maker_x, average_loc_1.pass_maker_y,
                      s = 350, color = '#87CEFA', edgecolor = 'white', linewidth = 1, alpha = 1, ax = ax)

    for index, row in average_loc_1.iterrows():
        jersey_number = players_1.get(row.name, 'Not found')
        pitch.annotate(jersey_number, xy=(row.pass_maker_x, row.pass_maker_y),
            c = 'white', va = 'center', ha = 'center', size = 10, ax = ax)
    plt.title(home_team, size = 20)
    plt.show()

    #Away
    pitch = pitch = Pitch(pitch_color = 'grass', line_color = 'white', stripe = True,
                        goal_type = 'box', label = False,
                      axis = True, tick = False)
    fig, ax = pitch.draw()
    arrows = pitch.arrows(120 -pass_2.pass_maker_x, pass_2.pass_maker_y,
                      120 -pass_2.pass_receiver_x, pass_2.pass_receiver_y, lw = 5,
                      color = 'white', zorder = 1, ax = ax)
    nodes = pitch.scatter(120 -average_loc_2.pass_maker_x, average_loc_2.pass_maker_y,
                      s = 350, color = '#CBC3E3', edgecolor = 'white', linewidth = 1, alpha = 1, ax = ax)

    for index, row in average_loc_2.iterrows():
        jersey_number = players_2.get(row.name, 'Not found')
        pitch.annotate(jersey_number, xy=(120 - row.pass_maker_x, row.pass_maker_y),
            c = 'white', va = 'center', ha = 'center', size = 10, ax = ax)
    plt.title(away_team, size = 20)
    plt.show()


# Main script execution
if __name__ == "__main__":
    home_team, away_team = get_user_input()
    match_id = find_match_id(home_team, away_team, mat)
    if match_id is not None:
        generate_pass_network(match_id, home_team, away_team)















    
    







    
    









