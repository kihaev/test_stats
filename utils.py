import pandas as pd


def add_data_to_db(
    csv_file_path="test_results.csv", connection="sqlite:///instance/app.db"
):
    with open(csv_file_path, "r") as file:
        data_df = pd.read_csv(file)
    data_df.to_sql(
        "test_result", con=connection, index=True, index_label="id", if_exists="append"
    )


if __name__ == "__main__":
    add_data_to_db()
