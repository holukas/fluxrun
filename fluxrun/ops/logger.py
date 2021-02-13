import logging
import sys
from pathlib import Path


def setup_logger(settings_dict):
    logfile_name = f"{settings_dict['run_id']}.log"
    logfile_path = settings_dict['dir_out_run_log'] / logfile_name
    logger = create_logger(logfile_path=logfile_path, name='main_logger')
    return logger


def create_logger(name: str, logfile_path: Path = None):
    """
    Create name logger and log outputs to file

    A new logger is only created if name does not exist.

    Parameters
    ----------
    logfile_path: Path
        Path to the log file to which the log output is saved.
    name:
        Corresponds to the __name__ of the calling file.

    Returns
    -------
    logger class

    References
    ----------
    https://www.youtube.com/watch?v=jxmzY9soFXg
    https://stackoverflow.com/questions/53129716/how-to-check-if-a-logger-exists
    """

    logger = logging.getLogger(name)

    # Only create new logger if it does not exist already for the respective module,
    # otherwise the log output would be printed x times because a new logger is
    # created everytime the respective module is called.
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s:%(name)s:  %(message)s')

        file_handler = logging.FileHandler(logfile_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
