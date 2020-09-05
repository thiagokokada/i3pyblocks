import setuptools

from i3pyblocks.__version__ import __version__


def requirements_from_pip(filename):
    with open(filename, "r") as pip:
        return [dep.strip() for dep in pip if not dep.startswith("#") and dep.strip()]


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="i3pyblocks",
    version=__version__,
    author="Thiago Kenji Okada",
    author_email="thiagokokada@gmail.com",
    description="A replacement for i3status, written in Python using asyncio.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiagokokada/i3pyblocks",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["i3pyblocks = i3pyblocks.__main__:main"]},
    extras_require={
        "aiohttp": ["aiohttp>=3.4.0"],
        "aionotify": ["aionotify>=0.1.0"],
        "i3ipc": ["i3ipc>=2.0.1"],
        "psutil": ["psutil>=5.4.8"],
        "pulsectl": ["pulsectl>=18.10.5"],
        "dev": requirements_from_pip("requirements/dev.in"),
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires=">=3.7",
)
