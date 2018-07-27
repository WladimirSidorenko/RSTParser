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
    def __init__(self, ifile=None):
        """Class constructor.

        :param ibuffer ifile: input file containing CoNLL parse trees.

        """
        # Token dict
        self.tokendict = {}
        # EDU dict
        self.edudict = {}
        if ifile is not None:
            self._parse(ifile)

    def _parse(self, ifile):
        sidx = 0
        for iline in ifile:
            iline = iline.strip()
            if not iline or iline.startswith(''):
                continue
            tok = CoNLLToken(iline)
            if tok.tidx == 0:
                sidx += 1
            tok.sidx = sidx
            self.tokendict[len(self.tokendict)] = tok


class CoNLLToken(object):
    """ Token class
    """
    def __init__(self, iline=None):
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
        if iline is not None:
            self._parse(iline)

    def _parse(self, iline):
        iline = iline.strip()
        fields = iline.split('\t')
        self.tidx = int(fields[0]) - 1
        self.word = fields[1]
        self.lemma = fields[2].lower()
        self.pos = fields[4]
        self.deplabel = fields[11]
        self.hidx = int(fields[9]) - 1

    def __repr__(self):
        return ("<ConLLToken sidx={:d}, tidx={:d}, gidx={:d}, "
                "word={:s}, lemma={:s}, pos={:s}, deplabel={:s}, "
                "hidx={:d}>").format(
                    self.sidx, self.tidx, self.gidx,
                    self.word, self.lemma, self.pos,
                    self.deplabel, self.hidx
        )
