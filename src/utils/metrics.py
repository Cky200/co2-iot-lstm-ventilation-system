from prometheus_client import Counter, Gauge, Histogram

# Sensor metrics
CO2_LEVEL_PPM = Gauge(
    "co2_level_ppm",
    "Current CO2 level in PPM",
    ["device_id"]
)

CO2_READINGS_TOTAL = Counter(
    "co2_readings_total",
    "Total number of CO2 readings processed",
    ["device_id"]
)

VENTILATION_RELAY_STATUS = Gauge(
    "ventilation_relay_status",
    "Current status of the ventilation relay (1=ON, 0=OFF)",
    ["device_id"]
)

CO2_VOLTAGE_VOLTS = Gauge(
    "co2_voltage_volts",
    "Current sensor voltage in Volts",
    ["device_id"]
)

# LSTM prediction metrics
CO2_PREDICTIONS_TOTAL = Counter(
    "co2_predictions_total",
    "Total number of LSTM predictions generated",
    ["device_id"]
)

CO2_PREDICTION_ERROR_MAE = Gauge(
    "co2_prediction_error_mae",
    "Mean Absolute Error of LSTM predictions",
    ["device_id"]
)

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)
