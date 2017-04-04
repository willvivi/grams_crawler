
.. _pure-mode:

Pure Python Mode
================

In some cases, it's desirable to speed up Python code without losing the
ability to run it with the Python interpreter.  While pure Python scripts
can be compiled with Cython, it usually results only in a speed gain of
about 20%-50%.

To go beyond that, Cython provides language constructs to add static typing
and cythonic functionalities to a Python module to make it run much faster
when compiled, while still allowing it to be interpreted.
This is accomplished either via an augmenting :file:`.pxd` file, or
via special functions and decorators available after importing the magic
``cython`` module.

Although it is not typically recommended over writing straight Cython code
in a :file:`.pyx` file, there are legitimate reasons to do this - easier
testing, collaboration with pure Python developers, etc.  In pure mode, you
are more or less restricted to code that can be expressed (or at least
emulated) in Python, plus static type declarations. Anything beyond that
can only be done in .pyx files with extended language syntax, because it
depends on features of the Cython compiler.


Augmenting .pxd
---------------

Using an augmenting :file:`.pxd` allows to let the original :file:`.py` file
completely untouched.  On the other hand, one needs to maintain both the
:file:`.pxd` and the :file:`.py` to keep them in sync.

While declarations in a :file:`.pyx` file must correspond exactly with those
of a :file:`.pxd` file with the same name (and any contradiction results in
a compile time error, see :doc:`pxd_files`), the untyped definitions in a
:file:`.py` file can be overridden and augmented with static types by the more
specific ones present in a :file:`.pxd`.

If a :file:`.pxd` file is found with the same name as the :file:`.py` file
being compiled, it will be searched for :keyword:`cdef` classes and
:keyword:`cdef`/:keyword:`cpdef` functions and methods.  The compiler will
then convert the corresponding classes/functions/methods in the :file:`.py`
file to be of the declared type.  Thus if one has a file :file:`A.py`::

    def myfunction(x, y=2):
        a = x-y
        return a + x * y

    def _helper(a):
        return a + 1

    class A:
        def __init__(self, b=0):
            self.a = 3
            self.b = b

        def foo(self, x):
            print x + _helper(1.0)

and adds :file:`A.pxd`::

    cpdef int myfunction(int x, int y=*)
    cdef double _helper(double a)

    cdef class A:
        cdef public int a,b
        cpdef foo(self, double x)

then Cython will compile the :file:`A.py` as if it had been written as follows::

    cpdef int myfunction(int x, int y=2):
        a = x-y
        return a + x * y

    cdef double _helper(double a):
        return a + 1

    cdef class A:
        cdef public int a,b
        def __init__(self, b=0):
            self.a = 3
            self.b = b

        cpdef foo(self, double x):
            print x + _helper(1.0)

Notice how in order to provide the Python wrappers to the definitions
in the :file:`.pxd`, that is, to be accessible from Python,

* Python visible function signatures must be declared as `cpdef` (with default
  arguments replaced by a `*` to avoid repetition)::

    cpdef int myfunction(int x, int y=*)

* C function signatures of internal functions can be declared as `cdef`::

    cdef double _helper(double a)

* `cdef` classes (extension types) are declared as `cdef class`;

* `cdef` class attributes must be declared as `cdef public` if read/write
  Python access is needed, `cdef readonly` for read-only Python access, or
  plain `cdef` for internal C level attributes;

* `cdef` class methods must be declared as `cpdef` for Python visible
  methods or `cdef` for internal C methods.


In the example above, the type of the local variable `a` in `myfunction()`
is not fixed and will thus be a Python object.  To statically type it, one
can use Cython's ``@cython.locals`` decorator (see :ref:`magic_attributes`,
and :ref:`magic_attributes_pxd`).

Normal Python (:keyword:`def`) functions cannot be declared in :file:`.pxd`
files.  It is therefore currently impossible to override the types of plain
Python functions in :file:`.pxd` files, e.g. to override types of their local
variables.  In most cases, declaring them as `cpdef` will work as expected.


.. _magic_attributes:

Magic Attributes
----------------

Special decorators are available from the magic ``cython`` module that can
be used to add static typing within the Python file, while being ignored
by the interpreter.

This option adds the ``cython`` module dependency to the original code, but
does not require to maintain a supplementary :file:`.pxd` file.  Cython
provides a fake version of this module as `Cython.Shadow`, which is available
as `cython.py` when Cython is installed, but can be copied to be used by other
modules when Cython is not installed.


"Compiled" switch
^^^^^^^^^^^^^^^^^

* ``compiled`` is a special variable which is set to ``True`` when the compiler
  runs, and ``False`` in the interpreter. Thus, the code

  ::

    if cython.compiled:
        print("Yep, I'm compiled.")
    else:
        print("Just a lowly interpreted script.")

  will behave differently depending on whether or not the code is executed as a
  compiled extension (:file:`.so`/:file:`.pyd`) module or a plain :file:`.py`
  file.


Static typing
^^^^^^^^^^^^^

* ``cython.declare`` declares a typed variable in the current scope, which can be
  used in place of the :samp:`cdef type var [= value]` construct. This has two forms,
  the first as an assignment (useful as it creates a declaration in interpreted
  mode as well)::

    x = cython.declare(cython.int)              # cdef int x
    y = cython.declare(cython.double, 0.57721)  # cdef double y = 0.57721

  and the second mode as a simple function call::

    cython.declare(x=cython.int, y=cython.double)  # cdef int x; cdef double y

  It can also be used to type class constructors::

    class A:
        cython.declare(a=cython.int, b=cython.int)
        def __init__(self, b=0):
            self.a = 3
            self.b = b

  And even to define extension type private, readonly and public attributes::

    @cython.cclass
    class A:
        cython.declare(a=cython.int, b=cython.int)
        c = cython.declare(cython.int, visibility='public')
        d = cython.declare(cython.int, 5)  # private by default.
        e = cython.declare(cython.int, 5, visibility='readonly')

* ``@cython.locals`` is a decorator that is used to specify the types of local
  variables in the function body (including the arguments)::

    @cython.locals(a=cython.double, b=cython.double, n=cython.p_double)
    def foo(a, b, x, y):
        n = a*b
        ...

* ``@cython.returns(<type>)`` specifies the function's return type.

* Starting with Cython 0.21, Python signature annotations can be used to
  declare argument types.  Cython recognises three ways to do this, as
  shown in the following example.  Note that it currently needs to be
  enabled explicitly with the directive ``annotation_typing=True``.
  This might change in a later version.

  ::

    # cython: annotation_typing=True

    def func(plain_python_type: dict,
             named_python_type: 'dict',
             explicit_python_type: {'type': dict},
             explicit_c_type: {'ctype': 'int'}):
        ...


C types
^^^^^^^

There are numerous types built into the Cython module.  It provides all the
standard C types, namely ``char``, ``short``, ``int``, ``long``, ``longlong``
as well as their unsigned versions ``uchar``, ``ushort``, ``uint``, ``ulong``,
``ulonglong``.  The special ``bint`` type is used for C boolean values and
``Py_ssize_t`` for (signed) sizes of Python containers.

For each type, there are pointer types ``p_int``, ``pp_int``, etc., up to
three levels deep in interpreted mode, and infinitely deep in compiled mode.
Further pointer types can be constructed with ``cython.pointer(cython.int)``,
and arrays as ``cython.int[10]``. A limited attempt is made to emulate these
more complex types, but only so much can be done from the Python language.

The Python types int, long and bool are interpreted as C ``int``, ``long``
and ``bint`` respectively. Also, the Python builtin types ``list``, ``dict``,
``tuple``, etc. may be used, as well as any user defined types.

Typed C-tuples can be declared as a tuple of C types.


Extension types and cdef functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* The class decorator ``@cython.cclass`` creates a ``cdef class``.

* The function/method decorator ``@cython.cfunc`` creates a :keyword:`cdef` function.

* ``@cython.ccall`` creates a :keyword:`cpdef` function, i.e. one that Cython code
  can call at the C level.

* ``@cython.locals`` declares local variables (see above). It can also be used to
  declare types for arguments, i.e. the local variables that are used in the
  signature.

* ``@cython.inline`` is the equivalent of the C ``inline`` modifier.

Here is an example of a :keyword:`cdef` function::

    @cython.cfunc
    @cython.returns(cython.bint)
    @cython.locals(a=cython.int, b=cython.int)
    def c_compare(a,b):
        return a == b


Further Cython functions and declarations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``address`` is used in place of the ``&`` operator::

    cython.declare(x=cython.int, x_ptr=cython.p_int)
    x_ptr = cython.address(x)

* ``sizeof`` emulates the `sizeof` operator.  It can take both types and
  expressions.

  ::

    cython.declare(n=cython.longlong)
    print cython.sizeof(cython.longlong)
    print cython.sizeof(n)

* ``struct`` can be used to create struct types.::

    MyStruct = cython.struct(x=cython.int, y=cython.int, data=cython.double)
    a = cython.declare(MyStruct)

  is equivalent to the code::

    cdef struct MyStruct:
        int x
        int y
        double data

    cdef MyStruct a

* ``union`` creates union types with exactly the same syntax as ``struct``.

* ``typedef`` defines a type under a given name::

    T = cython.typedef(cython.p_int)   # ctypedef int* T

* ``cast`` will (unsafely) reinterpret an expression type. ``cython.cast(T, t)``
  is equivalent to ``<T>t``. The first attribute must be a type, the second is
  the expression to cast. Specifying the optional keyword argument
  ``typecheck=True`` has the semantics of ``<T?>t``.

  ::

    t1 = cython.cast(T, t)
    t2 = cython.cast(T, t, typecheck=True)

.. _magic_attributes_pxd:

Magic Attributes within the .pxd
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The special `cython` module can also be imported and used within the augmenting
:file:`.pxd` file. For example, the following Python file :file:`dostuff.py`::

    def dostuff(n):
        t = 0
        for i in range(n):
            t += i
        return t

can be augmented with the following :file:`.pxd` file :file:`dostuff.pxd`::

    import cython

    @cython.locals(t = cython.int, i = cython.int)
    cpdef int dostuff(int n)

The :func:`cython.declare()` function can be used to specify types for global
variables in the augmenting :file:`.pxd` file.


Tips and Tricks
---------------

Calling C functions
^^^^^^^^^^^^^^^^^^^

Normally, it isn't possible to call C functions in pure Python mode as there
is no general way to support it in normal (uncompiled) Python.  However, in
cases where an equivalent Python function exists, this can be achieved by
combining C function coercion with a conditional import as follows::

    # in mymodule.pxd:

    # declare a C function as "cpdef" to export it to the module
    cdef extern from "math.h":
        cpdef double sin(double x)


    # in mymodule.py:

    import cython

    # override with Python import if not in compiled code
    if not cython.compiled:
        from math import sin

    # calls sin() from math.h when compiled with Cython and math.sin() in Python
    print(sin(0))

Note that the "sin" function will show up in the module namespace of "mymodule"
here (i.e. there will be a ``mymodule.sin()`` function).  You can mark it as an
internal name according to Python conventions by renaming it to "_sin" in the
``.pxd`` file as follows::

    cdef extern from "math.h":
        cpdef double _sin "sin" (double x)

You would then also change the Python import to ``from math import sin as _sin``
to make the names match again.


Using C arrays for fixed size lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since Cython 0.22, C arrays can automatically coerce to Python lists or tuples.
This can be exploited to replace fixed size Python lists in Python code by C
arrays when compiled.  An example::

    import cython

    @cython.locals(counts=cython.int[10], digit=cython.int)
    def count_digits(digits):
        """
        >>> digits = '01112222333334445667788899'
        >>> count_digits(map(int, digits))
        [1, 3, 4, 5, 3, 1, 2, 2, 3, 2]
        """
        counts = [0] * 10
        for digit in digits:
            assert 0 <= digit <= 9
            counts[digit] += 1
        return counts

In normal Python, this will use a Python list to collect the counts, whereas
Cython will generate C code that uses a C array of C ints.
