from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from geo.models import Country
from accounts.models import Role
from budgets.models import BudgetCategory, BudgetPeriod
from common.models import Scale
from common.models import Status
from institutions.models import InstitutionType
from geo.models import DocumentType

class Command(BaseCommand):
    help = "Populates base tables: Country, Role, BudgetCategory, BudgetPeriod"

    def handle(self, *args, **options):
        self.stdout.write("Starting base data population...")

        # -------------------------
        # 1. Load Countries
        # -------------------------
        country_names = [
            'Argentina',
            'Belice',
            'Bolivia',
            'Colombia',
            'Costa Rica',
            'El Salvador',
            'Guatemala',
            'Guyana',
            'Honduras',
            'Jamaica',
            'México',
            'Nicaragua',
            'Panamá',
            'Paraguay',
            'Perú',
            'República Dominicana',
            'Surinam',
            'Antillas Menores: Dominica',
            'Antillas Menores: Granada',
            'Antillas Menores: Santa Lucía',
            'Antillas Menores: San Vicente y las Granadinas',
            'Ecuador',
        ]

        created_countries = 0
        for name in country_names:
            obj, created = Country.objects.get_or_create(
                name=name,
                defaults={'phone_number_indicative': '+57'}  # Will update below
            )
            if created:
                created_countries += 1

        # Now set specific indicatives
        indicatives = {
            'Argentina': '+54',
            'Belice': '+501',
            'Bolivia': '+591',
            'Colombia': '+57',
            'Costa Rica': '+506',
            'El Salvador': '+503',
            'Guatemala': '+502',
            'Guyana': '+592',
            'Honduras': '+504',
            'Jamaica': '+1-876',
            'México': '+52',
            'Nicaragua': '+505',
            'Panamá': '+507',
            'Paraguay': '+595',
            'Perú': '+51',
            'República Dominicana': '+1-809',
            'Surinam': '+597',
            'Antillas Menores: Dominica': '+1-767',
            'Antillas Menores: Granada': '+1-473',
            'Antillas Menores: Santa Lucía': '+1-758',
            'Antillas Menores: San Vicente y las Granadinas': '+1-784',
            'Ecuador': '+593',
            'Chile': '+56',
        }

        updated_count = 0
        for name, indicative in indicatives.items():
            country = Country.objects.filter(name=name).first()
            if country and country.phone_number_indicative != indicative:
                country.phone_number_indicative = indicative
                country.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_countries} countries. Updated {updated_count} phone indicatives.")
        )

        # -------------------------
        # 2. Load Roles
        # -------------------------
        role_names = ['Researcher', 'Coordinator', 'Evaluator']
        created_roles = 0

        for role_name in role_names:
            obj, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': f'Rol de tipo: {role_name}',
                    'is_active': True
                }
            )
            if created:
                created_roles += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_roles} roles.")
        )

        # -------------------------
        # 3. Load Budget Categories
        # -------------------------
        category_data = [
            {'name': 'Salarios del equipo de trabajo', 'description': 'Honorarios y salarios profesionales claramente justificados relacionados directamente con la ejecución del proyecto (Anexo 1)'},
            {'name': 'Costos indirectos', 'description': 'Costos indirectos'},
            {'name': 'Auditoría externa', 'description': 'Auditoría externa'},
            {'name': 'Equipamiento, servicios especializados y gestión de datos', 'description': 'Equipamiento, servicios especializados y gestión de datos'},
            {'name': 'Actividades de campo, procesos de participación y formación', 'description': 'Actividades de campo, procesos de participación y formación'}
        ]

        created_categories = 0
        for data in category_data:
            obj, created = BudgetCategory.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_active': True
                }
            )
            if created:
                created_categories += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_categories} budget categories.")
        )

        # -------------------------
        # 4. Load Budget Periods
        # -------------------------
        period_data = [
            'Año 1 - Primer Semestre',
            'Año 1 - Segundo Semestre',
            'Año 2 - Primer Semestre',
            'Año 2 - Segundo Semestre',
            'Finalización y Sostenibilidad'
        ]

        created_periods = 0
        for order, name in enumerate(period_data, start=1):
            obj, created = BudgetPeriod.objects.get_or_create(
                name=name,
                defaults={
                    'order': order
                }
            )
            if created:
                created_periods += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_periods} budget periods.")
        )

        # -------------------------
        # 5. Load Scales
        # -------------------------
        scale_data = [
            {
                'name': 'S',
                'description': 'Hasta $250.000.000 COP',
                'min_amount': 0,
                'max_amount': 250000000,
                'is_active': True
            },
            {
                'name': 'M',
                'description': 'De $250.000.001 a $500.000.000 COP',
                'min_amount': 250000001,
                'max_amount': 500000000,
                'is_active': True
            },
            {
                'name': 'B',
                'description': 'Más de $500.000.000 COP',
                'min_amount': 500000001,
                'max_amount': 900000000,
                'is_active': True
            }
        ]
        
        created_scales = 0
        for data in scale_data:
            obj, created = Scale.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                created_scales += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_scales} project scales.")
        )

        self.stdout.write(
            self.style.SUCCESS("All base data loaded successfully.")
        )

        # -------------------------
        # 6. Load Status
        # -------------------------
        status_data = [
            {'name': 'Draft', 'description': None},
            {'name': 'Abierta', 'description': None}, # Y cerrada pillin?
            {'name': 'Borrador', 'description': None},
            {'name': 'Enviada', 'description': None},
            {'name': 'Aprobada', 'description': None},
            {'name': 'Pendiente', 'description': 'Evaluación pendiente de revisión'},
        ]
        
        created_statuses = 0
        for data in status_data:
            obj, created = Status.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_active': True,
                    'color': ''
                }
            )
            if created:
                created_statuses += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_statuses} statuses.")
        )

        # -------------------------
        # 7. Load Institution Types
        # -------------------------
        institution_type_names = [
            'Universidad',
            'Institución Académica',
            'Centro de Investigación',
            
        ] # 'CBO'
        
        created_institution_types = 0
        for name in institution_type_names:
            obj, created = InstitutionType.objects.get_or_create(
                name=name,
                defaults={'is_active': True}
            )
            if created:
                created_institution_types += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_institution_types} institution types.")
        )

        # -------------------------
        # 8. Load Document Types ("Documento de identificación") per Country
        # -------------------------
        doc_type_name = "Documento de identificación"
        created_doc_types = 0
        
        for country in Country.objects.all():
            obj, created = DocumentType.objects.get_or_create(
                country=country,
                name=doc_type_name
            )
            if created:
                created_doc_types += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_doc_types} document types ('{doc_type_name}') across all countries.")
        )
