#!/usr/bin/env python
#
# Copyright (c) 2013 Andreas Sandberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Andreas Sandberg

from gem5stats import log
from gem5stats import logquery
from gem5stats.util import BufferedISlice
import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Plot a time series from a gem5 log.')
    parser.add_argument('log', metavar='LOG', type=argparse.FileType('r'),
                        help='Log file')
    parser.add_argument('fun', metavar='FUN', type=str, nargs='+',
                        help='Function to plot')
    parser.add_argument('--fs', metavar='C', type=str,
                        default=":",
                        help='Field separator')

    parser.add_argument("--last", action="store_true", default=False,
                        help="Only print the last entry")

    parser.add_argument("--start", metavar="NUM", type=int, default=0,
                        help="Skip the first NUM entries")

    parser.add_argument("--stop", metavar="NUM", type=int, default=None,
                        help="Stop after NUM entries")

    parser.add_argument("--step", metavar="N", type=int, default=1,
                        help="Use every N windows")

    args = parser.parse_args()

    funs = []
    for fun in args.fun:
        funs.append(logquery.eval_fun(fun))

    for no, fun in enumerate(funs):
        print "# %i: %s" % (no, fun)

    out = []

    stream = BufferedISlice(log.stream_log(args.log),
                            start=args.start, stop=args.stop,
                            step=args.step)
    for step in stream:
        if isinstance(step, tuple):
            step = step[0]

        out = [ f(step) for f in funs ]
        if not args.last:
            print args.fs.join([ str(s) for s in out ])
    if args.last:
        print args.fs.join([ str(s) for s in out ])

if __name__ == "__main__":
    main()
