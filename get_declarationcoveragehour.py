# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 09:58:36 2021

@author: JPM
"""

import requests
import json
import pandas as pd
import datetime as dt


def get_declarationcoveragehour(start_date_str: str,
                                end_date_str: str,
                                save_to_parquet: bool = False) -> pd.DataFrame:
    '''
    Get elspot prices from EnergiDataService

    Parameters
    ----------
    start_date_str : str
        Start of period you want data from.
    end_date_str : str
        End of the period you want data from.
    save_to_file : bool, optional
        If you want the data saved this is set to True. The save name is
        elspot_prices_{start_date}_to_{end_date}.parquet. The default is False.

    Returns
    -------
    d_f : pandas.DataFrame
        Dataframe containing the elspot prices in hour resolution for the time
        period specified

    '''
    start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%d")

    url_call = "https://api.energidataservice.dk/datastore_search_sql"
    sql_call = f"""SELECT * FROM "declarationcoveragehour"
    WHERE "HourUTC" BETWEEN '{start_date}' AND '{end_date}'
    AND "PriceArea" BETWEEN 'DK1' AND 'DK2'"""

    response = requests.get(url_call,
                            params={"sql": ' '.join(sql_call.split())})
    response = response.content.decode()
    response = json.loads(response)

    d_f = pd.DataFrame(response['result']['records'])

    if save_to_parquet:
        file_name = 'data/get_declarationcoveragehour_'
        file_name += start_date_str + '_to_' + end_date_str + '.parquet'
        d_f.to_parquet(file_name)
    return d_f


if __name__ == '__main__':
    years = [2017, 2018, 2019, 2020]
    for year in years:
        start_date_str = str(year) + '-01-01'
        end_date_str = str(year) + '-12-31'
        d_f = get_declarationcoveragehour(start_date_str, end_date_str,
                                          save_to_parquet=True)
