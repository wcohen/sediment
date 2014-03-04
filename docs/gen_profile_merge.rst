Usage::

   gen_profile_merge [options]

`gen_profile_merge` takes one or more call graph (.gv) files, weights
each of them, and merges the call graph files into a single file.

**-h**, **--help**
   Provide the short usage message listing the supported options.

**-w**, **--weight=**\ *<float>*
   Change the weight to *<float>* for all the input files following
   this option until another weight option is encountered.  By default
   the weight value is 1.0.

**-f**, **--file=**\ *<input_file>*
   Specify a file to merge with outher.  Each files requires a **-f** option.

**-o**, **--output=**\ *<output_file>*
   Specify the file to write the output to.  An ouptut file must be secified.

**-d**, **--debug**
   Write additional information information to stderr for debugging.
   This option is for developers and maintainers of the Sediment
   package and is not for normal users.

Example::

   gen_profile_merge -o merged.gv -w 0.75 -f major_exp.gv -w 0.25 -f minor_exp.gv
