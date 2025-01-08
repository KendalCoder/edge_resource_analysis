
class EnvConfig():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, EnvConfig(**value))
            elif isinstance(value, list):
                setattr(self, key, [EnvConfig(**v) for v in value])
            else:
                setattr(self, key, value)

