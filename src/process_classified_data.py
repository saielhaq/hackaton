import pandas as pd 
import subprocess

def process_csv(input_file, output_file):
    # Read the input CSV file into a DataFrame
    df = pd.read_csv(input_file)
    # Group by 'source_ip' and count the number of connection attempts for each unique source IP
    connection_attempts = df.groupby('source_ip').size().reset_index(name='connection_attempts')

    # Merge the original DataFrame with the connection_attempts DataFrame to add the 'connection_attempts' column
    result_df = df[['timestamp', 'source_ip', 'classification']].copy()
    result_df = result_df.drop_duplicates(subset=['source_ip'])  # Ensure no duplicate source IPs
    result_df = result_df.merge(connection_attempts, on='source_ip', how='left')

    # Save the resulting DataFrame to the output CSV file
    result_df.to_csv(output_file, index=False)

    print(f"Processed data has been saved to {output_file}")

# Example usage
input_csv = r'.\data\classified_dataset.csv'
output_csv = r'.\data\data.csv'

process_csv(input_csv, output_csv) 

subprocess.run(["python", r"src\alerts.py"]) 
 