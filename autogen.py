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
FLINT_INCLUDE_DIR = "/home/doctorant/sage/local/include/flint"
if not os.path.isdir(FLINT_INCLUDE_DIR):
    print('Flint headers not found ({})'.format(FLINT_INCLUDE_DIR))
    sys.exit(1)

# location of flint documentation source files
FLINT_DOC_DIR = 'flint2/doc/source'
if not os.path.isdir(FLINT_DOC_DIR):
    print('Flint doc not found ({})'.format(FLINT_DOC_DIR))
    sys.exit(1)


class Extractor:
    r"""
    Tool to extract function declarations from a flint .rst file
    """
    NONE = 0
    FUNCTION_DECLARATION = 1
    FUNCTION_DOC = 2
    TYPE = 3
    MACRO = 4

    def __init__(self, filename):
        self.filename = filename
        if not filename.endswith('.rst'):
            raise ValueError

        # Attributes that are modified throughout the document parsing
        self.state = self.NONE    # position in the documentation
        self.section = None       # current section
        self.content = {}         # section -> list of pairs (function signatures, func documentation)
        self.functions = []       # current list of pairs (function signatures, func documentation)
        self.func_signatures = [] # current list of function signatures
        self.doc = []             # current function documentation

        with open(filename) as f:
            text = f.read()
        self.lines = text.splitlines()
        self.i = 0

    def run(self):
        while self.process_line():
            pass
        if self.state == self.FUNCTION_DECLARATION or self.state == self.FUNCTION_DOC:
            self.add_function()
        if self.functions:
            self.update_section()

    def update_section(self):
        if self.section not in self.content:
            self.content[self.section] = []
        self.content[self.section] += tuple(self.functions)
        self.functions.clear()

    def add_function(self):
        if self.state != self.FUNCTION_DECLARATION and self.state != self.FUNCTION_DOC:
            return
        while self.doc and not self.doc[-1]:
            self.doc.pop()
        for i, func_signature in enumerate(self.func_signatures):
            self.func_signatures[i] = func_signature.replace('slong', 'long').replace('ulong', 'unsigned long').replace('(void)', '()').replace(' enum ', ' ')
            if any(bad in self.func_signatures[i] for bad in [' in,', ' in)', '*in,', '*in)']):
                old = self.func_signatures[i]
                new = old.replace(' in,', ' input,').replace(' in)', ' input)').replace('*in,', '*input,').replace('*in)', '*input)')
                print('Warning: invalid python variable name in "{}" replaced with "{}"'.format(old, new))
                self.func_signatures[i] = new
        self.functions.append((tuple(self.func_signatures), tuple(self.doc)))
        self.func_signatures.clear()
        self.doc.clear()
        self.state = self.NONE

    def process_line(self):
        r"""
        Process one line of documentation.
        """
        if self.i >= len(self.lines):
            return 0

        line = self.lines[self.i]
        if line.startswith('.. function::'):
            self.add_function()
            if not line[13] == ' ':
                print('Warning: no space {}'.format(line))
            self.func_signatures.append(line[13:].strip())
            self.state = self.FUNCTION_DECLARATION
            self.i += 1
        elif line.startswith('.. type::'):
            # type
            # NOTE: we do nothing as the documentation duplicates type declaration
            # and lacks the actual list of attributes
            self.add_function()
            self.state = self.TYPE
            self.i += 1
        elif line.startswith('.. macro::'):
            # macro
            # TODO: these should be treated
            self.add_function()
            self.state = self.MACRO
            self.i += 1
        elif self.state == self.FUNCTION_DECLARATION:
            if len(line) > 14 and line.startswith(' ' * 14):
                # function with similar declaration
                line = line[14:].strip()
                if line:
                    self.func_signatures.append(line)
                self.i += 1
            elif not line.strip():
                # leaving function declaration
                self.state = self.FUNCTION_DOC
                self.i += 1
            else:
                raise ValueError(line)
        elif self.state == self.FUNCTION_DOC and line.startswith('    '):
            # function doc
            line = line.strip()
            if line:
                self.doc.append(line)
            self.i += 1
        elif self.i + 1 < len(self.lines) and self.lines[self.i + 1].startswith('----'):
            # new section
            self.add_function()
            self.IN_MACRO = self.IN_TYPE = False
            if self.functions:
                self.update_section()
            section = line
            self.i += 2
        elif not line:
            self.i += 1
        elif self.state == self.FUNCTION_DOC or self.state == self.FUNCTION_DECLARATION:
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
        continue
    if prefix == "machine_vectors":
        # TODO: fix me
        fft_small_absolute_header = os.path.join(FLINT_INCLUDE_DIR, 'fft_small.h')
        if not os.path.isfile(fft_small_absolute_header):
            print('Warning: skipping machine_vectors.h because fft_small.h is not there')
            continue
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
        for func_signatures, doc in content[section]:
            print(file=output)
            for line in func_signatures:
                print('    {}'.format(line), file=output)
            for line in doc:
                print('    # {}'.format(line), file=output)

    output.close()


for extra_header in ['nmod_types.h']:
    if extra_header in header_list:
        print('Warning: {} already in HEADER_LIST'.format(extra_header))
    header_list.append(extra_header)

with open('flint_wrap.h.template') as f:
    text = f.read()
with open(os.path.join(OUTPUT_DIR, 'flint_wrap.h'), 'w') as output:
    output.write(text.format(HEADER_LIST='\n'.join('#include <flint/{}>'.format(header) for header in header_list)))

with open('types.pxd.template') as f:
    text = f.read()
with open(os.path.join(OUTPUT_DIR, 'types.pxd'), 'w') as output:
    output.write(text.format(HEADER_LIST=' '.join('flint/{}'.format(header) for header in header_list)))
