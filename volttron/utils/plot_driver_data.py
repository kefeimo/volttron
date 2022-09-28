import sqlite3
import pandas as pd
from pandas.core.frame import DataFrame
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

from matplotlib import pyplot as plt
from time import sleep

import matplotlib


# import gnuplotlib as gp
import numpy as np





def get_df(f_path: str = "/home/kefei/.volttron/agents/"
                       "ba3caba2-2e44-49a3-a771-eaccf6b7bc3e/sqlhistorianagent-4.0.0/data/platform.historian.sqlite"
           ) -> pd.DataFrame:
    # f_path = "/home/kefei/.volttron/agents/85736715-3354-4b70-94d7-eb2ca6e88e48/sqlhistorianagent-4.0.0/data/platform.historian.sqlite"
    con = sqlite3.connect(f_path)

    # df = pd.read_sql_query("SELECT name FROM sqlite_schema WHERE type ='table' AND name NOT LIKE 'sqlite_%'", con)
    # df.head()

    df_data = pd.read_sql_query(sql="select * from data", con=con)
    # df_data

    df_topics = pd.read_sql_query(sql="select * from topics", con=con)
    # df_topics
    con.commit()  # to make sure refresh

    df_join = pd.merge(df_data, df_topics, on='topic_id')
    # df_join.head()

    return df_join


def get_df_plot(df_join: DataFrame, topic_name: str,
         ) -> DataFrame:
    df_join["topic_name_l4"] = df_join.topic_name.apply(lambda x: x.split("/")[-1])
    # df_join.head()

    df_cos = df_join[df_join.topic_id == 24] # TODO: make it parameterized

    # pd.to_datetime(df_cos.ts)
    df_cos_ts = df_cos[["ts", "value_string"]]
    df_cos_ts.ts = pd.to_datetime(df_cos.ts)
    df_cos_ts.value_string = df_cos_ts.value_string.astype(float)
    df_cos_ts.set_index('ts', inplace=True)
    # df_cos_ts.info()

    # only plot last 1 minute
    # TODO: need to make the time range adaptable to sampling rate
    last_index = df_cos_ts.index[-1]
    last_index
    last_index - pd.Timedelta("1 minute")
    # df_cos_ts[last_index - pd.Timedelta("1 minute"):].plot()

    df_plot = df_cos_ts[last_index - pd.Timedelta("1 minute"):]

    return df_plot


def plot(df_plot: DataFrame) -> None:

    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    # plt.plot(df_plot)
    # plt.show()

    plt.plot(df_plot)
    plt.draw()
    # plt.pause(1)
    plt.clf()


def plot_terminal(df_plot: DataFrame) -> None:
    matplotlib.use('module://drawilleplot')

    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True
    # plt.plot(df_plot)
    # plt.show()

    # gp.plot(df_plot)
    plt.plot(df_plot)
    plt.show()
    # plt.pause(1)
    # plt.close()
    plt.clf()




if __name__ == "__main__":

    while True:
        df = get_df()  # TODO: make it parameterized
        df_plot = get_df_plot(df, "EKG_Cos")
        # plot(df_plot)
        plot_terminal(df_plot)
        sleep(2)

        # plot_test()
