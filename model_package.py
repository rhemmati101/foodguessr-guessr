import pandas as pd

class ModelPackage():
    def __init__(self, name, params_string, data_version, path):
        self.name = name
        self.params_string = params_string
        self.data_version = data_version
        self.path = path

    def get_model_info(self):
        return {
            "name": self.name,
            "data_version": self.data_version,  ### what month and year the model's data goes up to
            "path": self.path,
            "params": self.params_string
        }
    
    # no idea if this works yet
    def get_accuracy(self, month, year):
        model_results = pd.read_csv(self.path + "/model_results.csv")
        model_results = model_results[model_results['date'].str.startswith(str(month))]
        model_results = model_results[model_results['date'].str.endswith(str(year))]

        if model_results.empty:
            return None
        
        return model_results['first_try_guesses'].mean() / 3
    
    # run model on data from after data version up until current date, add results to a corresponding csv file
    def update_model_scores(self, replace=False):
        pass