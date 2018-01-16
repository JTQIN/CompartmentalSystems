# Although the following packages are mentioned in setup.py as dependencies
# the install in the order determined by setuptools seems to fail sometimes, probably
# due to unstated dependencies of numpy and matlotlib.
# This script helps in such cases but is not intended to replace setup.py
# 

pip3 install --upgrade pip
pip3 install --upgrade setuptools


python3 setup.py develop

# enable jupyter notebook nbextensions
jupyter contrib nbextension install --user
jupyter nbextensions_configurator enable --user
jupyter nbextension enable python-markdown/main

