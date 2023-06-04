

class SubConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return str(self.__dict__)


class BaseConfig:
    max_param_combinations = 1000
    max_entry_exit_len = 50
