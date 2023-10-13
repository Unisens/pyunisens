from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pyunisens',
      python_requires='>=3.6',
      version='1.5.0',
      description='A python implementation of the Unisens standard',
      url='http://github.com/Unisens/pyUnisens',
      author='skjerns',
      license='GNU 2.0',
      packages=['unisens'],
      long_description=long_description,
      long_description_content_type="text/markdown",
      install_requires=[
         'numpy',
         'datetime',
         'pandas'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
      ],
      zip_safe=False)
