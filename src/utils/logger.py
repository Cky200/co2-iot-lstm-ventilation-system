import json
import logging
import os
import sys


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as single-line JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt) if record.created else "",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Extract extra properties dynamically (excluding logging internals)
        # Any extra fields supplied via logger.info("msg", extra={"key": "val"}) will be appended.
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName"
            }:
                log_data[key] = value

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a production-grade logger, supporting structured JSON logging.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Check if structured logging is enabled
        use_structured = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"

        if use_structured:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Stream Handler for Console
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger
