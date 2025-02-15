from config import get_api_key
from openai import OpenAI
import pandas as pd
import subprocess

# Load the API key
api_key = get_api_key()
client = OpenAI(api_key=api_key)

# Define paths
clean_data_path = r".\data\clean_network_traffic.csv"  # Path to clean data
anomalies_data_path = r".\data\anomalies_data.csv"  # Path to anomalies data
mixed_data_path = r".\data\mixed_network_traffic.csv"  # Path to mixed data
output_csv_path = r".\data\classified_dataset.csv"   # Path to save classified data

# Load clean data (comma-separated)
clean_data = pd.read_csv(clean_data_path)

# Load anomalies data (semicolon-separated) 
anomalies_data = pd.read_csv(anomalies_data_path)

# Load mixed data (semicolon-separated)
mixed_data = pd.read_csv(mixed_data_path)

# Standardize column names
clean_data.columns = ["timestamp", "source_ip", "destination_ip", "protocol", "bytes_sent", "bytes_received"]
anomalies_data.columns = ["timestamp", "source_ip", "destination_ip", "protocol", "bytes_sent", "bytes_received"]
mixed_data.columns = ["timestamp", "source_ip", "destination_ip", "protocol", "bytes_sent", "bytes_received"]

# Validate column names
required_columns = ["timestamp", "source_ip", "destination_ip", "protocol", "bytes_sent", "bytes_received"]
if not all(col in clean_data.columns for col in required_columns):
    raise ValueError("Clean data is missing required columns.")
if not all(col in anomalies_data.columns for col in required_columns):
    raise ValueError("Anomalies data is missing required columns.")
if not all(col in mixed_data.columns for col in required_columns):
    raise ValueError("Mixed data is missing required columns.")

# Extract examples of clean data and anomalies data
clean_examples = clean_data.head(5)  # Take the first 5 rows as examples of clean data
anomaly_examples = anomalies_data.head(5)  # Take the first 5 rows as examples of anomalies data

# Create a function to train the LLM on clean and anomaly data
def train_llm_on_data():
    # Create a prompt with examples of clean data
    prompt = """
    Here are examples of CLEAN network traffic data (normal behavior):
    """
    for _, row in clean_examples.iterrows():
        prompt += f"- timestamp: {row['timestamp']}, source_ip: {row['source_ip']}, destination_ip: {row['destination_ip']}, protocol: {row['protocol']}, bytes_sent: {row['bytes_sent']}, bytes_received: {row['bytes_received']} -> normal\n"
    
    # Add examples of anomalies data
    prompt += """
    Here are examples of ANOMALOUS network traffic data (abnormal behavior):
    """
    for _, row in anomaly_examples.iterrows():
        prompt += f"- timestamp: {row['timestamp']}, source_ip: {row['source_ip']}, destination_ip: {row['destination_ip']}, protocol: {row['protocol']}, bytes_sent: {row['bytes_sent']}, bytes_received: {row['bytes_received']} -> anomalous\n"
    
    # Add detailed instructions for classification
    prompt += """ (Very IMPORTANT)
    Classification Rules:
    ---------------------
    1. A user trying to log in more than 3 times (i.e., the same `source_ip` appears more than 3 times in the dataset) is automatically classified as an anomaly, regardless of the number of bytes sent or received , each row of this user with the same source_ip well have the class anomalous
    2. If the `bytes_sent` value exceeds 20, the traffic is automatically classified as an anomaly.
    3. If the `source_ip` does not follow the format `192.168.xx.xx`, it is classified as an anomaly.
    4. All other traffic is considered normal unless it violates one of the above rules.

    Remember:
    - Normal traffic typically has fewer login attempts and does not exceed 20 bytes sent.
    - Anomalous traffic may have multiple login attempts in a short period, exceed 20 bytes sent, or have an invalid source IP format.
    """
    return prompt

# Train the LLM
training_prompt = train_llm_on_data()

# Create a function to classify mixed traffic in batches
def classify_traffic_batch(rows):
    # Combine the training prompt with the batch of mixed data to classify
    prompt = training_prompt + """
    Classify the following network traffic as "normal" or "anomalous". Output each classification on a new line in the format:
    - <classification>
    For example:
    - normal
    - anomalous
    Traffic to classify:
    """
    for _, row in rows.iterrows():
        prompt += f"\n- timestamp: {row['timestamp']}, source_ip: {row['source_ip']}, destination_ip: {row['destination_ip']}, protocol: {row['protocol']}, bytes_sent: {row['bytes_sent']}, bytes_received: {row['bytes_received']}"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Process mixed data in batches
# Process mixed data in batches
batch_size = 10
mixed_data["classification"] = None  # Initialize classification column
for i in range(0, len(mixed_data), batch_size):
    batch = mixed_data.iloc[i:i + batch_size]
    classifications = classify_traffic_batch(batch)
    
    # Parse the LLM's response into individual classifications
    classification_list = classifications.split("\n")
    classification_list = [cls.strip("- ").lower() for cls in classification_list if cls.strip()]  # Clean up responses
    
    # Ensure only "normal" or "anomalous" classifications are allowed
    classification_list = [
        cls if cls in ["normal", "anomalous"] else "anomalous"  # Default to "anomalous" if invalid
        for cls in classification_list
    ]
    
    # Assign classifications to the DataFrame
    mixed_data.loc[i:i + batch_size - 1, "classification"] = classification_list[:len(batch)]

# Save the classified data to a new CSV file
mixed_data.to_csv(output_csv_path, index=False)
print(f"Classified mixed data saved to {output_csv_path}") 

subprocess.run(["python", r"src\process_classified_data.py"])  