import multiprocessing
from random import seed

import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

from Classifiers.Ensemble_Autoencoder.Ensemble_Data_Process import process_results
from Classifiers.Ensemble_Autoencoder.Ensemble_Functions import create_models, run_model_experiment, \
    get_column_indexes_with_skip
from Classifiers.Ensemble_Autoencoder.Ensemble_Models import create_ensemble_autoencoder_model_1_dynamic

seed(2)
np.random.seed(2)
tf.random.set_seed(2)  # set_random_seed(2)
EPOCHS = 100


def run_experiment(args):
    model_create_function = args[0]
    model_filename = args[1]
    column_indexes = args[2]
    experiment_name = args[3]
    run_count = args[4]
    index = args[5]
    sector = args[6]
    optimize_lr = args[7]
    run_model_experiment(
        model_create_function,
        experiment_name,
        run_count,
        column_indexes,
        index + 1,
        sector,
        scaler=StandardScaler(),
        epochs=EPOCHS,
        optimize_lr=optimize_lr)
    return


def create_args_list(model_create_function, models, column_indexes, experiment_name, run_count, sector, optimize_lr):
    args = []
    for index, model in enumerate(models):
        args.append((
            model_create_function,
            model,
            column_indexes[index],
            experiment_name,
            run_count,
            index,
            sector,
            optimize_lr))
    return args


def run_ensemble(
        model_create_function,
        number_of_ensembles,
        experiment_name,
        run_count,
        sector,
        index_selection_method,
        number_of_features=60,
        number_of_processes=5,
        from_columns_count=60,
        optimize_lr=False):
    models = create_models(model_create_function, number_of_ensembles, number_of_features)
    column_indexes = index_selection_method(number_of_ensembles, number_of_features, from_columns_count)
    data_pairs = create_args_list(model_create_function, models, column_indexes,
                                  experiment_name, run_count, sector, optimize_lr)
    if __name__ == '__main__':
        pool = multiprocessing.Pool(processes=number_of_processes)
        pool.map(run_experiment, data_pairs)
    return


# index_selection_method = get_column_index_by_years


RUN_COUNT = 20
if __name__ == '__main__':
    index_selection_method = get_column_indexes_with_skip
    for SECTOR in ['AGRICULTURE']:
        for ENCODERS, FROM_COLUMNS_COUNT, YEARS in [
            (100, 0, 'Y-3_AND_Y-2_AND_Y-1'),
            (66, 20, 'Y-2_AND_Y-1'),
            (33, 40, 'Y-1')]:
            NUMBER_OF_FEATURES = 8
            EXPERIMENT_NAME = '{}_01_ENCODERS_{:0>2}_EPOCHS_{}_LR_0.01_FEATURES_{:0>2}_RUNS_{:0>2}_STANDARD_{}' \
                .format(SECTOR, ENCODERS, EPOCHS, NUMBER_OF_FEATURES, RUN_COUNT, YEARS)
            run_ensemble(
                create_ensemble_autoencoder_model_1_dynamic,
                ENCODERS,
                EXPERIMENT_NAME,
                RUN_COUNT,
                SECTOR,
                number_of_processes=16,
                index_selection_method=index_selection_method,
                number_of_features=NUMBER_OF_FEATURES,
                from_columns_count=FROM_COLUMNS_COUNT,
                optimize_lr=False)
            process_results(EXPERIMENT_NAME, SECTOR, ENCODERS)
