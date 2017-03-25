This is a Python package for compartmental systems.

Python package to deal with compartmental models. These models can
be both nonlinear and nonautonomous. Consequently, this package can be seen
as an extension of [LAPM](https://github.com/goujou/LAPM) which deals
with linear autonomous models.
While [LAPM](https://github.com/goujou/LAPM) also allows explicit symbolic compuations of age distributions 
in compartmental systems, this package is mostly concerned with numerical
computations of

* age

    * compartmental age densities
    * system age densities
    * compartmental age mean and higher order moments
    * system age mean and higher order moments
    * compartmental age quantiles
    * system age quantiles

* transit time

    * forward and backward transit time densities
    * backward transit time mean and higher order moments
    * forward and backward transit time quantiles

---

[Documentation](http://compartmentalsystems.readthedocs.io/en/latest/)

---

Installation simply via the install script `install.sh`.
Be sure to have [LAPM](https://github.com/goujou/LAPM) installed.
Further required packages can be found in the install script.

---

Jupyter notebook examples
-------------------------

- [Nonlinear global carbon cycle model (html)](notebooks/nonl_gcm_3p/nonl_gcm_3p.html)
- [Nonlinear global carbon cycle model (ipynb)](notebooks/nonl_gcm_3p/nonl_gcm_3p.ipynb)



