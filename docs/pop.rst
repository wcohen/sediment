Sediment Function Reordering Principles of Operation
=================

Abstract
========
Despite the each generation of computer having larger amounts of
memory, the cost of Table Lookaside Buffers(TLB) changes and page
faults are still relatively expensive, and may benefit from program
layout optimizations, which will reduce the frequency of such
operations.
This proposal describes an approach to collect profiling
information from running Linux systems with perf, process the data,
and make use of the profiling information in the RPM builds.

Reordering functions can reduce the memory footprint of running
applications and improve start up time by decreasing the number of
pages that must be pulled in to start the program.
SGI's CORD reordering program had a 12% to 30% reduction in
instruction memory usage for the reordered libraries (mentioned in
1995 Usenix paper, [Ho95]_). More recently Mozilla developers have worked
on reducing startup latency with function reordering [Glek10]_ with a
30% reduction in startup time.


Introduction
============

Processor clock speed, main memory capacity, and disk drive capacity
have increased substantially in the past decade, allowing programmers
to run significantly larger programs.
However, processor clock speed has caused processor internal data
transfer rates to outpace the data transfer rates of main memory and
disk drives.
The result is operations dealing with memory management like
Translation Lookaside Buffer (TLB) updates and page faults are now
more costly.

Processors map virtual memory addresses used in programs into physical
addresses using multiple levels of page tables. Doing chained accesses
through the multiple level of page tables is slow.
Thus, every modern processor uses Translation Lookaside Buffers (TLB)
to cache recent page mappings. Typically there are between 32 and 1024
entries in each processor's TLB.
If each page is 4KB in size each processor would is limited to
addressing about 4MB of physical memory without a TLB update. If a TLB
update has be performed, it can cost ten's of processors clock cycles
[Gor10]_.

Linux uses demand paging to pull in pages of a program as needed from
the executable file on disk.
The functions in the executable are not arranged in any particular
order and portions of a page pulled via a major page fault in may
contain code that is very rarely executed.
Even though the machine may have enough RAM to store the entire
application, this slows the startup because more major page faults
occur than if the functions were arrange so that frequently executed
code was grouped together on pages.

Modern processors now have performance monitoring units (PMUs) that
allows measurement of hardware events such as TLB misses and paths
taken through code.

The perf tool in recent kernels provides access to this data and it 
is possible to provide information about which functions
frequently call each other in code.
Current versions of GCC and Binutils in Linux have means of ordering
the functions in an executable.
The missing infrastructure are tools and procedures that
allow that profiling information to be included in source RPM to allow
the RPM build to order the functions in the executables to make more
efficient use of memory and reduce the frequency of major page faults
and TLB misses.


Requirements
============

RPMs are typically the way that code is built and distributed both
inside and outside of Red Hat.
The implementation of the function reordering needs to be compatible
with source RPMs used to build packages.

Where to put the profiling information? Red Hat has a build system to
produce the RPM.
However, developers often build the RPMs on local machines and people
externally build the RPMs from the source RPMs.
It would be better to include the profile information in the source
RPM so the source RPM is self-contained.

In many cases the profiling information will be coming from people
using the binary RPMs and not from people building the RPMs. The
mechanism to package the data must make it easy for a non-developer to
collect the profiling data and submit it for inclusion with the
appropriate RPM. The complexity is that many programs use shared
libraries, causing the profile data to span several RPMs. Because
there will be multiple sources of profiling information the data will
need to be merged together; it is not feasible to have a separate
separate profile file for each submission. There will need to be some
way of weighting the profiles appropriately and merging them.

A single source RPM is used to create binaries for a number of
different architectures. The binaries for various architectures may
have very different functions invoked, for example /usr/bin/ld for
x86-64 and arm have to handle the specifics of each
architecture. Either the reordering must be tolerant of functions that
do not exist for the particular architecture or there needs to be
architecture specific link orders. It would be preferable to avoid
architecture specific profiles to allow uncommon architectures to
benefit from the profiling on commonly used systems, so that less
commonly used architecture such as the s390 benefit from x86-64
profiling.  Approach

The linker can be used to group strongly connected functions together
close to reduce number of pages in the page footprint. Perf will
collect the data on which functions call each other. Additional
scripts will be produced to convert the perf.data file data into files
suitable the RPM builds. There will need to be some modifications of
the source RPMs to support the function reordering.


Data Collection Approach
========================

There are two basic approaches to collecting information to decide on
the layout: static (compiler collected) and dynamic (runtime
collected). Currently, prototype implementations have been done for
both. The static data collection uses a gcc plugin that collects data
while building the package with an rpmbuild and the dynamic data
collection uses the perf infrastructure to collect call graph
information while the program is actually running. The static data
shows possible things that might be called from a particular location
in the, but may not have a enough information to predict the targets
of indirect calls or to estimate the relative frequency of different
calls. The dynamic data can provide insight into what the actual
targets are for calls and the relative frequency of those calls, but
the data may only be applicable to that particular run of the
program. Various invocations of the program may have very different
characteristics. For example a small test run of a program may be
dominated by the time spent in the IO code, but more realistic runs of
the same program would have a computational kernel dominate the total
run time.  Static Data Collection

The compiler already does a great amount of analysis to translate the
developer's source code into executable binaries. GCC now provides
infrastructure to write plugins that access gcc internal data
structures and analysis [GCC10]_. David Malcolm has developed python
plugin that provides support for Python code [Mal12]_. The python
plugin also provides support to access the callgraph information and
output dot file. Some minor modifications of an existing plugin allows
generation of .gv files for each compile unit.

With the python gcc plugin installed on the machine the .rpmmacros can
be setup to run the plugin for each compilation with something like::

  %__global_cflags	-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 %{_hardened_cflags} -ffunction-sections -fplugin=python3 -fplugin-arg-python3-script=/usr/bin/write-dot-callgraph.py``

The plugin generates files with .gv extenstion in the build
directory. The .gv file can be passed through dot::

  dot -Tsvg ceval.c.gv > /tmp/ceval.c.svg

The resulting graph can be examined to see which functions are calling
other functions. The current plug does not weight the edge. Future
versions of the plugin should make use of gcc's information about the
probability of calls and include that information, so that rarely used
functions such as error handlers can be placed on cold page.


Dynamic Data Collection
=======================

Recent Linux kernels provide access to the Intel processors' Last
Branch Record (LBR). This mechanism records samples listing the source
and destination of each call (and other jump operations) executed in
application code. perf can read this data out. Something like the
following command should be able to collect the data on Fedora 17::

  perf record -e branches:u -j any_call executable_under_test

The "perf report" command will generate a report that include the source and
destinations of the calls. As a quick proof of concept, a python
script perf2gv.py is used to convert the output of "perf report" into
a .gv file. The script doesn't on C++ code because of the spaces in
the method's signature argument list of the "perf report" output.

The examples directory in the sediment package contains examples of
the various outputs.
The
:download:`postgres12.out <../examples/postgres12.out>` is the raw output from
"perf report".
The script perf2gv.py converted the raw perf output into
:download:`postgres12.gv <../examples/postgres12.gv>`, a graphviz output.
The
:download:`postgres12.gv <../examples/postgres12.gv>` file can be converted
into a list of function in the desired link order with the gv2link.py
script as shown in
:download:`postgres12.link <../examples/postgres12.link>`
The graphviz output file can also be converted into a viewable callgraph with::

  dot -Tsvg -o postgres12.svg postgres12.gv

The resulting in
:download:`postgres12.svg <../examples/postgres12.svg>` , a graphiv
viewable in a many webbrowsers.
Each elipse in the graph is a function.
The functions are grouped together in a box representing the executable.
The edges show the calls that were sampled during the run.
The values for an edge can range from 0 to 1.
A value of 0.25 on an edge would indicate that a quarter of the
total samples were fore that edge.

Managing the data
=================

Scripts will be needed to package the information in a form that is
suitable for emailing and inclusion in source rpm files::

  gen_profiles output_file rpm_name perf.data

A file will be generated for each executables in the package rpm_name
with perf samples/backtraces. The file format will basically list the
relative freqency of calls between various functions. The files are
only required to list functions that have samples::

  gen_profiles_merge  merged_file_name weight1 file1 weight2 file2 ... ...

The rpm_profile_merge script for combining the multiple files received
into a single merged file. The floating point numerical weights
particular files to be weighted more heavily, e.g. adding a new sample
to an existing sum.


RPM Build Method
================

For the reordering to work, each function needed to be compiled into
separate text segment rather than just lumped into a single text
segment. This is accomplished with "-ffunction-sections" in the CFLAGS
and CXXFLAGS. The actual linking will need to use a link script
generated from the profiling information rather than using the default
script built into the linker. In a makefile LDFLAGS will be modified::

  gcc: -Wl,--script=`gen_link_order $@`
  ld: --script=`gen_link_order $@`

The following command would covert the call graph information into a
link order::

  gen_link_order executable_name gen_profile_file

The script gen_link_order generates a link script and returns the path
to the link script. It searches for executable_name.prof. If no
profile file for the executable is found, a default link script is
produced and a path to that link script is returned. If a
executable_name.prof exists gen_link_order will use the order of
function in the profile to produce the linker script and return the
path of the linker script. Assuming the "-ffunction-sections" option
was used to compile the functions, the linker can order the functions
into the order specified by the linker_script.

This will need to deal with situations like gcc where the source code
is one directory and the build is performed in another. Have
environment variable (PROF_DIR) pointing to default directory holding
profile files. It might be possible that the link order might be
performed in similar manner as the stripping of the debuginfo in an
rpmbuild, after the executable are installed. This may make it easier
map the collected data to the executable because when things are
installed they should have a similar layout to the real installed
files. (note: /usr/lib64 might be an issue that the scripts would have
to deal with).  Advantages of Approach:

* Reduce the frequency of page faults
* Uses existing functions available in Red Hat Distributions.
* Should be robust to changes in code. Worst case new functions not in the profile file are just linked toward the end of the executable and removed functions are quietly ignored.
* Portable between different architectures. Doesn't need detailed knowledge about binary file formats. 

Drawbacks of Approach:

* Modifying source RPM to make use of profiling information required
* The tool will only help traditionally compiled executable such as C/C++/Fortran. It will not help much with scripted code run in interpreters such as Ruby and Python.
* Merging data may be inaccurate either through weighting or architecture differences
* The expansion in the number of sections may affect tools such as gdb that read that information.
* Does not deal with layout between different binaries files (for example firefox calling mutex functions in glibc) 

Exploratory Work
================

The relative benefit of this optimization is going to depend greatly
on the hardware, software, and workloads used. As a quick measure the
postgres monitored with::

  $ perf stat -a -e instructions -e iTLB-misses pgbench -c 64 -T 300
  starting vacuum...end.
  transaction type: TPC-B (sort of)
  scaling factor: 5000
  query mode: simple
  number of clients: 64
  duration: 300 s
  number of transactions actually processed: 1916776
  tps = 6389.039641 (including connections establishing)
  tps = 6391.320862 (excluding connections establishing)

    Performance counter stats for 'pgbench -c 64 -T 300':

   2,493,217,429,858 instructions              #    0.00  insns per cycle         [100.00%]
       5,090,331,478 iTLB-misses
                                               

      300.293885544 seconds time elapsed

The run above indicates that iTLB miss rate is about 2 per 1000
instructions. Assuming 20 cycles per iTLB miss and 1 instruction per
clock cycle that would be about 2% of the time is spent dealing with
iTLB misses. Guest virtual machines have a higher cost for iTLB
updates is higher and guest virtual machines will benefit more from
reductions in iTLB updates.


References
==========

.. [GCC10] plugins, October 1, 2010, http://gcc.gnu.org/wiki/plugins 
.. [Glek10] Tarak Glek, Linux: How to Make Startup Suck Less (Also Reduce Memory Usage!) http://blog.mozilla.org/tglek/2010/04/05/linux-how-to-make-startup-suck-less-and-reduce-memory-usage/ 
.. [Gor10] Mel Gorman, Huge pages part 5: A deeper look at TLBs and costs March 23, 2010 http://lwn.net/Articles/379748/ 
.. [Ho95] W. Wilson Ho, et. al. Optimizing the Performance of Dynamically-Linked Programs http://www.usenix.org/publications/library/proceedings/neworl/ho.html 
.. [Mal12] David Malcolm, GCC Python Plugin https://fedorahosted.org/gcc-python-plugin/ 
