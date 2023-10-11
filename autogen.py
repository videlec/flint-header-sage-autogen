r"""
Autogeneration of the flint Cython header files for sage

It generates a pxd header for each flint header fline as well as the
flint_wrap.h files that properly include all flint headers.
"""

#*****************************************************************************
#       Copyright (C) 2023 Vincent Delecroix <20100.delecroix@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

import sys, os

if not os.path.isdir('flint2'):
    print('You must first clone the flint git repo')
    sys.exit(1)

# where the output files will be created
OUTPUT_DIR = 'pxd_headers'
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

# location of flint headers
if os.path.isdir('flint2/src'):
    FLINT_INCLUDE_DIR = 'flint2/src'
else:
    FLINT_INCLUDE_DIR = 'flint2'
if not os.path.isdir(FLINT_INCLUDE_DIR):
    print('Flint include dir not found ({})'.format(FLINT_INCLUDE_DIR))

# location of flint documentation source files
FLINT_DOC_DIR = 'flint2/doc/source'
if not os.path.isdir(FLINT_DOC_DIR):
    print('Flint doc dir not found ({})'.format(FLINT_DOC_DIR))


class Extractor:
    r"""
    Tool to extract function declarations from a .rst file
    """
    def __init__(self, filename):
        self.filename = filename
        if not filename.endswith('.rst'):
            raise ValueError
        self.IN_FUNCTION = False
        self.IN_TYPE = False
        self.IN_MACRO = False
        self.section = None
        self.doc = []
        self.content = {}
        self.functions = []
        with open(filename) as f:
            text = f.read()
        self.lines = text.splitlines()
        self.i = 0

    def run(self):
        while self.process_line():
            pass
        if self.IN_FUNCTION:
            self.add_function()

    def add_function(self):
        if not self.IN_FUNCTION:
            raise RuntimeError
        while self.doc and not self.doc[-1]:
            self.doc.pop()
        self.functions.append((self.func_signature, tuple(self.doc)))
        self.func_signature = None
        self.doc.clear()
        self.IN_FUNCTION = False

    def process_line(self):
        if (self.IN_FUNCTION + self.IN_TYPE + self.IN_MACRO) > 1:
            raise RuntimeError('IN_FUNCTION={} IN_TYPE={} IN_MACRO={}'.format(self.IN_FUNCTION, self.IN_TYPE, self.IN_MACRO))
        if self.i >= len(self.lines):
            return 0

        line = self.lines[self.i]
        if line.startswith('.. function::'):
            if self.IN_FUNCTION:
                self.add_function()
            self.func_signature = line[14:]
            self.IN_FUNCTION = True
            self.IN_TYPE = self.IN_MACRO = False
            self.i += 1
        elif line.startswith('.. type::'):
            # type
            # NOTE: we do nothing as the documentation duplicates type declaration
            # and lacks the actual list of attributes
            if self.IN_FUNCTION:
                self.add_function()
            self.IN_MACRO = False
            self.IN_TYPE = True
            self.i += 1
        elif line.startswith('.. macro::'):
            if self.IN_FUNCTION:
                self.add_function()
            self.IN_TYPE = False
            self.IN_MACRO = True
            self.i += 1
        elif line.startswith('              ') and self.IN_FUNCTION:
            # continuation of function signature
            self.func_signature += line[14:]
            self.i += 1
        elif line.startswith('    ') and self.IN_FUNCTION:
            # function doc
            self.doc.append(line[4:])
            self.i += 1
        elif self.i + 1 < len(self.lines) and self.lines[self.i + 1].startswith('----'):
            # new section
            if self.IN_FUNCTION:
                self.add_function()
            if self.functions:
                self.content[self.section] = tuple(self.functions)
                self.functions.clear()
            section = line
            self.i += 2
        elif not line:
            self.i += 1
        elif self.IN_FUNCTION:
            self.add_function()
            self.i += 1
        else:
            self.i += 1

        return 1


def extract_functions(filename):
    r"""
    OUTPUT:

    dictionary: section -> list of pairs (func_sig, doc)
    """
    e = Extractor(filename)
    e.run()
    return e.content


header_list = []
for filename in os.listdir(FLINT_DOC_DIR):
    if not filename.endswith('.rst'):
        continue
    prefix = filename[:-4]

    absolute_filename = os.path.join(FLINT_DOC_DIR, filename)
    content = extract_functions(absolute_filename)
    if not content:
        # NOTE: skip files with no function declaration
        continue

    # try to match header
    header = prefix + '.h'
    absolute_header = os.path.join(FLINT_INCLUDE_DIR, header)
    if not os.path.isfile(absolute_header):
        print('Warning: skipping {} because no associated .h found'.format(filename))
    header_list.append(header)

    output = open(os.path.join(OUTPUT_DIR, prefix + '.pxd'), 'w')

    print('# distutils: libraries = flint', file=output)
    print('# distutils: depends = flint/{}'.format(prefix + '.h'), file=output)
    print(file=output)
    print('#' * 80, file=output)
    print('# This file is auto-generated. Do not modify by hand', file=output)
    print('#' * 80, file=output)
    print(file=output)

    print('from libc.stdio cimport FILE', file=output)
    print('from sage.libs.gmp.types cimport *', file=output)
    print('from sage.libs.mpfr.types cimport *', file=output)
    print('from sage.libs.flint.types cimport *', file=output)
    print(file=output)

    print('cdef extern from "flint_wrap.h":', file=output)

    for section in content:
        if section is not None:
            print('    ## {}'.format(section), file=output)
        print(file=output)
        for func_signature, doc in content[section]:
            print('    {}'.format(func_signature), file=output)
            for line in doc:
                print('    # {}'.format(line), file=output)
            print(file=output)

    output.close()

with open('flint_wrap.h.template') as f:
    text = f.read()
with open(os.path.join(OUTPUT_DIR, 'flint_wrap.h'), 'w') as output:
    output.write(text.format(HEADER_LIST='\n'.join('#include <flint/{}>'.format(header) for header in header_list)))

with open('types.pxd.template') as f:
    text = f.read()
with open(os.path.join(OUTPUT_DIR, 'types.pxd'), 'w') as output:
    output.write(text.format(HEADER_LIST=' '.join('flint/{}'.format(header) for header in header_list)))
