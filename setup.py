import sys

import setuptools
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def requirements_from_pip(filename):
    with open(filename, "r") as pip:
        return [dep.strip() for dep in pip if not dep.startswith("#") and dep.strip()]


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="i3pyblocks",
    version="0.1.0",
    author="Thiago Kenji Okada",
    author_email="thiagokokada@gmail.com",
    description="A replacement for i3status, written in Python using asyncio.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiagokokada/i3pyblocks",
    packages=setuptools.find_packages(),
    extras_require={
        "aiohttp": ["aiohttp>=3.4.0"],
        "aionotify": ["aionotify>=0.1.0"],
        "i3ipc": ["i3ipc>=2.0.1"],
        "psutil": ["psutil>=5.4.8"],
        "pulsectl": ["pulsectl>=18.10.5"],
    },
    tests_require=requirements_from_pip("requirements/dev.in"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    python_requires=">=3.7",
    cmdclass={"test": PyTest},
)
