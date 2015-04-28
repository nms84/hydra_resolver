from setuptools import setup, find_packages

setup(
    name = 'hydra_resolver',
    version = '1.0',
    description = 'An asynchronous hostname resolver powered by Twisted',
    packages = find_packages(),
    package_data = {'hydra_resolver': ['data/tld_nameservers.pkl']},
    url = 'https://github.com/nms84/hydra_resolver',
    license = 'GPLv3',
    author = 'Nick Summerlin',
    author_email = 'nick@sinkhole.me',
    install_requires = [
        "twisted >= 13.2.0"
    ]
)