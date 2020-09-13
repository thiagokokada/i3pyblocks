from string import Formatter


class ExtendedFormatter(Formatter):
    # Based on https://stackoverflow.com/a/46160537
    def convert_field(self, value, conversion):
        """Extended conversion symbols.

        The following additional symbols have been added:

            - l: convert to string and lower case
            - u: convert to string and upper case

        Defaults are:

            - s: convert with str()
            - r: convert with repr()
            - a: convert with ascii()
        """

        if conversion == "u":
            return str(value).upper()
        elif conversion == "l":
            return str(value).lower()

        return super().convert_field(value, conversion)
