#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals

from .utils import LOGGER, getgrams


##################################################################
# Class
class FeatureExtractor(object):
    @classmethod
    def extract_feats(cls, stack_node1, stack_node2,
                      queue_node, conll):
        """Main function to extract features.

        :param class cls: pointer to this class
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        LOGGER.debug("stack_node1: %r", stack_node1)
        LOGGER.debug("stack_node2: %r", stack_node2)
        LOGGER.debug("queue_node: %r", queue_node)
        LOGGER.debug("conll: %r", conll)
        feats = {}
        # Status features (Basic features)
        cls.extract_status_feats(feats, stack_node1, stack_node2,
                                 queue_node, conll)
        # Lexical features
        cls.extract_lex_feats(feats, stack_node1, stack_node2,
                              queue_node, conll)
        # Structural features
        cls.extract_struct_feats(feats, stack_node1, stack_node2,
                                 queue_node, conll)
        # EDU features
        cls.extract_edu_feats(feats, stack_node1, stack_node2,
                              queue_node, conll)
        # Distributional representation
        cls.extract_distrib_feats(feats, stack_node1, stack_node2,
                                  queue_node, conll)
        LOGGER.debug("feats: %r", feats)
        # No Brown clusters
        return feats

    @classmethod
    def extract_struct_feats(cls, feats, stack_node1, stack_node2,
                             queue_node, conll):
        """Main function to extract structural features.

        :param class cls: pointer to this class
        :param dict feats: target dictionary of features
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        doclen = len(conll.edudict)
        if stack_node1 is not None:
            span = stack_node1
            # Span Length wrt EDUs
            edulen1 = span.eduspan[1] - span.eduspan[0] + 1
            feats[('Top1-Stack', 'Length-EDU')] = edulen1
            # Distance to the beginning of the document wrt EDUs
            feats[('Top1-Stack', 'Dist-To-Begin')] = span.eduspan[0]
            # Distance to the end of the document wrt EDUs
            feats[('Top1-Stack', 'Dist-To-End')] = doclen - span.eduspan[1]
        if stack_node2 is not None:
            span = stack_node2
            edulen2 = span.eduspan[1]-span.eduspan[0] + 1
            feats[('Top2-Stack', 'Length-EDU')] = edulen2
            feats[('Top2-Stack', 'Dist-To-Begin')] = span.eduspan[0]
            feats[('Top2-Stack', 'Dist-To-End')] = doclen - span.eduspan[1]
        if queue_node is not None:
            span = queue_node
            feats[('First-Queue', 'Dist-To-Begin')] = span.eduspan[0]

    @classmethod
    def extract_status_feats(cls, feats, stack_node1, stack_node2,
                             queue_node, conll):
        """Main function to extract status features.

        :param class cls: pointer to this class
        :param dict feats: target dictionary of features
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        # Stack
        if (stack_node1 is None) and (stack_node2 is None):
            feats[('Stack', 'Empty')] = 1
        elif (stack_node1 is not None) and (stack_node2 is None):
            feats[('Stack', 'OneElem')] = 1
        elif (stack_node1 is not None) and (stack_node2 is not None):
            feats[('Stack', 'MoreElem')] = 1
        else:
            raise ValueError("Unrecognized stack status")
        # Queue
        if (queue_node is None):
            feats[('Queue', 'Empty')] = 1
        else:
            feats[('Queue', 'NonEmpty')] = 1

    @classmethod
    def extract_edu_feats(cls, feats, stack_node1, stack_node2,
                          queue_node, conll):
        """Main function to extract EDU features.

        :param class cls: pointer to this class
        :param dict feats: target dictionary of features
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        tokendict = conll.tokendict
        # ---------------------------------------
        # EDU length
        if stack_node1 is not None:
            eduspan = stack_node1.eduspan
            feats[('Top1-Stack', 'nEDUs')] = eduspan[1] - eduspan[0]+1
        if stack_node2 is not None:
            eduspan = stack_node2.eduspan
            feats[('Top1-Stack', 'nEDUs')] = eduspan[1] - eduspan[0]+1
        # ---------------------------------------
        # Whether within same sentence
        # Span 1 and 2
        # Last word from span 1, first word from span 2
        try:
            text1, text2 = stack_node1.text, stack_node2.text
            if (tokendict[text1[-1]].sidx == tokendict[text2[0]].sidx):
                feats[('Top12-Stack', 'SameSent')] = 1
            else:
                feats[('Top12-Stack', 'SameSent')] = 0
        except AttributeError:
            feats[('Top12-Stack', 'SameSent')] = 0
        # Span 1 and top span
        # First word from span 1, last word from span 3
        try:
            text1, text3 = stack_node1.text, queue_node.text
            if (tokendict[text1[0]].sidx == tokendict[text3[-1]].sidx):
                feats[('Stack-Queue', 'SameSent')] = 1
            else:
                feats[('Stack-Queue', 'SameSent')] = 0
        except AttributeError:
            feats[('Stack-Queue', 'SameSent')] = 0

    @classmethod
    def extract_lex_feats(cls, feats, stack_node1, stack_node2,
                          queue_node, conll):
        """Main function to extract lexical features.

        :param class cls: pointer to this class
        :param dict feats: target dictionary of features
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        tokendict = conll.tokendict
        if stack_node1 is not None:
            span = stack_node1
            # feats[('Top1-Stack', 'nTokens', len(span.text))
            grams = getgrams(span.text, tokendict)
            for gram in grams:
                feats[('Top1-Stack', 'nGram', gram)] = 1
        if stack_node2 is not None:
            span = stack_node2
            # feats[('Top2-Stack', 'nTokens', len(span.text))
            grams = getgrams(span.text, tokendict)
            for gram in grams:
                feats[('Top2-Stack', 'nGram', gram)] = 1
        if queue_node is not None:
            span = queue_node
            # feats[('First-Queue', 'nTokens', len(span.text))
            grams = getgrams(span.text, tokendict)
            for gram in grams:
                feats[('First-Queue', 'nGram', gram)] = 1

    @classmethod
    def extract_distrib_feats(cls, feats, stack_node1, stack_node2,
                              queue_node, conll):
        """Main function to extract distributional features.

        :param class cls: pointer to this class
        :param dict feats: target dictionary of features
        :param stack_node1: first RST node on the stack
        :type stack_node1: SpanNode or None
        :param stack_node2: second RST node on the stack
        :type stack_node2: SpanNode or None
        :param queue_node: first RST node in the queue
        :type queue_node: SpanNode or None
        :param conll: conll document
        :type conll: CoNLLDoc

        """
        tokendict = conll.tokendict
        edudict = conll.edudict
        if stack_node1 is not None:
            eduidx = stack_node1.nucedu
            for gidx in edudict[eduidx]:
                word = tokendict[gidx].lemma.lower()
                feats[('DisRep', 'Top1Span', word)] = 1
        if stack_node2 is not None:
            eduidx = stack_node2.nucedu
            for gidx in edudict[eduidx]:
                word = tokendict[gidx].lemma.lower()
                feats[('DisRep', 'Top2Span', word)] = 1
        if queue_node is not None:
            eduidx = queue_node.nucedu
            for gidx in edudict[eduidx]:
                word = tokendict[gidx].lemma.lower()
                feats[('DisRep', 'FirstSpan', word)] = 1
