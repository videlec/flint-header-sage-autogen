r"""
Paths of the flint source and installation
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

import os

if not os.path.isdir('flint2'):
    raise ValueError('You must first clone the flint git repo')

# location of flint headers
FLINT_INCLUDE_DIR = "/home/doctorant/sage/local/include/flint"
if not os.path.isdir(FLINT_INCLUDE_DIR):
    raise ValueError('Flint headers not found ({})'.format(FLINT_INCLUDE_DIR))

# location of flint documentation source files
FLINT_DOC_DIR = 'flint2/doc/source'
if not os.path.isdir(FLINT_DOC_DIR):
    raise ValueError('Flint doc not found ({})'.format(FLINT_DOC_DIR))
