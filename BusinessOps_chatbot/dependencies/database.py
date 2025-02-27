import mysql.connector
import sqlalchemy
from sqlalchemy.pool import QueuePool
from config.config import USER, HOST, DATABASE, PASSWORD

# Function to create a MySQL connection
def getconn():
    return mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        auth_plugin='mysql_native_password',  
        connection_timeout=30
    )

# SQLAlchemy connection pool
pool = sqlalchemy.create_engine(
    "mysql+mysqlconnector://", 
    creator=getconn, 
    poolclass=QueuePool, 
    pool_size=25, 
    max_overflow=50, 
    pool_timeout=45, 
    pool_recycle=1800, 
    pool_pre_ping=True
)

# Function to get a connection from the pool
def get_mysql_connection():
    conn = pool.connect()
    return conn