from setuptools import setup, find_packages

setup(
	name = "pyside6_utils",
	version= "1.2.0",
	packages=find_packages('.'),
    description="A collection of useful widgets and utilities for PySide6 compatible with pyside6-designer.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown", #Long description is in markdown
    author="Wouter Stokman",
    url="https://github.com/Woutah/pyside6-utils",
    license="LPGPLv2",
    include_package_data=True,
    install_requires=[
        'pandas>=1.5.2', #Works for 1.23.5
        'numpy>=1.0.0', #Works for 1.23.5
        'PySide6>=6.0.0', # Qt for Python, works for 6.5.1.1
        'pathos>=0.3.0', #Works for 0.3.0
        'setuptools>=65.0.0', #Works for 65.5.0
        'winshell>=0.6; platform_system == "Windows"'
	]
)