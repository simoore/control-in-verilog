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
civ_install_requires = ['numpy', 'jinja2', 'scipy', 'deap']
civ_pacakges = ['controlinverilog']
civ_version = 0.1

with open(readme_file, encoding='utf-8') as f:
    civ_long_description = f.read()

setup(name=civ_name,
      version=civ_version,
      description=civ_description,
      long_description=civ_long_description,
      url=civ_url,
      author=civ_author,
      author_email=civ_author_email,
      license=civ_license,
      packages=civ_pacakges,
      install_requires=civ_install_requires,
      zip_safe=False,
      include_package_data=True)
