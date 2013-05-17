from setuptools import setup, find_packages
from multiprocessing import util

setup(
    name="epubbuilder",
    version="0.1.1",
    author="Anders Pearson",
    author_email="anders@columbia.edu",
    url="",
    description="epub builder library",
    long_description="forked from python-epub-builder",
    install_requires = [
        "lxml", "genshi", "nose"
        ],
    scripts = [],
    license = "BSD",
    platforms = ["any"],
    zip_safe=False,
    packages=['epubbuilder'],
    test_suite='nose.collector',
    include_package_data=True,
    )
