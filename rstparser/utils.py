## util.py
## Author: Yangfeng Ji
## Date: 09-13-2014
## Time-stamp: <yangfeng 09/16/2014 13:09:09>

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals

from scipy.sparse import lil_matrix
import logging
import os


##################################################################
# Variables and Constants
DFLT_ENCODING = "utf-8"
DFLT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "rstpaser.model"
)
LOG_LVL = logging.INFO
LOGGER = logging.getLogger("RSTParser")
LOGGER.setLevel(LOG_LVL)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
sh = logging.StreamHandler()
sh.setLevel(LOG_LVL)
sh.setFormatter(formatter)
LOGGER.addHandler(sh)


##################################################################
# Methods
def label2action(label):
    """ Transform label to action
    """
    items = label.split('-')
    if len(items) == 1:
        action = (items[0], None, None)
    elif len(items) == 3:
        action = tuple(items)
    else:
        raise ValueError("Unrecognized label: {}".format(label))
    return action


def action2label(action):
    """ Transform action into label
    """
    if action[0] == 'shift':
        label = action[0]
    elif action[0] == 'reduce':
        label = '-'.join(list(action))
    else:
        raise ValueError("Unrecognized parsing action: {}".format(action))
    return label


def vectorize(features, vocab):
    """ Transform a feature list into a numeric vector
        with a given vocab
    """
    vec = lil_matrix((1, len(vocab)))
    for feat in features:
        try:
            fidx = vocab[feat]
            vec[0, fidx] += 1.0
        except KeyError:
            pass
    return vec


def extractrelation(s, level=0):
    """ Extract discourse relation on different level
    """
    return s.lower().split('-')[0]


def reversedict(dct):
    """ Reverse the {key:val} in dct to
        {val:key}
    """
    # print labelmap
    newmap = {}
    for (key, val) in dct.iteritems():
        newmap[val] = key
    return newmap


def getgrams(text, tokendict):
    """ Generate first one, two words from the token list

    :type text: list of int
    :param text: indices of words with the text span

    :type tokendict: dict of Token (data structure)
    :param tokendict: all tokens in the doc, indexing by the
                      document-level index
    """
    n = len(text)
    grams = []
    # Get lower-case of words
    if n >= 1:
        grams.append(tokendict[text[0]].word.lower())
        grams.append(tokendict[text[-1]].word.lower())
        grams.append(tokendict[text[0]].pos)
        grams.append(tokendict[text[-1]].pos)
    if n >= 2:
        token = tokendict[text[0]].word.lower() \
            + ' ' + tokendict[text[1]].word.lower()
        grams.append(token)
        token = tokendict[text[-2]].word.lower() \
            + ' ' + tokendict[text[-1]].word.lower()
        grams.append(token)
    return '-%-'.join(grams)
