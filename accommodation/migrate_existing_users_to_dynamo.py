import os
import sys
import django
from django.utils import timezone

# ✅ Add outer project folder to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthost.settings')

django.setup()

from django.contrib.auth.models import User
from accommodation.models import Profile
from accommodation.dynamo_users import add_user_to_dynamo

def migrate_users():
    profiles = Profile.objects.all()
    for profile in profiles:
        user = profile.user
        role = profile.role
        print(f"➡️ Migrating {user.username} ({role}) to DynamoDB...")
        add_user_to_dynamo(user, role)
    print("✅ All users migrated successfully!")

if __name__ == '__main__':
    migrate_users()
