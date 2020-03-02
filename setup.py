from setuptools import setup

setup(name='pyunisens',
      python_requires='>=3.6',
      version='1.02',
      description='A python implementation of the Unisens standard',
      url='http://github.com/skjerns/pyUnisens',
      author='skjerns',
      license='GNU 2.0',
      packages=['unisens'],
      install_requires=[
         'numpy',
         'datetime',
         'pandas'],
      zip_safe=False)
