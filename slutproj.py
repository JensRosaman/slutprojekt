import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg , NavigationToolbar2Tk
from time import time
import PySimpleGUI as sg



# Privata api nyckel till SteamWebApi
apiKey = "1661C2636C7937D634C34C6DA3218414"



userID = "76561199195339368"
# wilmer 76561199195339368
# jag 76561198427126142

sTime = time()

# Körs endast 1 gång
def cleanStoreData():
    "Rensar steamStore.csv och lämnar relevant data --> steamStore DataFrame"
    path = r"slutprojekt\steamStore.csv" # windows path till filen

    # CSV --> DF
    storeDf = pd.read_csv(path)
    
    # Slänger oanvända kolluner
    toDrop = [
         "required_age",
         "steamspy_tags",
         "positive_ratings",
         "negative_ratings",
         "english",
         "developer",
         "publisher",
         "platforms",
         "release_date"
    ]
    storeDf.drop(toDrop,axis=1, inplace=True)
    storeDf.reset_index(drop=True, inplace=True)

    return storeDf


def get_owned_games(userID):
    # Anger de saker som APIn ska hämta
    params = {
    'key': apiKey,
    'steamid': userID,
    'include_appinfo': 1,
    'include_played_free_games': 1
    }
    # Hämatar datan och lägger allt i response
    print("Kontaktar steam servern...")
    response = requests.get("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/" , params=params)

    # kollar om API förfrågan fungerade, exit kod 200 ger lyckad hämtning
    if response.status_code == 200:
        print("Data hämtad")
        # Gör det till ett python object
        response = response.json()
        # tar ut datan som är nested inuti response
        response = response["response"]
        return response

    else:
        raise Exception("Ingen kontakt med steam servern, vänligen försök igen eller undevik funktion tills vidare")

def user_games():
    "SteamUserID --> dataFrame with users games and playtime"
    # Hämtar användar info från SteamWebAPI
    userData = get_owned_games(userID)


    #with open(r'slutprojekt\data\user_data.json', 'r') as f:
        #userData = json.load(f)
    
    # Tar ut den nested datan ur json objektet --> användarens spel och tid spelat
    userLib = userData["games"]
    
    # Json -> DataFrame
    userLib = pd.json_normalize(userLib)

    # Specifierar den datan som ska tas bort och droppar den
    toDrop = [
         "has_leaderboards",
         #"playtime_2weeks",
         "content_descriptorids",
         "rtime_last_played",
         "img_icon_url",
         "has_community_visible_stats",
         'playtime_windows_forever',
         "playtime_mac_forever",
         "playtime_linux_forever"
         ]
    userLib = userLib.drop(toDrop,axis=1)
    
    return userLib





def sharedData(userLib,storeDf):
    "samlar den delade datan i en df. Input: userLib,storeDf"
    storeDf = pd.DataFrame(storeDf)
    userLib = pd.DataFrame(userLib)
    todrop = [
        "categories",
        "genres",
        "achievements",
    ]
    storeDf.drop(todrop,axis=1,inplace=True)
    #oldstoreDf = storeDf.copy()
    #for index, row in oldstoreDf.iterrows():
        #if row["appid"] in userLib["appid"].values:
            #print(row["appid"], " found")
            #continue
        #else:
            #storeDf.drop(index,inplace=True)

    # Skapar en df endast med appid som delas av både StoreDf och userlib
    sharedDf = storeDf[storeDf['appid'].isin(userLib['appid'])].reset_index(drop=True).copy(deep=True)
    userLib = userLib[userLib['appid'].isin(storeDf['appid'])].reset_index(drop=True).copy(deep=True)

    mergedDf = sharedDf.merge(userLib[['appid', 'playtime_forever']], on='appid', how='left')
    mergedDf.to_csv("merged.csv")
    #print(mergedDf.head(10))
    return mergedDf

        
    
def drawPlot(df,type):
    # gör det till en dataframe för att undevika problem + syntax highligthing
    df = pd.DataFrame(df)

    # skapar en till kollumn som visar procentuell skillnad mellan medelmåttigspeltid och användarens
    df["percent_diff"] = round((df["playtime_forever"]/df["median_playtime"]),1)
    
    # min -> tim
    df["playtime_forever"] = round((df["playtime_forever"] / 60),1)
    df["median_playtime"] = round((df["median_playtime"] / 60),1)
    

    # namn ger kollumnen mer användar vänligt
    df.rename(columns={"playtime_forever":"user_playtime"},inplace=True)

    dfPlaytime = df[['median_playtime','user_playtime','percent_diff','name']]
    dfPlaytime.sort_values(by="median_playtime")
    dfPlaytime.set_index('name',inplace=True)

    # Typ av graf
    if type == 1:
        ax = dfPlaytime.plot(kind='barh')
        for i, bar in enumerate(ax.containers):
            ax.bar_label(bar)
    
    draw_figure_w_toolbar(window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)
    

    




def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)



def pygMenu():
    sg.theme('black')
    layout = [
            [sg.Text("""Vänligen skriv in din steam userID \n Alternativt använd ett exempel id nedan:
                        Litet bibleotek - 76561199195339368
                        Stort - 76561198427126142""",key="-title")],
            [sg.Input(key="-userid")],
            [sg.Button("Skicka in")],
            [sg.Button("hej")],
            [sg.Button("hej")],
            [sg.Button("hej")],
            [sg.Button("hej")],
              ]

    window = sg.Window("menu", 
                       layout,
                       default_button_element_size=(12, 1))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        if event == "Skicka in":
            userInput = values["-userid"]
            print(f"Användaren skrev in {userInput}")

            if isValidSteamID(userInput):
                window["-title"].update("Använar ID noterad; Välj funktion nedan")

            
def isValidSteamID(steam_id):
    
    # hämta data
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={apiKey}&steamids={steam_id}"
    response = requests.get(url)
    data = response.json()

    # Kollar om det finns data i svaret
    if "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
        return True

    elif response.status_code != 200:
        print("Ej giltlig användar ID")
        return False
    else:
        return False




# TEMP 
#pgPlot(drawPlot(sharedData(user_games(),cleanStoreData()),1))
#pygMenu()
drawPlot(sharedData(user_games(),cleanStoreData()),1)
endTime = time()
print("Koden körde på ", round(endTime - sTime))
