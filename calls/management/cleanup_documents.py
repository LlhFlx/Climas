from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from expressions.models import ExpressionDocument

class Command(BaseCommand):
    help = 'Delete temporary expression documents older than 7 days'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = ExpressionDocument.objects.filter(
            created_at__lt=cutoff,
            expression__status__name__ne='Enviada'  # Not submitted
        ).delete()
        self.stdout.write(f'Deleted {deleted} old temporary documents.')