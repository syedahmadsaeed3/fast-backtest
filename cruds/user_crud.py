"""
TODO: explore supabase docs for better user management
"""
def get_user(db, jwt: str):
    data = db.auth.get_user(jwt)
    return data


def get_users(db, skip: int = 0, limit: int = 100):
    pass

