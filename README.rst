Python Decompiler
=================

This project aims to create a comprehensive decompiler for Python bytecode.
At the moment it is relatively incomplete, with many things not supported,
including, but certainly not limited to:

 * Unpacking
 * try/except/finally
 * else clauses on try/for loops
 * any sort of arithmatic
 * keyword argument and *args, **kwargs to functions

I'm taking patches, but I suspect at least some of those will require
refactorings and I've grown a tad too bored to do it myself.