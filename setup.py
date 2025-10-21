from setuptools import setup, find_packages


setup(
    name='pyrift',
    version='0.0.0',
    url='https://github.com/96-LB/pyrift',
    license='MIT',
    author='96 LB',
    author_email='pyrift@96lb.me',
    description='Python library for managing Rift of the NecroDancer charts',
    packages=find_packages(),
    package_data={
        'pyrift': [
            'py.typed'
        ]
    },
    platforms='any',
    install_requires=[
    ]
)
