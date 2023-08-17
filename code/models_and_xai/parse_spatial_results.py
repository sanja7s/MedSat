import re, os
import pandas as pd


input_results_folder = "../../results/models/spatialRegression/"
output_results_folder = input_results_folder + "variable_importance/"

def parse_spatial_regression(output):
    # Splitting the output into lines
    lines = output.split("\n")
    
    # Find the start of the table
    for idx, line in enumerate(lines):
        if "Variable" in line and "Coefficient" in line:
            start_idx = idx + 1
            break
    
    # Collecting and parsing the table data
    data = []
    for line in lines[start_idx:]:
        # Stop if we reach a line without data or the eof report
        if not line.strip() or 'END OF REPORT' in line:
            break

        if "---------" in line:
            continue
        
        # Split the line into its components
        parts = line.split()
        variable = ' '.join(parts[:-4])  # Variables can have spaces, so we join all parts except the last 4
        coefficient, std_error, z_statistic, probability = map(float, parts[-4:])

        print (variable, coefficient, std_error, z_statistic, probability)
        
        # Append to the data
        data.append({
            "Variable": variable,
            "Coefficient": coefficient,
            "Std.Error": std_error,
            "z-Statistic": z_statistic,
            "Probability": probability
        })
    
    return data


def read_file(file_path):
    """Read a file and return its content."""
    with open(file_path, 'r') as file:
        return file.read()


def main():
    directory_path = input_results_folder  # Replace this with the path to your directory
    files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]

    for file in files:
        file_path = os.path.join(directory_path, file)
        data = read_file(file_path)

        # Parse the data
        parsed_data = parse_spatial_regression(data)

        df_output = pd.DataFrame(parsed_data)
        df_output = df_output.sort_values(by=['Probability'])

        # print (df_output)
        output_file_name = file.replace(".txt", "_variable_importance.csv")
        output_file_path = os.path.join(output_results_folder, output_file_name)
        df_output.to_csv(output_file_path)


if __name__ == "__main__":
    main()
