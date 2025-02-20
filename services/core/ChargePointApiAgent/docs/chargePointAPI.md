### Documentation for ChargePoint API Service and CLI

The `chargepoint_api_service` module is designed to interact with the ChargePoint API to retrieve and manage electric vehicle charging session data. It provides utilities to handle paginated API responses, parse time duration strings, and work with data within a SQLite database for persistent storage.

#### Key Components

1. **Paginated API Call Decorator:**
   - This decorator is used for handling API methods that require pagination.
   - Automatically manages the retrieval of data across multiple pages until all data is fetched or a set limit of iterations is reached.

2. **Time Parsing and Timestamp Utilities:**
   - `parse_time_duration`: Parses a string to extract numeric value and time unit.
   - `get_past_timestamp`: Returns a timestamp that is a certain duration in the past based on the current time.

3. **Database Management:**
   - `EnergyDataHandler`: Manages SQLite database connections, creating tables, inserting data, and querying data.
   - Automatically handles primary keys and avoids duplications during data insertion.

4. **API Classes:**
   - `Get15minChargingSessionDataAPI` and `GetChargingSessionDataAPI`: These classes encapsulate the functionality needed to interact with specific ChargePoint API endpoints.

#### Examples

1. **Retrieving 15-Minute Charging Session Data:**
   ```python
   api = Get15minChargingSessionDataAPI(username, password)
   session_data = api.get15minCharginSessionDataAPI(sessionID=123456)
   print(session_data)
   ```

2. **Handling Paginated Charging Session Data:**
   ```python
   api = GetChargingSessionDataAPI(username, password)
   charging_sessions = api.getChargingSessionDataAPI(stationID="1:2345")
   for session in charging_sessions:
       print(session)
   ```

3. **Creating and Using a Database for Charging Data:**
   ```python
   db_handler = EnergyDataHandler(db_path="path_to_db.db")
   db_handler.create_table("charging_data", [
       ("sessionID", "INTEGER PRIMARY KEY"),
       ("energyConsumed", "REAL")
   ], ["sessionID"])
   db_handler.insert_data_to_table("charging_data", pd.DataFrame(charging_sessions))
   print(db_handler.query_data_from_table("charging_data"))
   ```

4. **Parsing Time Duration and Calculating Past Timestamps:**
   ```python
   print(parse_time_duration("3h"))  # Outputs: (3.0, 'h')
   past_timestamp = get_past_timestamp("2d")
   print(f"Timestamp for 2 days ago: {past_timestamp}")
   ```

5. **CLI Usage for Retrieving Data and Optionally Saving to CSV:**
   ```bash
   python chargepoint_cli.py get_15min --sessionID 123456 --to_csv
   # This command retrieves 15-minute charging session data for the given session ID and saves it to a CSV file.
   ```

Below are additional examples of how to use the `chargepoint_cli.py` for various operations. These examples assume that the CLI is set up to handle arguments as specified in the script, allowing users to interact with the ChargePoint API and retrieve data related to electric vehicle charging sessions.

### Extended CLI Usage Examples

1. **Retrieve Charging Session Data for a Specific Station ID and Save to CSV:**
   ```bash
   python chargepoint_cli.py get_charging_session --stationID "5:15504761" --to_csv
   # Retrieves all charging session data for station ID "5:15504761" and saves it to a CSV file.
   ```

1. **Retrieve 15-Minute Charging Data for Multiple Sessions:**
   ```bash
   python chargepoint_cli.py get_15min --stationIDs "5:15504761" "5:11649381" --to_csv
   # Retrieves detailed 15-minute interval charging data for multiple session IDs and saves it to a CSV.
   ```

1. **Retrieve Charging Session Data Using a Time Filter:**
   ```bash
   python chargepoint_cli.py get_charging_session --fromTimeStamp "2023-01-01" --toTimeStamp "2023-01-31" --stationID "1:2345"
   # Retrieves charging session data for a specific station within the specified date range.
   ```

1. **Retrieve Data and Filter by Geographic Proximity:**
   ```bash
   python chargepoint_cli.py get_charging_session --City "Richland" --Proximity 50 --proximityUnit "K"
   # Retrieves charging session data for sessions within 50 km of Richland.
   ```

1. **Retrieve Session Data Including User and Vehicle Information:**
   ```bash
   python chargepoint_cli.py get_charging_session --userID "user123" 
   # Retrieves charging session data for a specific user and vehicle make.
   ```

1. **Handling Pagination Manually (If Needed Outside of Decorator Functionality):**
   ```bash
   python chargepoint_cli.py get_charging_session --startRecord 1 --stationID "1:2345"
   # Retrieves the first page of charging session data for a specific station.
   ```

1. **Check for Active Sessions Only:**
   ```bash
   python chargepoint_cli.py get_charging_session --activeSessionsOnly --stationID "5:15504761"
   # Retrieves only active charging sessions for a specific station.
   ```

1. **Specify Port Number to Filter Sessions on a Specific Charger:**
   ```bash
   python chargepoint_cli.py get_charging_session --portNumber "2" --stationID "5:15504761"
   # Retrieves charging session data for a specific port on a given station.
   ```

1. **Define a Time Period from Current Date Automatically:**
   ```bash
   python chargepoint_cli.py get_charging_session --start_period_ago "7d" --stationID "1:2345"
   # Retrieves charging session data from the last week for a specific station.
   ```

1. **Advanced Usage - Combining Filters:**
    ```bash
    python chargepoint_cli.py get_charging_session --fromTimeStamp "2025-01-01" --toTimeStamp "2025-01-31" --City "Richland" ---to_csv
    # Retrieves charging session data for Richland, within January 2025 and saves it to CSV.
    ```

1. **get load workflow demo:**
    ```bash
    python chargepoint_cli.py get_load --stationID "5:15504761"
    # Retrieves live load data by stationID
    ```

These examples demonstrate how the CLI can be flexibly used to retrieve detailed data based on various criteria, supporting operations such as data filtering, time-based queries, and geographical considerations. The CLI's functionality, as showcased, is robust, making it a powerful tool for users needing detailed insights into EV charging behaviors and trends directly from ChargePoint's comprehensive datasets.