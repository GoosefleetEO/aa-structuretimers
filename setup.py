import os

from setuptools import find_packages, setup

from structuretimers import __version__

# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="aa-structuretimers",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license="MIT",
    description=(
        "An app for keeping track of Eve Online structure timers "
        "with Alliance Auth and Discord"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/ErikKalkoken/aa-structuretimers",
    author="Erik Kalkoken",
    author_email="kalkoken87@gmail.com",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires="~=3.7",
    install_requires=[
        "allianceauth>=2.15.1",
        "django-eveuniverse>=0.16",
        "redis-simple-mq>=0.4",
        "dhooks_lite>=0.6.1",
        "django-multiselectfield",
        "requests",
        "allianceauth-app-utils>=1.13",
    ],
)
