Sediment Function Reordering Principles of Operation
====================================================

Abstract
========
Despite each generation of computer having larger amounts of
physical Random Access Memory (RAM) then the previous generation,
there is a limited amount of RAM that can be
addressed without changing enties in the Table Lookaside Buffers(TLB).
Updates to the TLB entries can be relatively expensive.
Program layout optimizations may reduce the frequency of such
operations.

Reordering functions in an executable can reduce the memory footprint of running
applications and improve start up time by decreasing the number of
pages that must be pulled in to start the program.
SGI's CORD reordering program had a 12% to 30% reduction in
instruction memory usage for the reordered libraries (mentioned in
1995 Usenix paper, [Ho95]_). More recently Mozilla developers have worked
on reducing startup latency with function reordering [Glek10]_ with a
30% reduction in startup time.

The Sediment code ordering tool is  designed to use profiling
information from a variety of sources on Linux systems including
perf, valgrind, and gprof.
Sediment processes the profiling data to produces an ordered list of
the functions to put functions frequently calling each other close to together
in the executable.
Sediment is designed to address issues of building packages using RPM
and allows data to collected on other machines, packaged in the source
RPM, and the source RPM built on other machines or architectures.
Preliminary experiments with Sediment function reordering and
postgresql pgbench program show
improvements between 4.8% to 7.1% for the instructions per clock (IPC). 



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
Thus, every modern processor uses Translation Lookaside Buffers (TLBs)
to cache recent virtual to physical page mappings.
Typically there are between 32 and 1024
entries in each processor's TLB.
If each page is 4KB in size each processor would is limited to
addressing about 4MB of physical memory without a TLB update.
If a TLB update has be performed, it can cost dozens of processors clock cycles
[Gor10]_.

Linux uses demand paging to pull in pages of a program as needed from
the executable file on disk.
The functions in the executable are not arranged in any particular
order and portions of a page pulled in via a major page fault may
contain code that is very rarely executed.
Even though the machine may have enough RAM to store the entire
application, having the executed functions scatter
across many pages slows the startup because more major page faults
occur than if the functions were arrange so that frequently executed
code was grouped together on pages.

Modern processors now have Performance Monitoring Units (PMUs) that
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

The implementation of the function reordering needs to be compatible
with packaging tools such as RPM/dpkg for example.

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
separate profile file for every submission. There will need to be some
way of weighting the profiles appropriately and merging them.

A single source RPM is used to create binaries for a number of
different architectures. The binaries for various architectures may
have very different functions invoked, for example /usr/bin/ld for
x86-64 and arm have to handle the specifics of each
architecture. Either the reordering must be tolerant of functions that
do not exist for the particular architecture or there needs to be
architecture specific link orders. It would be preferable to avoid
architecture specific profiles to allow uncommon architectures to
benefit from the profiling on commonly used systems, so 
architecture such as the s390 benefit from x86-64
profiling data.

Approach
========

The linker can be used to group strongly connected functions close together
to reduce number of pages in the page footprint. Perf will
collect the data to build a callgraph. Additional
scripts will be produced to convert the perf.data file data into files
suitable the RPM builds. There will need to be some modifications of
the source RPMs to support the function reordering.


Data Collection Approach
========================

There are two basic approaches to collecting information to decide on
the layout: static (compiler collected) and dynamic (runtime
collected). Currently, prototype implementations have been done for
both. The static data collection uses a gcc plugin that collects data
while building the package with rpmbuild and the dynamic data
collection uses the perf infrastructure to collect call graph
information while the program is actually running. The static data
shows functions that might be called from a particular location
in the code, but may not have enough information to predict the targets
of indirect calls or to estimate the relative frequency of different
calls. The dynamic data can provide insight into the actual
targets for calls and the relative frequency of those calls, but
the data may only be applicable to that particular run of the
program. Various invocations of the program may have very different
characteristics. For example a small test run of a program may be
dominated by the time spent in the IO and startup code,
but more realistic runs of
the same program would have a computational kernel dominate the total
run time.

Static Data Collection
======================

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

  %__global_cflags	-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 %{_hardened_cflags} -ffunction-sections -fplugin=python3 -fplugin-arg-python3-script=/usr/libexec/sediment/write-dot-callgraph.py``

The plugin generates files with .gv extenstion in the build
directory. The .gv file can be passed through dot::

  dot -Tsvg ceval.c.gv > /tmp/ceval.c.svg

The resulting graph can be examined to see which functions are calling
other functions. The current plug does not weight the edgse. Future
versions of the plugin should make use of GCC's information about the
probability of calls and include that information, so that rarely used
functions such as error handlers can be placed on cold page.


Dynamic Data Collection
=======================

Recent Linux kernels provide access to the Intel processors' Last
Branch Record (LBR). This mechanism records samples listing the source
and destination of each call (and other jump operations) executed in
application code. perf can read this data out. Something like the
following command can collect the data on Fedora 41::

  perf record -e branches:u -j any_call executable_under_test

The "perf report" command will generate a report that include the
source and destinations of the calls. As a proof of concept, the
Python script perf2gv is used to convert the output of "perf report"
into a .gv file. The script does not handle demangled C++ code output
and one should use the perf "--no-demangle" option..

The examples directory in the sediment package contains examples of
the various outputs.
The
:download:`postgresql16.out <examples/postgresql16.out>` is the raw output from
"perf report --no-demangle --sort=comm,dso_from,symbol_from,dso_to,symbol_to".
The script perf2gv converted the raw perf output into
:download:`postgresql16.gv <examples/postgresql16.gv>`, a graphviz file.
The
:download:`postgresql16.gv <examples/postgresql16.gv>` file can be converted
into a list of function in the desired link order with the gv2link
script as shown in
:download:`postgresql16.link <examples/postgresql16.link>`
The graphviz output file can also be converted into a viewable callgraph with::

  dot -Tsvg -o postgresql16.svg postgresql16.gv

The result is
:download:`postgresql16.svg <examples/postgresql16.svg>` ,
a scalable vector graphics file viewable in a many webbrowsers.
Each elipse in the graph is a function.
The functions are grouped together in a box representing the executable.
The edges show the calls that were sampled during the run.
The values for an edge is a floating point number ranging from 0 to 1.
A value of 0.25 on an edge would indicate that a quarter of the
total samples were for that edge.

Managing the data
=================

Scripts are needed to package the information in a form that is
suitable for emailing and inclusion in source rpm files::

  gen_profiles output_file rpm_name perf.data

A file will be generated for each executables in the package rpm_name
with perf samples/backtraces. The file format will basically list the
relative freqency of calls between various functions. The files are
only required to list functions that have samples::

  gen_profile_merge  -o merged_file_name -w weight1 -f file1 -w weight2 -f file2 ... ...

The gen_profile_merge script combines the multiple files received
into a single merged file. The floating point numerical weights allow
particular files to be weighted more heavily, e.g. adding a new sample
to an existing sum.


RPM Build Methods
=================

For the reordering to performed on Linux,
each function needed to be compiled into
separate text segment rather than just lumped into a single text
segment.
This is accomplished with "-ffunction-sections" in the CFLAGS
and CXXFLAGS.
The actual linking will need specify the order of the functions
in the exectuable based on the profiling information 
rather than using the default.
Newer versions of binutils (2.43) include a ld linker with an option
to specify the order of functions in the executable, "--section-ordering-file".
The special flags can be included directly in the SRPM's spec file using specific macros.
Alternatively, a .rpmmacros file can be created to supply the needed options to the compilers and liners.


Providing Compiler and Linker Options in a RPM spec file
--------------------------------------------------------

It is possible to modify a SRPM spec file using the RPM _distro_extra_*
macros to provide the needed compiler and linker options.
A example of the changes to python3.13-3.13.0-1.fc41 spec file are contained
in :download:`python_layout.patch <examples/python_layout.patch>`.
The first line of the changes allow the build to default to enabling the code layout optimization by default::

  %bcond opt 1

If one wants to disable the code layout optimization, one would build the rpm with::

  rpmbuild --without opt python3.13.spec

The Release has the layout suffix to allow easier switching between the code laytout optimized and non-optimized builds::

  Release: 1%{?dist}%{?with_opt:_opt}

The following conditional sets the addition compiler and linker flags needed for the code layout optimization.
It also adds the dependency on sediment as it is needed to produce information about appropriate
order to link the code::

  %if %{with opt}
  # Settings to enable building with code layout optimization
  BuildRequires: sediment
  %global _distro_extra_cflags -ffunction-sections -fdata-sections
  %global _distro_extra_cxxflags -ffunction-sections -fdata-sections
  %global _distro_extra_fflags -ffunction-sections -fdata-sections
  
  %global __global_link_order %{_builddir}/%{name}-%{version}-%{release}.order
  %global _distro_extra_ldflags -Wl,\"--section-ordering-file,%{__global_link_order}\"
  %endif

The RPM spec file needs to include the callgraph file which is stored as just another source file.
The call_graph define points to the file to allow sediment to produce the link order file.::

  # Call graph information
  SOURCE12: perf_pybenchmark.gv
  %global call_graph %{SOURCE12}

Finally, in the %prep section of the spec file there is the following coditional to
generate the link order file.
This needs be be done before the configuration is done as the linking
expects the __global_link_order file to exist.
If the file does not exist, the various steps of configuration will fail.::

  %if %{with opt}
  #Generate the code layout file before configuration done
  gv2link < %{call_graph} > %{__global_link_order}
  %endif


Using .rpmmacros File to Supply Need Options
--------------------------------------------

There is a "make_sediment_rpmmacros" command in sediment to produce appropriate macros that to store in the local .rpmmacros file.
The RPM macros will be modified using a .rpmmacro file with::

  %build_cflags -O2 -flto=auto -ffat-lto-objects -fexceptions -g -grecord-gcc-switches -pipe -Wall -Werror=format-security -Wp,-U_FORTIFY_SOURCE,-D_FORTIFY_SOURCE=3 -Wp,-D_GLIBCXX_ASSERTIONS -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 -fstack-protector-strong -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1  -m64 -march=x86-64 -mtune=generic -fasynchronous-unwind-tables -fstack-clash-protection -fcf-protection -mtls-dialect=gnu2 -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer %{?call_graph:%{?pgo:-ffunction-sections -fdata-sections}}
  %build_cxxflags -O2 -flto=auto -ffat-lto-objects -fexceptions -g -grecord-gcc-switches -pipe -Wall -Werror=format-security -Wp,-U_FORTIFY_SOURCE,-D_FORTIFY_SOURCE=3 -Wp,-D_GLIBCXX_ASSERTIONS -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 -fstack-protector-strong -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1  -m64 -march=x86-64 -mtune=generic -fasynchronous-unwind-tables -fstack-clash-protection -fcf-protection -mtls-dialect=gnu2 -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer %{?call_graph:%{?pgo:-ffunction-sections -fdata-sections}}
  %build_fflags -O2 -flto=auto -ffat-lto-objects -fexceptions -g -grecord-gcc-switches -pipe -Wall -Wp,-U_FORTIFY_SOURCE,-D_FORTIFY_SOURCE=3 -Wp,-D_GLIBCXX_ASSERTIONS -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 -fstack-protector-strong -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1  -m64 -march=x86-64 -mtune=generic -fasynchronous-unwind-tables -fstack-clash-protection -fcf-protection -mtls-dialect=gnu2 -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer -I/usr/lib64/gfortran/modules  %{?call_graph:%{?pgo:-ffunction-sections -fdata-sections}}
  %__global_link_order \"%{u2p:%{_builddir}}/%{name}-%{version}-%{release}.order\"
  %build_ldflags	-Wl,-z,relro %{_hardened_ldflags} %{?call_graph:%{?pgo:-Wl,"--section-ordering-file,%{__global_link_order}"}}

The .rpmmacro file includes a definition for %dist to note whether the
rpm is a normal rpm or a Program Guided Optimization (PGO) rpm to make it easier
to have both a PGO and non-PGO version of the RPMs for performance evaluation::

  %dist .fc42%{?pgo:_pgo}

Currently, the source RPMs files include a call graph file used to compute
the link order and a define for pgo_file::

  SOURCE18: postgresql.gv
  %global call_graph %{SOURCE18}

The .rpmmacro file adds the following line to the %__build_pre macro
to generate the link order when a call graph is available and pgo
(Profile Guided Optimization) is set::

  %{?call_graph:%{?pgo: gv2link < %{call_graph} > %{__global_link_order}  } }

An example for x86_64 the macros above are contained in :download:`.rpmmacros
<.rpmmacros>`.  However, it is probably better to generate the appropriate RPM macros
with the "make_sediment_rpmmacros" output as these are going to vary by architecture
and Linux distribution.
The building with the function reordering is enabled with::

  rpmbuild -ba --define "pgo 1" <spec_file>

In the future would prefer to have more finer grain control rather
than one call graph and link order for all the executables in the rpm.
Maybe have something link the following to take the callgraph (.gv)
file in the source RPM and then have the RPM macros use the following
command would covert the call graph information into a link order for
a specific executable::

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

This will need to deal with situations where the source code
is one directory and the build is performed in another. Having an
environment variable (PROF_DIR) pointing to default directory holding
profile files. It might be possible that the link order might be
performed in similar manner as the stripping of the debuginfo in an
rpmbuild, after the executable are installed. This may make it easier
map the collected data to the executable because when things are
installed they should have a similar layout to the real installed
files. (note: /usr/lib64 might be an issue that the scripts would have
to deal with).

Advantages of Function Reordering Approach:

* Reduce the frequency of page faults
* Uses existing functions available in Red Hat Distributions.
* Should be robust to changes in code. Worst case new functions not in the profile file are just linked toward the end of the executable and removed functions are quietly ignored.
* Portable between different architectures. Doesn't need detailed knowledge about binary file formats. 

Drawbacks of Function Reordering Approach:

* Modifying source RPM to make use of profiling information required
* The tool will only help traditionally compiled executable such as C/C++/Fortran. It will not help with scripted languages using interpreters such as Ruby and Python.
* Merging data may be inaccurate either through weighting or architecture differences
* The expansion in the number of sections may affect tools such as gdb that read that information.
* Does not deal with layout between different binaries files (for example firefox calling mutex functions in glibc) 

Exploratory Work
================

The benefits of this optimization depends greatly on the hardware,
software, and workloads used. The postgresql database excercised with
pgbench was used as a testcase to gauge the performance improvements
on several Fedora 41 environments.  The postgresql package was
selected as the /usr/bin/postgres executable is 9.4MB stripped on
x86_64 Fedora 41 and would potentially benefit from reordering code to
group commonly used functions on the same or adjacent pages of memory.
Overall, between 3.3% and 6.1% improvement in IPC was observed. The
number of instructions between iTLB miss increased between 11.2% to
47.4%.

An initial training run of pgbench was run on the x86_64 machine to
obtain information about relative frequency of call graph paths in the
code, the sediment tool was used to convert the perf data into a call
graph.  The call graph file was added to the stock
postgresql-16.3-3.fc41.x86_64 SRPM and RPMs were built with and
without enabling the code layout optimization.  Six runs were made
with each version of the RPMs installed and the results were were
averaged.  The following script was used to collect data on postgres
binary when pgbench was running::

  #!/bin/sh
  #
  # make sure the postgres running
  systemctl restart  postgresql.service
  pgb="pgbench"
  su postgres -c "$pgb -c 64 -T 300" &
  sleep 1
  perf stat -e cycles -e instructions -e iTLB-load-misses -e LLC-load-misses -e minor-faults -e major-faults -e cpu-clock -e task-clock --pid=`pidof /usr/bin/postgres|tr " " ","` pidwait "$pgb"

Three Fedora 41 environments were used for the experiments: x86_64
bare metal, x86_64 guest VM, and an aarch64 cortex a57 machine.  The
postgres rpms were built locally with and without function reordering.
The table below summarize the hardware characteristics.


=======================	=============	===========	======================
hardware		 physical	virtual		
characteristics		 x86_64		x86_64		aarch64
=======================	=============	===========	======================
Machine			Lenovo P51	Lenovo P51	NVidia Jeton Nano
processor manufacter	Intel		Intel		Nvidia
processor family	6		6		ARM Cortex
processor model		158		158		A57
clock			3.00GHz		3.00GHz		1.91GHz
processor cores		4		2		4
virtual processors	8		2		4
ram			32GB		4GB		4GB
=======================	=============	===========	======================

Below are table for the bare metal x86_64 machine and guest VM on the same
machine.  The transactions per second (tps) do not change
significantly.  There appear to be other limitations on the machine
besides the processor that limit the performance.  It is notable that
the number of cycles consumed by the postgres binary, the cpu-clock,
and the task clock for the same wallclock time (5 minutes, 300
seconds) were are all reduced.  The IPC (Instructions Per Cycle) and
the average instructions between iTLB misses also improved.

=======================	============    =========== 	=======
x86_64 physical machine postgresql	postgresql
metric          	baseline	reordered	%change
=======================	============    =========== 	=======
tps (excluding conn)	318.5		319.9		0.43%
cycles			3.339E+011	3.236E+011	-3.1%
instructions		1.555E+011	1.567E+011	0.77%
IPC			.466		.484		4.0%
Itlb-load-misses	3.600E+008	2.461E+008	-31.6%
i per iTLB-miss		432		637		47.4%
Cpu-clock		127,926ms	124,895ms	-2.37%
Task-clock		130,625ms	127,596ms	-2.32%
=======================	============    =========== 	=======

=======================	============    =========== 	=======
x86_64 qemu guest	postgresql	postgresql
metric          	baseline	reordered	%change
=======================	============    =========== 	=======
tps (excluding conn)	230.1		231.5		0.6%
cycles			3.0751E+011	2.9502E+011	-4.1%
instructions		1.7732E+011	1.7604E+011	-0.7%
IPC			.577		.597		3.3%
Itlb-load-misses	4.736E+008	3.805E+008	-19.7%
i per iTLB-miss		374		462		23.5%
Cpu-clock		165,610ms	160,785ms	-2.9%
Task-clock		167,212ms	162,393ms	-2.9%
=======================	============    =========== 	=======



To test the portability of the technique the same postgresql source
RPM was build on aarch64.  the following table summarizes the results.
The iTLB-load-misses on the aarch64 only measure the misses in the 48
element first level instruction TLB.  Like the x86_64 platform the
aarch64 machine shows reductions in the number of cycles used and
improvement in the IPC of 6.1%. The average number of instructions
between iTLB misses also improves, probably due to the relatively
small size of the L1 iTLB size.
			
			
====================	===========	===========	========
armv8 cortext a57
metric			baseline	reordered	%change
====================	===========	===========	========
tps (excluding conn)	53.1		51.3		-3.3%
cycles			1.484E+011	1.356E+011	-8.6%
instructions		3.509E+10	3.396E+010	-3.2%
IPC			.236		.250		6.1%
Itlb-load-misses	1.495E+008	1.292E+008	-13.6%
i per iTLB-miss		235		263		11.2%
Cpu-clock		205,022ms	202,764ms	-1.1%
Task-clock		208,491ms	206,936ms	-0.7%
====================	===========	===========	========

Older Experiments on Fedora 18
==============================

Used three Fedora 18 environments: x86_64 raw, x86_64 guest vm, and
armv7 hard float on armv7 cortex a15 machine.  The postgres rpms were
built locally with and without function reordering.
The table below summarize the hardware characteristics.

=======================	=============	===========	======================
hardware		 physical	virtual		
characteristics		 x86_64		x86_64		armv7
=======================	=============	===========	======================
Machine			Lenovo W530	Lenovo W530	Samsung Arm Chromebook
processor manufacter	Intel		Intel		Samsung
processor family	6		6		exynos
processor model		58		58		5250
clock			2.3GHz		2.3GHz		1.7GHz
processor cores		4		2		2
virtual processors	8		2		2
ram			16GB		2GB		2GB
=======================	=============	===========	======================

The first experiments were on the physical x86_64 machine and the
table below summarizes the averages of six runs.  The Transactions Per
Second (tps) do not change much, about 1% improvement.  Performance
appears to be limited the the disk device on the machine.
Because instruction TLB misses drop significantly (19.8% drop) the instruction
per clock IPC improves significantly, 4.8% and the number of cycles consumed
during the run drops by 3.13%.

			
=======================	============    =========== 	=======
x86_64 physical machine postgresql	postgresql
metric          	baseline	reordered	%change
=======================	============    =========== 	=======
tps (including conn)	1,366.59	1,378.95	0.90%
tps (excluding conn)	1,365.51	1,380.06	1.07%
cycles			1.20E+012	1.16E+012	-3.13%
instructions		7.06E+011	7.17E+011	1.56%
IPC			.59		.62		4.84%
Itlb-load-misses	1.24E+009	9.95E+008	-19.79%
i per iTLB-miss		568.97		720.40		26.61%
Cpu-clock		997,897.58	974,661.58	-2.33%
Task-clock		1,000,752.83	977,629.52	-2.31%
=======================	============    =========== 	=======

The experiment in the x86_64 guest vm summarized in the table below show
greater improvement that running on raw hardware.
This may be due to the additional overheads introduced for TLB fixup and
pressure on the TLB due to having additional code to run to simulate
hardware for the guest.
There are more frequent iTLB misses for the virtualized machine and the
reductions are greater for iTLB misses when postgresql layout is
optimized.
The function reordering of the qemu-kvm slightly helped performance.
The last two columns show the improvements for only optimizing postgresql and
optimizing both postgresql and the user-space kvm-qemu.
			
			
=====================	============	==============	==========	==============  =============	=============
x86_64 kvm guest	kvm		kvm		kvm_pgo		kvm_pgo		only postgres	both postgres
metric			postgresql	postgresql_pgo	postgresql	postgresql_pgo	reordered	reordered
			baseline							vs baseline	vs baseline
=====================	============	==============	==========	==============  =============	=============
tps (including conn)	722.19		745.67		720.10		747.87		3.25%		3.56%
tps (excluding conn)	722.41		745.15		721.37		749.26		3.15%		3.72%
cycles			4.12E+011	3.99E+011	4.12E+011	3.99E+011	-3.11%		-3.12%
instructions		2.55E+011	2.65E+011	2.54E+011	2.66E+011	3.78%		4.28%
IPC			.62		.66		.62		.67		7.11%		7.64%
Itlb-load-misses	9.33E+008	6.65E+008	9.32E+008	6.68E+008	-28.69%		-28.35%
i per iTLB-miss		273.22		397.62		272.42		397.67		45.53%		45.55%
Cpu-clock		177,030.63	174,455.12	176,798.16	173,752.65	-1.45%		-1.85%
Task-clock		177,174.29	174,616.27	176,926.93	173,901.29	-1.44%		-1.85%
=====================	============	==============	==========	==============  =============	=============


To test the portability of the technique the same postgresql source
RPM was build on armv7.  the following table summarizes the results.
The iTLB-load-misses on the arm onlhy measure the misses in the 32
element first level instruction TLB.  No matter what is done there
will always be a great number of misses.  However, the number of
instructions excuted during the fixed run time and the IPC showed
improvement.  The IPC improved by 4.88%.
			
			
====================	===========	===========	========
armv7 cortext a15
metric			baseline	reordered	%change
====================	===========	===========	========
tps (including conn)	477.46		491.08		2.85%
tps (excluding conn)	479.06		492.34		2.77%
cycles			5.22E+011	5.60E+011	7.30%
instructions		1.53E+011	1.72E+011	12.53%
IPC			.29		.31		4.88%
Itlb-load-misses	1.79E+009	1.81E+009	0.93%
i per iTLB-miss		85.39		95.20		11.49%
Cpu-clock		317,669.31	343,863.71	8.25%
Task-clock		319,782.35	346,122.26	8.24%
====================	===========	===========	========

These preliminary results show modest but useful improvements in
performance for the function reordering.
The IPC improved from 4.8% to 7.64%.
On x86_64 the iTLB miss rates significantly improve and more so
for code running in a guest VM.


References
==========

.. [GCC10] plugins, October 1, 2010, http://gcc.gnu.org/wiki/plugins 
.. [Glek10] Taras Glek, Linux: How to Make Startup Suck Less (Also Reduce Memory Usage!) http://blog.mozilla.org/tglek/2010/04/05/linux-how-to-make-startup-suck-less-and-reduce-memory-usage/ 
.. [Gor10] Mel Gorman, Huge pages part 5: A deeper look at TLBs and costs March 23, 2010 http://lwn.net/Articles/379748/ 
.. [Ho95] W. Wilson Ho, et. al. Optimizing the Performance of Dynamically-Linked Programs http://www.usenix.org/publications/library/proceedings/neworl/ho.html 
.. [Mal12] David Malcolm, GCC Python Plugin https://github.com/davidmalcolm/gcc-python-plugin/
