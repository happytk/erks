'''
To run:
CUDA_VISIBLE_DEVICES="" python3.5 main.py &
CUDA_VISIBLE_DEVICES=1 python3.5 main.py &
CUDA_VISIBLE_DEVICES=2 python3.5 main.py &
CUDA_VISIBLE_DEVICES=3 python3.5 main.py &
'''
from __future__ import print_function
import os
import argparse
from argparse import RawTextHelpFormatter
import sys
from erks.erks_bps.neuroner.src.neuroner import NeuroNER

import warnings
warnings.filterwarnings('ignore')

import datetime
from erks.utils.log_exception import log_exception
def parse_arguments(arguments=None):
    ''' Parse the NeuroNER arguments

    arguments:
        arguments the arguments, optionally given as argument
    '''
    parser = argparse.ArgumentParser(description='''NeuroNER CLI''', formatter_class=RawTextHelpFormatter)
    parser.add_argument('--parameters_filepath', required=False, default=os.path.join('.','parameters.ini'), help='The parameters file')

    argument_default_value = 'argument_default_dummy_value_please_ignore_d41d8cd98f00b204e9800998ecf8427e'
    parser.add_argument('--character_embedding_dimension', required=False, default=argument_default_value, help='')
    parser.add_argument('--character_lstm_hidden_state_dimension', required=False, default=argument_default_value, help='')
    parser.add_argument('--check_for_digits_replaced_with_zeros', required=False, default=argument_default_value, help='')
    parser.add_argument('--check_for_lowercase', required=False, default=argument_default_value, help='')
    parser.add_argument('--dataset_text_folder', required=False, default=argument_default_value, help='')
    parser.add_argument('--debug', required=False, default=argument_default_value, help='')
    parser.add_argument('--dropout_rate', required=False, default=argument_default_value, help='')
    parser.add_argument('--experiment_name', required=False, default=argument_default_value, help='')
    parser.add_argument('--freeze_token_embeddings', required=False, default=argument_default_value, help='')
    parser.add_argument('--gradient_clipping_value', required=False, default=argument_default_value, help='')
    parser.add_argument('--learning_rate', required=False, default=argument_default_value, help='')
    parser.add_argument('--load_only_pretrained_token_embeddings', required=False, default=argument_default_value, help='')
    parser.add_argument('--load_all_pretrained_token_embeddings', required=False, default=argument_default_value, help='')
    parser.add_argument('--main_evaluation_mode', required=False, default=argument_default_value, help='')
    parser.add_argument('--maximum_number_of_epochs', required=False, default=argument_default_value, help='')
    parser.add_argument('--number_of_cpu_threads', required=False, default=argument_default_value, help='')
    parser.add_argument('--number_of_gpus', required=False, default=argument_default_value, help='')
    parser.add_argument('--optimizer', required=False, default=argument_default_value, help='')
    parser.add_argument('--output_folder', required=False, default=argument_default_value, help='')
    parser.add_argument('--patience', required=False, default=argument_default_value, help='')
    parser.add_argument('--plot_format', required=False, default=argument_default_value, help='')
    parser.add_argument('--pretrained_model_folder', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_character_embeddings', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_character_lstm', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_crf', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_feedforward', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_token_embeddings', required=False, default=argument_default_value, help='')
    parser.add_argument('--reload_token_lstm', required=False, default=argument_default_value, help='')
    parser.add_argument('--remap_unknown_tokens_to_unk', required=False, default=argument_default_value, help='')
    parser.add_argument('--spacylanguage', required=False, default=argument_default_value, help='')
    parser.add_argument('--tagging_format', required=False, default=argument_default_value, help='')
    parser.add_argument('--token_embedding_dimension', required=False, default=argument_default_value, help='')
    parser.add_argument('--token_lstm_hidden_state_dimension', required=False, default=argument_default_value, help='')
    parser.add_argument('--token_pretrained_embedding_filepath', required=False, default=argument_default_value, help='')
    parser.add_argument('--tokenizer', required=False, default=argument_default_value, help='')
    parser.add_argument('--train_model', required=False, default=argument_default_value, help='')
    parser.add_argument('--use_character_lstm', required=False, default=argument_default_value, help='')
    parser.add_argument('--use_crf', required=False, default=argument_default_value, help='')
    parser.add_argument('--use_pretrained_model', required=False, default=argument_default_value, help='')
    parser.add_argument('--verbose', required=False, default=argument_default_value, help='')

    try:
        arguments = parser.parse_args(args=arguments)
    except:
        parser.print_help()
        sys.exit(0)

    arguments = vars(arguments) # http://stackoverflow.com/questions/16878315/what-is-the-right-way-to-treat-python-argparse-namespace-as-a-dictionary
    arguments['argument_default_value'] = argument_default_value
    return arguments

def run_neuroner_predict_standalone(argv=sys.argv):
    neuroner_home_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'erks/erks_bps/neuroner')
    dataset_text_folder = os.path.join(neuroner_home_dir, 'data/my_document2')
    pretrained_model_folder = os.path.join(neuroner_home_dir, 'trained_models/my_model')
    output_folder = os.path.join(neuroner_home_dir, 'output')
    argv.append('--train_model=False')
    argv.append('--use_pretrained_model=True')
    argv.append('--dataset_text_folder='+dataset_text_folder)
    argv.append('--pretrained_model_folder='+pretrained_model_folder)
    argv.append('--output_folder=' + output_folder)
    arguments = parse_arguments(argv[1:])
    nn = NeuroNER(**arguments)
    nn.fit()
    nn.close()


def run_neuroner_predict_erks(project_id, document):
    neuroner_home_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'erks/erks_bps/neuroner')
    pretrained_model_folder = os.path.join(neuroner_home_dir, 'trained_models/my_model_2')
    output_folder = os.path.join(neuroner_home_dir, 'output')
    dataset_text_folder = os.path.join(neuroner_home_dir, "data", project_id+"_"+datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    deploy_dir = os.path.join(dataset_text_folder, 'deploy')
    result = None
    try:
        os.makedirs(deploy_dir)
        with open(os.path.join(deploy_dir, "document1.txt"), 'w') as d:
            d.writelines(document)
        argv = []
        argv.append('--train_model=False')
        argv.append('--use_pretrained_model=True')
        argv.append('--dataset_text_folder=' + dataset_text_folder)
        argv.append('--pretrained_model_folder=' + pretrained_model_folder)
        argv.append('--output_folder=' + output_folder)
        arguments = parse_arguments(argv)
        nn = NeuroNER(**arguments)
        nn.fit()
        nn.close()
        result = nn.brat_entities

    except Exception as e:
        log_exception(e)

    return result

if __name__ == "__main__":
    run_neuroner_predict_standalone()


