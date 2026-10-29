import random
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
import Classifiers.Ensemble_Autoencoder.Ensemble_Constants as ec
#from Classifiers.Ensemble_Autoencoder.Ensemble_Plot_Functions import plot_gemetric_means
import tensorflow as tf
#import matplotlib.pyplot as plt
#from sklearn.metrics import mean_squared_error

'''
def load_experiment_files_list(experiment_data):
    df_data_to_process = pd.read_csv(ec.PREPARED_DATA_DIRECTORY + '/' + experiment_data, header=None, index_col=0)
    df_data_to_process.columns = ['sector', 'year', 'run', 'processed']
    return df_data_to_process
'''


def learn_and_predict(autoencoder, df, sector, year, run, column_indexes, nb_epoch=300,
                      scaler=MinMaxScaler(feature_range=(0, 1)),optimize_lr=False,threadId = 0):
    imputer = SimpleImputer()
    df_train = df[df['TYPE'] == 'TRAIN']
    df_test = df[df['TYPE'] == 'TEST']
    df_valid = df[df['TYPE'] == 'VALID']
    true_class = df[df['TYPE'] == 'TEST']['IS_BANKRUPT'].copy()
    #mean_nonbankrupt = df_train.mean()

    columns_to_drop = ['Seq_Number', 'IS_BANKRUPT', 'TYPE', 'RUN']

    df_train = df_train.drop(columns_to_drop, axis=1)
    df_test = df_test.drop(columns_to_drop, axis=1)
    df_valid = df_valid.drop(columns_to_drop, axis=1)

    #df_train.fillna(mean_nonbankrupt, inplace=True)
    #df_test.fillna(mean_nonbankrupt, inplace=True)
    #df_valid.fillna(mean_nonbankrupt, inplace=True)

    df_train = imputer.fit_transform(df_train)
    df_test = imputer.transform(df_test)
    df_valid = imputer.transform(df_valid)

    df_train_scaled = pd.DataFrame(scaler.fit_transform(df_train))
    df_test_scaled = pd.DataFrame(scaler.transform(df_test))
    df_valid_scaled = pd.DataFrame(scaler.transform(df_valid))

    df_train_scaled = df_train_scaled.iloc[:, column_indexes]
    df_test_scaled = df_test_scaled.iloc[:, column_indexes]
    df_valid_scaled = df_valid_scaled.iloc[:, column_indexes]

    #print(df_train_scaled)
    #print(df_train_scaled.columns)

    #df_test_scaled[df_test_scaled > 1] = 1
    #df_test_scaled[df_test_scaled < -1] = -1
    #df_valid_scaled[df_valid_scaled > 1] = 1
    #df_valid_scaled[df_valid_scaled < -1] = -1

    lr_schedule=[]
    if(optimize_lr):
        lr_schedule = [tf.keras.callbacks.LearningRateScheduler(
        lambda epoch: 1e-8 * 10 ** (epoch / 20))]

    history = autoencoder.fit(df_train_scaled, df_train_scaled,
                              epochs=nb_epoch,
                              batch_size=10000,
                              shuffle=True,
                              validation_data=(df_valid_scaled, df_valid_scaled),
                              verbose=0).history

    #plt.plot(history['loss'], linewidth=2, label='Train')
    #plt.plot(history['val_loss'], linewidth=2, label='Valid')
    #plt.legend(loc='upper right')
    #plt.title('Model loss')
    #plt.ylabel('Loss')
    #plt.xlabel('Epoch')
    #plt.savefig("Results/Plots/Model_Loss_{}_{}_Run_{}_Thread_{}.png".format(sector, year, run,threadId), dpi=199)
    #plt.close()

    #plt.semilogx(history["lr"], history["loss"])
    #plt.axis([1e-8, 1e-4, 0, 30])

    test_predictions = autoencoder.predict(df_test_scaled)
    #valid_predictions = autoencoder.predict(df_valid_scaled)
    #train_predictions = autoencoder.predict(df_train_scaled)

    #mse_valid = np.mean(np.power(df_valid_scaled - valid_predictions, 2), axis=1)
    #mse_train = np.mean(np.power(df_train_scaled - train_predictions, 2), axis=1)

    #print(df_test_scaled.values[0,:])
    #print(test_predictions[0,:])
    mse = np.mean(np.power(df_test_scaled - test_predictions, 2), axis=1)
    msa = np.mean((np.abs(df_test_scaled - test_predictions)), axis=1)

    rmse = np.sqrt(mse)

    df_result = pd.DataFrame({
        'sector': sector,
        'year': year,
        'run': run,
        'true_class': true_class.values,
        'reconstruction_error': mse,
        'mean_absolute_error':msa,
        'root_mean_squared_error':rmse,
        'epochs': nb_epoch
        # 'max_reconstruction_error_valid': np.max(mse_valid),
        # 'min_reconstruction_error_valid': np.min(mse_valid),
        # 'mean_reconstruction_error_valid': np.mean(mse_valid),
        # 'median_reconstruction_error_valid': np.median(mse_valid),
        # 'max_reconstruction_error_train': np.max(mse_train),
        # 'min_reconstruction_error_train': np.min(mse_train),
        # 'mean_reconstruction_error_train': np.mean(mse_train),
        # 'median_reconstruction_error_train': np.median(mse_train)
    })

    history['sector'] = sector
    history['year'] = year
    history['run'] = run

    dict_result = {
        "predictions": df_result,
        "history": history #,
        #"lr":history["lr"],
        #"loss":history["loss"]
    }

    return dict_result


def run_model_experiment(model_create_function, experiment_name, run_count, column_indexes, thread_id, sector, epochs=300,
                         scaler=MinMaxScaler(feature_range=(-1, 1)), optimize_lr=False):

    columns_file_name = "{}/{}/COLUMNS_{}_{}_ENCODER_{:0>2}.csv".format(ec.RESULTS_DIRECTORY, sector,len(column_indexes), experiment_name,
                                                                   thread_id)
    np.asarray(column_indexes).astype(int)
    #np.savetxt(columns_file_name, np.asarray(column_indexes).T.astype(int), fmt='%i', delimiter=",")
    for run in range(1,run_count+1):
        for year in [13,14,15,16]:
            #opt = tf.keras.optimizers.Adam(learning_rate=1e-5)
            opt = tf.keras.optimizers.Adam(learning_rate=1e-2)
            model = model_create_function(input_dim=len(column_indexes))
            model.compile(metrics=['accuracy'], loss='mean_squared_error', optimizer=opt)

            data_filename = '{}_{}_{}.csv'.format(sector, year, run)

            print("{} PROCESSING: {}".format(thread_id, data_filename))

            df_file = pd.read_csv(ec.PREPARED_DATA_DIRECTORY + "/" + data_filename)
            run_result = learn_and_predict(model, df_file, sector, year, run, column_indexes, epochs,
                                           scaler=scaler,optimize_lr=optimize_lr,threadId=thread_id)
            result_file_name = "{}/{}/{}_ENCODER_{:0>2}_RESULT.csv".format(ec.RESULTS_DIRECTORY, sector, experiment_name,thread_id)
            print("{} PROCESSING FINISHED: {}".format(thread_id, data_filename))
            df_predictions = run_result['predictions']
            df_predictions['ThreadId'] = thread_id

            pd.DataFrame(df_predictions).to_csv(result_file_name, mode='a', header=False)
    return


def get_column_indexes(autoencoders_count, columns_count, from_columns_count = 60):
    # indexes = np.random.random_integers(0, 60, size=(autoencoders_count, columns_count))
    indexes = []
    for i in range(autoencoders_count):
        ind = random.sample(range(from_columns_count), columns_count)
        # print(type(ind))
        # ind =ind.sort()
        # print(type(ind))
        #ind.sort()
        # print(ind)
        indexes.append(ind)
    return indexes

def get_column_indexes_with_skip(autoencoders_count, columns_count, skip):
    # indexes = np.random.random_integers(0, 60, size=(autoencoders_count, columns_count))
    indexes = []
    for i in range(autoencoders_count):
        ind = random.sample(range(skip, 60), columns_count)
        # print(type(ind))
        # ind =ind.sort()
        # print(type(ind))
        #ind.sort()
        # print(ind)
        indexes.append(ind)
    return indexes

#def get_column_index_for_last_n_years(autoencoders_count, columns_count, from_columns_count = 60)


def get_column_index_by_years(autoencoders_count, columns_count, from_columns_count = 60):
    indexes = []
    for i in range(autoencoders_count):
        if i == 0:
            indexes.append(list(np.arange(0,columns_count)))
        else:
            indexes.append(list(np.arange(20 * i , 20 * i  + columns_count )))
    return indexes


def create_models(model_method, number_of_models, input_dim):
    model_filenames = []
    for i in range(0, number_of_models):
        model = model_method(input_dim = input_dim)
        model.compile(metrics=['accuracy'], loss='mean_squared_error', optimizer='adam')
        model_filename = 'model_{}.h5'.format(str(i))
        model.save_weights(ec.TEMP_DIRECTORY + '/' + model_filename)
        model_filenames.append(model_filename)
    return model_filenames
