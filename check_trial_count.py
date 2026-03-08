"""
Quick script to check trial count in Aurora database
"""
import json
import boto3
import psycopg2

# Get database credentials from Secrets Manager
secrets_client = boto3.client('secretsmanager')
secret_response = secrets_client.get_secret_value(
    SecretId='arn:aws:secretsmanager:us-east-1:835703987264:secret:dev/vitalmatch/db-credentials-2pMZqF'
)
secret = json.loads(secret_response['SecretString'])

# Database connection parameters
db_params = {
    'host': 'dev-vitalmatch-aurora-v2.cluster-cibaikqmyoag.us-east-1.rds.amazonaws.com',
    'database': 'trials_db',
    'user': secret['username'],
    'password': secret['password'],
    'port': 5432,
    'connect_timeout': 10,
    'sslmode': 'require'
}

# Connect and query
print("Connecting to Aurora...")
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM trials")
total_count = cursor.fetchone()[0]
print(f"\nTotal trials in database: {total_count}")

# Get sample of recent trials
cursor.execute("""
    SELECT id, title, condition, created_date, updated_date 
    FROM trials 
    ORDER BY created_date DESC 
    LIMIT 5
""")
print("\nSample of 5 most recent trials:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"Title: {row[1][:60]}...")
    print(f"Condition: {row[2]}")
    print(f"Created: {row[3]}, Updated: {row[4]}")
    print("-" * 80)

# Get count by date
cursor.execute("""
    SELECT DATE(created_date) as date, COUNT(*) as count
    FROM trials
    GROUP BY DATE(created_date)
    ORDER BY date DESC
    LIMIT 7
""")
print("\nTrials by creation date (last 7 days):")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} trials")

cursor.close()
conn.close()
print("\nDone!")
