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

# This simple script convert callgraph information in graphviz formated input
# into a link order

import sys
import gv
import fileinput
import heapq

def read_graph():
    text =  ''
    for line in fileinput.input():
        text += line
    return gv.readstring (text)

def simple_order(in_graph):
    # just spit out list of nodes in some order
    func_order = []
    sbg = gv.firstsubg(in_graph)
    while gv.ok(sbg):
        n = gv.firstnode(sbg)
        while gv.ok(n):
            name = gv.nameof(n)
            func_order.append(name)
            n = gv.nextnode(sbg, n)
        sbg = gv.nextsubg(in_graph, sbg)
    return func_order


def group_order(in_graph):
    # put edges in priority queue
    heap = []
    sbg = gv.firstsubg(in_graph)
    while gv.ok(sbg):
        e = gv.firstedge(sbg)
        while gv.ok(e):
            # add edge to priority queue
            weight = - float(gv.getv(e, "label"))
            heapq.heappush(heap, (weight, e))
            e = gv.nextedge(sbg, e)
        sbg = gv.nextsubg(in_graph, sbg)


    e = gv.firstedge(in_graph)
    while gv.ok(e):
        # add edge to priority queue
        weight = - float(gv.getv(e, "label"))
        heapq.heappush(heap, (weight, e))
        e = gv.nextedge(in_graph, e)

    # pull out edges and group functions together until all edges processed
    sn = int(0)
    super_node = {}
    super_node_rename = {}
    func_member = {}
    while heap:
        group = heapq.heappop(heap)
        head = gv.nameof(gv.headof(group[1]))
        tail = gv.nameof(gv.tailof(group[1]))
        # print ( '%s -> %s %3f' % (tail, head, group[0]))
        if not(head in func_member) and not(tail in func_member):
            # print "new supernode"
            sn += 1
            func_member[tail] = super_node_rename[tail] = sn
            func_member[head] = super_node_rename[head] = sn
            super_node[sn] = [tail]
            super_node[sn].append(head)
        elif (head in func_member) and (tail in func_member):
            # print "combine supernode"
            super_node[super_node_rename[tail]].extend(super_node[super_node_rename[head]])
            super_node[super_node_rename[head]] = []
            super_node_rename[head] = super_node_rename[tail]
        elif not(head in func_member) and (tail in func_member):
            # print "append to supernode"
            super_node[super_node_rename[tail]].append(head)
            func_member[head] = func_member[tail]
            super_node_rename[head] = super_node_rename[tail]
        elif (head in func_member) and not(tail in func_member):
            # print "prepend to supernode"
            super_node[super_node_rename[head]].insert(0, tail)
            func_member[tail] = func_member[head]
            super_node_rename[tail] = super_node_rename[head]

            # otherwise nothing to do

    # concatenate the super nodes
    func_order = []
    for i in super_node:
        func_order.extend(super_node[i])
    
    return func_order


def gen_order(in_graph):
    #return simple_order(in_graph)
    return group_order(in_graph)

def print_order(order):
    for n in order:
        print ('.text.%s' % n)
    #everything else
    print ('.text.*')

the_graph = read_graph()
gv.write(the_graph, "/tmp/output.log")
link_order = gen_order(the_graph)
print_order(link_order)
