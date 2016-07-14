
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

CRSS = (
    4326,  # WGS84
    32661, 32761,  # WGS84 UPS-N and UPS-S
    32601, 32602, 32603, 32604, 32605, 32606, 32607, 32608, 32609, 32610,  # WGS84 UTM  1N-10N
    32611, 32612, 32613, 32614, 32615, 32616, 32617, 32618, 32619, 32620,  # WGS84 UTM 11N-20N
    32621, 32622, 32623, 32624, 32625, 32626, 32627, 32628, 32629, 32630,  # WGS84 UTM 21N-30N
    32631, 32632, 32633, 32634, 32635, 32636, 32637, 32638, 32639, 32640,  # WGS84 UTM 31N-40N
    32641, 32642, 32643, 32644, 32645, 32646, 32647, 32648, 32649, 32650,  # WGS84 UTM 41N-50N
    32651, 32652, 32653, 32654, 32655, 32656, 32657, 32658, 32659, 32660,  # WGS84 UTM 51N-60N
    32701, 32702, 32703, 32704, 32705, 32706, 32707, 32708, 32709, 32710,  # WGS84 UTM  1S-10S
    32711, 32712, 32713, 32714, 32715, 32716, 32717, 32718, 32719, 32720,  # WGS84 UTM 11S-20S
    32721, 32722, 32723, 32724, 32725, 32726, 32727, 32728, 32729, 32730,  # WGS84 UTM 21S-30S
    32731, 32732, 32733, 32734, 32735, 32736, 32737, 32738, 32739, 32740,  # WGS84 UTM 31S-40S
    32741, 32742, 32743, 32744, 32745, 32746, 32747, 32748, 32749, 32750,  # WGS84 UTM 41S-50S
    32751, 32752, 32753, 32754, 32755, 32756, 32757, 32758, 32759, 32760,  # WGS84 UTM 51S-60S
    0, # ImageCRS
)


pep_path = '/home/tamp/pep.lib/scripts/tampDataAssessmentUtility.py'


class execute_pep_process(Component):
    """ API for pep processing
    """
    implements(ProcessInterface)

    identifier = "execute_assessment"
    title = "Execute assessment process of the PEP Library"
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]



# usage: tampDataAssessmentUtility.py [-h] -c COVERAGE [-g GROUND_PRODUCT] -u
#                                     UR_LAT -d LL_LAT -l LL_LON -r UR_LON -s
#                                     T_S [-e T_E] [--spatialtolerance degree]
#                                     [--temporaltolerance mins]
#                                     FUNCTION

# Utility used to provide results "on-the-fly" between wcs data and ground db
# data

# optional arguments:
#   -h, --help            show this help message and exit

# Required function:
#   FUNCTION              Available functions are: correlation

# Coverage required options:
#   -c COVERAGE           CoverageID to search in wcs server
#   -g GROUND_PRODUCT     Ground product to search in DB, used in correlation
#                         function
#   -u UR_LAT             Upper latitude
#   -d LL_LAT             Lower latitude
#   -l LL_LON             Far west latitude
#   -r UR_LON             Far east latitude
#   -s T_S                Start time/date expressed in Unix Timestamp
#   -e T_E                End time/date expressed in Unix Timestamp

# Function 'correlation' optional arguments:
#   --spatialtolerance degree
#                         Apply the spatialtolerance in correlation function,
#                         default 1 degree
#   --temporaltolerance mins
#                         Apply the temporaltolerance in correlation function,
#                         default 60 mins



    inputs = [
        ("process", LiteralData('process', str, optional=False,
            abstract="Assesment functions; Available functions are: correlation",
        )),
        ("collection", LiteralData('collection', str, optional=False,
            abstract="CoverageID to search in wcs server",
        )),
        ("o_collection", LiteralData('o_collection', str, optional=True,
            abstract="(collection name, to be used in case of combination functions",
        )),
        ("ground_product", LiteralData('ground_product', str, optional=False,
            abstract="Ground product to search in DB",
        )),
        ("bbox", BoundingBoxData("bbox", crss=CRSS, optional=False,
            abstract="Bounding Box used for computation",
        )),
        ("start_time", LiteralData('start_time', str, optional=False,
            abstract="Start time/date expressed in Unix Timestamp",
        )),
        ("end_time", LiteralData('end_time', str, optional=True,
            default=None, abstract="End time/date expressed in Unix Timestamp",
        )),
        ("spatialtolerance", LiteralData('spatialtolerance', str, optional=True,
            default=None, abstract="Apply the spatialtolerance in correlation function, default 1 degree",
        )),
        ("temporaltolerance", LiteralData('temporaltolerance', str, optional=True,
            default=None, abstract="Apply the temporaltolerance in correlation function, default 60 mins",
        )),
    ]


    outputs = [
        ("output", LiteralData('output', str,
            abstract="pep Processing result"
        )),
    ]
    

    def execute(self, process, collection, o_collection, ground_product, bbox, start_time, 
                end_time,  spatialtolerance, temporaltolerance, **kwarg):

        outputs = {}

        cmd_args = [
            'python', pep_path, process,
            '-c', collection,
            '-u', str(bbox.upper[1]), '-d', str(bbox.lower[1]),
            '-l', str(bbox.lower[0]), '-r', str(bbox.upper[0]),
            '-s', start_time,
            '-e',str(end_time)
        ]

        if o_collection:
            cmd_args.extend(['-o',o_collection])

        if ground_product:
            cmd_args.extend(['-g',ground_product])

        if spatialtolerance:
            cmd_args.extend(['--spatialtolerance',spatialtolerance])

        if temporaltolerance:
            cmd_args.extend(['--temporaltolerance',temporaltolerance])


        result = check_output(cmd_args)
        outputs['output'] = result


        return outputs

