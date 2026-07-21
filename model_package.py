import os
import pandas as pd
from datetime import datetime, timedelta

class ModelPackage():
    def __init__(self, name, params_string, data_version):
        self.name = name
        self.params_string = params_string
        self.data_version = data_version

    def get_model_info(self):
        return {
            "name": self.name,
            "data_version": self.data_version,
            "params": self.params_string
        }

    def __repr__(self):
        return f"ModelPackage(name={self.name}, data_version={self.data_version}, params_string={self.params_string})"
    
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

    # run model on data from after data version up until current date, add results to a corresponding csv file
    # if replace is False, keep existing results in the csv file and append new results
    def update_model_scores(self, replace=False, model_scores_dir_path="model_scores"):
        save_path = os.path.join(model_scores_dir_path, f"{self.name}_scores.csv")
        if replace or not os.path.exists(save_path):
            # Create a new DataFrame with the scores for the model
            scores_df = pd.DataFrame(columns=["date", "first_try_guesses", "scores", "border_scores", "geodist_scores", "geoall_scores"])
        else:
            # Load existing scores from the CSV file
            scores_df = pd.read_csv(save_path)

        # run the models or something, idk?


    def get_stats_for_date_range(self, start_month=None, start_year=None, end_month=None, end_year=None):
        month_after_training_date = datetime.strptime(self.data_version, "%m_%Y")
        start_date = datetime(start_year, start_month, 1) if start_month and start_year else month_after_training_date
        end_date = datetime(end_year, end_month, 1) if end_month and end_year else datetime.now() + timedelta(days=1)

        if start_date < month_after_training_date:
            raise ValueError(f"Start month {start_date.strftime('%m_%Y')} is before (included in) the model's training data version {self.data_version}")

        model_scores_file_path = os.path.join("model_scores", f"{self.name}_scores.csv")
        scores_df = pd.read_csv(model_scores_file_path)
        scores_df["date"] = pd.to_datetime(scores_df["date"])
        filtered_scores_df = scores_df[(scores_df['date'] >= start_date) & (scores_df['date'] < end_date)]

        if filtered_scores_df.empty:
            raise ValueError(f"No scores found for model {self.name} in the date range {start_date.strftime('%m_%Y')} to {end_date.strftime('%m_%Y')}")

        stats = {
            "accuracy": filtered_scores_df['first_try_guesses'].mean() / 3,
            "avg_score_nongeo": filtered_scores_df['scores'].mean(),
            "avg_score_borders": filtered_scores_df['border_scores'].mean(),
            "avg_score_dist": filtered_scores_df['geodist_scores'].mean(),
            "avg_score_allgeo": filtered_scores_df['geoall_scores'].mean()
        }

        return stats


if __name__ == "__main__":
    model_package = ModelPackage(name="rf_05_2026", params_string="I forgor", data_version="05_2026")
    print(model_package.get_stats_for_date_range())
    model_package.export_to_csv()
    