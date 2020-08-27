class AttributeDict(dict):
    """Dict that supports key access via attributes

    For example:
    >>> attr_dict = AttributeDict(a="foo", b="bar")
    >>> attr_dict["a"] == attr_dict.a  # True

    Why is this useful? To simulate namedtuples without having to actually
    create one.

    Can be used in tests to simulate response from external libraries.
    """

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value
