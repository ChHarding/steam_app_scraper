# https://nik-davis.github.io/posts/2019/steam-data-collection/

# standard library imports
import csv
import datetime as dt
import json
import os
import statistics
import time
import pickle
from glob import glob


# third-party imports
import numpy as np
import pandas as pd
import urllib3
import requests
from pprint import pprint


def get_request(url, parameters=None):
    """Return json-formatted response of a get request using optional parameters.
    
    Parameters
    ----------
    url : string
    parameters : {'parameter': 'value'}
        parameters to pass as part of get request
    
    Returns
    -------
    json_data
        json-formatted response (dict-like)
    """
    urllib3.disable_warnings()
    try:
        time.sleep(0.2) # wait so we don't flood the server
        response = requests.get(url=url, params=parameters, verify=False)
    except Exception as s:
        print('SSL Error:', s)
        
        for i in range(5, 0, -1):
            print('\rWaiting... ({})'.format(i), end='')
            time.sleep(1)
        print('\rRetrying.' + ' '*10)
        
        # recursively try again
        return get_request(url, parameters)
    
    if response:
        return response.json()
    else:
        # response is none usually means too many requests. Wait and try again 
        print('No response, waiting 10 seconds...')
        time.sleep(10)
        print('Retrying.')
        return get_request(url, parameters)

def parse_steam_request(appid, name):
    """Unique parser to handle data from Steam Store API.
    
    Returns : json formatted data (dict-like)
    """
    url = "http://store.steampowered.com/api/appdetails/"
    parameters = {"appids": appid}
    
    json_data = get_request(url, parameters=parameters)
    json_app_data = json_data[str(appid)]
    
    if json_app_data['success']:
        data = json_app_data['data']
        return data
    
    return None # Error, go no data

# MAIN


# info to get per app from steamspy
'''
appid - Steam Application ID. If it's 999999, then data for this application is hidden on developer's request, sorry.
name - game's name
developer - comma separated list of the developers of the game
publisher - comma separated list of the publishers of the game
score_rank - score rank of the game based on user reviews
owners - owners of this application on Steam as a range.
average_forever - average playtime since March 2009. In minutes.
average_2weeks - average playtime in the last two weeks. In minutes.
median_forever - median playtime since March 2009. In minutes.
median_2weeks - median playtime in the last two weeks. In minutes.
ccu - peak CCU yesterday.
price - current US price in cents.
initialprice - original US price in cents.
discount - current discount in percents.
'''

if 0:  # set to 0 once you have a app list csv
    # get appid, name and genre in batches of 1000
    steam_spy_df_lst = []
    num_pages = 10
    for p in range(0, num_pages):
        url = "https://steamspy.com/api.php"
        parameters = {"request": "all", "page": p}

        # request 'all' from steam spy and parse into dataframe
        json_data = get_request(url, parameters=parameters)
        steam_spy = pd.DataFrame.from_dict(json_data, orient='index')
        steam_spy_df_lst.append(steam_spy)
        print(str(p), end=" ")
    print()
    # make into single df
    steam_spy_all = pd.concat(steam_spy_df_lst, axis=0, ignore_index=True)

    # make new df from appid and name, sort by appid
    app_list = steam_spy_all[['appid', 'name']].sort_values('appid').reset_index(drop=True)

    # save to csv for later
    app_list.to_csv(f'app_list.csv', index=False)
    print("got", len(app_list), "steam apps")


# Example of what info will be scraped from store.steampowered.com given an id and name
d = parse_steam_request(47890,"The Sims 3")
pprint(d)

# list of app ids with names
app_list = pd.read_csv('app_list.csv')


# make new columns to store scrape results
app_list['categories'] = None # list of categories
app_list['genres'] = None # list of genres


# create several smaller csvs that can be glue
start = 460
end = 480
for i in range(start, end): # set your batch limits here
    appid = app_list["appid"].loc[i]
    name = app_list["name"].loc[i]

    data = parse_steam_request(appid, name)
    if data != None:
        try:
            cat_dict = data["categories"]
            genre_dict = data["genres"]
        except Exception as e:
            print(e) # usually a key error
        else:
            cat_lst = [d["description"] for d in cat_dict]
            genre_lst = [d["description"] for d in genre_dict]

            app_list.at[i, "categories"] = cat_lst
            app_list.at[i, "genres"] = genre_lst

            print(i, app_list.loc[i])
    else:
        print("Error for", appid, name)

# Save the current chunk as pickle so we can read them all later with pd.read_pickle()
# and concat them into a single df
current_chunk = app_list.loc[start:end]      
print(current_chunk)
current_chunk.to_pickle(f'app_data_{start}_{end-1}.pkl')

# make full df from all .pkl files
pkl_lst = glob("*.pkl")
df_lst = [pd.read_pickle(fn) for fn in pkl_lst]

full_df = pd.concat(df_lst, axis=0, ignore_index=True)
full_df = full_df.sort_values('appid').reset_index(drop=True) # sort by app id and re-index
full_df.to_csv("app_data_full.csv", mode="w+", index=False)