#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

""" Shift-reduce parser, including following functions
1, Initialize parsing status given a sequence of texts
2, Change the status according to a specific parsing action
3, Get the status of stack/queue
4, Check whether should stop parsing
- YJ

"""

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals

try:
    from cPickle import dump, load
except ImportError:
    from _pickle import dump, load

from .model import Model
from .node import SpanNode
from .exceptions import ActionError, ParseError
from .utils import LOGGER


##################################################################
# Constants


##################################################################
# Class
class RSTParser(object):
    """Shift-reduce rhetorical structure parser.

    """
    def __init__(self, queue, stack, mpath=None):
        """Class constructor.

        :param list queue: EDUs to be processed
        :param list stack: currently processed EDUs
        :param str mpath: path to pretrained model

        """
        self._queue = queue
        self._stack = stack
        self._mpath = mpath
        if mpath is None:
            self._model = Model()
        else:
            self.load(mpath)

    @property
    def stack(self):
        """Get internal stack of processed states.

        :return: stack of states
        :rtype: list

        """
        return self._stack

    @property
    def queue(self):
        """Get internal queue of states which need to be processed.

        :return: queue of states to be processed
        :rtype: list

        """
        return self._queue

    def train(self, rst_trees):
        """Train internal model on the provided data.

        :param rst_tree: list of RST trees
        :type data: list[rstparser.tree.RSTTree]

        """
        LOGGER.debug("rst_trees: %r", rst_trees)
        actions = []
        samples = []
        for tree in rst_trees:
            t_actions, t_samples = tree.generate_samples()
            actions.extend(t_actions)
            samples.extend(t_samples)
        self._model.train(samples, actions)

    def parse(self, queue, conll_doc):
        """Construst an RST tree from a list of EDU nodes.

        :param list[SpanNode] queue: list of input EDUs
        :param CoNLLDoc conll_doc: list of input EDUs

        """
        if self.queue or self.stack:
            LOGGER.warn(
                "Attempting to parse with non-empty queue and stack."
            )
            self.reset()
        self._queue = queue
        while not self._endparsing():
            # Generate features
            stack_node1 = None if len(self.stack) < 1 else self.stack[-1]
            stack_node2 = None if len(self.stack) < 2 else self.stack[-2]
            queue_node = queue[0] if queue else None
            actions = self._model.predict(stack_node1, stack_node2,
                                          queue_node, conll_doc)
            for action in actions:
                try:
                    self.operate(action)
                    break
                except ActionError:
                    # print "Parsing action error with {}".format(action)
                    pass
            else:
                raise ActionError("No action could be performed.")
        tree = self._getparsetree()
        self.reset()
        return tree

    def save(self, mpath):
        """Save internal model at specifed location.

        :param str mpath: path at which to store the model

        """
        LOGGER.debug("Saving model to %s", mpath)
        self._model.reset()
        with open(mpath, "wb") as ofile:
            dump(self._model, ofile)
        self._model.restore()
        self._mpath = mpath
        LOGGER.debug("Model saved")

    def load(self, mpath):
        """Save internal model at the specifed location.

        :param str mpath: path from which to load the model

        """
        LOGGER.debug("Loading model to %s", mpath)
        with open(mpath, 'rb') as ifile:
            self._model = load(ifile)
        self._model.restore()
        self._mpath = mpath
        LOGGER.debug("Model loaded")

    def operate(self, action_tuple):
        """According to parsing label to modify the status of the Stack/Queue

        Need a special exception for parsing error -YJ

        :type action_tuple: tuple (,,)
        :param action_tuple: one specific parsing action,
                             for example: reduce-NS-elaboration

        """
        action, form, relation = action_tuple
        if action == 'shift':
            if len(self.queue) == 0:
                raise ActionError("Shift action with an empty queue")
            node = self.queue.pop(0)
            self.stack.append(node)
        elif action == 'reduce':
            if len(self.stack) < 2:
                raise ActionError(
                    "Reduce action with stack which has less than 2 spans"
                )
            rnode = self.stack.pop()
            lnode = self.stack.pop()
            # Create a new node
            # Assign a value to prop, only when it is someone's
            #   children node
            node = SpanNode(prop=None)
            # Children node
            node.lnode, node.rnode = lnode, rnode
            # Parent node of children nodes
            node.lnode.pnode, node.rnode.pnode = node, node
            # Node text
            node.text = lnode.text + rnode.text
            # EDU span
            node.eduspan = (lnode.eduspan[0], rnode.eduspan[1])
            # Nuc span / Nuc EDU
            if form == 'NN':
                node.nucspan = (lnode.eduspan[0], rnode.eduspan[1])
                node.nucedu = lnode.nucedu
                node.lnode.prop = "Nucleus"
                node.lnode.relation = relation
                node.rnode.prop = "Nucleus"
                node.rnode.relation = relation
            elif form == 'NS':
                node.nucspan = lnode.eduspan
                node.nucedu = lnode.nucedu
                node.lnode.prop = "Nucleus"
                node.lnode.relation = "span"
                node.rnode.prop = "Satellite"
                node.rnode.relation = relation
            elif form == 'SN':
                node.nucspan = rnode.eduspan
                node.nucedu = rnode.nucedu
                node.lnode.prop = "Satellite"
                node.lnode.relation = relation
                node.rnode.prop = "Nucleus"
                node.rnode.relation = "span"
            else:
                raise ValueError("Unrecognized form: {}".format(form))
            self.stack.append(node)
            # How about prop? How to update it?
        else:
            raise ValueError("Unrecoginized parsing action: {}".format(action))

    def _endparsing(self):
        """ Whether we should end parsing
        """
        if (len(self.stack) == 1) and (len(self.queue) == 0):
            return True
        elif (len(self.stack) == 0) and (len(self.queue) == 0):
            raise ParseError("Illegal stack/queue status")
        else:
            return False

    def _getparsetree(self):
        """ Get the entire parsing tree
        """
        if (len(self.stack) == 1) and (len(self.queue) == 0):
            return self.stack[0]
        else:
            return None

    def reset(self):
        """Clear stack and queue.

        """
        del self.stack[:]
        del self.queue[:]
