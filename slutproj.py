import requests
import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg , NavigationToolbar2Tk
from time import time
import PySimpleGUI as sg

# Privata api nyckel till SteamWebApi
apiKey = "1661C2636C7937D634C34C6DA3218414"




sTime = time()
def getFilePath(fileName):
    scriptPath = os.path.abspath(__file__)
    filePath = os.path.join(os.path.dirname(scriptPath), fileName)
    return filePath



# Körs endast 1 gång
def cleanStoreData():
    "Rensar steamStore.csv och lämnar relevant data --> steamStore DataFrame"
    
    
    csvFile = "steamStore.csv"
    filePath = getFilePath(csvFile)



    # CSV --> DF
    storeDf = pd.read_csv(filePath)
    
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


def get_owned_games(userID: str):
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

def user_games(userID: str):
    "SteamUserID --> dataFrame with users games and playtime"
    # Hämtar användar info från SteamWebAPI
    userData = get_owned_games(userID)


 
    
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

    # syntax higlighting
    storeDf = pd.DataFrame(storeDf)
    userLib = pd.DataFrame(userLib)
    todrop = [
        "categories",
        "genres",
        "achievements",
    ]
    storeDf.drop(todrop,axis=1,inplace=True)

    # Skapar en df endast med appid som delas av både StoreDf och userlib
    sharedDf = storeDf[storeDf['appid'].isin(userLib['appid'])].reset_index(drop=True).copy(deep=True)
    userLib = userLib[userLib['appid'].isin(storeDf['appid'])].reset_index(drop=True).copy(deep=True)

    #Sätter ihop dem
    mergedDf = sharedDf.merge(userLib[['appid', 'playtime_forever']], on='appid', how='left')
    return mergedDf

def isValidSteamID(userID: str) -> bool:
    "Kollar om det givna användar id'et är giltligt och finns i steam databasen"
    # hämtar data
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
    


# stulen kod github
def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        # förstör barn
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

# witch craft
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

#-------------------------------SimpleGui--------------------------

class plot:
    """
    Skapar och tillhandahåller funktioner relaterade till en matplotlib fig, kan ändra vilka rows som är med.
    rowsToDisplay: Anger hur många rader top till botten av de mest spelade spelen utifrån användaren ska visas i .drawFig
    """
    def __init__(self, df: int = 10) -> None:
        self.df = pd.DataFrame(df)
        # Skapar en kolumn där förhållandet mellan de två andra kollumnerna visas
        self.df["percent_diff"] = round((self.df["playtime_forever"] / self.df["median_playtime"]), 1)

        # Omvandlar från minut -> timmar och avrundar
        self.df["playtime_forever"] = round((self.df["playtime_forever"] / 60), 1)
        self.df["median_playtime"] = round((self.df["median_playtime"] / 60), 1)

        #Updatetar namn för att förbättra användarvänligheten
        self.df.rename(columns={"playtime_forever": "User Playtime"}, inplace=True)

        self.dfPlaytime = self.df[['median_playtime', 'User Playtime', 'percent_diff', 'name']].copy()
        self.dfPlaytime.set_index('name', inplace=True) 
        self.dfPlaytime.sort_values(by="User Playtime", inplace=True, axis=0)

        # Tar bort värden som är "inf" som är en bug
        self.dfPlaytime['percent_diff'].replace(np.inf, 0, inplace=True)
        self.maxDiff = self.dfPlaytime['percent_diff'].max()
        self.nameMaxDiff = self.dfPlaytime['percent_diff'].idxmax()

    def changeHead(self, rowsToDisplay):
        "Changes the dfPlaytimeHead value to a new specefied value"
        self.dfPlaytimeHead = self.dfPlaytime.head(rowsToDisplay)

    def filterRows(self,rowsToDrop):
        "filterar vilka rader som är med i dataframen med en lista som input"
        for name in rowsToDrop:
            self.dfPlaytime.drop(self.dfPlaytime[self.dfPlaytime.index == name].index, inplace=True)
            self.df.drop(self.df[self.df.index == name].index, inplace=True)


    def drawFig(self, graphType: int=1, rowsToDisplay: int = None):
        "Ritar ploten och returnerar en figure"
        if graphType == 1:
            if rowsToDisplay is None:
                ax = self.dfPlaytime.plot(kind='barh')
                print("visar alla spel")
            else:
                ax = self.dfPlaytime.head(rowsToDisplay).plot(kind="barh")
                print(f"visar {rowsToDisplay} spel")
            # Sätter stapelns värde bredvid stapeln - https://towardsdatascience.com/7-steps-to-help-you-make-your-matplotlib-bar-charts-beautiful-f87419cb14cb
            for i, bar in enumerate(ax.containers):
                    ax.bar_label(bar)

            ax.spines[['right', "top", "bottom"]].set_visible(False)       
            # hämtar figure
        fig = ax.get_figure()
        return fig
    
 


def sgPlot(userID:str = None):
    "Skapar ett pysimplegui fönster med kontroller där användaren kan se datan och kontrollera den"

    def updateData():
        "Visar grafen i pysimplegui fönstret"

        # Kontrollerar att använder id är anget och skapar en figur och plottar den
        if userID != None:
                fig = dfPlot.drawFig(rowsToDisplay=rowsToDisplay)
                draw_figure_w_toolbar(window['fig_cv'].TKCanvas, fig, window['controls_cv'].TKCanvas)
        else:
            window["-idText"].update("Skriv in ID först")
            window["-idText"].update(text_color='red')

        # Hämtar steam användar namnet hård kodat in wilmer pga olämligt namn
        if userID != "76561199195339368":
            url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={apiKey}&steamids={userID}'
            response = requests.get(url)
            data = response.json()
            
            if 'response' in data and 'players' in data['response']:
                players = data['response']['players']
                if players:
                    username = players[0]['personaname']
            else:
                print("Problem med att hämta användarnamn")
            
        else:
            username = "Wilmer"
        window["-graphTitle"].update(f"Visar: {username}")
        print("Visar ", username)
        window["-mostplayed"].update(f"Du har spelat {dfPlot.nameMaxDiff} {dfPlot.maxDiff} gånger mer än den meddelmåtigaspelaren!")
    # sätter ett defualt använddar namn innan användaren skrivit in sitt ID
    username = "Ingen"


    # Specifierar mängden data som ska plotas
    rowsToDisplay = 15



    sg.theme("DarkBlue")
    # skapar layout
    layout = [
        [sg.B('Ändra spel'), sg.B("Ändra staplar") ,sg.Text("",key="-idText"), sg.Input(key="-userid", background_color="white", text_color="Black"), sg.Submit("Submit/reset") ,  sg.B('Exit')],
        [sg.T('Rader som plottas, skriv "Alla" för att visa alla', key="-rowTitle"),sg.Input(f"{rowsToDisplay}", size=5, key="-rows"), sg.Submit("Ange") , sg.T("Exempel ID:"), sg.I("76561199195339368", readonly=True, size=20, text_color="black")],
        [sg.T('Controls:')],
        [sg.Canvas(key='controls_cv'), sg.T("", key="-mostplayed")],
        [sg.Text(f'Visar: {username}',key="-graphTitle")],
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
    ]
    # skapar fönstret
    window = sg.Window('Steam Graph', layout, grab_anywhere_using_control=True , finalize=True)



    # Kollar om användaren redan skrivit in userID för att förbättra användar vänligheten
    if userID == None:
        window["-idText"].update("Vänligen skriv användar Id i fältet")
    else:
        window["-userid"].update(userID)
        df = sharedData(user_games(userID),cleanedStoreData)
        dfPlot = plot(df)
        updateData()

    while True:
        event, values = window.read()
        print(event, values)
        if event in (sg.WIN_CLOSED, 'Exit'):  # Exit knapp
            break
            
        elif event == "Ange":
            userInput = values["-rows"]
            try:
                if userInput == "Alla":
                    rowsToDisplay = None
                else:
                    userInput = int(userInput)
                    if userInput <= len(dfPlot.dfPlaytime.index.to_list()):
                        rowsToDisplay = userInput
                    else:
                        window["-rows"].update(f"{rowsToDisplay}")
                
                window["-rowTitle"].update("Nytt värde noterat")
                updateData()
            except:
                print("Exception förebyggd")
                window["-rows"].update(f"{rowsToDisplay}")
            
        # kollar användarens data om den fungerar och sätter den i så fall --> userID
        elif event == "Submit/reset":
            userInput = values["-userid"]
            print(f"Användaren skrev in {userInput}")
            if isValidSteamID(userInput):
                userID = userInput
                df = sharedData(user_games(userID),cleanedStoreData)
                dfPlot = plot(df)
                window["-idText"].update("Användar ID noterad")
                window["-idText"].update(text_color='white')
                updateData()

            
            else:
                window["-idText"].update("ID fungerade inte, vänlig kontrollera ID")
                window["-idText"].update(text_color='red')

        
        # Skapar ett til fönster med funktioner för att ta bort uppvisade spel
        elif event == "Ändra spel":
            games = dfPlot.dfPlaytime.index.to_list()
            checkboxes = [[sg.Checkbox(name, key=f"chk_{name}")] for name in games]

            checkbox_column = sg.Column(checkboxes, scrollable=True, vertical_scroll_only=True, size=(300, 200))

            layout2 = [
                [sg.Text('Tar bort de valda spelen som standard läge'),sg.Checkbox("Visa endast valda spel:", key="mode")],
                [sg.Text("", key="-errorText", text_color='red')],
                [checkbox_column],
                [sg.B("Skicka in")],
                [sg.Button('Stäng')]
            ]

            # Create the second window
            window2 = sg.Window('Second Window', layout2, finalize=True)
            window2.bring_to_front()

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WINDOW_CLOSED or event2 == 'Stäng':
                    break

                elif event2 == "Skicka in":
                    checkedBoxes = []
                    for name in games:
                        if values2[f"chk_{name}"] is True:
                            checkedBoxes.append(name)
                    print("Användaren bockade av: ", checkedBoxes)

                    # Om läge två är valt ta bort alla spel förutom de valda
                    if values2["mode"] is True:
                        # tar bort de valda värdena från inputen till filterRows
                        gamesToRemove = list(set(dfPlot.dfPlaytime.index) - set(checkedBoxes))
                        #filterar raderna
                        dfPlot.filterRows(gamesToRemove)
                    else:
                        if len(checkedBoxes) >= len(dfPlot.dfPlaytime.index.to_list()):
                            window["-errorText"].update("Du kan inte bocka av alla spel")
                        else:   
                            # Tar bort de valda elementen
                            dfPlot.filterRows(checkedBoxes)
                    updateData()
                    window2.close()

            window2.close()






        elif event == "Ändra staplar":
            # Hämtar de collumner som plottas
            columns = dfPlot.dfPlaytime.columns.to_list()
            checkboxes = [[sg.Checkbox(column, key=f"chk_{column}")] for column in columns]

            checkboxColumn = sg.Column(checkboxes, scrollable=True, vertical_scroll_only=True, size=(300, 200))

            layout3 = [
                [sg.Text('Välj de staplar som skall tas att ta bort')],
                [checkboxColumn],
                [sg.B("Skicka in")],
                [sg.Button('Stäng')]
            ]

            # Create the second window
            window3 = sg.Window('Ändra staplar', layout3, finalize=True)
            window3.bring_to_front()

            while True:
                event3, values3 = window3.read()

                if event3 == sg.WINDOW_CLOSED or event3 == 'Stäng':
                    break

                elif event3 == "Skicka in":
                    checkedBoxes = []
                    for column in columns:
                        if values3[f"chk_{column}"] is True:
                            checkedBoxes.append(column)
                    print("Användaren bockade av: ", checkedBoxes)
                    dfPlot.dfPlaytime.drop(checkedBoxes, axis=1, inplace=True)
                    updateData()
                    window3.close()

            window3.close()
    window.close()

if __name__ == "__main__":
    cleanedStoreData = cleanStoreData()
    sgPlot(userID="76561198372292545")
    # vidar 76561198372292545
    # TEMP 
    endTime = time()
    print("Koden körde på ", round(endTime - sTime))

