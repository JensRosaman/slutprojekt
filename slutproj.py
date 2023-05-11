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



#userID = "76561199195339368"
# wilmer 76561199195339368
# jag 76561198427126142

sTime = time()

# Körs endast 1 gång
def cleanStoreData():
    "Rensar steamStore.csv och lämnar relevant data --> steamStore DataFrame"
    
    path = r"steamStore.csv" # windows path till filen

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
    print(f"Kontaktar steam servern med användar ID {userID}...")
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

def user_games(userID):
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

def isValidSteamID(userID):
    
    # hämta data
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={apiKey}&steamids={userID}"
    response = requests.get(url)
    data = response.json()

    # Kollar om det finns data i svaret, json börjar med en response embedd
    if "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
        print("Giltligt användar ID")
        return True

    elif response.status_code != 200:
        print("Ej giltlig användar ID")
        return False
    else:
        return False      
    



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

# Stulen kod ingen aning vad den gör för witch craft
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

#-------------------------------SimpleGui--------------------------

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


class plot:
    "Skapar och tillåter funktioner relaterade till en matplotlib fig, kan ändra vilka rows som är med"
    def __init__(self, df) -> None:
        self.df = pd.DataFrame(df)
        self.df["percent_diff"] = round((self.df["playtime_forever"] / self.df["median_playtime"]), 1)
        self.df["playtime_forever"] = round((self.df["playtime_forever"] / 60), 1)
        self.df["median_playtime"] = round((self.df["median_playtime"] / 60), 1)
        self.df.rename(columns={"playtime_forever": "user_playtime"}, inplace=True)

        self.dfPlaytime = self.df[['median_playtime', 'user_playtime', 'percent_diff', 'name']].copy()
        self.dfPlaytime.sort_values(by="median_playtime", inplace=True)
        self.dfPlaytime.set_index('name', inplace=True)    
        

    def filterRows(self,rowsToDrop):
        "filterar vilka rader som är med i dataframen med en lista som input"
        for name in rowsToDrop:
            self.dfPlaytime = self.dfPlaytime.drop(self.dfPlaytime[self.dfPlaytime['name'] == name].index)

    def drawFig(self, graphType=1):
        if graphType == 1:
            ax = self.dfPlaytime.plot(kind='barh')
            # Namn ger varje stapel till index
            for i, bar in enumerate(ax.containers):
                ax.bar_label(bar)
            
            # hämtar figure
        fig = ax.get_figure()
        return fig
    
 


def sgPlot():
    "Skapar ett pysimplegui fönster med kontroller där användaren kan se datan och kontrollera den"
    layout = [
        [sg.T('Graph')],
        [sg.B('Plot'), sg.B('Ändra spel') ,sg.Text("",key="-idText"), sg.Input(default_text="", key="-userid"), sg.Submit() ,  sg.B('Exit')],
        [sg.T("Exempel ID:"), sg.I("76561198427126142", readonly=True, size=20)],
        [sg.T('Controls:')],
        [sg.Canvas(key='controls_cv')],
        [sg.T('Figure:')],
        [sg.Column(
            layout=[
                [sg.Canvas(key='fig_cv',
                        # it's important that you set this size
                        size=(400 * 2, 400)
                        )]
            ],
            background_color='#DAE0E6',
            pad=(0, 0)
        )],
        [sg.B('Alive?')]
    ]
    window = sg.Window('Graph with controls', layout, finalize=True)
    userID = None



    # Kollar om användaren redan skrivit in userID för att förbättra användar vänligheten
    if userID == None:
        window["-idText"].update("Vänligen skriv användar Id i fältet")
    else:
        window["-userid"].update(defualt_text=userID)


    while True:
        event, values = window.read()
        print(event, values)
        if event in (sg.WIN_CLOSED, 'Exit'):  # Exit knapp
            break

        # kollar användarens data om den fungerar och sätter den i så fall --> userID
        elif event == "Submit":
            userInput = values["-userid"]
            print(f"Användaren skrev in {userInput}")
            if isValidSteamID(userInput):
                userID = userInput
                df = sharedData(user_games(userID),cleanStoreData())
                dfPlot = plot(df)
                window["-idText"].update("Användar ID noterad, Tryck på 'plot' för att börja grafa")
            
            else:
                window["-idText"].update("ID fungerade inte, vänlig kontrollera ID")
                window["-idText"].update(text_color='red')

        
        # Skapar ett til fönster med funktioner för att ta bort uppvisade spel
        elif event == "Ändra spel":
            games = df['name'].tolist()
            # Create the layout for the second window
            layout2 = [[sg.Text('Second Window')],
                       [sg.Checkbox(name, key="chk_{name}") for name in games],
                       [sg.B("Skicka in")],
                        [sg.Button('Stäng')]]

            # Create the second window
            window2 = sg.Window('Second Window', layout2, finalize=True)

            # Bring the second window to the front
            window2.bring_to_front()

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WINDOW_CLOSED or event2 == 'Stäng':
                    break
                
                elif event2 == "Skicka in":
                    checkedBoxes = []
                    for name in games:
                        if values2["chk_{name}"] is True:
                            checkedBoxes.append(name)
                
                    dfPlot.filterRows(checkedBoxes)
                    window2.close()

            window2.close()









        # plottar datan
        elif event == 'Plot':
            # Ritar plot
            if userID != None:
                fig = dfPlot.drawFig()
                draw_figure_w_toolbar(window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)
            else:
                window["-idText"].update("Skriv in ID först")
                window["-idText"].update(text_color='red')


    window.close()


sgPlot()

# TEMP 
#pgPlot(drawPlot(sharedData(user_games(),cleanStoreData()),1))
#pygMenu()
#drawPlot(sharedData(user_games(),cleanStoreData()),type=1)
endTime = time()
print("Koden körde på ", round(endTime - sTime))

