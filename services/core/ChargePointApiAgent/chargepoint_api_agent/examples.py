import argparse
import datetime
import os
import sys

import pandas as pd
from chargepoint_api_service import (
    EnergyDataHandler,
    Get15minChargingSessionDataAPI,
    GetChargingSessionDataAPI,
    GetLoadAPI,
)


def main():
    charge_point = Get15minChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    resonse = charge_point.get15minCharginSessionDataCollection(
        session_ids=[101542479, 101268659, 100412719]
    )  # 101268659
    # print(resonse)
    df = pd.DataFrame(resonse)
    # print(df)

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "get15minCharginSessionData"
    table_schema = [
        ("stationTime", "TEXT"),
        ("energyConsumed", "REAL"),
        ("peakPower", "REAL"),
        ("rollingPowerAvg", "REAL"),
        ("sessionID", "INTEGER"),
    ]
    pks = ["stationTime", "sessionID"]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, pks)
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        df,
    )

    # # Query and print the data
    # results = db_handler.query_data_from_table(table_name)
    print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main2():
    charge_point = GetChargingSessionDataAPI(username, password)
    # res = charge_point.getChargingSessionDataAPI(
    #     # stationID="5:15504761",  # 5:11649381
    #     fromTimeStamp="2024-12-01",
    #     # toTimeStamp="2024-12-15"
    # )
    res = charge_point.getChargingSessionDataAPI(
        # stationID="5:15504761",  # 5:11649381
        fromTimeStamp="2024-12-01",
        stationIDs=["5:15504761", "5:11649381"],
        # toTimeStamp="2024-12-15"
    )
    print(pd.DataFrame(res).info())
    # print(pd.DataFrame(res))

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "getChargingSessionData"
    table_schema = [
        ("stationID", "TEXT"),
        ("stationName", "TEXT"),
        ("portNumber", "TEXT"),
        ("Address", "TEXT"),
        ("City", "TEXT"),
        ("State", "TEXT"),
        ("Country", "TEXT"),
        ("postalCode", "TEXT"),
        (
            "sessionID",
            "INTEGER",
        ),  # ("sessionID", "INTEGER PRIMARY KEY"),  # Assuming sessionID is unique
        ("Energy", "REAL"),
        ("startTime", "TEXT"),  # Storing as ISO8601 string
        ("endTime", "TEXT"),  # Storing as ISO8601 string
        ("totalChargingDuration", "TEXT"),  # Could be INTEGER if stored as seconds
        ("totalSessionDuration", "TEXT"),  # Could be INTEGER if stored as seconds
        ("userID", "TEXT"),
        ("startBatteryPercentage", "REAL"),
        ("stopBatteryPercentage", "REAL"),
        ("recordNumber", "INTEGER"),
        ("credentialID", "TEXT"),
        ("endedBy", "TEXT"),
        ("vehicleMake", "TEXT"),
        ("vehicleModel", "TEXT"),
        ("vehicleModelYear", "INTEGER"),
        ("vehicleType", "TEXT"),
        ("vehiclePortMAC", "TEXT"),
        ("driverOptedOut", "INTEGER"),  # Assuming this is a boolean flag (0 or 1)
        ("driverOptOutTimestamp", "TEXT"),  # Storing as ISO8601 string
        ("paymentTerminalInfo", "TEXT"),
    ]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, ["sessionID"])
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        pd.DataFrame(res),
    )

    # # # Query and print the data
    # # results = db_handler.query_data_from_table(table_name)
    # print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main3():
    charge_point = Get15minChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    resonse = charge_point.get15minCharginSessionDataAPI(
        stationID="5:15504761", portNumber="2"
    )  # 101268659
    # print(resonse)
    df = pd.DataFrame(resonse)
    # print(df)

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "get15minCharginSessionData"
    table_schema = [
        ("stationTime", "TEXT"),
        ("energyConsumed", "REAL"),
        ("peakPower", "REAL"),
        ("rollingPowerAvg", "REAL"),
        ("sessionID", "INTEGER"),
    ]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, ["stationTime", "sessionID"])
    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        df,
    )

    # # Query and print the data
    # results = db_handler.query_data_from_table(table_name)
    print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main4():
    charge_point = GetLoadAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    resonse = charge_point.getLoadAPI(
        stationID="5:15504761",
    )  # 101268659
    # print(resonse)
    df = pd.DataFrame(resonse)
    print(df.values)
    print(df.info())

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # print("Script is running in:", script_directory)
    db_path = os.path.join(script_directory, "chargePoint_testing.db")
    # Initialize the handler
    db_handler = EnergyDataHandler(db_path)
    table_name = "getLoad"
    table_schema = [
        ("portNumber", "TEXT"),
        ("userID", "TEXT"),
        ("credentialID", "TEXT"),
        ("shedState", "INTEGER"),
        ("portLoad", "REAL"),
        ("allowedLoad", "REAL"),
        ("percentShed", "REAL"),
        ("sessionID", "INTEGER"),
        ("lastBatteryPercent", "REAL"),
        ("stationID", "TEXT"),
        ("stationName", "TEXT"),
        ("Address", "TEXT"),
        ("stationLoad", "REAL"),
        ("queryTimeUTC", "TEXT"),
    ]
    # db_handler.remove_table(table_name)
    db_handler.create_table(table_name, table_schema, ["queryTimeUTC", "sessionID"])

    # Insert data
    results = db_handler.insert_data_to_table(
        table_name,
        df,
    )

    # # Query and print the data
    # results = db_handler.query_data_from_table(table_name)
    print(results)
    # for row in results:
    #     print(row)

    # Close the database connection
    db_handler.close()


def main5():
    # verify is_period_auto_defined
    charge_point = GetChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    for i in range(3):
        resonse = charge_point.getChargingSessionDataAPI(
            stationID="5:15504761",
            # portNumber="2",
            start_period_ago="0.1h",
            is_period_auto_defined=True,
        )  # 101268659
        # print(resonse)
        df = pd.DataFrame(resonse)
        print(f"{i = }, {len(df) = }")


def main5b():
    # verify is_period_auto_defined
    charge_point = Get15minChargingSessionDataAPI(username, password)
    # resonse = charge_point._get15minChargingSessionData(sessionID=101542479) # 101268659
    for i in range(3):
        resonse = charge_point.get15minCharginSessionDataAPI(
            stationID="5:15504761",
            # portNumber="2",
            start_period_ago="2d",
            is_period_auto_defined=True,
        )  # 101268659
        # print(resonse)
        df = pd.DataFrame(resonse)
        print(f"{i = }, {len(df) = }")


username = os.getenv(
    "CHARGEPOINT_USERNAME"
)  # "9c2fc57f048fd5c2f740dcf8e0a6f69c677c424289bda1736196674"
password = os.getenv("CHARGEPOINT_PASSWORD")  # "d67f1b3e02ff57fb6d90fc8a770db00b"


if __name__ == "__main__":
    # Entry point for script
    try:
        sys.exit(main5b())
    except KeyboardInterrupt:
        pass
