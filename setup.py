# vim:set ff=unix expandtab ts=4 sw=4:
from setuptools import setup, find_packages
def readme():
    with open('README.md') as f:
        return f.read()

#def requirements():
#    with open('requirements.txt') as f:
#        return f.read()

setup(name='CompartmentalSystems',
        version='1.0',
        #test_suite="example_package.tests",#http://pythonhosted.org/setuptools/setuptools.html#test
        description='Compartmental Systems',
        long_description=readme(),#avoid duplication 
        author='Holger Metzler, Markus Müller',
        author_email='hmetzler@bgc-jena.mpg.de',
        #url='https://projects.bgc-jena.mpg.de/hg/SOIL-R/Code/packageTests/bgc_md',
        packages=find_packages(), #find all packages (multifile modules) recursively
        #py_modules=['external_module'], # external_module.py is a module living outside this dir as an example how to iclude something not 
        classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Education "
        ],
        entry_points={
        'console_scripts': [
                #'generate_website= bgc_md.autoGeneratedMD_holger:parse_args', # creates an executable with name foo
                ]
        },
        dependency_links=['git+ssh://git@github.com/MPIBGC-TEE/LAPM.git#egg=LAPM'],   
        install_requires=[
        #'sympy',
        #'numpy',
        #'scipy',
    	#'matplotlib',
        #'plotly',
        #'concurrencytest',
        #'LAPM',
        #'jupyter',
        #'tqdm'
        ],
        # to hopefully make RTD work
        include_package_data=True,
        zip_safe=False)

