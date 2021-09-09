from os.path import join

from hdx.utilities import CleanCommand, PackageCommand, PublishCommand
from hdx.utilities.loader import load_file_to_str
from setuptools import find_namespace_packages, setup

requirements = [
    "hdx-python-utilities>=3.0.2",
    "libhxl>=4.24.1",
    "pyphonetics",
    "exchangerates",
]

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

PublishCommand.version = load_file_to_str(
    join("src", "hdx", "location", "version.txt"), strip=True
)

setup(
    name="hdx-python-country",
    description="HDX Python country mapping utilities",
    license="MIT",
    url="https://github.com/OCHA-DAP/hdx-python-country",
    version=PublishCommand.version,
    author="Michael Rans",
    author_email="rans@email.com",
    keywords=[
        "HDX",
        "location",
        "country code",
        "country",
        "iso 3166",
        "iso2",
        "iso3",
        "region",
    ],
    long_description=load_file_to_str("README.md"),
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    zip_safe=True,
    classifiers=classifiers,
    install_requires=requirements,
    cmdclass={
        "clean": CleanCommand,
        "package": PackageCommand,
        "publish": PublishCommand,
    },
)
