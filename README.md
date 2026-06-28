python manage.py shell

from accounts.models import User

User.objects.create_user(
    username='admin1',
    password='admin123',
    role='ADMIN'
)


from accounts.models import User

User.objects.create_user(
    username='admin97',
    password='@#adminfleet!!!1',
    role='ADMIN'
)

from accounts.models import User

admin = User.objects.create_user(
    username="admin1",
    password="admin123",
    role="ADMIN"
)

admin.is_staff = True
admin.is_superuser = True
admin.save()