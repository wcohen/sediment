#!/usr/bin/python2
#   Copyright 2011 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2011 Red Hat, Inc.
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

# Sample python script, to be run by our gcc plugin
# Show the call graph (interprocedural analysis), using GraphViz
import gcc
from gccutils import invoke_dot

# In theory we could have done this with a custom gcc.Pass registered
# directly after "*build_cgraph_edges".  However, we can only register
# relative to passes of the same kind, and that pass is a
# gcc.GimplePass, which is called per-function, and we want a one-time
# pass instead.
#
# So we instead register a callback on the one-time pass that follows it

class CallgraphPrettyPrinter:
    def node_id(self, cgn):
        return '"%s"' % cgn.decl.name

    def node_to_dot_label(self, cgn):
        return str(cgn.decl.name)

    def edge_to_dot(self, e):
        return ('%s -> %s'
                % (self.node_id(e.caller),
                   self.node_id(e.callee)))

    def to_dot(self):
        result = 'digraph Callgraph {\n'
        result += '  node [shape=ellipse];\n'
        # Consolidate duplicate edges together
        counts = { }
        for cgn in gcc.get_callgraph_nodes():
            for edge in cgn.callers:
                edge_name = self.edge_to_dot(edge)
                counts[edge_name] = counts.get(edge_name, 0.0) + 0.001
        # Print the accumulated edges
        for edge_name in counts:
            result += ('   %s ' % edge_name)
            result += ('[ label = %.3f ];\n' % counts[edge_name])
        result += '}\n'
        return result

def callgraph_to_dot():
    pp = CallgraphPrettyPrinter()
    return pp.to_dot()


def on_pass_execution(p, fn):
    if p.name == '*free_lang_data':
        # The '*free_lang_data' pass is called once, rather than per-function,
        # and occurs immediately after "*build_cgraph_edges", which is the
        # pass that initially builds the callgraph
        #
        # So at this point we're likely to get a good view of the callgraph
        # before further optimization passes manipulate it
        dot = callgraph_to_dot()
        # invoke_dot(dot)
        filename = '%s.gv' % (gcc.get_dump_base_name())
        with open(filename, "w") as f:
            f.write(dot)

gcc.register_callback(gcc.PLUGIN_PASS_EXECUTION,
                      on_pass_execution)
