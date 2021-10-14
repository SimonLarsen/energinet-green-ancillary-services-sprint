# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 14:00:49 2021

@author: JPM
"""
import pandas as pd


def get_prod_proportion(file: str,
                        start_date: str,
                        end_date: str,
                        dist_area: str) -> pd.DataFrame:
    '''


    Parameters
    ----------
    start_date : TYPE
        DESCRIPTION.
    end_date : TYPE
        DESCRIPTION.
    dist_area : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    non_ve = ['Affald', 'Atomkraft', 'Biogas', 'Halm', 'Kul', 'Naturgas',
              'Olie', 'Træ_mm']

    df = pd.read_parquet(file)
    df = df.drop(columns=['_id', 'Edition', 'HourDK'])
    df = df[df['ProductionGroup'].isin(non_ve)]

    df_dk = df[df['PriceArea'] == dist_area]

    df_dk = df_dk[df_dk['HourUTC'] >= start_date]
    df_dk = df_dk[df_dk['HourUTC'] < end_date]

    df_group_dk = df_dk.groupby(['HourUTC', 'ProductionGroup']).sum()

    df_group_dk = df_group_dk.reset_index()

    df_tot_per_prod = df_group_dk.groupby('ProductionGroup').sum()
    total = df_tot_per_prod.sum()

    df_mean_per_prod = df_tot_per_prod/total

    df_mean_per_prod = df_mean_per_prod.reset_index()

    # Collect Træ_mm and Halm under Biomasse
    df_mean_per_bio = df_mean_per_prod[
        df_mean_per_prod['ProductionGroup'] == 'Træ_mm']['Share'].values[0] \
        + df_mean_per_prod[
            df_mean_per_prod['ProductionGroup'] == 'Halm']['Share'].values[0]

    df_mean_per_prod = df_mean_per_prod[
        ~df_mean_per_prod['ProductionGroup'].isin(['Træ_mm', 'Halm'])
                                        ]
    df_mean_per_prod = df_mean_per_prod.append({'ProductionGroup': 'Biomasse',
                                                'Share': df_mean_per_bio},
                                               ignore_index=True)

    return df_mean_per_prod


if __name__ == '__main__':
    dist_area = 'DK1'
    start_date = '2020-01-01'
    end_date = '2020-12-31'

    path = 'C:/Users/JPM/Energinet.dk/Grønne Systemydelser - Data/'
    filename = 'declarationcoveragehour.parquet'

    file = path + filename
    df = get_prod_proportion(file, start_date, end_date, dist_area)
    print(df)
