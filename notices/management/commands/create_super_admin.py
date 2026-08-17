from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create or update a Super Admin (superuser) account."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin", help="Superuser username")
        parser.add_argument("--email", default="admin@communotice.local", help="Superuser email")
        parser.add_argument("--password", default="admin12345", help="Superuser password")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]

        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Super Admin user '{username}' successfully created!"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Super Admin user '{username}' password and permissions updated!"))
