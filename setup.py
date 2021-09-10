from setuptools import setup, find_packages

setup(
    name="weathermonitor",
    version="1.0.2",
    description="Simple weather-monitor for Zigbee/Phoscon sensors",
    url="https://github.com/exhuma/config_resolver",
    author="Michel Albert",
    author_email="michel@albert.lu",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "packaging",
        "pytz",
        "requests",
        "python-dateutil",
        "gouge",
        "influxdb_client",
        "python-dotenv",
    ],
)
