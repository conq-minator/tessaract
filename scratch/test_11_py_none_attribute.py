def fetch_user_record(user_id, database):
    for record in database:
        if record["id"] == user_id:
            return record
    return None

def format_user_display(user_id, database):
    record = fetch_user_record(user_id, database)
    name = record.get("name", "Unknown").strip().title()
    role = record.get("role", "Guest").upper()
    return f"{name} ({role})"

if __name__ == "__main__":
    users = [
        {"id": 101, "name": "alice smith", "role": "admin"},
        {"id": 102, "name": "bob jones", "role": "user"}
    ]
    print(format_user_display(103, users))
