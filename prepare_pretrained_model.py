from erks.erks_bps.neuroner.src.prepare_pretrained_model import prepare_pretrained_model_for_restoring

if __name__ == '__main__':
    output_folder_name = 'en_2017-11-04_17-02-33-840727'
    epoch_number = 3
    model_name = 'my_model'
    delete_token_mappings = False
    prepare_pretrained_model_for_restoring(output_folder_name, epoch_number, model_name, delete_token_mappings)