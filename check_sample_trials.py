import json
import boto3
import psycopg2

# Get credentials
secrets_client = boto3.client('secretsmanager')
secret = json.loads(secrets_client.get_secret_value(
    SecretId='arn:aws:secretsmanager:us-east-1:835703987264:secret:dev/vitalmatch/db-credentials-2pMZqF'
)['SecretString'])

# Connect
conn = psycopg2.connect(
    host='dev-vitalmatch-aurora-v2.cluster-cibaikqmyoag.us-east-1.rds.amazonaws.com',
    database='trials_db',
    user=secret['username'],
    password=secret['password'],
    port=5432,
    sslmode='require'
)
cursor = conn.cursor()

# Get sample breast cancer trials
cursor.execute("""
    SELECT id, title, condition, min_age, max_age, gender_criteria 
    FROM trials 
    WHERE condition ILIKE '%breast cancer%' 
    LIMIT 3
""")

print('\nSample Breast Cancer trials:')
for row in cursor.fetchall():
    print(f'\nID: {row[0]}')
    print(f'Title: {row[1][:60]}...')
    print(f'Condition: {row[2]}')
    print(f'Age: {row[3]}-{row[4]}')
    print(f'Gender: {row[5]}')

cursor.close()
conn.close()
