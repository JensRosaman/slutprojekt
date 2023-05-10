import PySimpleGUI as sg
import numpy as np
import pandas as pd
"""
    Embedding the Matplotlib toolbar into your application

"""
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Age': [25, 30, 35, 40],
    'City': ['New York', 'London', 'Paris', 'Tokyo']
}

data = pd.DataFrame(data)

test = data['Age','City',None]

print(test.head())