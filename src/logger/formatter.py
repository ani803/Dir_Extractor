import logging


class CustomFormatter(logging.Formatter):

    FORMAT = (
        "%(asctime)s | "
        "%(levelname)-8s | "
        "%(name)-20s | "
        "%(message)s"
    )

    DATEFMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):

        super().__init__(
            fmt=self.FORMAT,
            datefmt=self.DATEFMT
        )