from model_package import ModelPackage
import pandas as pd
import os

class ModelPackageManager():
    def __init__(self, info_csv_path="model_info.csv"):
        self.model_packages = []

        # Load model packages from the CSV file if it exists
        if os.path.exists(info_csv_path):
            df = pd.read_csv(info_csv_path)
            for _, row in df.iterrows():
                model_package = ModelPackage(
                    name=row['name'],
                    params_string=row['params'],
                    data_version=row['data_version']
                )
                self.model_packages.append(model_package)
        else:
            print(f"No model info CSV found at {info_csv_path}. Starting with an empty ModelPackageManager.")

    def __repr__(self):
        return_string = f"ModelPackageManager(model_packages=[\n"
        for model_package in self.model_packages:
            return_string += f"  {model_package},\n"
        return_string += "])"
        return return_string
    
    def combined_stats_for_date_range(self, start_month=None, start_year=None, end_month=None, end_year=None):
        combined_stats = {}
        for model_package in self.model_packages:
            stats = model_package.get_stats_for_date_range(start_month, start_year, end_month, end_year)
            combined_stats[model_package.name] = stats
        return combined_stats


if __name__ == "__main__":
    manager = ModelPackageManager()
    #combined_stats = manager.combined_stats_for_date_range(start_month=6, start_year=2026)
    #print(combined_stats)
    print(manager)