import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
readme_file = os.path.join(here, 'README.md')

civ_name = 'controlinverilog'
civ_description = 'Templating signal processing and control functions in verilog.'
civ_license = 'MIT'
civ_author = 'Steven Moore'
civ_author_email = 'steven.ian.moore@gmail.com'
civ_url = 'http://github.com/simoore/control-in-verilog'
civ_install_requires = ['numpy', 'jinja2']
civ_pacakges = ['controlinverilog']
civ_version = 0.1

with open(readme_file, encoding='utf-8') as f:
    civ_long_description = f.read()

#civ_classifiers = [
#    'Environment :: Console',
#    'License :: OSI Approved :: MIT License',
#    'Operating System :: MacOS :: MacOS X',
#    'Operating System :: Microsoft :: Windows',
#    'Operating System :: POSIX',
#    'Programming Language :: Python :: Implementation :: CPython',
#    'Programming Language :: Python :: 2.7',
#    'Programming Language :: Python :: 3.3',
#    'Programming Language :: Python :: 3.4',
#    'Programming Language :: Python :: 3.5',
#    'Programming Language :: Python :: 3.6',
#    'Topic :: Utilities'
#]

setup(name=civ_name,
      version=civ_version,
      description=civ_description,
      long_description=civ_long_description,
      url=civ_url,
      #classifiers=civ_classifiers,
      author=civ_author,
      author_email=civ_author_email,
      license=civ_license,
      packages=civ_pacakges,
      install_requires=civ_install_requires,
      zip_safe=False,
      include_package_data=True)
