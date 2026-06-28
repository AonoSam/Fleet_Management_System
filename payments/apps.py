# from django.apps import AppConfig


# class PaymentsConfig(AppConfig):
#     name = 'payments'

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        import payments.signals  # noqa — registers the payment success signal