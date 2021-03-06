import os
import shutil
import subprocess
import torch

def main():
    # Output directory for all the models after successful training
    output_dir = 'result/caltech_cameratrap2'
    # Parameters shared across all runs
    shared_params = ['--data_root', '/data/lila/caltech/batch_cropped_dataset/',
                     '--train_file', 'train.json',
                     '--val_file', 'test.json',
                     '--label_smoothing', '0']
    # Name tags for the different models that we will train
    tags = []
    # The run specific parameters, should correspond to the order in TAGS
    params = []

    ### Preparing the training configurations
    # For each model training, we define a tag and the parameters
    tags.append('resnext_224')
    params.append(['--model_type', 'resnext101',
                '--image_size', '224',
                '--epochs', '10000',
                '--epoch_decay', '20',
                '--warm_up_iterations', '1000',
                '--lr_decay', '0.1',
                '--lr', '0.01',
                '--batch_size', '16'])

    tags.append('resnext_448')
    params.append(['--model_type', 'resnext101',
                '--image_size', '448',
                '--epochs', '10000',
                '--epoch_decay', '20',
                '--start_epoch', '0',
                '--warm_up_iterations', '1000',
                '--lr_decay', '0.1',
                '--lr', '0.001',
                '--batch_size', '16',
                '--resume', get_best_model_path(output_dir, 'resnext_224')])


    # Checking if everything is set up properly
    assert len(tags) == len(params)

    ### The actual training
    for tag, param in zip(tags, params):
        print('Starting training of', tag)
        result_dir = get_result_dir(output_dir, tag)
        model_best = get_best_model_path(output_dir, tag)
        if os.path.isfile(model_best):
            print('Found existing trained model at {}, skipping the training of {}'.format(model_best, tag))
        else:
            # Check for checkpoint
            checkpoint_file = 'checkpoint.pth.tar'
            if os.path.isfile(checkpoint_file):
                resume_param = ['--resume', checkpoint_file]
            else:
                resume_param = []
            subprocess.run(['python', 
                             '-m', 'torch.distributed.launch', 
                             '--nproc_per_node={}'.format(torch.cuda.device_count()),
                             'train.py']
                           + param + shared_params + resume_param, check=True)
            assert os.path.isfile('model_best.pth.tar'), 'ERROR: The training did not produce model_best.pth.tar, ' + \
                                                         'You might need to adjust learning parameters.'
            print('Seems training finished, moving trained models and log directory to', result_dir)
            os.makedirs(result_dir, exist_ok=True)
            shutil.move('model_best.pth.tar', result_dir)
            shutil.move('checkpoint.pth.tar', result_dir)
            shutil.move('log', result_dir)


def get_result_dir(output_dir, tag):
    ''' Returns the directory, where we will store all models and logs after successful training '''
    return os.path.join(output_dir, tag)

def get_best_model_path(output_dir, tag):
    ''' Returns the path, where we will store the best model after successful training '''
    return os.path.join(get_result_dir(output_dir, tag), 'model_best.pth.tar')

if __name__ == '__main__':
    main()
