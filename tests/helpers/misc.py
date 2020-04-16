class AttributeDict(dict):
    __getattr__ = dict.__getitem__  # type: ignore
    __setattr__ = dict.__setitem__  # type: ignore
