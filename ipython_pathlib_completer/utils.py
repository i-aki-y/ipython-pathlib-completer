from pathlib import Path
import logging


def enable_debug_log(log_file_path, format=None):
    """
    Enables debug logging for the ipython_pathlib_completer package.

    This function configures the logger for the package to output messages
    at DEBUG level and above to a specified file.

    Args:
        log_file_path (str): The path to the file where debug logs will be
                             written. This will create or append to the
                             specified file.
        format (str, optional): A custom log format string. If not provided,
                                a default format will be used. Defaults to None.
    """
    log_file_path = Path(log_file_path)
    logger_name = "ipython_pathlib_completer"
    handler = logging.FileHandler(filename=log_file_path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(format or "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger = logging.getLogger(logger_name)

    # Remove existing handlers to avoid duplicate log entries
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
