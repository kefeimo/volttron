import logging
import sqlite3
from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

# Create a file handler and set its level to DEBUG
file_handler = logging.FileHandler("chargepoint_api.log")
file_handler.setLevel(logging.DEBUG)

# Create a stream handler and set its level to INFO
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
_log.addHandler(file_handler)
_log.addHandler(stream_handler)


class BaseDataHandler:
    """Abstract base class for handling database operations."""

    @abstractmethod
    def create_table(self, table_name, schema, primary_keys):
        pass

    @abstractmethod
    def insert_data_to_table(self, table_name, df) -> pd.DataFrame:
        pass

    @abstractmethod
    def query_data_from_table(self, table_name) -> pd.DataFrame:
        pass

    @abstractmethod
    def remove_table(self, table_name):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def execute_query(self, query):
        pass


class EnergyDataHandlerPostGreSQL(BaseDataHandler):
    def __init__(
        self,
        db_name="energy_data",
        user="postgres",
        password="yourpassword",
        host="localhost",
        logger=None,
    ):
        """Initialize the database connection to a persistent PostgreSQL database."""
        self.engine = self.create_connection(db_name, user, password, host)
        self.conn = self.engine.connect()
        if logger is not None:
            self.logger = logger
        else:
            self.logger = _log
        # self.metadata = MetaData()

    def create_connection(self, db_name, user, password, host):
        # Create the initial connection to the PostgreSQL server
        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}/postgres"
        )
        conn = engine.connect()
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Check if the database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name},
        )
        exists = result.fetchone()

        # If the database does not exist, create it
        if not exists:
            conn.execute(text(f"CREATE DATABASE {db_name}"))

        # Close the initial connection
        conn.close()

        # Connect to the newly created or existing database
        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}/{db_name}"
        )
        return engine

    def create_table(self, table_name, schema, primary_keys):
        """Create a table if it does not exist, using a defined schema."""
        try:
            # Define columns using SQLAlchemy
            columns = [
                Column(name, self.get_sqlalchemy_type(dtype)) for name, dtype in schema
            ]
            # Add primary key constraint if primary keys are specified
            if primary_keys:
                columns.append(PrimaryKeyConstraint(*primary_keys))

            # Create the table object
            metadata = MetaData()
            table = Table(table_name, metadata, *columns, extend_existing=True)

            # Create the table in the database
            table.create(self.engine, checkfirst=True)

            # Log the successful creation
            print(f"Table '{table_name}' created or verified successfully.")
        except SQLAlchemyError as e:
            print(f"Error creating table: {e}")
            raise

    def get_sqlalchemy_type(self, dtype):
        """Map data types to SQLAlchemy types."""
        type_mapping = {"INTEGER": Integer, "REAL": Float, "TEXT": String}
        return type_mapping.get(
            dtype.upper(), String
        )  # Default to String if type is unknown

    def _filter_duplicates(self, target_df, reference_df, pk_columns):
        """Filter out duplicates based on primary key columns."""
        target_df_copy = target_df.copy()
        reference_df_copy = reference_df.copy()
        indexed_A = reference_df_copy.set_index(pk_columns)
        indexed_B = target_df_copy.set_index(pk_columns)
        unique_indices = ~indexed_B.index.isin(indexed_A.index)
        target_df_filtered = target_df[unique_indices]
        return target_df_filtered

    def insert_data_to_table(self, table_name, df: pd.DataFrame) -> pd.DataFrame:
        """Insert data from a pandas DataFrame"""
        pk_columns = self.get_primary_key_columns(table_name)
        ref_df = self.query_data_from_table(table_name)
        df_filtered = self._filter_duplicates(
            target_df=df, reference_df=ref_df, pk_columns=pk_columns
        )
        self.logger.info(f"Data to be inserted {df_filtered = } ")
        if not df_filtered.empty:
            self._insert_data_to_table(table_name, df_filtered)
            self.logger.info(
                f"Data inserted successfully: {len(df_filtered)} records added."
            )
        else:
            self.logger.warning("No new records to insert; all records are duplicates.")

            """Insert data from a pandas DataFrame."""
        return df_filtered

    def _insert_data_to_table(self, table_name, df):
        """Insert data from a pandas DataFrame."""
        try:
            # Reflect the table schema from the database
            metadata = MetaData()
            metadata.reflect(bind=self.engine)

            # Ensure the table exists and get the table schema
            if table_name in metadata.tables:
                table = metadata.tables[table_name]
                # Align DataFrame columns to the table schema: this prevents issues with column order or missing columns
                df = df[list(table.columns.keys())]

                # Insert data ensuring the DataFrame's columns match the order and presence of the table's columns
                df.to_sql(table_name, self.engine, if_exists="append", index=False)

                self.logger.info(
                    f"Data inserted successfully: {len(df)} records added."
                )
            else:
                self.logger.error(f"Table '{table_name}' does not exist.")
                raise ValueError(f"Table '{table_name}' does not exist.")
        except SQLAlchemyError as e:
            self.logger.error(f"Error inserting data to {table_name}: {str(e)}")
            raise SQLAlchemyError(f"Error inserting data to {table_name}: {str(e)}")

        return df

    def get_primary_key_columns(self, table_name):
        """Retrieve the list of primary key columns for a given table."""
        result = self.conn.execute(
            text(
                f"SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) WHERE i.indrelid = '\"{table_name}\"'::regclass AND i.indisprimary;"
            )
        )
        columns = [row[0] for row in result.fetchall()]
        return columns

    def query_data_from_table(self, table_name):
        """Query all data from the table (for verification)."""
        return pd.read_sql(f'SELECT * FROM "{table_name}"', self.conn)

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            # print("Database connection closed")
            self.logger.info("Database connection closed")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error closing the database connection: {e}")

    def remove_table(self, table_name):
        """Remove a specified table from the database."""
        try:
            self.conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            # print(f"Table {table_name} has been removed successfully.")
            self.logger.info(f"Table {table_name} has been removed successfully.")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error removing table {table_name}: {e}")


class EnergyDataHandlerSqlite(BaseDataHandler):
    def __init__(self, db_path="energy_data.db", logger=None):
        """Initialize the database connection to a persistent SQLite database."""
        self.db_path = db_path
        self.conn = self.create_connection()
        self.cursor = self.conn.cursor()
        if logger is not None:
            self.logger = logger
        else:
            self.logger = _log

    def create_connection(self):
        """Create and return a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            self.logger.info(
                f"SQLite Database connected successfully at {self.db_path}"
            )
            return conn
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error connecting to database: {e}")

    def create_table(self, table_name, schema, primary_keys):
        """
            Create a table if it does not exist, using a defined schema.

            Args:
            table_name (str): Name of the table to create.
            schema (list of tuples): Each tuple contains the column name followed by the SQL type and optionally constraints.

            Example schema:
            table_schema = [
            ("stationTime", "TEXT"),
            ("energyConsumed", "REAL"),
            ("peakPower", "REAL"),
            ("rollingPowerAvg", "REAL"),
            ("sessionID", "INTEGER")
        ]

            primary_keys = ['stationTime', 'sessionID']
        """
        try:
            # Build the column definitions from the schema
            columns = (
                ", ".join([f"{col_name} {data_type}" for col_name, data_type in schema])
                + ","
            )
            # Prepare the PRIMARY KEY clause
            primary_keys_sql = f"PRIMARY KEY ({', '.join(primary_keys)})"

            # Create SQL query for creating the table
            query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
                {primary_keys_sql}
            )
            """
            self.conn.execute(query)
            self.conn.commit()
            self.logger.info("Table created or verified successfully")
        except Exception as e:
            raise Exception(f"Error creating table: {e}")

    @staticmethod
    def _filter_duplicates(
        target_df: pd.DataFrame,
        reference_df: pd.DataFrame,
        pk_columns: list[str],
    ):
        """Filter out duplicates based on 'stationTime' and 'sessionID'."""
        target_df_copy = target_df.copy()
        reference_df_copy = reference_df.copy()
        # Force columns to be of type string for comparison
        for column, dtype in reference_df_copy.dtypes.items():
            target_df_copy[column] = target_df_copy[column].astype(str)
            reference_df_copy[column] = reference_df_copy[column].astype(str)
        # Set indices to the columns used for determining duplicates
        # print(f"{pk_columns = }")
        indexed_A = reference_df_copy.set_index(pk_columns)
        indexed_B = target_df_copy.set_index(pk_columns)

        # Filter DataFrameB to only include records that are not in DataFrameA
        # This uses the index created and checks for non-overlapping indices in DataFrameB
        unique_indices = ~indexed_B.index.isin(indexed_A.index)
        target_df_filtered = target_df[unique_indices]
        return target_df_filtered

    def insert_data_to_table(self, table_name, df: pd.DataFrame) -> pd.DataFrame:
        """Insert data from a pandas DataFrame"""
        pk_columns = self.get_primary_key_columns(table_name)
        ref_df = self.query_data_from_table(table_name)
        df_filtered = self._filter_duplicates(
            target_df=df, reference_df=ref_df, pk_columns=pk_columns
        )
        if not df_filtered.empty:
            df_filtered.to_sql(table_name, self.conn, if_exists="append", index=False)
            self.logger.info(
                f"Data inserted successfully: {len(df_filtered)} records added."
            )
        else:
            self.logger.warning("No new records to insert; all records are duplicates.")

            """Insert data from a pandas DataFrame."""
        return df_filtered

    def get_primary_key_columns(self, table_name):
        """Retrieve the list of primary key columns for a given table."""
        query = f"PRAGMA table_info({table_name})"
        self.cursor.execute(query)
        columns = []
        for row in self.cursor.fetchall():
            # Column info: (cid, name, type, notnull, dflt_value, pk)
            if row[5] > 0:  # pk value is > 0 if the column is part of the primary key
                columns.append(row[1])
        return columns

    def query_data_from_table(self, table_name) -> pd.DataFrame:
        """Query all data from the table (for verification)."""
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            self.logger.info("Database connection closed")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error closing the database connection: {e}")

    def remove_table(self, table_name):
        """
        Remove a specified table from the database.

        Args:
        table_name (str): The name of the table to be removed.
        """
        try:
            # SQL command to drop a table
            query = f"DROP TABLE IF EXISTS {table_name}"
            self.conn.execute(query)
            self.conn.commit()
            self.logger.info(f"Table {table_name} has been removed successfully.")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error removing table {table_name}: {e}")
