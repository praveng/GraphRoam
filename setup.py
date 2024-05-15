from setuptools import setup, find_packages

setup(
    name='GraphRoam',           # Update this with your desired package name
    version='0.1.0',            # Initial version number
    packages=find_packages(),   # Automatically find packages in the directory
    install_requires=[
        'duckdb>=0.10.2',
        'numpy>=1.26.4',
        'pyarrow>=16.0.0',
        'scipy>=1.13.0'
    ],
    description='A Python library for efficient random walks on massive graphs',
    author='praveng',         # Replace with your name
    url='https://github.com/praveng/graphroam',  # Replace with your project's URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',    # Specify compatible Python versions
    include_package_data=True,
    package_data={
        '': ['graphroam/logo-graphroam.png'],
    }
)

