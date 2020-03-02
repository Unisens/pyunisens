from setuptools import setup

setup(name='pyunisens',
      python_requires='>=3.6',
      version='1.0',
      description='A python implementation of the Unisens standard',
      url='http://github.com/skjerns/pyUnisens',
      author='skjerns',
      author_email='nomail',
      license='GNU 2.0',
      packages=['unisens'],
      install_requires=[
         'numpy',
         'datetime'],
      zip_safe=False)
