import argparse
import datetime
import os

import pandas as pd

from services.core.ChargePointApiAgent.chargepoint_api_agent.chargepoint_api_service import (
    Get15minChargingSessionDataAPI,
    GetChargingSessionDataAPI,
)


def main():
    username = os.getenv("CHARGEPOINT_USERNAME")
    password = os.getenv("CHARGEPOINT_PASSWORD")

    parser = argparse.ArgumentParser(
        description="CLI for managing ChargePoint data retrieval"
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        help="additional help",
        dest="subcommand",  # This should be 'subcommand', not 'command'
    )
    subparsers.required = True

    # Shared arguments definition
    method_common_args = {
        "stationID": {"help": "Station ID"},
        "sessionID": {"type": int, "help": "Session ID"},
        "userID": {"help": "User ID"},
        "stationName": {"help": "Station name"},
        "Address": {"help": "Station address"},
        "City": {"help": "City"},
        # "State": {"help": "State"}, # Note: disable State parameter since the API is not working.
        "Country": {"help": "Country"},
        "postalCode": {"help": "Postal code"},
        "Proximity": {"help": "Proximity"},
        "proximityUnit": {"help": "Unit of proximity"},
        "fromTimeStamp": {"help": "Start timestamp for data"},
        "toTimeStamp": {"help": "End timestamp for data"},
        "startRecord": {"type": int, "help": "Start record number"},
        "Geo": {"help": "Geographical data"},
        "stationIDs": {"nargs": "*", "help": "List of station IDs"},
        "activeSessionsOnly": {
            "action": "store_true",
            "help": "Only include active sessions",
        },
        "portNumber": {"help": "Port number"},
        "start_period_ago": {"help": "Time period to start data collection from"},
        "is_period_auto_defined": {
            # "type": bool,
            "action": "store_true",
            "help": "Whether the time period is automatically defined",
        },
    }
    extra_common_args = {
        "to_csv": {
            "action": "store_true",
            # "type": bool,
            "help": "Whether to save the data to a CSV file",
        }
    }

    # Subcommand for 15-minute session data
    parser_15min = subparsers.add_parser(
        "get_15min", help="Get 15-minute charging session data"
    )
    common_args = method_common_args.copy()
    common_args.update(extra_common_args)
    for arg, options in common_args.items():
        parser_15min.add_argument(f"--{arg}", **options)
    # parser_15min.set_defaults(func=Get15minChargingSessionDataAPI)

    # Subcommand for charging session data
    parser_charging = subparsers.add_parser(
        "get_charging_session", help="Get charging session data"
    )
    for arg, options in common_args.items():
        parser_charging.add_argument(f"--{arg}", **options)
    # parser_charging.set_defaults(func=GetChargingSessionDataAPI)

    args = parser.parse_args()

    # Initialize the correct API based on the subcommand
    if args.subcommand == "get_15min":
        method = Get15minChargingSessionDataAPI(
            username, password
        ).get15minCharginSessionDataAPI
    elif args.subcommand == "get_charging_session":
        method = GetChargingSessionDataAPI(username, password).getChargingSessionDataAPI

    # Extract remaining arguments to pass to the function
    kwargs = {
        k: v
        for k, v in vars(args).items()
        if k not in {"func", "subcommand"} and k in method_common_args.keys()
    }

    # Assuming there is a common method to be called that requires the parameters
    # print(f"Calling {method.__name__} with the following parameters: {kwargs}")
    response = method(**kwargs)
    df_response = pd.DataFrame(response)
    if args.to_csv:
        csv_filename = f"/tmp/{args.subcommand}-{datetime.datetime.now()}.csv"
        df_response.to_csv(csv_filename)
        print(f"Saved data to {csv_filename}")
    else:
        print(df_response)


if __name__ == "__main__":
    main()
