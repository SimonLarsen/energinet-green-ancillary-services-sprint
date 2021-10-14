# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 09:17:54 2021

@author: JPM
"""

import pandas as pd
import datetime as dt
import pytz


def get_co2_reduction(start_date: dt.datetime,
                      end_date: dt.datetime,
                      price_area: str):
    ve_types = ["Solceller", "Anden VE", "Sol",
                "Onshore", "Offshore", "Vandkraft"]

    ch4_to_co2equiv = 0.025

    share_by_type = (
        pd.read_parquet("data/declarationcoveragehour.parquet")
        .assign(
            IsVe=lambda df: df.ProductionGroup.isin(ve_types)
        )
        .groupby(["HourUTC", "PriceArea", "IsVe"]).sum().reset_index()
        .filter(["HourUTC", "PriceArea", "IsVe", "Share"])
    )
    share_by_type = share_by_type[share_by_type['HourUTC'] >= start_date]
    share_by_type = share_by_type[share_by_type['HourUTC'] <= end_date]
    share_by_type = share_by_type[share_by_type['PriceArea'] == price_area]

    emission_by_hour = (
        pd.read_parquet("data/declarationemissionhour.parquet")
        .assign(
            CO2Equiv=lambda df: df.CO2PerkWh + df.CH4PerkWh * ch4_to_co2equiv
        )
        .filter(["HourUTC", "PriceArea", "CO2Equiv"])
    )
    emission_by_hour = emission_by_hour[
        emission_by_hour['HourUTC'] >= start_date]
    emission_by_hour = emission_by_hour[
        emission_by_hour['HourUTC'] <= end_date]
    emission_by_hour = emission_by_hour[
        emission_by_hour['PriceArea'] == price_area]

    mwh_to_kwh = 1000

    consumption_by_hour = (
        pd.read_parquet("data/productionconsumptionsettlement.parquet")
        .filter(["HourUTC", "PriceArea", "GrossConsumptionMWh"])
        .rename(columns={"GrossConsumptionMWh": "Consumption"})
        .assign(Consumption=lambda df: df.Consumption * mwh_to_kwh)
    )
    consumption_by_hour = consumption_by_hour[
        consumption_by_hour['HourUTC'] >= start_date]
    consumption_by_hour = consumption_by_hour[
        consumption_by_hour['HourUTC'] <= end_date]
    consumption_by_hour = consumption_by_hour[
        consumption_by_hour['PriceArea'] == price_area]

    df = (
        share_by_type
        .pivot(["HourUTC", "PriceArea"], "IsVe", "Share")
        .reset_index()
        .rename(columns={True: "ShareVE", False: "ShareNonVE"})
        .merge(emission_by_hour, on=["HourUTC", "PriceArea"], how="inner")
        .merge(consumption_by_hour, on=["HourUTC", "PriceArea"], how="inner")
        .assign(
            CO2EquivNonVE=lambda df: df.CO2Equiv / df.ShareNonVE,
            ConsumptionNonVE=lambda df: df.ShareNonVE * df.Consumption,
            CO2NonVE=lambda df: df.ConsumptionNonVE * df.CO2Equiv,
            CO2NonVEMonth=lambda df: df.groupby(["PriceArea",
                                                 df.HourUTC.dt.month]
                                                ).CO2NonVE.transform("sum"),
            ConsumptionNonVEMonth=lambda df: df.groupby(["PriceArea",
                                                         df.HourUTC.dt.month]
                                                        ).ConsumptionNonVE.transform("sum")
        )
        .assign(CO2EquivMonth=lambda df: df.CO2NonVEMonth / df.ConsumptionNonVEMonth)
    )

    df = df.assign(CO2Diff=lambda df: df.CO2EquivNonVE - df.CO2Equiv)
    df = df.set_index('HourUTC')

    df_co2_diff = df['CO2Diff']

    return df_co2_diff

if __name__ == '__main__':
    start_date = dt.datetime(2020, 1, 1, tzinfo=pytz.UTC)
    end_date = dt.datetime(2020, 1, 31, tzinfo=pytz.UTC)
    price_area = 'DK1'

    df = get_co2_reduction(start_date,
                           end_date,
                           price_area)

    print(df)
