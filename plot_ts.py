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

import matplotlib.pyplot as plt

def plot(stream, fun_x, *args, **kwargs):
    x = []
    y = [ list() for fun_y in args ]
    for step in stream:
        if isinstance(step, tuple):
            step = step[0]

        x.append(fun_x(step))
        for _y, fun_y in zip(y, args):
            _y.append(fun_y(step))

    fig = plt.figure()
    plt.hold(True)
    plt.xlim(x[0], x[-1])
    if 'title' in kwargs:
        plt.title(kwargs['title'])

    plt.xlabel(str(fun_x))

    for fun_y, _y in zip(args, y):
        plt.plot(x, _y,
                 '-+',
                 label=str(fun_y),
                 drawstyle="steps-post")

    plt.legend()
    plt.hold(False)

    return plt

def main():
    parser = argparse.ArgumentParser(description='Plot a time series from a gem5 log.')
    parser.add_argument('log', metavar='LOG', type=argparse.FileType('r'),
                        help='Log file')
    parser.add_argument('fun', metavar='FUN', type=str, nargs='+',
                        help='Function to plot')

    parser.add_argument('--x', metavar='FUN', type=str,
                        default="LV('sim_insts')",
                        help='Function for the x-axis')

    parser.add_argument('--save-fmt', metavar='FMT', type=str,
                        default="pdf",
                        help='Format of saved plot')

    parser.add_argument('--save', metavar='FILE', type=argparse.FileType('w'),
                        default=None,
                        help='Store plot to file')

    parser.add_argument("--start", metavar="NUM", type=int, default=1,
                        help="Skip the first NUM entries")

    parser.add_argument("--stop", metavar="NUM", type=int, default=None,
                        help="Stop after NUM entries")

    parser.add_argument("--step", metavar="N", type=int, default=1,
                        help="Use every N windows")

    args = parser.parse_args()

    fun_x = logquery.eval_fun(args.x)
    fun_y = []
    for fun in args.fun:
        fun_y.append(logquery.eval_fun(fun))

    stream = BufferedISlice(log.stream_log(args.log),
                            start=args.start, stop=args.stop,
                            step=args.step)

    plt = plot(stream, fun_x, *fun_y, title=args.log.name)
    if args.save:
        plt.savefig(args.save, format=args.save_fmt)
    else:
        plt.show()

if __name__ == "__main__":
    main()
