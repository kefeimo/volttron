import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class EnergyDataHandlerPostGreSQL:
    def __init__(
        self,
        db_name="energy_data",
        user="postgres",
        password="yourpassword",
        host="localhost",
    ):
        """Initialize the database connection to a persistent PostgreSQL database."""
        self.engine = self.create_connection(db_name, user, password, host)
        self.conn = self.engine.connect()

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
            columns = ", ".join(
                [f"{col_name} {data_type}" for col_name, data_type in schema]
            )
            primary_keys_sql = f"PRIMARY KEY ({', '.join(primary_keys)})"
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns}, {primary_keys_sql})"
            self.conn.execute(text(query))
            print("Table created or verified successfully")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error creating table: {e}")

    def _filter_duplicates(self, target_df, reference_df, pk_columns):
        """Filter out duplicates based on primary key columns."""
        target_df_copy = target_df.copy()
        reference_df_copy = reference_df.copy()
        indexed_A = reference_df_copy.set_index(pk_columns)
        indexed_B = target_df_copy.set_index(pk_columns)
        unique_indices = ~indexed_B.index.isin(indexed_A.index)
        target_df_filtered = target_df[unique_indices]
        return target_df_filtered

    def insert_data_to_table(self, table_name, df):
        """Insert data from a pandas DataFrame."""
        try:
            df.to_sql(table_name, self.engine, if_exists="append", index=False)
            print(f"Data inserted successfully: {len(df)} records added.")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error inserting data: {e}")

    def get_primary_key_columns(self, table_name):
        """Retrieve the list of primary key columns for a given table."""
        result = self.conn.execute(
            text(
                f"SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) WHERE i.indrelid = '{table_name}'::regclass AND i.indisprimary;"
            )
        )
        columns = [row[0] for row in result.fetchall()]
        return columns

    def query_data_from_table(self, table_name):
        """Query all data from the table (for verification)."""
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            print("Database connection closed")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error closing the database connection: {e}")

    def remove_table(self, table_name):
        """Remove a specified table from the database."""
        try:
            self.conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            print(f"Table {table_name} has been removed successfully.")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Error removing table {table_name}: {e}")
