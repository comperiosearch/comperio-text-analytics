# coding=utf-8
import logging
from argparse import ArgumentParser
import os
import sys
import datetime

from es_text_analytics.data.ndt_dataset import NDTDataset
from es_text_analytics.tagger import train_hunpos_model, FEATURES_MAP



# Trains a Norwegian part-of-speech tagger with the NDT dataset.
# The tagger is trained on the combined Bokmål and Nynorsk material.

# Arguments:
# -f, --features The normalized feature set, no-feats, simple or universal. See tagger.py for details.
# -m, --model-file Where to save the resulting model. Crearet a default filename in the current directory
#   if omitted.
# -d, -dataset-file Where to find the NDT dataset. Uses default location if omitted.


FIELDS = ['form', 'postag', 'feats']


def main():
    parser = ArgumentParser()
    parser.add_argument('-f', '--features')
    parser.add_argument('-m', '--model-file')
    parser.add_argument('-d', '--dataset-file')

    args = parser.parse_args()

    features = args.features
    model_fn = args.model_file
    dataset_fn = args.dataset_file

    if not features in FEATURES_MAP:
        logging.error('Unknown feature identifier %s (one of <%s>) ...'
                      % (features, '|'.join(FEATURES_MAP.keys())))
        sys.exit(1)

    if dataset_fn and not os.path.exists(dataset_fn):
        logging.error('Could not find NDT dataset archive %s ...' % dataset_fn)
        sys.exit(1)

    if not model_fn:
        # noinspection PyUnresolvedReferences
        model_fn = 'no-ndt-hunpos-%s-%s' % (features, datetime.now().strftime("%Y-%m-%d-%H-%M"))

    if dataset_fn:
        dataset = NDTDataset(dataset_fn=dataset_fn, normalize_func=None, fields=FIELDS)
    else:
        dataset = NDTDataset(normalize_func=None, fields=FIELDS)
        dataset.install()

    pos_norm_func = FEATURES_MAP[features]
    seq_gen = ([(form, pos_norm_func(form, pos, feats)) for form, pos, feats in sent] for sent in dataset)

    stats = train_hunpos_model(seq_gen, model_fn)

    # print the stats from the hunpos output
    for k, v in stats.items():
        print '%s:\t%s' % (k, v)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()
