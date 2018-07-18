#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals


##################################################################
# Class
class CoNLLDoc(object):
    """CoNLL document.

    """
    def __init__(self, ifile):
        """Class constructor.

        :param ibuffer ifile: input file containing CoNLL parse trees.

        """
        # Token dict
        self.tokendict = {}
        # EDU dict
        self.edudict = {}
        self._parse(ifile)

    def _parse(self, ifile):
        sidx = 0
        gidx = len(self.tokendict)
        for iline in ifile:
            iline = iline.strip()
            if not iline or iline.startswith(''):
                continue
            tok = CoNLLToken(iline)
            if tok.tidx == 0:
                sidx += 1
            tok.sidx = sidx
            self.tokendict[gidx] = tok
            gidx += 1


class CoNLLToken(object):
    """ Token class
    """
    def __init__(self, iline):
        # Sentence index, token index (within sent)
        self.sidx = -1          # sentence index within document
        self.tidx = -1          # token index within sentence
        self.gidx = -1          # global token idex
        # Word, Lemma
        self.word = None
        self.lemma = None
        # POS tag
        self.pos = None
        # Dependency label, head index
        self.deplabel = None
        self.hidx = None
        # EDU index
        self.eduidx = None
        self._parse(iline)

    def _parse(self, iline):
        iline = iline.strip()
        fields = iline.split('\t')
        self.tidx = int(fields[0]) - 1
        self.word = fields[1]
        self.lemma = fields[2]
        self.pos = fields[4]
        self.deplabel = fields[11]
        self.hidx = int(fields[9]) - 1
