from garminexport.garminclient import GarminClient, require_session
from datetime import datetime, timedelta
from typing import Union


def daterange(start_date, end_date):
    """
    A range of dates
    Source: https://stackoverflow.com/a/1060330
    """
    end_date += timedelta(days=1)
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


class GClient(GarminClient):
    WELLNESS_URL = "https://connect.garmin.com/modern/proxy/wellness-service/wellness"
    """A GarminClient with extended functionality"""
    def __init__(self, username, password, uuid):
        self.uuid = uuid
        super().__init__(username, password)

    @require_session
    def get_sleep_data(self, date: Union[datetime, str], sleep_buffer_minutes: int = 60):
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")

        url = f"{self.WELLNESS_URL}/dailySleepData/{self.uuid}?date={date}&nonSleepBufferMinutes={sleep_buffer_minutes}"
        response = self.session.get(url)

        return response.json()

    @require_session
    def get_bulk_sleep_data(self, start: Union[datetime, str], end: Union[datetime, str], sleep_buffer_minutes: int = 60):
        if isinstance(start, str):
            start = datetime.fromisoformat(start)

        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        data = []
        for date in daterange(start, end):
            data.append(self.get_sleep_data(date, sleep_buffer_minutes))

        return data


