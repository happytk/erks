from erks.erks_bps.neuroner.src.prepare_pretrained_model import prepare_pretrained_model_for_restoring

if __name__ == '__main__':
    output_folder_name = 'en_2017-11-05_01-37-12-592712'
    epoch_number = 51
    model_name = 'my_model_2'
    delete_token_mappings = False
    prepare_pretrained_model_for_restoring(output_folder_name, epoch_number, model_name, delete_token_mappings)