import sys


class Logger(object):
    def __init__(self, name, linebreak=False):
        # if ironpython
        if sys.implementation.name == "ironpython":
            # if in pyrevit
            try:
                from pyrevit import script

                self.logger = script.get_logger()
            # if not
            except ImportError:
                self.logger = self._start_logger(name, linebreak)
        # if cpython
        elif sys.implementation.name == "cpython":
            self.logger = self._start_logger(name, linebreak)

        else:
            print(sys.implementation.name)
            self.logger = self._start_logger(name, linebreak)

    @staticmethod
    def _start_logger(name, linebreak):
        if linebreak:
            lb = "\n    "
        else:
            lb = " "
        LOG_FORMAT = (
            "%(asctime)s (%(name)s):" + lb + "%(levelname)s - %(message)s"
        )
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S (UTC/GMT %z)"

        import logging

        # Create a custom logger
        logger = logging.getLogger(name)

        # Create a handler
        handler = logging.StreamHandler()

        # Create a formatter
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)

        # Add handler & set level
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.propagate = False

        return logger

    def __call__(self):
        return self.logger


if __name__ == "__main__":
    cl = Logger("foo")
    cl.logger.info("foo")

    logger = Logger("bar")()
    logger.info("bar")
