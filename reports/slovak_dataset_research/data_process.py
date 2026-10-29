from Classifiers.Ensemble_Autoencoder.Ensemble_Constants import RESULTS_DIRECTORY
import os
import pandas as pd

def process_results(experiment, sector, encoders=30):
    df_final_result = pd.DataFrame()
    results_path = RESULTS_DIRECTORY + '/' + sector
    loaded_encoders = 0;
    for index, filename in enumerate(os.listdir(results_path)):

        if(loaded_encoders==encoders):
            break
        if not filename.startswith(experiment):
            continue
        if "AGGREGATED" in filename:
            continue
        print(filename)
        loaded_encoders = loaded_encoders + 1


        filename_splits = filename.split('_')
        thread_id = (filename_splits[len(filename_splits) - 2])
        file_path = results_path + '/' + filename
        #df_result = pd.read_csv(file_path, header=None, index_col=0)
        df_result = pd.read_csv(file_path,  index_col=0)

        df_result.columns = ['sector', 'year', 'run', 'true_class', 'reconstruction_error_' + str(thread_id),'mean_absolute_error'+ str(thread_id),'root_mean_squared_error'+ str(thread_id), 'epochs', 'thread_id']


        if df_final_result.empty:
            df_final_result = df_result[['sector', 'year', 'run', 'true_class', 'epochs', 'thread_id', 'reconstruction_error_' + str(thread_id)]]
        else:
            df_final_result['reconstruction_error_' + str(thread_id)] = df_result['reconstruction_error_' + str(thread_id)]


    #df_final_result['reconstruction_error_mean'] = df_final_result.iloc[:, 6:].mean(axis=1)
    median = df_final_result.iloc[:, 6:].median(axis=1)
    mean = df_final_result.iloc[:, 6:].mean(axis=1)
    df_final_result["reconstruction_error_median"] = median
    df_final_result["reconstruction_error_mean"] = mean
    #df_final_result['reconstruction_error_median'] = df_final_result.iloc[:, 5:].median(axis=1)
    #print(type(df_final_result.iloc[:, 6:].values[0][0]))

    #print(df_final_result.iloc[:, 6:].values)
    #print(np.array(df_final_result.iloc[:, 6:].values).astype(np.float).mean(axis=1))
    #df_final_result = df_final_result[[ 'sector', 'year', 'run', 'true_class', 'reconstruction_error_mean','', 'epochs', 'thread_id']]
    output_filename = "{}/{}/{}_ENCODERS_{:0>2}_AGGREGATED_RESULTS.CSV".format(RESULTS_DIRECTORY, sector, experiment,encoders)
    df_final_result.to_csv(output_filename,header=True)
    print(df_final_result)
    return
