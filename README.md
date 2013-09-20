gem5 utilities
===============


Query Language
--------------
The query language used in this package is based on Python. Queries
are evaluated as Python expressions in a special environment
containing a set of classes that create an expression tree that
analyzes a gem5 stats file.

The objects are then called with a stats dump as its parameter to
evaluate the expression on that dump. Entries in the expression tree
are allowed to contain internal state and can be reset by calling the
reset method on the root node of the tree.

For example:

    tree = eval_fun("Accumulate(IPC('system.cpu'))")

Will return a tree with an instance of the Accumulate object as its
root node. The accumulate object contains a reference to an instance
of the IPC object. When evaluating the tree 

The tree can then be evaluated on a log dump as follows:

    for dump in log.stream_log("stats.txt"):
      print tree(dump)

The analysis language automatically supports the common arithmetic
operators through overloading. See logquery.py for a complete list of
supported functions.

query.py
--------

Tool to evaluate one or more queries on a stat file and return the
results as a CSV file. One CSV entry is emitted per dump.

plot_ts.py
----------

Tool to evaluate one or more queries on a stat file and plot the
results using matplotlib.

