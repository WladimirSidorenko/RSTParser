# RST Parser

This project is a fork of [Ji's shift-reduce RST
parser](https://github.com/jiyfeng/DPLP), wrapped as a Python package
and adjusted to the peculiarities of German data.

## Training ##

To train the parser on [PCC
data](http://angcl.ling.uni-potsdam.de/resources/pcc.html) you can use
the following command:

```shell
rst_parser train data/pcc-dis-bhatia/ data/conll/
```

where `data/pcc-dis-bhatia/` is a directory containing files with RST
trees in dis format, and `data/conll` contains parse trees of
corresponding sentences in the CoNLL format. (Note that the
tokenization of files in both directories should be the same)

After you have trained your parser, you can apply it to new data by
executing the following command:

```shell
rst_parser test data/pcc-dis-bhatia/test/edu/ data/conll/ data/pcc-dis-bhatia/test/predicted/
```

where `data/pcc-dis-bhatia/test/edu/` is a directory containing files
with discourse segments in EDU format (you can use
[`dsegmneter`](https://github.com/WladimirSidorenko/DiscourseSegmenter)
to obtain these segments from CoNLL parse trees), `data/conll/`
comprises syntactic parse trees of the corresponding sentences in the
CoNLL format, and `data/pcc-dis-bhatia/test/predicted/` is the output
directory, in which to store the produced RST trees.

## Modules ##

- tree: any operation about an RST tree is included in this module. For example
    - Build general/binary RST tree from annotated file
    - Binarize a general RST tree to the binary form (original RST trees in the RST treebank may not in the binary form)
    - Generate bracketing sequence for evaluation
    - Write an RST tree into file (not implemented yet)
    - Generate Shift-reduce parsing action examples
    - Get all EDUs from the RST tree
- parser: an implementation of the shift-reduce parsing algorithm, including following functions:
    - Initialize parsing status given a sequence of texts
    - Change the status according to a specific parsing action
    - Get the status of stack/queue
    - Check whether should stop parsing
- model: an parsing model module, where a trained parsing model could predict parsing actions. This module includes:
    - Batch training on the data generated by the data module
    - Predict parsing actions for a given feature set
    - Save/load parsing model
- feature: an feature generator, which can generate features from current stack/queue status.
- data: generate training data for offline training


## Main Classes
(For all the following functions, please refer to the code for more explanation)

- RSTTree (in tree module):
    - build(): Build an binary RST tree from an annotated discourse file
    - generate_sample(): Generate a sequence of parsing actions and the corresponding training examples, which can be used for offline training on parsing model
    - getedutext(): Get a sequence of EDU texts from the given RST tree
    - bracketing: Generate bracketing sequence for evaluation
- SRParser (in parser module):
    - init(texts): Initialize the queue status from the given text sequence. Each element in this sequence will be treated as an EDU
    - operate(action_tuple): Change the queue/stack according to the action tuple, for example, the operation *(Shift, None, None)* will move one element from the head of the queue to the top of the stack
    - getparsetree(): Return the entire RST tree
- FeatureGenerator (in feature module):
   - features(): the major generator which could extract all the necessary features from current queue/stack. You can **extend** this generator by calling other sub-functions in it.
- ParsingModel (in model module):
    - train(trnM, trnL): Offline training on the parsing model (aka, a multi-class classifier) from the given training data *trnM* and corresponding labels *trnL*
    - predict(features): Predict a parsing action according to the given feature generator
    - sr_parse(texts): Performing shift-reduce RST parsing on the given text sequence. Each element in this sequence will be treated as an EDU
- Data (in data module):
    - buildvocab(thresh): Build feature vocab by removing some low-frequency features. The same vocab will also be used for future parsing work in test stage.
    - buildmatrix(): Build data matrix for offline training
    - savematrix(fname): Save data matrix and corresponding labels into **fname**
    - getvocab(): Get feature vocab
    - savevocab(fname): Save feature vocab and relation mapping (from relations to indices) into **fname**

## Reference

- Yangfeng Ji, Jacob Eisenstein, **[Representation Learning for
  Text-level Discourse
  Parsing](https://github.com/jiyfeng/jiyfeng.github.io/blob/master/papers/ji-acl-2014.pdf)**,
  Proceedings of ACL, 2014
