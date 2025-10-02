from django.core.management.base import BaseCommand
from django.db.models.signals import post_migrate

def load_initial_data(sender, **kwargs):
    from accounts.models import Role
    from geo.models import Country
    from budgets.models import BudgetCategory, BudgetPeriod

    # Load Roles
    for name in ['Researcher', 'Evaluator', 'Coordinator']:
        Role.objects.get_or_create(
            name=name,
            defaults={'description': f'Rol de tipo: {name}', 'is_active': True}
        )

    # Load Countries
    country_list = [
        'Argentina', 'Belice', 'Bolivia', 'Colombia', 'Costa Rica',
        'Ecuador', 'El Salvador', 'Guatemala', 'Guyana', 'Honduras',
        'Jamaica', 'México', 'Nicaragua', 'Panamá', 'Paraguay',
        'Perú', 'República Dominicana', 'Surinam',
        'Antillas Menores: Dominica', 'Antillas Menores: Granada',
        'Antillas Menores: Santa Lucía', 'Antillas Menores: San Vicente y las Granadinas'
    ]
    for name in country_list:
        Country.objects.get_or_create(name=name, defaults={'phone_number_indicative': '+57'})

    # Load Budget Categories
    categories = [
        {'name': 'Personal', 'description': 'Salarios, honorarios'},
        {'name': 'Equipos e Infraestructura', 'description': 'Computadores, herramientas'},
        {'name': 'Viajes y Logística', 'description': 'Transporte, alojamiento'},
        {'name': 'Actividades Comunitarias', 'description': 'Talleres, participación'}
    ]
    for cat in categories:
        BudgetCategory.objects.get_or_create(name=cat['name'], defaults={
            'description': cat['description'],
            'is_active': True
        })

    # Load Budget Periods
    periods = [
        'Año 1 - Primer Semestre',
        'Año 1 - Segundo Semestre',
        'Año 2 - Primer Semestre',
        'Año 2 - Segundo Semestre',
        'Finalización y Sostenibilidad'
    ]
    for order, name in enumerate(periods, start=1):
        BudgetPeriod.objects.get_or_create(name=name, defaults={'order': order})

class Command(BaseCommand):
    help = "Load base data after migrations"

    def handle(self, *args, **options):
        self.stdout.write("Loading base data...")
        load_initial_data(None)
        self.stdout.write(self.style.SUCCESS("Base data loaded successfully."))