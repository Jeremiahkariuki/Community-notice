from django.core.management.base import BaseCommand
from notices.models import Category

DEFAULT_CATEGORIES = [
    "Community Meeting",
    "Alerts",
    "Events",
    "Lost & Found",
    "Services",
    "Sports & Recreation",
]


class Command(BaseCommand):
    help = "Create a starter set of notice categories."

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_CATEGORIES:
            _, was_created = Category.objects.get_or_create(name=name)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Done. {created} new categories created ({len(DEFAULT_CATEGORIES)} total available)."
        ))
