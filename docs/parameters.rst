======================
Parameters combination
======================

Then submission of parametric jobs requires to gather in a *parameter*
file all the combinations of parameters that one wants to run a job
against. This list of combination can be described as an explicit
array of values of programatically via a Python or shell script or
using simple directives.

While the execution of parametric workflows is described 
here_, here are detailed four ways of defining parameters. .


.. _here: http:workflows.html#parametric-job-workflow

array of values
---------------

The simplest way to describe the set of parameter combinations that
needs to be tested consists in listing them extensively as an array
of values. The first row of this array is the name of each
parameters and each row is one possible combination.

Here is a parameters file listing all possible combinations for 3
parameters (i,j,k), each of them taking the value 1 or 2.

::

       # array-like description of parameter combinations
       
       i  j  k

       1  1  1
       1  1  2
       1  2  1
       1  2  2
       2  1  1
       2  1  2
       2  2  1
       2  2  2

Notice that:

- spaces, void lines are ignored.
- every thing following a *#* is considered as a comment and ignored


Combined parameter sweep
------------------------

In case of combinations that sweeps all possible set of values based on
the domain definition of each variable, a more compact declarative syntax
is also available. The same set of parameters can be generated with the
following file:

::

       # combine-like description of parameter combinations

       #DECIM COMBINE i = [1,2]
       #DECIM COMBINE j = [1,2]
       #DECIM COMBINE k = [1,2]

Every line starting with *#DECIM* is parsed as a special command.


Parameters depending on simple formulas
---------------------------------------

Some parameters can also be computed from others using simple arithmetic formulas.
Here is a way to declare them:

::

       # combine-like description of parameter combinations

       #DECIM COMBINE i = [1,2]
       #DECIM COMBINE j = [1,2]
       #DECIM COMBINE k = [1,2]

       #DECIM p = i*j*k

which is a short way to describe the same 8 combinations as expressed in the following
array-like parameter file:

::
   
       # array-like description of parameter combinations
       
       i  j  k  p

       1  1  1  1
       1  1  2	2
       1  2  1	2
       1  2  2	4
       2  1  1	2
       2  1  2	4
       2  2  1	4
       2  2  2	8


an additional parameter can also be described by a list of values:

::

       # combine-like description of parameter combinations

       #DECIM COMBINE i = [1,2]
       #DECIM COMBINE j = [1,2]
       #DECIM COMBINE k = [1,2]

       #DECIM p = i*j*k

       #DECIM t = [1,2,4,8,16,32,64,128,256]
       
which is a short way to describe the same 8 combinations as expressed in the following
array-like parameter file:

::
   
       # array-like description of parameter combinations
       
       i  j  k  p    t

       1  1  1  1    1
       1  1  2	2    2
       1  2  1	2    4
       1  2  2	4    8
       2  1  1	2   16
       2  1  2	4   32
       2  2  1	4   64
       2  2  2	8  128



For each parameter added via a list of values, the conformance with the existing
number of already possible combinations is checked. For example, the following
parameter file...
       
::

       # combine-like description of parameter combinations

       #DECIM COMBINE i = [1,2]
       #DECIM COMBINE j = [1,2]
       #DECIM COMBINE k = [1,2]

       #DECIM p = i*j*k

       #DECIM t = [1,2,4,8,16,32,64,128,256]

...produces the error:

::

   [ERROR] parameters number mistmatch for expression
   [ERROR] 	 t = [1,2,4,8,16,32,64,128,256] 
   [ERROR] 	 --> expected 8 and got 9 parameters...

   


More complex Python expressions
-------------------------------

For a high number of parameters, a portion of code written in Python can also be embedded
after a *#DECIM PYTHON* directive till the end of the file.

::

   # pythonic parameter example file

   #DECIM COMBINE nodes = [2,4,8]
   #DECIM COMBINE ntasks_per_node = [16,32]
   
   #DECIM k = range(1,7)
   
   #DECIM PYTHON

   import math

   ntasks = nodes*ntasks_per_node
   nthreads = ntasks * 2
   
   NPROC = 2; #Number of processors
   
   t = int(2**(k))
   T = 15



which is a short way to describe the same 8 combinations as expressed in the following
array-like parameter file:

::
   
       # array-like description of parameter combinations
       
       nodes  ntasks_per_node  k  ntasks  nthreads   t  NPROC    T
          2               32  1      64       128   2      2	15 
          2               64  2     128       256   4      2	15 
          4               32  3     128       256   8      2	15 
          4               64  4     256       512  16      2	15 
          8               32  5     256       512  32      2	15 
          8               64  6     512      1024  64      2	15 

A python section is always evaluated at the end. Each new variables
set at the end of the evaluation is added as a new parameter computed
against each of the already built combinations. The conformance to the
number of combinations already set is also checked if the variable is
a set of values. 
