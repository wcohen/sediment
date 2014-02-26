Usage::

   perf2gv.py < PERF_OUTPUT > CALL_GRAPH.gv

`perf2gv.py` is a simple script that generates a call graph from the
perf data collected on Intel machines using the Last Branch Register
(LBR) hardware:

  perf record -e branches:u -j any_call executable_under_test

Example::

  perf record -e branches:u -j any_call example_prog
  perf report --no-demangle | perf2gv.py > example_prog.gv
