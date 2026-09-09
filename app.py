import sqlite3


def lookup_user(username):
    connection = sqlite3.connect(":memory:")
    query = "SELECT * FROM users WHERE username = '" + username + "';"
    result = connection.execute(query).fetchall()
    connection.close()
    return result


if __name__ == "__main__":
    username = input("Enter username: ")
    print(lookup_user(username))