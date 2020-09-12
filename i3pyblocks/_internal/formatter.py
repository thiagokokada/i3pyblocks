from string import Formatter


class ExtendedFormatter(Formatter):
    def convert_field(self, value, conversion):
        """Extend conversion symbol. Based on https://stackoverflow.com/a/46160537

        Following additional symbol has been added:

            - l: convert to string and low case
            - u: convert to string and up case

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
