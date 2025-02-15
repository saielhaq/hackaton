import pandas as pd
import datetime as dt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

# Load the CSV file containing anomalies
df = pd.read_csv(r'.\data\data.csv')
# Current date and time
now = dt.datetime.now()
# Email configuration
my_mail = 'bidrissikandri@gmail.com'
password = 'sxfrjxijasuldwgo'
receiver = 'badr.kandri.10@gmail.com'
# SMTP connection setup
connection = smtplib.SMTP('smtp.gmail.com', 587)
connection.starttls()  # Secure the connection
connection.login(user=my_mail, password=password)

# Filter anomalies that occurred today and are classified as "anomalous"
today = now.date()
df['timestamp'] = pd.to_datetime(df['timestamp'])  # Convert timestamp to datetime
anomalies_today = df[(df['timestamp'].dt.date == today) & (df['classification'] == 'anomalous')]
if not anomalies_today.empty:
    # Extract unique anomalous IP addresses
    anomalous_ips = anomalies_today['source_ip'].unique()
    # Block each anomalous IP using Windows Firewall (netsh)
    for ip in anomalous_ips:
        try:
            # Add a rule to block the IP using netsh, suppressing stderr
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', 'name=Block_IP_' + ip, 'dir=in', 'action=block', 'remoteip=' + ip],check=False,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Ignore all exceptions silently
            pass
    # Generate the email content (without blocked IPs)
    email_body = f"Today's Anomaly Report ({now.strftime('%Y-%m-%d')}):\n\n"
    for _, row in anomalies_today.iterrows():
        email_body += (
            f"Time: {row['timestamp'].strftime('%H:%M:%S')}\n"
            f"Source IP: {row['source_ip']}\n"
            f"Connection Attempts: {row['connection_attempts']}\n"
            "---------------------------------------------\n")
    # Add a message directing the user to the RedGuard Dashboard
    email_body += "\nFor more details about the blocked IP addresses, please visit the RedGuard Dashboard : http://192.168.11.190:8502"
    # Create a MIME message
    msg = MIMEMultipart()
    msg['From'] = my_mail
    msg['To'] = receiver
    msg['Subject'] = 'Daily Anomaly Report - Detected Security Threats'
    # Attach the email body
    msg.attach(MIMEText(email_body, 'plain'))
    # Send the email
    connection.sendmail(from_addr=my_mail, to_addrs=receiver, msg=msg.as_string())
    print(f"Report email is sent to: {receiver}")
else:
    print("No anomalous activities detected today. No IPs blocked.")
# Close the SMTP connection
connection.quit() 

subprocess.run(["python", r"src\dashboard.py"]) 
