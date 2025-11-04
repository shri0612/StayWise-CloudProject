from django.contrib.sessions.backends.db import SessionStore as DBStore

class SessionStore(DBStore):
    @classmethod
    def get_model_class(cls):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manager_sessions';")
            exists = cursor.fetchone()
        if exists:
            from django.contrib.sessions.models import Session
            Session._meta.db_table = "manager_sessions"
        return Session
