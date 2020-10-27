from utils.garminclient import GClient
from datetime import datetime, timedelta
import pandas as pd


class SleepDownloader:
    def __init__(self, username, password, uuid):
        self.client = GClient(username, password, uuid)
        self.client.connect()

    @staticmethod
    def dto_to_df(data: list[dict]):
        """Collects all dailySleepDTO data into a df"""
        dto_data = {}
        for key in data[0]["dailySleepDTO"].keys():
            dto_data[key] = [d["dailySleepDTO"].get(key) for d in data]

        df = pd.DataFrame.from_dict(dto_data)
        df = df.dropna(subset=["id"])

        return df

    def last_n_days(self, n):
        """Downloads sleep data from the last `n` days"""
        today = datetime.today()
        return self.client.get_bulk_sleep_data(today-timedelta(days=n), today)

    def download_data(self, data, path):
        """Download data as csv"""
        df = self.dto_to_df(data)
        df.to_csv(path)


if __name__ == '__main__':
    d = SleepDownloader("[redacted]", "[redacted]", "[redacted]")
    d.download_data(d.last_n_days(100), "data/sleep.csv")
