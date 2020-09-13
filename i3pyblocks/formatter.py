from string import Formatter


class ExtendedFormatter(Formatter):
    # Based on https://stackoverflow.com/a/46160537
    def convert_field(self, value, conversion):
        """Extended conversion symbols.

        The following additional symbols have been added:

            - l: convert to string and lower case
            - u: convert to string and UPPER CASE
            - c: convert to string and Capitalize
            - t: convert to string and Title-Ize

        Defaults are:

            - s: convert with str()
            - r: convert with repr()
            - a: convert with ascii()
        """

        if conversion == "u":
            return str(value).upper()
        elif conversion == "l":
            return str(value).lower()
        elif conversion == "c":
            return str(value).capitalize()
        elif conversion == "t":
            return str(value).title()

        return super().convert_field(value, conversion)
