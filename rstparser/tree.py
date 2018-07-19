#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

""" Any operation about an RST tree should be here
1) Build general/binary RST tree from annotated file
2) Binarize a general RST tree to the binary form
3) Generate bracketing sequence for evaluation
4) Write an RST tree into file (not implemented yet)
5) Generate Shift-reduce parsing action examples
6) Get all EDUs from the RST tree
- YJ
"""

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals

import re

from .node import SpanNode
from .parser import RSTParser
from .utils import LOGGER


##################################################################
# Variables and Constants
SPACE_RE = re.compile(r'\s+')


##################################################################
# Methods
def preprocess(tokens):
    """ Preprocessing token list for filtering '(' and ')' in text

    :type tokens: list
    :param tokens: list of tokens
    """
    identifier = '_!'
    within_text = False
    for (idx, tok) in enumerate(tokens):
        if identifier in tok:
            for _ in range(tok.count(identifier)):
                within_text = not within_text
        if ('(' in tok) and (within_text):
            tok = tok.replace('(', '-LB-')
        if (')' in tok) and (within_text):
            tok = tok.replace(')', '-RB-')
        tokens[idx] = tok
    return tokens


##################################################################
# Class
class RSTTree(object):
    def __init__(self, dis, conll_doc=None):
        """Class cosntructor.

        :param string dis: content of dis file
        :param CoNLLDoc conll_doc: corresponding document with CoNLL parses

        """
        self.binary = False
        self._tree = None
        self._conll_doc = conll_doc
        self.parse_dis(dis)
        # synchronize internal RST tree with CoNLL information
        self._sync()
        self.backprop()

    @property
    def tree(self):
        """ Get the RST tree
        """
        return self._tree

    @property
    def tokendict(self):
        """ Get the RST tree
        """
        return self._conll_doc.tokendict

    @property
    def edudict(self):
        """ Get the RST tree
        """
        return self._conll_doc.edudict

    def parse_dis(self, dis):
        """Parse dis file.

        :type text: string
        :param text: dis file content

        """
        dis = dis.strip().replace('\n', ' ')
        dis = dis.replace('(', ' ( ').replace(')', ' ) ')
        tokens = preprocess(dis.split())
        stack = []
        while tokens:
            token = tokens.pop(0)
            if token == ')':
                # If ')', start processing
                content = []  # Content in the stack
                while stack:
                    cont = stack.pop()
                    if cont == '(':
                        break
                    else:
                        content.append(cont)
                content.reverse()  # Reverse to the original order
                # Parse according to the first content word
                if len(content) < 2:
                    raise ValueError("content = {}".format(content))
                label = content.pop(0)
                if (label == 'Root' or label == 'Nucleus'
                        or label == 'Satellite'):
                    node = self.createnode(
                        SpanNode(prop=label), content
                    )
                    stack.append(node)
                elif label == 'span':
                    # Merge
                    beginindex = int(content.pop(0))
                    endindex = int(content.pop(0))
                    stack.append(('span', beginindex, endindex))
                elif label == 'leaf':
                    # Merge
                    eduindex = int(content.pop(0))
                    self.checkcontent(label, content)
                    stack.append(('leaf', eduindex, eduindex))
                elif label == 'rel2par':
                    # Merge
                    relation = content.pop(0)
                    self.checkcontent(label, content)
                    stack.append(('relation', relation))
                elif label == 'text':
                    # Merge
                    txt = self.createtext(content)
                    stack.append(('text', txt))
                else:
                    raise ValueError(
                        ("Unrecognized parsing label: {} \n\twith"
                         " content = {}\n\tstack={}\n\tqueue={}").format(
                             label, content, stack, tokens))
            else:
                # else, keep push into the stack
                stack.append(token)
        self._tree = stack[-1]
        self.binarize()

    def generate_samples(self):
        """ Generate samples from an binary RST tree
        """
        # Sample list
        samplelist = []
        # Parsing action
        actionlist = self.decodeSRaction()
        # Initialize queue and stack
        queue = self.get_edu_nodes()
        stack = []
        sr = RSTParser(queue, stack, None)
        # Start simulating the shift-reduce parsing
        for action in actionlist:
            # Generate sample states
            sample = (stack[-1] if len(stack) else None,
                      stack[-2] if len(stack) > 1 else None,
                      queue[0] if len(queue) else None,
                      self)
            samplelist.append(sample)
            # Change status of stack/queue
            sr.operate(action)
        return (actionlist, samplelist)

    def backprop(self):
        """Starting from leaf node, propagating node information back to root node

        :type tree: SpanNode instance
        :param tree: an binary RST tree

        """
        treenodes = self.bin_bft()
        treenodes.reverse()
        edudict = self._conll_doc.edudict
        for node in treenodes:
            if (node.lnode is not None) and (node.rnode is not None):
                # Non-leaf node
                node.eduspan = self._getspaninfo(node.lnode, node.rnode)
                node.text = self._gettextinfo(edudict, node.eduspan)
                if node.relation is None:
                    # If it is a new node
                    if node.prop == 'Root':
                        pass
                    else:
                        node.relation = self._getrelationinfo(
                            node.lnode, node.rnode
                        )
                node.form, node.nucspan = self._getforminfo(
                    node.lnode, node.rnode
                )
            elif (node.lnode is None) and (node.rnode is not None):
                # Illegal node
                raise ValueError("Unexpected left node")
            elif (node.lnode is not None) and (node.rnode is None):
                # Illegal node
                raise ValueError("Unexpected right node")
            else:
                # Leaf node
                node.text = self._gettextinfo(edudict, node.eduspan)
        return treenodes[-1]

    def binarize(self):
        """ Convert a general RST tree to a binary RST tree

        :type tree: instance of SpanNode
        :param tree: a general RST tree
        """
        queue = [self._tree]
        while queue:
            node = queue.pop(0)
            queue += node.nodelist
            # Construct binary tree
            if len(node.nodelist) == 2:
                node.lnode = node.nodelist[0]
                node.rnode = node.nodelist[1]
                # Parent node
                node.lnode.pnode = node
                node.rnode.pnode = node
            elif len(node.nodelist) > 2:
                # Remove one node from the nodelist
                node.lnode = node.nodelist.pop(0)
                newnode = SpanNode(node.nodelist[0].prop)
                newnode.nodelist += node.nodelist
                # Right-branching
                node.rnode = newnode
                # Parent node
                node.lnode.pnode = node
                node.rnode.pnode = node
                # Add to the head of the queue
                # So the code will keep branching
                # until the nodelist size is 2
                queue.insert(0, newnode)
            # Clear nodelist for the current node
            node.nodelist = []
        return self

    def bin_bft(self):
        """ Breadth-first treavsal on binary RST tree

        """
        queue = [self._tree]
        bft_nodelist = []
        while queue:
            node = queue.pop(0)
            bft_nodelist.append(node)
            if node.lnode is not None:
                queue.append(node.lnode)
            if node.rnode is not None:
                queue.append(node.rnode)
        return bft_nodelist

    def bracketing(self):
        """ Generate brackets according an Binary RST tree
        """
        nodelist = self.postorder_DFT(self._tree, [])
        nodelist.pop()  # Remove the root node
        brackets = []
        for node in nodelist:
            relation = node.relation
            b = (node.eduspan, node.prop, relation)
            brackets.append(b)
        return brackets

    def checkcontent(self, label, c):
        """ Check whether the content is legal

        :type label: string
        :param label: parsing label, such 'span', 'leaf'

        :type c: list
        :param c: list of tokens
        """
        if len(c) > 0:
            raise ValueError("{} with content={}".format(label, c))

    def createnode(self, node, content):
        """ Assign value to an SpanNode instance

        :type node: SpanNode instance
        :param node: A new node in an RST tree

        :type content: list
        :param content: content from stack
        """
        for c in content:
            if isinstance(c, SpanNode):
                # Sub-node
                node.nodelist.append(c)
                c.pnode = node
            elif c[0] == 'span':
                node.eduspan = (c[1], c[2])
            elif c[0] == 'relation':
                node.relation = c[1]
            elif c[0] == 'leaf':
                node.eduspan = (c[1], c[1])
                node.nucspan = (c[1], c[1])
                node.nucedu = c[1]
            elif c[0] == 'text':
                node.text = c[1]
            else:
                raise ValueError("Unrecognized property: {}".format(c[0]))
        return node

    def createtext(self, lst):
        """Create text from a list of tokens

        :type lst: list
        :param lst: list of tokens

        """
        newlst = []
        for item in lst:
            item = item.replace("_!", "")
            newlst.append(item)
        text = ' '.join(newlst)
        # Lower-casing
        return text.lower()

    def _getspaninfo(self, lnode, rnode):
        """ Get span size for parent node

        :type lnode,rnode: SpanNode instance
        :param lnode,rnode: Left/Right children nodes
        """
        try:
            eduspan = (lnode.eduspan[0], rnode.eduspan[1])
        except TypeError:
            LOGGER.error(
                "Error on getting span information: "
                "lnode.prop: %r, rnode.prop: %r, "
                "lnode.nucspan: %r, rnode.nucspan: %r;",
                lnode.prop, rnode.prop,
                lnode.nucspan, rnode.nucspan)
        return eduspan

    def _getforminfo(self, lnode, rnode):
        """ Get Nucleus/Satellite form and Nucleus span

        :type lnode,rnode: SpanNode instance
        :param lnode,rnode: Left/Right children nodes
        """
        if (lnode.prop == 'Nucleus') and (rnode.prop == 'Satellite'):
            nucspan = lnode.eduspan
            form = 'NS'
        elif (lnode.prop == 'Satellite') and (rnode.prop == 'Nucleus'):
            nucspan = rnode.eduspan
            form = 'SN'
        elif (lnode.prop == 'Nucleus') and (rnode.prop == 'Nucleus'):
            nucspan = (lnode.eduspan[0], rnode.eduspan[1])
            form = 'NN'
        else:
            raise ValueError("")
        return (form, nucspan)

    def _getrelationinfo(self, lnode, rnode):
        """Get relation information

        :type lnode,rnode: SpanNode instance
        :param lnode,rnode: Left/Right children nodes
        """
        if (lnode.prop == 'Nucleus') and (rnode.prop == 'Nucleus'):
            relation = lnode.relation
        elif (lnode.prop == 'Nucleus') and (rnode.prop == 'Satellite'):
            relation = lnode.relation
        elif (lnode.prop == 'Satellite') and (rnode.prop == 'Nucleus'):
            relation = rnode.relation
        else:
            LOGGER.error(
                "Error on getting relation information: "
                "lnode.prop = {}, lnode.eduspan = {}, "
                "rnode.prop = {}, lnode.eduspan = {};",
                lnode.prop, lnode.eduspan,
                rnode.prop, rnode.eduspan)
            raise ValueError("Error when find relation for new node")
        return relation

    def _gettextinfo(self, edudict, eduspan):
        """ Get text span for parent node

        :type edudict: dict of list
        :param edudict: EDU from this document

        :type eduspan: tuple with two elements
        :param eduspan: start/end of EDU IN this span
        """
        # text = lnode.text + " " + rnode.text
        # LOGGER.debug("_gettextinfo: edudict: %r", edudict)
        # LOGGER.debug("_gettextinfo: eduspan: %r", eduspan)
        text = []
        for idx in range(eduspan[0], eduspan[1]+1, 1):
            text += edudict[idx]
        # Return: A list of token indices
        return text

    def _sync(self):
        """Synchronize RST tree with CoNLL information.

        """
        if self._conll_doc is None:
            return
        gidx = 0
        edu_nodes = self.get_edu_nodes()
        edudict = self._conll_doc.edudict
        tokendict = self.tokendict
        for node_i in edu_nodes:
            if node_i.text is None:
                continue
            edu_id = node_i.nucedu
            toks = SPACE_RE.split(node_i.text)
            for tok_i in toks:
                tok_i = tok_i.strip()
                if tok_i:
                    if tok_i.lower() != tokendict[gidx].word.lower():
                        LOGGER.warn(
                            "Different tokens: %r vs %r",
                            tok_i, tokendict[gidx].word
                        )
                    if edu_id not in edudict:
                        edudict[edu_id] = [gidx]
                    else:
                        edudict[edu_id].append(gidx)
                    gidx += 1
        if gidx != len(self.tokendict):
            LOGGER.error(
                "Different number of tokens in dis and conll files: %d vs %d",
                gidx, len(tokendict)
            )

    def get_edu_nodes(self):
        """Get all EDU leaves.

        :type tree: SpanNode instance
        :param tree: an binary RST tree
        """
        edulist = [
            node
            for node in self.postorder_DFT(self.tree, [])
            if (node.lnode is None) and (node.rnode is None)
        ]
        return edulist

    def postorder_DFT(self, tree, nodelist):
        """Post order traversal on binary RST tree.

        :type tree: SpanNode instance
        :param tree: an binary RST tree

        :type nodelist: list
        :param nodelist: list of node in post order

        """
        if tree.lnode is not None:
            self.postorder_DFT(tree.lnode, nodelist)
        if tree.rnode is not None:
            self.postorder_DFT(tree.rnode, nodelist)
        nodelist.append(tree)
        return nodelist

    def decodeSRaction(self):
        """Decoding Shift-reduce actions from an binary RST tree.

        :type tree: SpanNode instance
        :param tree: an binary RST tree
        """
        # Start decoding
        post_nodelist = self.postorder_DFT(self._tree, [])
        actionlist = []
        for node in post_nodelist:
            if (node.lnode is None) and (node.rnode is None):
                actionlist.append(('shift', None, None))
            elif (node.lnode is not None) and (node.rnode is not None):
                form = node.form
                if (form == 'NN') or (form == 'NS'):
                    relation = node.rnode.relation
                else:
                    relation = node.lnode.relation
                actionlist.append(('reduce', form, relation))
            else:
                raise ValueError("Can not decode Shift-Reduce action")
        return actionlist
