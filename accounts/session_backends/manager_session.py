from django.contrib.sessions.backends.db import SessionStore as DBStore

class SessionStore(DBStore):
    """Separate session store for Manager"""
    @classmethod
    def get_model_class(cls):
        from django.contrib.sessions.models import Session
        Session._meta.db_table = "manager_sessions"  # 👈 separate table
        return Session
