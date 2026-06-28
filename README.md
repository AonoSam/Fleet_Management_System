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



python manage.py shell

from accounts.models import User

admin = User.objects.create_user(
    username="admin91",
    password="@#adminfleet!!!1",
    role="ADMIN"
)

admin.is_staff = True
admin.is_superuser = True
admin.save()

print("Admin created successfully!")




from accounts.models import User

admin = User.objects.create_user(
    username="admin93",
    password="@#adminfleet!!!1",
    role="ADMIN",
)

admin.is_staff = True
admin.is_superuser = True
admin.save()

print("Admin created successfully!")




from accounts.models import User

user = User.objects.get(username="admin93")

print(user.username)
print(user.role)
print(user.is_staff)
print(user.is_superuser)
print(user.check_password("@#adminfleet!!!1"))