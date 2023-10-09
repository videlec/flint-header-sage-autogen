r"""
Autogeneration of the flint Cython header files for sage

It generates a pxd header for each flint header fline as well as the
flint_wrap.h files that properly include all flint headers.
"""
import os
import sys

if not os.isdir('flint2'):
    print('You must first clone the flint git repo')
    sys.exit(1)

FLINT_DOC_DIR = 'flint2/doc/source'
INCLUDE_DIR = 'flint2/src/'
OUTPUT_DIR = 'pxd_headers'

header_list = []

for filename in os.listdir(FLINT_DOC_DIR):
    if not filename.endswith('.rst'):
        continue
    prefix = filename[:-4]

    # try to match header
    header = os.path.join(INCLUDE_DIR, prefix + '.h')
    if not os.path.isfile(header):
        print('no header for prefix={} (tried {})'.format(prefix, header))
        continue
    header_list.append(prefix + '.h')

    print('treat {}'.format(prefix))
    full_filename = os.path.join(FLINT_DOC_DIR, filename)
    with open(full_filename) as f:
        text = f.read()

    lines = text.splitlines()
    output = open(os.path.join(OUTPUT_DIR, prefix + '.pxd'), 'w')

    print('# distutils: libraries = flint', file=output)
    print('# distutils: depends = flint/{}'.format(prefix + '.h'), file=output)
    print(file=output)

    print('from libc.stdio cimport FILE', file=output)
    print('from sage.libs.gmp.types cimport *', file=output)
    print('from sage.libs.flint.types cimport *', file=output)
    print('from sage.libs.mpfr.types cimport *', file=output)

    print(file=output)
    print('cdef extern from "flint_wrap.h":', file=output)

    IN_FUNCTION = False
    comment = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith('.. function::'):
            if IN_FUNCTION:
                print(file=output)
            func_signature = line[14:]
            print('    {}'.format(func_signature), file=output)
            IN_FUNCTION = True
            i += 1
            continue
        elif line.startswith('              ') and IN_FUNCTION:
            func_signature = line[14:]
            print('    {}'.format(func_signature), file=output)
            i += 1
            continue
        elif not line:
            i += 1
            continue
        elif IN_FUNCTION and line.startswith('    '):
            comment = line[4:]
            print('    # {}'.format(comment), file=output)
            i += 1
            continue
        elif i + 1 < len(lines) and lines[i + 1].startswith('----') and not line.startswith('Types'):
            # section
            print(file=output)
            print('    ## {}'.format(line), file=output)
            print(file=output)
            IN_FUNCTION = False
            i += 2
            continue
        elif IN_FUNCTION:
            IN_FUNCTION = False
            print(file=output)
            i += 1
            continue
        else:
            i += 1
            continue
        
    output.close()

with open('flint_wrap.h.template') as f:
    text = f.read()
with open(os.path.join(OUTPUT_DIR, 'flint_wrap.h'), 'w') as output:
    output.write(text.format(HEADER_LIST='\n'.join('#include <flint/{}>'.format(header) for header in header_list)))
