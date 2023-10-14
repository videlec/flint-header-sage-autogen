r"""
Autogeneration of the flint Cython header files for sage

It generates a pxd header for each flint header fline as well as the types.pxd
declaring flint types and flint_wrap.h files that properly include all flint
headers.
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

import os, shutil
from .env import FLINT_INCLUDE_DIR, FLINT_DOC_DIR


class Extractor:
    r"""
    Tool to extract function declarations from a flint .rst file
    """
    NONE = 0
    DOC = 1
    FUNCTION_DECLARATION = 2
    MACRO_DECLARATION = 4
    TYPE_DECLARATION = 8

    def __init__(self, filename):
        self.filename = filename
        if not filename.endswith('.rst'):
            raise ValueError

        # Attributes that are modified throughout the document parsing
        self.state = self.NONE    # position in the documentation
        self.section = None       # current section
        self.content = {}         # section -> list of pairs (function signatures, func documentation)
        self.functions = []       # current list of pairs (function signatures, func documentation)
        self.signatures = []      # current list of function/macro/type signatures
        self.doc = []             # current function documentation

        with open(filename) as f:
            text = f.read()
        self.lines = text.splitlines()
        self.i = 0

    def run(self):
        while self.process_line():
            pass
        if self.state & self.FUNCTION_DECLARATION:
            self.add_function()
        if self.state & self.MACRO_DECLARATION:
            self.add_macro()
        if self.functions:
            self.update_section()
        self.state = self.NONE

    def update_section(self):
        if self.section not in self.content:
            self.content[self.section] = []
        self.content[self.section] += tuple(self.functions)
        self.functions.clear()

    def clean_doc(self):
        # Remove empty lines at the end of documentation
        while self.doc and not self.doc[-1]:
            self.doc.pop()

        for i, line in enumerate(self.doc):
            # To make sage linter happier
            line = line.replace('\\choose ', 'choose ')
            self.doc[i] = line

    def clean_signatures(self):
        if (self.state & self.FUNCTION_DECLARATION) or (self.state & self.MACRO_DECLARATION):
            for i, func_signature in enumerate(self.signatures):
                replacement = [('(void)', '()'), (' enum ', ' ')]
                for bad_type, good_type in replacement:
                    func_signature = func_signature.replace(bad_type, good_type)

                bad_arg_names = [('in', 'input'), ('lambda', 'lmbda'), ('iter', 'it')]
                replacements = [(pattern.format(bad), pattern.format(good)) for pattern in [' {},', ' {})', '*{},', '*{})'] for bad, good in bad_arg_names]
                for bad_form, good_form in replacements:
                    func_signature = func_signature.replace(bad_form, good_form)

                self.signatures[i] = func_signature

    def add_declaration(self):
        if self.state & self.FUNCTION_DECLARATION:
            self.add_function()
        elif self.state & self.MACRO_DECLARATION:
            self.add_macro()
        elif self.state & self.TYPE_DECLARATION:
            self.add_type()

        self.signatures.clear()
        self.doc.clear()
        self.state = self.NONE

    def add_function(self):
        self.clean_doc()

        # Drop va_list argument
        signatures = []
        for func_signature in self.signatures:
            if '(' not in func_signature or ')' not in func_signature:
                raise RuntimeError(func_signature)
            elif 'va_list ' in func_signature:
                print('Warning: va_list unsupported {}'.format(func_signature))
            else:
                signatures.append(func_signature)
        self.signatures = signatures
        self.clean_signatures()

        self.functions.append((tuple(self.signatures), tuple(self.doc)))

    def add_macro(self):
        # TODO: we might want to support auto-generation of macros
        return

    def add_type(self):
        # TODO: we might want to support auto-generation of types
        return
 
    def process_line(self):
        r"""
        Process one line of documentation.
        """
        if self.i >= len(self.lines):
            return 0

        if bool(self.state & self.FUNCTION_DECLARATION) + bool(self.state & self.MACRO_DECLARATION) + bool(self.state & self.TYPE_DECLARATION) > 1:
            raise RuntimeError('self.state = {} and i = {}'.format(self.state, self.i))

        line = self.lines[self.i]
        if line.startswith('.. function::'):
            self.add_declaration()
            if line[13] != ' ':
                print('Warning: no space {}'.format(line))
            self.signatures.append(line[13:].strip())
            self.state = self.FUNCTION_DECLARATION
            self.i += 1
        elif line.startswith('.. macro::'):
            self.add_declaration()
            if line[10] != ' ':
                print('Warning no space{}'.format(line))
            self.signatures.append(line[10:].strip())
            self.state = self.MACRO_DECLARATION
            self.i += 1
        elif line.startswith('.. type::'):
            # type
            # NOTE: we do nothing as the documentation duplicates type declaration
            # and lacks the actual list of attributes
            self.add_declaration()
            self.state = self.TYPE_DECLARATION
            self.i += 1
        elif self.state == self.FUNCTION_DECLARATION:
            if len(line) > 14 and line.startswith(' ' * 14):
                # function with similar declaration
                line = line[14:].strip()
                if line:
                    self.signatures.append(line)
                self.i += 1
            elif not line.strip():
                # leaving function declaration
                self.state |= self.DOC
                self.i += 1
            else:
                raise ValueError(line)
        elif self.state == self.MACRO_DECLARATION:
            if len(line) > 10 and line.startswith(' ' * 10):
                # macro with similar declaration
                line = line[10:].strip()
                if line:
                    self.signatures.append(line)
                self.i += 1
            elif not line.strip():
                # leaving macro declaration
                self.state |= self.DOC
                self.i += 1
            else:
                raise ValueError(line)
        elif (self.state & self.DOC) and line.startswith('    '):
            # function doc
            line = line.strip()
            if line:
                self.doc.append(line)
            self.i += 1
        elif self.i + 1 < len(self.lines) and self.lines[self.i + 1].startswith('----'):
            # new section
            self.add_declaration()
            if self.functions:
                self.update_section()
            section = line
            self.i += 2
        elif not line:
            self.i += 1
        else:
            self.add_declaration()
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


def write_flint_cython_headers(output_dir):
    r"""
    Write cython header files.

    Arguments
    output_dir -- (string) path where to write the .pxd files
    """
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

        output = open(os.path.join(output_dir, prefix + '.pxd'), 'w')

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

        if os.path.isfile(os.path.join('macros', prefix + '_macros.pxd')):
            print('\nfrom .{} cimport *'.format(prefix + '_macros'), file=output)

        output.close()


    for extra_header in ['nmod_types.h']:
        if extra_header in header_list:
            print('Warning: {} already in HEADER_LIST'.format(extra_header))
        header_list.append(extra_header)

    with open('flint_wrap.h.template') as f:
        text = f.read()
    with open(os.path.join(output_dir, 'flint_wrap.h'), 'w') as output:
        output.write(text.format(HEADER_LIST='\n'.join('#include <flint/{}>'.format(header) for header in header_list)))

    with open('types.pxd.template') as f:
        text = f.read()
    with open(os.path.join(output_dir, 'types.pxd'), 'w') as output:
        output.write(text.format(HEADER_LIST=' '.join('flint/{}'.format(header) for header in header_list)))

    for filename in os.listdir('macros'):
        prefix = filename[:-4]
        shutil.copy(os.path.join('macros', filename), os.path.join(output_dir, filename))
