### README for ChargePoint API Service and CLI Setup

This README provides instructions on setting up a virtual environment, installing necessary packages, and using the ChargePoint API Service and CLI. It also directs you to detailed documentation for a deeper understanding of how to interact with ChargePoint's API for managing electric vehicle charging session data.

#### Prerequisites
Ensure you have Python installed on your machine (Python 3.6 or newer is recommended). You can download Python from [python.org](https://www.python.org/downloads/).

#### Setup Instructions

1. **Clone the Repository (if applicable):**
   If you have a repository URL, start by cloning the repo. If you are setting this up from a local directory, skip to the next step.
   ```bash
   git clone https://your-repository-url.com/path/to/repo.git
   cd repo-directory
   ```

2. **Create a Virtual Environment:**
   It's recommended to create a virtual environment to manage dependencies separately from your system installations.
   ```bash
   python -m venv venv
   ```

   Activate the virtual environment:
   - On Windows:
     ```cmd
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install Required Packages:**
   Install all required packages using `pip`. The `requirements.txt` file should list all necessary libraries.
   ```bash
   pip install -r requirements.txt
   ```

   If you do not have a `requirements.txt` file, you need at least `zeep` and `pandas` for the API service and CLI:
   ```bash
   pip install zeep pandas
   ```

4. **Environment Variables:**
   Set up the necessary environment variables for authentication with the ChargePoint API:
   ```bash
   export CHARGEPOINT_USERNAME='your_username'
   export CHARGEPOINT_PASSWORD='your_password'
   ```

   On Windows, use `set` instead of `export`:
   ```cmd
   set CHARGEPOINT_USERNAME='your_username'
   set CHARGEPOINT_PASSWORD='your_password'
   ```

5. **Run the CLI:**
   To use the CLI, navigate to the directory containing `chargepoint_cli.py` and run one of the commands based on the examples provided in the documentation.
   ```bash
   python chargepoint_cli.py [command] [options]
   ```

   ```bash
    (venv) (base) kefei@WE44933:~/project/ires-rtac-deployment/SEL_RTAC_AcSelerator/ChargePointApiAgent$ python chargepoint_api_agent/chargepoint_cli.py get_charging_session --start_period_ago 1d
        stationID       stationName portNumber  ... driverOptedOut driverOptOutTimestamp paymentTerminalInfo
    0   5:14285201      PNNL / GSL 1          1  ...           None                  None                None
    1   5:13059121        PNNL / CSF          1  ...           None                  None                None
    2   5:13097841      PNNL / ETB 1          1  ...           None                  None                None
    3   5:13059121        PNNL / CSF          2  ...           None                  None                None
    4   5:15504761       PNNL / MSL5          1  ...           None                  None                None
    5   5:13791221  PNNL / MATH BLDG          2  ...           None                  None                None
    6   5:14285201      PNNL / GSL 1          1  ...           None                  None                None
    7   5:13090581    PNNL / EMSL 10          1  ...           None                  None                None
    8   5:13059121        PNNL / CSF          1  ...           None                  None                None
    9   5:11649381      PNNL / ESC 2          2  ...           None                  None                None
    10  5:13097851      PNNL / ETB 2          2  ...           None                  None                None
    11  5:13097851      PNNL / ETB 2          2  ...           None                  None                None
    12  5:15504761       PNNL / MSL5          1  ...           None                  None                None
    13  5:13059121        PNNL / CSF          2  ...           None                  None                None
    14  5:13059121        PNNL / CSF          2  ...           None                  None                None
    15  5:13059121        PNNL / CSF          1  ...           None                  None                None
    16  5:13097841      PNNL / ETB 1          1  ...           None                  None                None
    17  5:13791221  PNNL / MATH BLDG          2  ...           None                  None                None
    ```

#### Documentation Reference

For detailed information on how the `chargepoint_api_service` module functions, please refer to the provided documentation. It includes comprehensive details on each component, examples of retrieving data, and explanations of the CLI commands available for interacting with the ChargePoint API. The documentation covers topics such as:

- Paginated API Calls
- Parsing Time Durations
- Database Management for session data
- Examples of CLI Usage

This documentation can be found within your project directory or accessible through your project documentation resources.

#### Support

If you encounter any issues during setup or execution, consult the project documentation first. If further assistance is needed, please contact your support team or reach out via the project's issue tracker.

By following these steps, you should have a functional setup for interacting with the ChargePoint API to manage and retrieve electric vehicle charging session data.