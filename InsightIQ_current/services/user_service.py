
"""MySQL user profile service for InsightIQ Analytics."""

from db_connection import get_connection


class UserService:
    def get_users(self):
        """Return existing users from MySQL."""
        connection = None
        cursor = None

        try:
            connection = get_connection()
            if connection is None:
                return []

            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id, username, email, created_at
                FROM users
                ORDER BY user_id
            """)
            return cursor.fetchall()

        except Exception as exc:
            print(f"Could not load users: {exc}")
            return []

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_user(self, user_id):
        """Return one user by ID."""
        connection = None
        cursor = None

        try:
            connection = get_connection()
            if connection is None:
                return None

            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id, username, email, created_at
                FROM users
                WHERE user_id = %s
            """, (user_id,))

            return cursor.fetchone()

        except Exception as exc:
            print(f"Could not load user profile: {exc}")
            return None

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def update_user(self, user_id, username, email):
        """Update a user's name and email."""
        username = username.strip()
        email = email.strip()

        if not username or not email:
            return False, "Name and email are required."

        connection = None
        cursor = None

        try:
            connection = get_connection()
            if connection is None:
                return False, "MySQL connection is unavailable."

            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users
                SET username = %s, email = %s
                WHERE user_id = %s
            """, (username, email, user_id))

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT user_id FROM users WHERE user_id = %s",
                    (user_id,)
                )
                if cursor.fetchone() is None:
                    connection.rollback()
                    return False, "User ID was not found."

            connection.commit()
            return True, "Profile updated successfully."

        except Exception as exc:
            if connection:
                connection.rollback()

            message = str(exc)
            if "1062" in message:
                message = "This email address is already in use."

            return False, message

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
