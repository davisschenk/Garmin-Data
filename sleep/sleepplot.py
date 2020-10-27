import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime
from typing import Union


class SleepPlot:
    def __init__(self, df=None, sleep_data_path=None):
        self.fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                 vertical_spacing=0.02)

        if df is not None:
            self.df = df
        elif sleep_data_path:
            self.df = pd.read_csv(sleep_data_path)
        else:
            raise ValueError("You need to provide a dataframe or a path")

    @staticmethod
    def format_timedelta(x: Union[datetime.timedelta, pd.Timedelta]) -> str:
        """This function takes a timedelta and formats it to hh:mm"""
        return f'{x.components.hours:02d}:{x.components.minutes:02d}' if not pd.isnull(x) else ''

    @staticmethod
    def make_relative(dt: datetime.datetime, date: datetime.datetime) -> float:
        """This function finds the total seconds between `dt` and midnight on `date`"""
        midnight = datetime.datetime.combine(date, datetime.datetime.min.time())
        difference = dt - midnight

        return -difference.total_seconds()

    @staticmethod
    def seconds_to_time(s: int, date: datetime.datetime) -> datetime.datetime:
        """Converts seconds relative to midnight back into a datetime using midnight on `date`"""
        return datetime.datetime.combine(date, datetime.datetime.min.time()) - datetime.timedelta(seconds=s)

    @staticmethod
    def datetime_to_12hr(dt: datetime.datetime) -> str:
        """Formats a datetime into 12hr time"""
        return dt.strftime("%I:%M %p")

    @classmethod
    def format_relative_seconds(cls, seconds: int, date: datetime.datetime) -> str:
        if pd.isnull(seconds):
            return ""
        return cls.datetime_to_12hr(cls.seconds_to_time(seconds, date))

    def clean_data(self) -> None:
        """Creates new columns of datetimes from raw sleep data"""
        # Remove all data without an an ID
        self.df = self.df.dropna(subset=["id"])

        # Convert raw dates into more useful datetimes
        self.df["date"] = pd.to_datetime(self.df["calendarDate"], format="%Y-%m-%d")
        self.df["bedtime"] = pd.to_datetime(self.df['sleepStartTimestampLocal'], unit='ms')
        self.df["wakeup"] = pd.to_datetime(self.df['sleepEndTimestampLocal'], unit='ms')
        self.df["sleeptime"] = pd.to_timedelta(self.df["sleepTimeSeconds"], unit='s')

        # Sort dataframe by date, this is mainly for the rolling average
        self.df = self.df.sort_values("date")

        # These columns represent the bedtime/wakeup in seconds relative to midnight
        self.df["r_bedtime"] = self.df.apply(lambda row: self.make_relative(row.bedtime, row.date), axis=1)
        self.df["r_wakeup"] = self.df.apply(lambda row: self.make_relative(row.wakeup, row.date), axis=1)

        # Formatted seconds to midnight
        self.df["f_bedtime"] = self.df.apply(lambda row: self.format_relative_seconds(row.r_bedtime, row.date), axis=1)
        self.df["f_wakeup"] = self.df.apply(lambda row: self.format_relative_seconds(row.r_wakeup, row.date), axis=1)

        # Rolling means for bedtime and wakeup
        self.df["rm_bedtime"] = self.df["r_bedtime"].rolling(7).mean()
        self.df["rm_wakeup"] = self.df["r_wakeup"].rolling(7).mean()

    def create_traces(self) -> None:
        """Adds all the traces"""
        self.fig.add_trace(
            go.Bar(
                name="Sleeping Hours",
                x=self.df["date"],
                base=self.df["r_wakeup"],
                y=self.df["r_bedtime"] - self.df["r_wakeup"],
                customdata=np.stack(
                    (self.df.f_bedtime, self.df.f_wakeup, self.df.sleeptime.apply(self.format_timedelta)), axis=-1),
                hovertemplate="Date: %{x}<br>"
                              "Bedtime: %{customdata[0]}<br>"
                              "Wakeup: %{customdata[1]}<br>"
                              "Total Time: %{customdata[2]}"
                              "<extra></extra>",
            )
        )

        self.fig.add_trace(
            go.Scatter(
                name="Wakeup 7 Day Rolling Average",
                x=self.df["date"],
                y=self.df["rm_wakeup"],
                customdata=self.df.apply(lambda row: self.format_relative_seconds(row.rm_wakeup, row.date), axis=1),
                hovertemplate="Average Wakeup: %{customdata}"
                              "<extra></extra>",
            ),
            row=1, col=1
        )

        self.fig.add_trace(
            go.Scatter(
                name="Bedtime 7 Day Rolling Average",
                x=self.df["date"],
                y=self.df["rm_bedtime"],
                customdata=self.df.apply(lambda row: self.format_relative_seconds(row.rm_bedtime, row.date), axis=1),
                hovertemplate="Average Bedtime: %{customdata}"
                              "<extra></extra>",
            ),
            row=1, col=1
        )

        self.fig.add_trace(
            go.Scatter(
                name="Sleep Time",
                x=self.df["date"],
                y=self.df["sleeptime"],
                customdata=self.df.apply(lambda row: self.format_timedelta(row.sleeptime), axis=1),
                hovertemplate="Sleep Time: %{customdata}",
                yaxis='y2'
            ),
            row=2, col=1
        )

    def update_layout(self) -> None:
        """Updates the plots layout to change hovermode, ticks, title and theme"""
        time_range = list(range(86400, -86400, -3600))  # All hours of the day in seconds relative to midnight
        delta_range = [pd.Timedelta(hours=n) for n in range(16)]
        self.fig.update_layout(
            title="Davis' Sleep Schedule",
            hovermode="x unified",
            yaxis=dict(
                tickmode='array',
                tickvals=time_range,
                ticktext=[self.format_relative_seconds(time, datetime.datetime.today()) + "  " for time in time_range]
            ),
            yaxis2=dict(
                    tickmode='array',
                    tickvals=delta_range,
                    ticktext=[self.format_timedelta(n) for n in delta_range]
                ),
            template="plotly_dark",
        )

    def show(self) -> None:
        """Displays the plot"""
        self.fig.show()

    def save(self, path: str) -> None:
        """Saves the plot as html, I also add some styling to the html tag so it looks a bit nicer"""
        with open(path, "w") as w:
            w.write(self.fig.to_html().replace("<html>", "<html style='background:#111111'>"))

    def generate(self, show: bool = True, path: str = None) -> None:
        """Generates the plot, if path is not None then it will be saved"""
        self.clean_data()
        self.create_traces()
        self.update_layout()

        if show:
            self.show()

        if path:
            self.save(path)


if __name__ == "__main__":
    sp = SleepPlot(sleep_data_path="data/sleep.csv")
    sp.generate(path="sleep_data.html")
