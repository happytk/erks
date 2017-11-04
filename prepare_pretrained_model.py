'''
This script prepares a pretrained model to be shared without exposing the data used for training.
'''

from erks.erks_bps.neuroner.src.prepare_pretrained_model import prepare_pretrained_model_for_restoring


if __name__ == '__main__':
    output_folder_name = 'en_2017-11-04_17-02-33-840727'
    epoch_number = 3
    model_name = 'my_model'
    delete_token_mappings = False
    prepare_pretrained_model_for_restoring(output_folder_name, epoch_number, model_name, delete_token_mappings)
    
#     model_name = 'mimic_glove_spacy_iobes'
#     model_folder = os.path.join('..', 'trained_models', model_name)
#     check_contents_of_dataset_and_model_checkpoint(model_folder)