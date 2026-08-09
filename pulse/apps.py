from django.apps import AppConfig


class PulseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pulse'

    def ready(self):
        # Wire post_save(User) → UserProfile creation.
        import pulse.signals  # noqa: F401
