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

class BufferedISlice(object):
    """Iterator with semantics similar to normal array slicing
    ([start:stop:step]).

    Unlike itertools.islice, this iterator supports negative stop
    values. A major difference compared to normal array slicing is
    that this iterator always returns a tuple containing all elements
    in a step. Additionally, if the last step runs out of data, it
    will return a short tuple.  For example,
    list(BufferedISlice("abcde", 0, None, 2)) will result in [ ('a',
    'b'), ('c', 'd'), ('e') ].
    """

    def __init__(self, stream, start=0, stop=None, step=1):
        self.cur = 0
        self.start = start
        self.stop = stop
        self.step = step

        self.buffer_size = step if stop == None or stop > 0 \
            else step + -stop

        self.buffer = []

        self.stream = stream

    def __iter__(self):
        return self

    def __test_stop_condition(self):
        if self.stop is None or self.stop < 0:
            return False
        elif self.stop >= 0:
            return self.cur >= self.stop

    def next(self):
        if self.stream is None:
            raise StopIteration()

        while self.cur < self.start:
            self.cur += 1
            self.stream.next()

        try:
            while len(self.buffer) < self.buffer_size and \
                    (self.stop is None or self.stop < 0 or self.stop > self.cur):
                self.cur += 1
                self.buffer.append(self.stream.next())
        except StopIteration:
            pass

        if len(self.buffer) < self.buffer_size:
            # We didn't read enough data to fill the entire buffer, so
            # we have reached the stop condition.
            self.stream = None

            # We might have some valid entries in the buffer, emit
            # them and pad with None.
            valid = self.step - (self.buffer_size - len(self.buffer))
            if valid > 0:
                out = tuple(self.buffer[0:valid])
                return out
            else:
                raise StopIteration()
        else:
            out = tuple(self.buffer[0:self.step])
            self.buffer = self.buffer[self.step:]
            return out[0] if self.step == 1 else out
