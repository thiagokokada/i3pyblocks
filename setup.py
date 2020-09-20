import setuptools

from i3pyblocks.__version__ import __version__

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
    url="https://i3pyblocks.readthedocs.io",
    project_urls={
        "Documentation": "https://i3pyblocks.readthedocs.io",
        "Source": "https://github.com/thiagokokada/i3pyblocks",
    },
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["i3pyblocks = i3pyblocks.cli:main"]},
    extras_require={
        "blocks.dbus": ["dbus-next>=0.1.1"],
        "blocks.http": ["aiohttp>=3.4.0"],
        "blocks.i3ipc": ["i3ipc>=2.0.1"],
        "blocks.inotify": ["aionotify>=0.2.0"],
        "blocks.ps": ["psutil>=5.4.8"],
        "blocks.pulse": ["pulsectl>=18.10.5"],
        "blocks.x11": ["python-xlib>=0.2.8"],
        # Non-runtime deps
        "dev": [
            "black",
            "flake8",
            "flake8-bugbear",
            "isort",
            "mypy",
            "pip-tools",
        ],
        "docs": [
            "sphinx",
            "sphinx-autoapi",
            "sphinx-rtd-theme",
        ],
        "test": [
            "asynctest",
            "pytest",
            "pytest-aiohttp",
            "pytest-asyncio",
            "pytest-cov",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires=">=3.6",
)
