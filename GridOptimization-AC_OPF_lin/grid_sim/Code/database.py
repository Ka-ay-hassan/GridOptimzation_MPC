import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd


class Database:
    def __init__(self, bucket: str, organization: str, api_token: str, url: str) -> None:
        """class to create interface for database"""
        self.bucket = bucket
        self.organization = organization
        self.api_token = api_token
        self.url = url
        self.client = self._create_client()

    def write_to_db(self, data: pd.DataFrame, measurement: str) -> None:
        if not self.client:
            self.client = self._create_client()
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        try:
            # column names are fields
            write_api.write(bucket=self.bucket, org=self.organization, record=data,
                            data_frame_measurement_name=measurement)  # _measurement
        except Exception as e:
            print(e)
        write_api.__del__()

    def _create_client(self) -> influxdb_client.InfluxDBClient:
        return influxdb_client.InfluxDBClient(url=self.url, token=self.api_token, org=self.organization, timeout=30_000)

    def close_client(self) -> None:
        self.client.__del__()

