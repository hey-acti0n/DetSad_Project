from django.core.management.base import BaseCommand
from core import storage


class Command(BaseCommand):
    help = "Перезаписать правила начисления очков (actions_config.json) дефолтными из кода."

    def handle(self, *args, **options):
        storage.reset_actions_config_to_defaults()
        self.stdout.write(self.style.SUCCESS("Правила начисления очков сброшены на дефолтные из кода."))
