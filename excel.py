import pandas as pd


def extract_values_excel(path='CES Företagslistan.xlsx'):
    listOfTuple = []
    data = pd.read_excel(path)
    new_data = data.loc[:, ['Nr', 'Företagsnamn', 'Hemsida']]

    for col in range(len(new_data)):
        data_tuple = (data._get_value(col, 'Nr'), data._get_value(col, 'Företagsnamn'), data._get_value(col, 'Hemsida'))
        if type(data_tuple[-1]) == str and data_tuple[-1].startswith('http'):
            listOfTuple.append(data_tuple)

    return listOfTuple
