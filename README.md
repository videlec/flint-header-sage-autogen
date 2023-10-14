Autogeneration of flint header files for SageMath
=================================================

Instructions
------------

1. Obtain a clone of the flint repo, eg `git clone https://github.com/flintlib/flint2`

2. Checkout to the appropriate commit, eg `git checkout v2.9.0`

3. Manually adjust the content of `types.pxd.template` (which will be used to generate
   types.pxd)

4. Manually adjust the content of `flint_pxd_autogen/env.py`

5. Run the `autogen.py` script, eg `python autogen.py`

6. Copy all the files generated in `pxd_headers` inside the sage source tree (ie `SAGE_SRC/sage/libs/flint`)
