class StopProcessException(Exception):
    def __init__(self):
        self.code = 0

    def __str__(self):  # pragma: no cover
        return 'Stop Process'
