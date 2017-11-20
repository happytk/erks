# -*-encoding:utf8 -*-
import os
import pickle
from . import utils_nlp
from flask import current_app


def get_dataset(parameters):
    if current_app.config['DATASET'] is None:
        print("reloading dataset...")
        current_app.config['DATASET'] = pickle.load(open(os.path.join(parameters['pretrained_model_folder'], 'dataset.pickle'), 'rb'))
    return current_app.config['DATASET']


def get_token_to_vector(parameters):
    if current_app.config['TOKEN_TO_VECTOR'] is None:
        print("reloading vectors")
        current_app.config['TOKEN_TO_VECTOR'] = utils_nlp.load_pretrained_token_embeddings(parameters)
    return current_app.config['TOKEN_TO_VECTOR']

