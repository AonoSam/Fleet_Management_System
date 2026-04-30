from .models import User


def get_all_users():
    return User.objects.all()


def create_user(form):
    return form.save()