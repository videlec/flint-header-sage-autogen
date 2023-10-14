import os
from flint_pxd_autogen import write_flint_cython_headers

# where the output files will be created
OUTPUT_DIR = 'pxd_headers'
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

write_flint_cython_headers(OUTPUT_DIR)
