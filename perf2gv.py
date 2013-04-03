#!/usr/bin/env python
# Copyright 2013  William Cohen <wcohen@redhat.com>
# Copyright 2013 Red Hat, Inc.
#
#   This is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see
#   <http://www.gnu.org/licenses/>.

# This simple script convert the perf report output for something that
# has callgraph information into a graphviz output

import fileinput
import re

def header():
    result = 'digraph Callgraph {\n'
    result += '  node [shape=ellipse];\n'
    return result

def footer():
    result = '}\n'
    return result

# func@plt should just be treated the same as a direct call the func
def extract_func(func):
    return re.sub(r'@plt', "", func)

def body(threshold, const):
    #munge the output to give a call graph information
    result = ''
    counts = { }
    subgraphs = { }
    for line in fileinput.input():
        #skip comments and blank lines
        if line.startswith("#"):
            continue
        element = line.split()
        if len(element) < 8:
            continue
        weight = float(element[0].replace("%","")) / 100.00 * const
        if weight > threshold:
            caller_bin =  element[2]
            caller = extract_func(element[4])
            callee_bin =  element[5]
            callee = extract_func(element[7])
            counts[('  "%s" -> "%s" ' % (caller, callee))] = weight
            # add function to subgraph
            if subgraphs.has_key(caller_bin) :
                subgraphs[caller_bin].add(caller)
            else:
                subgraphs[caller_bin] = set([ caller ])
            if subgraphs.has_key(callee_bin) :
                subgraphs[callee_bin].add(callee)
            else:
                subgraphs[callee_bin] = set([ callee ])
    # print out subgraphs
    i = 0
    for graph in subgraphs:
        result += ('  subgraph cluster%d {\n' % i)
        for node in subgraphs[graph]:
            result += ('    "%s" ;\n' % node)
        result += ('    label = "%s";\n' % graph)
        result += ('  }\n\n')
        i = i + 1
    # Print the accumulated edges
    for edge_name in counts:
        result += ('   %s ' % edge_name)
        result += ('[ label = %.3f ];\n' % counts[edge_name])
    return result
 
print header()
print body(0.000, 1.0)
print footer()
