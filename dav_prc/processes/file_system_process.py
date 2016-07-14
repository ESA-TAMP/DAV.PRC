
#-------------------------------------------------------------------------------

# Project: EOxServer <http://eoxserver.org>
# Authors: Daniel Santillan <daniel.santillan@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


import os 
from uuid import uuid4
import os.path
import base64
from subprocess import CalledProcessError, check_output, Popen

import datetime as dt
import time

from itertools import izip
from lxml import etree
from StringIO import StringIO

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.exceptions import InvalidOutputDefError
from eoxserver.services.result import ResultBuffer, ResultFile
from eoxserver.services.ows.wps.parameters import (
    ComplexData, CDObject, CDTextBuffer, CDFile, 
    FormatText, FormatXML, FormatJSON, FormatBinaryRaw, FormatBinaryBase64,
    BoundingBoxData, BoundingBox,
    LiteralData, String,
    AllowedRange, UnitLinear,
)

pep_path = '/home/tamp/pep.lib/scripts/FilesystemData.py'


class execute_file_system(Component):
    """ API for pep file system processing
    """
    implements(ProcessInterface)

    identifier = "execute_file_system"
    title = "Execute process of the file system PEP Library"
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]


# Usage, in folder “/home/tamp/pep.lib/scripts”:

# usage: FilesystemData.py [-h] [--standalone] -f func -l label [-c coverage]
#                          [-n name] -u value [-i dir] [-o dir] [--gain val]
#                          [--offset val]

# Utility used to reprocess entire collections on filesystem

# optional arguments:
#   -h, --help    show this help message and exit
#   --standalone  Execute the module stand-alone, without going through ingester in das_ing

# Required Arguments:
#   -f func       available functions are: verticalIntegration, convert
#   -l label      new label to attach to new filename

# Required Arguments if NOT executed stand-alone:
#   -c coverage   Coverage_ID in data_ingestion_collectiontable
#   -n name       New name for data_ingestion_collectiontable
#   -u value      measurement unit for new collection

# Required Arguments if executed stand-alone:
#   -i dir        directory where search tif recoursively
#   -o dir        directory where put results, Created if not exists

# function 'convert' optional arguments (Result = (coverage_ID+offset)*gain) :
#   --gain val    apply the gain in conversion function, default 1

#   --offset val  apply the offset in conversion function, default 0


    inputs = [
        ("process", LiteralData('process', str, optional=False,
            abstract="available functions are: verticalIntegration, convert",
        )),
        ("label", LiteralData('label', str, optional=False,
            abstract="new label to attach to new filename",
        )),
        ("collection", LiteralData('collection', str, optional=False,
            abstract="collection name",
        )),
        ("name", LiteralData('name', str, optional=False,
            abstract="New name for data_ingestion_collectiontable",
        )),
        ("value", LiteralData('value', str, optional=False,
            abstract="measurement unit for new collection",
        )),
        ("gain", LiteralData('gain', str, optional=True,
            default=None, abstract="The gain factor (needed only for conversion unit function) (--gain)",
        )),
        ("offset", LiteralData('offset', str, optional=True,
            default=None, abstract="The offset factor (needed only for conversion unit function) (--offset)",
        ))
    ]


    outputs = [
        ("output", LiteralData('output', str,
            abstract="pep Processing result"
        )),
    ]
    

    def execute(self, process, label, collection, name, value, gain,
                offset, **kwarg):

        outputs = {}

        cmd_args = ['python', pep_path,
                    '-f', process,
                    '-l', label,
                    '-c', collection,
                    '-n', name,
                    '-u', value ]

        if gain:
            cmd_args.extend(['--gain',str(gain)])

        if offset:
            cmd_args.extend(['--offset',offset])


        result = check_output(cmd_args)
        outputs['output'] = result


        return outputs

