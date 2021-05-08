import csv
import json
import logging
from datetime import datetime
from io import StringIO
from os import getenv
from pathlib import Path
from typing import Any, Dict, Generator

import pytz
import requests
from dateutil.parser import parse
from gouge.colourcli import Simple
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

LOG = logging.getLogger(__name__)
Simple.basicConfig(level=logging.INFO)
UTC = pytz.timezone("UTC")
Lux = pytz.timezone("Europe/Luxembourg")


class Client:
    def __init__(self, url: str = "", auth_file_name: str = "") -> None:
        self.url = getenv("PHOSCON_URL", url)
        if url == "":
            raise ValueError("URL cannot be empty!")
        self.auth_file_name = getenv("PHOSCON_AUTH_FILENAME", auth_file_name)
        self.key = ""

    def login(self) -> None:
        config = Path(self.auth_file_name)
        if self.auth_file_name and config.exists():
            auth_data = json.loads(config.read_text())
            LOG.info("Credentials loaded from %r", config)
            self.key = auth_data["username"]
            return

        LOG.info("%r not found. Requesting new key", config)
        response = requests.post(
            f"{self.url}/api", json={"devicetype": "influxmonitor"}
        )
        if response.status_code > 400:
            if response.json()[0]["error"]["type"] == 101:
                LOG.error(
                    "Looks like the endpoint does not allow requesting new "
                    "keys. Refer to the documentation on how to open up the "
                    "gateway."
                )
            LOG.debug("Error response: %r", response.text)
            response.raise_for_status()
        data = response.json()
        auth_data = data[0]["success"]
        if self.auth_file_name:
            with config.open("w") as fptr:
                json.dump(auth_data, fptr)
                LOG.info("Credentials stored to %r", config)
        self.key = auth_data["username"]

    def sensors(self) -> Generator[dict, None, None]:
        response = requests.get(f"{self.url}/api/{self.key}/sensors")
        response.raise_for_status()
        data = response.json()
        for info in data.values():
            yield info

    def get_weather(self) -> Dict[str, Any]:
        sensorstates = {}
        for row in self.sensors():
            if row["modelid"] != "lumi.weather":
                continue
            sensordata = sensorstates.setdefault(row["name"], {})
            naive = parse(row["state"]["lastupdated"])
            sensordata["lastupdated"] = UTC.localize(naive)
            sensordata["battery"] = row["config"]["battery"]
            if row["type"] == "ZHAHumidity":
                sensordata["humidity"] = row["state"]["humidity"] / 100
            elif row["type"] == "ZHATemperature":
                sensordata["temperature"] = row["state"]["temperature"] / 100
            elif row["type"] == "ZHAPressure":
                sensordata["pressure"] = row["state"]["pressure"]
        return sensorstates


def as_csv(data: Dict[str, Any]) -> str:
    """
    Convert a measurement dict to a CSV line
    """
    outfile = StringIO()
    writer = csv.writer(outfile)
    for key, values in data.items():
        line = [
            values["lastupdated"].isoformat(),
            key,
            values["battery"],
            values["temperature"],
            values["humidity"],
            values["pressure"],
        ]
        writer.writerow(line)
    return outfile.getvalue().strip()


class FileOutput:
    def __init__(self) -> None:
        self.filename = getenv("PHOSCON_OUTFILE", "")
        if not self.filename:
            raise Exception("Env-var PHOSCON_OUTFILE is required!")

    def put(self, data: Dict[str, Any]) -> None:
        with open(self.filename, "a+") as fptr:
            print(as_csv(data), file=fptr)


class InfluxOutput:
    def __init__(self) -> None:
        self.host = self._safeget("INFLUX_HOST")
        self.token = self._safeget("INFLUX_TOKEN")
        self.org = self._safeget("INFLUX_ORG")
        self.bucket = self._safeget("INFLUX_BUCKET")

    def _safeget(self, key: str) -> str:
        value = getenv(key, "")
        if not value:
            raise Exception(f"Env-var {key} is required!")
        return value

    def put(self, data: Dict[str, Any]) -> None:
        client = InfluxDBClient(url=self.host, token=self.token)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        for sensor_name, values in data.items():
            point = (
                Point("climate")
                .tag("sensor", sensor_name)
                .field("battery", float(values["battery"]))
                .field("temperature", float(values["temperature"]))
                .field("humidity", float(values["humidity"]))
                .field("pressure", float(values["pressure"]))
                .time(datetime.utcnow(), WritePrecision.NS)
            )
            write_api.write(self.bucket, self.org, point)


def main():
    from time import sleep

    from dotenv import load_dotenv

    load_dotenv(".env")

    client = Client("http://192.168.178.43:8888", "auth/auth.json")
    client.login()
    output = InfluxOutput()

    while True:
        data = client.get_weather()
        output.put(data)
        print(as_csv(data))
        sleep(60 * 15)


if __name__ == "__main__":
    main()
