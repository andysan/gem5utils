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

from abc import *
import numbers
import types
import inspect

def box(val):
    """Automatically wrap common Python types.

    This method takes its input and wraps it to allow it to be used in
    a log query. Strings are automatically translated to translated to
    log values and numbers are translated to constants.

    This enables expressions on the form: LV("sim_seconds") / 60
    """
    if isinstance(val, M5Value):
        return val
    elif isinstance(val, str):
        return LogValue(val)
    elif isinstance(val, numbers.Number):
        return Constant(val)
    else:
        raise RuntimeError("Illegal type in argument")

class M5Value(object):
    """Base class for all elements in a gem5 log expression.

    A gem5 log expression is essentially a tree of objects derived
    from the M5Value class. The expression is evaluated by calling the
    root node with a stat dump as its sole parameter, which returns
    the results of the query.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    def __add__(self, other):
        return Add(self, other)

    def __sub__(self, other):
        return Sub(self, other)

    def __mul__(self, other):
        return Mul(self, other)

    def __div__(self, other):
        return Div(self, other)

    @abstractmethod
    def __call__(self, dump):
        """Evaluate a gem5 query.

        Arguments:
          dump -- Stats dump
        """
        pass

    @abstractmethod
    def __str__(self):
        """Return a text representation of the query."""
        pass

    def reset(self):
        """Reset internal state to allow reuse of an evaluated query."""
        pass

class BinOperator(M5Value):
    """Base class for binary operators.

    Binary operators should normally derive from this class. It
    provides consistent handling of arguments and printing. A minimal
    implementation only needs to overload _fun.
    """
    def __init__(self, lhs, rhs, name):
        M5Value.__init__(self)
        self.lhs = box(lhs)
        self.rhs = box(rhs)
        self.name = name

    def __call__(self, x):
        return self._fun(self.lhs(x), self.rhs(x))

    def __str__(self):
        return "(%s %s %s)" % (str(self.lhs), self.name, str(self.rhs))

    def reset(self):
        self.lhs.reset()
        self.rhs.reset()

    @abstractmethod
    def _fun(self, lhs, rhs):
        """Evaluate a binary operator.

        Arguments:
          lhs -- Results from the left hand side of the expression.
          rhs -- Results from the right hand side of the expression.
        """
        pass

class Add(BinOperator):
    """Add two elements"""

    def __init__(self, lhs, rhs):
        BinOperator.__init__(self, lhs, rhs, "+")

    def _fun(self, lhs, rhs):
        return lhs + rhs


class Sub(BinOperator):
    """Subtract two elements"""

    def __init__(self, lhs, rhs):
        BinOperator.__init__(self, lhs, rhs, "-")

    def _fun(self, lhs, rhs):
        return lhs - rhs

class Mul(BinOperator):
    """Multiply two elements"""

    def __init__(self, lhs, rhs):
        BinOperator.__init__(self, lhs, rhs, "*")

    def _fun(self, lhs, rhs):
        return lhs * rhs

class Div(BinOperator):
    """Divide two elements"""

    def __init__(self, lhs, rhs):
        BinOperator.__init__(self, lhs, rhs, "/")

    def _fun(self, lhs, rhs):
        return lhs / rhs


class LogValue(M5Value):
    """Get the value of a named element in a statistics dump. Raises a
    KeyError exception if the attribute cannot be found and no default
    has been provided.

    Arguments:
      attr -- Name of the attribute to return.

    Keyword Arguments:
      default -- Default value to return if not found.
    """

    def __init__(self, attr, default=None):
        M5Value.__init__(self)
        self.attr = attr
        self.default = default

    def __call__(self, x):
        return x.get_float(self.attr, default=self.default)

    def __str__(self):
        if self.default != None:
            return """LV("%s", default=%s)""" % (self.attr, self.default)
        else:
            return """LV("%s")""" % (self.attr)

LV = LogValue

class DerivedLogValue(M5Value):
    """Base class for derived log values."""

    def __init__(self, attr, name=None):
        M5Value.__init__(self)
        self.attr = attr
        self.name = name if name != None else self.__class__.__name__

    def __str__(self):
        return "%s(\"%s\")" % (self.name, self.attr)

class IPC(DerivedLogValue):
    """Return the IPC of a CPU.

    Arguments:
      attr -- Base name of the CPU (e.g., 'system.cpu')

    Keyword Arguments:
      default -- Default value if the CPU didn't execute any instructions.
    """
    def __init__(self, attr, default=None):
        DerivedLogValue.__init__(self, attr)
        self.default = default

    def __call__(self, x):
        try:
            return x.get_float("%s.committedInsts" % self.attr) / \
                x.get_float("%s.numCycles" % self.attr)
        except ZeroDivisionError:
            return self.default

class CPI(DerivedLogValue):
    """Return the CPI of a CPU.

    Arguments:
      attr -- Base name of the CPU (e.g., 'system.cpu')

    Keyword Arguments:
      default -- Default value if the CPU didn't execute any instructions.
    """

    def __init__(self, m5name, default=None):
        DerivedLogValue.__init__(self, m5name)
        self.default = default

    def __call__(self, x):
        try:
            return x.get_float("%s.numCycles" % self.attr) / \
                x.get_float("%s.committedInsts" % self.attr)
        except ZeroDivisionError:
            return self.default

class Constant(M5Value):
    """Return a constant value.

    Arguments:
      constant -- Value to return.
    """

    def __init__(self, constant):
        M5Value.__init__(self)
        self.constant = constant

    def __call__(self, x):
        return self.constant

    def __str__(self):
        return str(self.constant)


class Function(M5Value):
    """Base class for functions.

    A basic function implementation only needs to overload _fun. The
    base class will automatically evaluate all arguments in order and
    call _fun with the results as a list of arguments.
    """
    def __init__(self, params, name=None):
        M5Value.__init__(self)
        params = params if isinstance(params, (list, tuple)) else (params,)
        self.params = tuple([ box(p) for p in params ])
        self.name = name if name != None else self.__class__.__name__

    def __call__(self, x):
        return self._fun(*[ p(x) for p in self.params ])

    def __str__(self):
        params = ",".join([ str(p) for p in self.params ])
        return "%s(%s)" % (self.name, params)

    def reset(self):
        for p in self.params:
            p.reset()

        self._reset()

    def _reset(self):
        pass

    @abstractmethod
    def _fun(self, *args):
        pass


class Accumulate(Function):
    """Function accumulating the results of its parameter. The
    accumulator is returned on every call."""
    def __init__(self, param, start=0.0):
        Function.__init__(self, param)
        self.start = start
        self.reset()

    def _fun(self, x):
        self.accumulator += x
        return self.accumulator

    def _reset(self):
        self.accumulator = self.start

AC=Accumulate

class ArithmeticMean(Function):
    """Function returning the arithmetic mean of its parameter."""
    def __init__(self, param, start=0.0):
        Function.__init__(self, param)
        self.reset()

    def _fun(self, x):
        self.sum += x
        self.count += 1
        return float(self.sum) / self.count

    def _reset(self):
        self.sum = 0.0
        self.count = 0

AMean=ArithmeticMean

class GeometricMean(Function):
    """Function returning the geometric mean of its parameter."""
    def __init__(self, param):
        Function.__init__(self, param)
        self.reset()

    def _fun(self, x):
        self.product *= x
        self.count += 1

        return self.product ** (1.0 / count)

    def _reset(self):
        self.product = 1.0
        self.count = 0

GMean=GeometricMean

class HarmonicMean(Function):
    """Function returning the harmonic mean of its parameter."""
    def __init__(self, param):
        Function.__init__(self, param)
        self.reset()

    def _fun(self, x):
        self.denominator += 1.0 / x
        self.numerator += 1

        return self.numerator / self.denominator

    def _reset(self):
        self.denominator = 0.0
        self.numerator = 0

HMean=HarmonicMean

class SlidingWindowBase(Function):
    """Base class for functions working on a sliding window."""

    def __init__(self, param, length):
        Function.__init__(self, param)
        self.length = length
        self.reset()

    def _fun(self, x):
        self.window = [ x ] + self.window[0:self.length - 1]
        return self._eval_window(self.window)

    @abstractmethod
    def _eval_window(self, window):
        """Evaluate the function for a window of values.

        Argument:
          window -- Tuple of values in the window
        """
        pass

    def _reset(self):
        self.window = []

    def __str__(self):
        return "%s(%s, length=%i)" % (self.name, self.params[0], self.length)

class SlidingSum(SlidingWindowBase):
    """Calculate the a sliding window sum.

    Arguments:
      param  -- Parameter to evaluate.
      length -- Size of the window.
    """
    def __init__(self, param, length):
        SlidingWindowBase.__init__(self, param, length)

    def _eval_window(self, window):
        return sum(window)

class SlidingArithmeticMean(SlidingWindowBase):
    """Calculate the a sliding window arithmetic mean.

    Arguments:
      param  -- Parameter to evaluate.
      length -- Size of the window.
    """
    def __init__(self, param, length):
        SlidingWindowBase.__init__(self, param, length)

    def _eval_window(self, window):
        return float(sum(window)) / len(window)

SlidingAMean=SlidingArithmeticMean

class SlidingGeometricMean(SlidingWindowBase):
    """Calculate the a sliding window geometric mean.

    Arguments:
      param  -- Parameter to evaluate.
      length -- Size of the window.
    """
    def __init__(self, param, length):
        SlidingWindowBase.__init__(self, param, length)

    def _eval_window(self, window):
        return reduce(lambda a,b: a*b, window) ** (1.0 / len(window))

SlidingGMean=SlidingGeometricMean

class SlidingHarmonicMean(SlidingWindowBase):
    """Calculate the a sliding window harmonic mean.

    Arguments:
      param  -- Parameter to evaluate.
      length -- Size of the window.
    """
    def __init__(self, param, length):
        SlidingWindowBase.__init__(self, param, length)

    def _eval_window(self, window):
        return len(window) / sum([ 1.0 / x for x in window ])

SlidingHMean=SlidingHarmonicMean

def eval_fun(expr, extra=None):
    """Evaluate a gem5 stats query and return an expression tree.

    Keyword Arguments:
      extra -- Dictionary of additional functions to include.
    """

    def is_valid(atom):
        return inspect.isclass(atom) and \
            not inspect.isabstract(atom) and \
            issubclass(atom, M5Value)

    expr_context = dict([ (key, value) for (key, value) in globals().items() if 
                        is_valid(value) ])
    if extra:
        for k, v in extra.items():
            expr_context[k] = v

    return eval(expr, expr_context, {})


if __name__ == "__main__":
    expr_a = LogValue("host_seconds") / LogValue("sim_seconds")
    expr_b = LogValue("host_seconds") / "sim_seconds"
    expr_c = expr_b + 2
    expr_d = HarmonicMean(expr_a)

    print expr_a
    print expr_b
    print expr_c
    print expr_d
    print IPC("system.cpu_kvm")
    print eval_fun("LV('host_seconds') + 1.0")
