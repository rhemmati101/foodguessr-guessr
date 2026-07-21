import os
import pandas as pd

class ModelPackage():
    def __init__(self, name, params_string, data_version):
        self.name = name
        self.params_string = params_string
        self.data_version = data_version

    def get_model_info(self):
        return {
            "name": self.name,
            "data_version": self.data_version,  ### what month and year the model's data goes up to
            "params": self.params_string
        }
    
    # get statistics of model on data from a given month and year
    def get_stats_for_month(self, month, year):
        pass
    
    # get statistics of model on data from a given month and year range
    def get_stats_for_date_range(self, start_month, start_year, end_month=None, end_year=None):
        pass

    # run model on data from after data version up until current date, add results to a corresponding csv file
    # if replace is False, keep existing results in the csv file and append new results
    def update_model_scores(self, replace=False):
        pass

    # save model info to a csv file
    def export_to_csv(self, file_path="model_info.csv"):
        model_info = self.get_model_info()
        df = pd.DataFrame([model_info])
        df.to_csv(
            file_path,
            index=False,
            mode='a' if os.path.exists(file_path) else 'w',
            header=not os.path.exists(file_path)
        )