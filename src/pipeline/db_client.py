import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from src.utils.logger import get_logger

logger = get_logger(__name__)

class InfluxDBWrapper:
    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN", "super-secret-auth-token")
        self.org = os.getenv("INFLUXDB_ORG", "co2-org")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "co2-data")
        
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info(f"Initialized InfluxDB client at {self.url}")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            raise

    def write_sensor_data(self, device_id: str, ppm: float, voltage: float, relay_state: bool):
        try:
            point = (
                Point("co2_measurement")
                .tag("device", device_id)
                .field("ppm", float(ppm))
                .field("voltage", float(voltage))
                .field("relay_state", int(relay_state))
                .time(None, WritePrecision.NS) # Uses current time
            )
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def query_recent_data(self, minutes_back: int = 60) -> list:
        """
        Query data from the last X minutes.
        Returns a list of dictionaries with time, ppm, voltage, relay_state.
        """
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -{minutes_back}m)
          |> filter(fn: (r) => r["_measurement"] == "co2_measurement")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> yield(name: "results")
        '''
        results = []
        try:
            tables = self.query_api.query(query, org=self.org)
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "ppm": record.values.get("ppm"),
                        "voltage": record.values.get("voltage"),
                        "relay_state": record.values.get("relay_state")
                    })
        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            
        return results

    def close(self):
        self.client.close()
