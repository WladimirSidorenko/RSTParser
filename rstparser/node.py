#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals
from future.utils import python_2_unicode_compatible


##################################################################
# Class
@python_2_unicode_compatible
class SpanNode(object):
    """ RST tree node
    """
    def __init__(self, prop):
        """ Initialization of SpanNode

        :type prop: string
        :param prop: property of this span wrt its parent node.
                     Only two possible values: Nucleus or Satellite
        """
        # Text of this span / Discourse relation
        self.text, self.relation = None, None
        # EDU span / Nucleus span (begin, end) index
        self.eduspan, self.nucspan = None, None
        # Nucleus single EDU
        self.nucedu = None
        # Property: it is a Nucleus or Satellite
        self.prop = prop
        # Children node
        # Each of them is a node instance
        # N-S form (for binary RST tree only)
        self.lnode, self.rnode = None, None
        # Parent node
        self.pnode = None
        # Node list (for general RST tree only)
        self.nodelist = []
        # Relation form: NN, NS, SN
        self.form = None

    def to_str(self, conll_doc, indent=0):
        """Return string representation of the given node in DIS format.

        """
        prfx = "  " * indent
        if self.prop:
            ret = '(' + self.prop + '\n'
        else:
            ret = "(Root\n"
        if self.lnode is None and self.rnode is None:
            ret += prfx + "(leaf " + str(self.eduspan[0]) + ")\n"
        else:
            ret += prfx + "(span " + ' '.join(
                str(i) for i in self.eduspan) + ")\n"
        if self.relation:
            ret += prfx + "(rel2par " + self.relation + ")\n"
        if self.lnode:
            ret += prfx + self.lnode.to_str(conll_doc, indent=indent + 1)
        if self.rnode:
            ret += prfx + self.rnode.to_str(conll_doc, indent=indent + 1)
        if self.lnode is None and self.rnode is None:
            tokendict = conll_doc.tokendict
            ret += prfx + "(text _!" + ' '.join(tokendict[i].word
                                                for i in self.text) + "_!)\n"
        ret += prfx + ")\n"
        return ret
