from setuptools import setup, find_packages

setup(
    name='dstcalc',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'shiny',
        'numpy',
        'openpyxl',
        'pytest',
    ],
    author='Bea Loubser',
    description='Drug Susceptibility Testing Calculator (CLI and Shiny app)',
    include_package_data=True,
    python_requires='>=3.8',
) 