"""Database connection and utilities"""

# Global database instance
db = None

def get_database():
    """Dependency to get database instance"""
    return db

def set_database(database):
    """Set the database instance"""
    global db
    db = database