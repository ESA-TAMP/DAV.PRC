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


pep_path = '/home/tamp/pep.lib/scripts/tampProcessingUtilities.py'


class execute_pep_process(Component):
    """ Process to calcuate coverage spatial average
    """
    implements(ProcessInterface)

    identifier = "execute_pep_process"
    title = "Execute process of the PEP Library"
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("coverage", LiteralData('coverage', str, optional=False,
            abstract="ID of coverage to be used in processing",
        )),
        ("process", LiteralData('process', str, optional=False,
            abstract="PEP Process to be called by request",
        )),
        ("begin_time", LiteralData('begin_time', str, optional=False,
            abstract="Start of the time interval",
        )),
        ("end_time", LiteralData('end_time', str, optional=True,
            default=None, abstract="End of the time interval",
        )),
        ("bbox", BoundingBoxData("bbox", crss=CRSS, optional=False,
            abstract="Bounding Box used for computation",
        )),
        ("o_coverage", LiteralData('o_coverage', str, optional=True,
            default=None, abstract="ID for coverage to be used in band combination",
        )),
        ("gain", LiteralData('gain', str, optional=True,
            default=None, abstract="Gain factor for unit conversion",
        )),
        ("offset", LiteralData('offset', str, optional=True,
            default=None, abstract="Offset factor for unit conversion",
        )),
    ]


    outputs = [
        ("output", LiteralData('output', str,
            abstract="Average of coverage"
        )),
    ]
    
    #outputs = [
    #    ("output",
    #        ComplexData('output',
    #            title="PEP Process result",
    #            abstract="Returns the PEP process call results",
    #            formats=FormatText('text/plain')
    #        )
    #    ),
    #]

    def execute(self, coverage, process, begin_time, end_time, bbox,
                o_coverage, gain, offset, **kwarg):

        outputs = {}

        cmd_args = ['python', pep_path, process,
                    '-c', 'ALARO_Surface_pressure_surface_4326_0059882',
                    '-u', str(bbox.upper[1]), '-d', str(bbox.lower[1]),
                    '-l', str(bbox.lower[0]), '-r', str(bbox.upper[0]),
                    '-s', str(1368576000)]

        if end_time:
            cmd_args.extend(['-e',str(end_time)])

        if o_coverage:
            cmd_args.extend(['-o',o_coverage])

        if gain:
            cmd_args.extend(['--gain',str(gain)])

        if offset:
            cmd_args.extend(['--offset',offset])

        result = check_output(cmd_args)
        outputs['output'] = result


        return outputs

