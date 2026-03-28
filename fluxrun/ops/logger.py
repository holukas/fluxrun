import logging
import sys


def setup_logger(settings: dict,
                 log_level: int = logging.DEBUG,
                 log_format: str = '%(asctime)s [%(levelname)s]    %(message)s'):
    """
    Configure logger to write all logs to a main file and warnings/errors/critical
    logs to a separate warnings file.

    logger.debug('This debug message will only be in main.log.')
    logger.info('This info message will only be in main.log.')
    logger.warning('This warning message will be in both main.log and warnings.log!')
    logger.error('This error message will also be in both files.')
    logger.critical('This critical message will also be in both files.')

    Args:
        settings: fluxrun settings.
        log_level: The lowest logging level to capture for the main logger.
                         Defaults to logging.DEBUG.
        log_format: The format string for log messages.
    """
    # Main logfile
    main_logfile = f"{settings['_run_id']}_main.log"
    main_logfile_path = settings['_dir_out_run_log'] / main_logfile

    # Warnings logfile
    warnings_logfile = f"{settings['_run_id']}_warnings_errors.log"
    warnings_logfile_path = settings['_dir_out_run_log'] / warnings_logfile

    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create handler for main log file
    main_handler = logging.FileHandler(main_logfile_path)
    main_handler.setLevel(log_level)
    main_handler.setFormatter(formatter)
    logger.addHandler(main_handler)

    # Add stream handler for main log file
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Create handler for warnings file
    warnings_handler = logging.FileHandler(warnings_logfile_path)
    warnings_handler.setLevel(logging.WARNING)
    warnings_handler.setFormatter(formatter)
    logger.addHandler(warnings_handler)

    return logger


def log_section_start(logger: logging.Logger, section_name: str) -> None:
    """Log the start of a major processing section with visual separator.

    Args:
        logger: Logger instance to write to.
        section_name: Name of the section being started.
    """
    logger.info("")  # Blank line for readability
    logger.info("=" * 80)
    logger.info(section_name)
    logger.info("=" * 80)


def log_subsection_start(logger: logging.Logger, subsection_name: str) -> None:
    """Log the start of a subsection with dash separator.

    Args:
        logger: Logger instance to write to.
        subsection_name: Name of the subsection being started.
    """
    logger.info("-" * 40)
    logger.info(subsection_name)
    logger.info("-" * 40)


def log_eddypro_output(logger: logging.Logger, line: str, command: str) -> None:
    """Log EddyPro subprocess output with consistent formatting.

    Detects flux averaging period markers and formats them distinctly.

    Args:
        logger: Logger instance to write to.
        line: Output line from EddyPro subprocess.
        command: Name of the EddyPro command being executed.
    """
    if 'processing new flux averaging period' in line.lower():
        logger.info("-" * 60)
    else:
        logger.info(f"[EDDYPRO] [{command}] {line}")


def log_completion(logger: logging.Logger, operation_name: str, success: bool = True) -> None:
    """Log successful or failed completion of an operation.

    Args:
        logger: Logger instance to write to.
        operation_name: Name of the operation being completed.
        success: Whether the operation succeeded (default: True).
    """
    symbol = "✓" if success else "✗"
    status = "completed successfully" if success else "failed"
    logger.info(f"{symbol} {operation_name} {status}")


# def setup_logger(settings_dict):
#     logfile_name = f"{settings_dict['_run_id']}.log"
#     logfile_path = settings_dict['_dir_out_run_log'] / logfile_name
#     logger = create_logger(logfile_path=logfile_path, name='main_logger')
#     return logger

#
# def create_logger(name: str, logfile_path: Path = None):
#     """
#     Create name logger and log outputs to file
#
#     A new logger is only created if name does not exist.
#
#     Parameters
#     ----------
#     logfile_path: Path
#         Path to the log file to which the log output is saved.
#     name:
#         Corresponds to the __name__ of the calling file.
#
#     Returns
#     -------
#     logger class
#
#     References
#     ----------
#     https://www.youtube.com/watch?v=jxmzY9soFXg
#     https://stackoverflow.com/questions/53129716/how-to-check-if-a-logger-exists
#     """
#
#     logger = logging.getLogger(name)
#
#     # Only create new logger if it does not exist already for the respective module,
#     # otherwise the log output would be printed x times because a new logger is
#     # created everytime the respective module is called.
#     if not logger.hasHandlers():
#         logger.setLevel(logging.DEBUG)
#
#         formatter = logging.Formatter('%(asctime)s:%(name)s:  %(message)s')
#
#         file_handler = logging.FileHandler(logfile_path)
#         file_handler.setLevel(logging.DEBUG)
#         file_handler.setFormatter(formatter)
#
#         stream_handler = logging.StreamHandler(stream=sys.stdout)
#         stream_handler.setFormatter(formatter)
#
#         logger.addHandler(file_handler)
#         logger.addHandler(stream_handler)
#
#     return logger
