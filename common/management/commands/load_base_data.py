from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict

from geo.models import Country
from accounts.models import Role, CustomUser
from budgets.models import BudgetCategory, BudgetPeriod
from common.models import Scale
from common.models import Status
from institutions.models import InstitutionType
from geo.models import DocumentType
from proponent_forms.models import (
    SharedQuestionCategory,
    SharedQuestion,
    SharedQuestionOption,
    ProponentForm,
    ProponentFormQuestion
)
from evaluations.models import (
    EvaluationTemplate,
    TemplateCategory,
    TemplateSubcategory,
    TemplateItem,
    TemplateItemOption
)
from calls.models import Call

class Command(BaseCommand):
    help = "Populates base tables: Country, Role, BudgetCategory, BudgetPeriod. Also, load sample proponent and evaluation questions with options"

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

        self.stdout.write("Loading sample proponent and evaluation questions...")

        # -------------------------
        # 19. PROPONENT QUESTIONS
        # -------------------------
        # Create two shared categories
        prop_cat1, _ = SharedQuestionCategory.objects.get_or_create(
            name="Madurez del eje temático seleccionado para el país en el que se desarrolla el proyecto.",
            defaults={"description": "Rúbrica de Evaluación", "is_active": True}
        )

        prop_cat2, _ = SharedQuestionCategory.objects.get_or_create(
            name=" Disponibilidad de información y datos para su recolección y análisis.",
            defaults={"description": "Rúbrica de Evaluación", "is_active": True}
        )

        # Create questions for proposal
        created_questions = []
        # =============== Question 1 ===============
        sq = SharedQuestion.objects.get_or_create(
            question=f"¿Dentro de la bibliografia para la construcción del marco teorico, existe evidencia de investigaciones conceptuales y empiricas sustanciales en el eje temático en el que desarrolla el proyecto?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat1,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq,
            display_text=f"1. Existe un conjunto sustancial de investigaciones conceptuales y empiricas.",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq,
            display_text=f"2.Escasas investigaciones conceptuales o empiricas en este campo.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq,
            display_text=f"3. No existen investigaciones en este campo",
            defaults={'score': 3.0}
        )
        created_questions.append(sq)

        # =============== Question 2 ===============
        sq2 = SharedQuestion.objects.get_or_create(
            question=f"¿Qué tanto material de consulta y divulgación del conocimiento existe en el eje temático seleccionado?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat1,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq2,
            display_text=f"1. Existe un conjunto sustancial de puntos de intercambio de conocimientos discernibles (conferencias, seminarios, materiales de divulgación).",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq2,
            display_text=f"2. Puntos de intercambio de conocimientos discernibles (conferencias, seminarios, materiales de divulgación) emergentes.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq2,
            display_text=f"3. Escasos puntos de intercambio de conocimientos discernibles (conferencias, seminarios, materiales de divulgación).",
            defaults={'score': 3.0}
        )
        created_questions.append(sq2)

        # =============== Question 3 ===============
        sq3 = SharedQuestion.objects.get_or_create(
            question=f"¿Qué tan consolidada es la comunidad de investigadores y/o expertos en el eje temático seleccionado dentro del país en el que se llevara a cabo el proyecto?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat1,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq3,
            display_text=f"1. Existe una comunidad de investigadores expertos activos en el eje seleccionado que se conectan mutuamente.",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq3,
            display_text=f"2. Existe un grupo emergente de investigadores activos en el eje temático seleccionado y que estan abiertos a conectarse mutuamente.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq3,
            display_text=f"3. Existen escasos investigadores activos en el eje temático seleccionado para la investigación.",
            defaults={'score': 3.0}
        )
        created_questions.append(sq3)

        # =============== Question 4 ===============
        sq4 = SharedQuestion.objects.get_or_create(
            question=f"¿Cúal es la disponibilidad de las herramientas de recolección y análisis de información en el eje temático seleccionado acotado al contexto de su proyecto?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat2,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq4,
            display_text=f"1. Los intrumentos de recolección de datos y de análisis de los mismos estan disponibles y son ampliamente acordados.",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq4,
            display_text=f"2. Los instrumentos de recolección y análisis de datos estan generalmente disponibles.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq4,
            display_text=f"3. Hay pocos instrumentos disponibles para la recolección y el análisis de datos.",
            defaults={'score': 3.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq4,
            display_text=f"4. Los instrumentos para la recolección y el análisis de los datos no está disponible.",
            defaults={'score': 4.0}
        )
        created_questions.append(sq4)

        # =============== Question 5 ===============
        sq5 = SharedQuestion.objects.get_or_create(
            question=f"¿Cúal es el acceso y la disponibilidad de datos primarios y secundarios en el eje temático seleccionado acotado al contexto de su proyecto?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat2,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq5,
            display_text=f"1. Existen conjuntos de datos secundarios accesibles,  bien desarrollados, estables, significativos y oportunos.",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq5,
            display_text=f"2. Existen conjuntos de datos rasonablemente accesibles y fiables.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq5,
            display_text=f"3. Existe un limitado acceso a los datos existentes y brechas en la fiabilidad de los mismos.",
            defaults={'score': 3.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq5,
            display_text=f"4. Datos disponibles escasos y poco fiables.",
            defaults={'score': 4.0}
        )
        created_questions.append(sq5)

        # =============== Question 6 ===============
        sq6 = SharedQuestion.objects.get_or_create(
            question=f"¿Cúal es la cantidad de fuentes de datos disponibles en el eje temático seleccionado acotado al contexto del proyecto?",
            field_type='dropdown',
            target_category='proposal',
            defaults={
                'category': prop_cat2,
                'is_required': True,
                'is_active': True
            }
        )[0]
        # Add options
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq6,
            display_text=f"1. Abundante cantidad de fuentes de datos nacionales e internacionales.",
            defaults={'score': 1.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq6,
            display_text=f"2. Fuentes de datos internacionales disponibles pero pocas fuentes de datos nacionales.",
            defaults={'score': 2.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq6,
            display_text=f"3. Limitadas fuentes de datos nacionales e internacionales.",
            defaults={'score': 3.0}
        )
        SharedQuestionOption.objects.get_or_create(
            shared_question=sq6,
            display_text=f"4. Fuentes de datos nacionales e internacionales escasas o poco fiables.",
            defaults={'score': 4.0}
        )
        created_questions.append(sq6)

        self.stdout.write(self.style.SUCCESS(f"Created {len(created_questions)} proponent questions with their options."))

        # Create and link call
        call_title = "Convocatoria CLIMAS 2025"
        status_abierta = Status.objects.filter(name='Abierta').first()
        
        if not status_abierta:
            self.stdout.write(self.style.ERROR("No se encuentra el estado 'Abierta'. No se pudo crear la convocatoria."))
        else:
            call, created = Call.objects.get_or_create(
                title=call_title,
                defaults={
                    'status': status_abierta,
                    'description': 'Convocatoria creada automáticamente para cargar preguntas de ejemplo.',
                    'opening_datetime': timezone.now(),
                    'closing_datetime': timezone.now() + timezone.timedelta(days=30),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Se ha creado la convocatoria: '{call.title}'"))                
            else:
                self.stdout.write(self.style.WARNING(f"La convocatoria '{call.title}' ya existía. Reutilizando..."))

            try:
                coordinator_role = Role.objects.get(name="Coordinator")
                coordinator = CustomUser.objects.filter(role=coordinator_role).first()
                
                if coordinator:
                    call.coordinator = coordinator
                    call.save(update_fields=['coordinator'])
                    self.stdout.write(
                        self.style.SUCCESS(f"Convocatoria '{call.title}' asignada al usuario {coordinator}.")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("No se encontró un Coordinador. La convocatoria permanece sin asignar.")
                    )
            except Role.DoesNotExist:
                self.stdout.write(self.style.ERROR("¡Rol 'Coordinator' faltante!"))
        
            # Create or get ProponentForm for this call
            form, form_created = ProponentForm.objects.get_or_create(
                call=call,
                defaults={'title': f'Formulario para {call.title}'}
            )
            if form_created:
                self.stdout.write(self.style.SUCCESS(f"Se ha creado el formulario: '{form.title}'"))
            else:
                self.stdout.write(self.style.WARNING(f"El formulario'{form.title}' ya existía. Reutilizando..."))

            # Link ONLY the 6 created questions
            for order, sq in enumerate(created_questions, start=1):
                proponent_form_question, _ = ProponentFormQuestion.objects.update_or_create(
                    form=form,
                    shared_question=sq,
                    defaults={'order': order}
                )
                if proponent_form_question:
                    self.stdout.write(self.style.SUCCESS(f"Pregunta {order} creada con éxito."))
                else:
                    self.stdout.write(self.style.WARNING(f"Hubo un error creando la pregunta {order}"))


            self.stdout.write(
                self.style.SUCCESS(f"Linked {len(created_questions)} specific SharedQuestions to call: {call.title}")
            )

        # ===================================
        # 2. EVALUATION QUESTIONS 
        # ===================================
        # Create Evaluation Template
        template, _ = EvaluationTemplate.objects.get_or_create(
            name="Plantilla Evaluaciones Convocatoria CLIMAS 2025",
            defaults={
                "description": "Creada por script de carga",
                "is_active": True,
                "applies_to_expression": True,
                "applies_to_proposal": True
            }
        )

        # --- TEMPLATE CATEGORIES ---
        ev_cat1, _ = TemplateCategory.objects.get_or_create(
            template=template,
            name="Rigor científico",
            defaults={'order': 1}
        )
        ev_cat2, _ = TemplateCategory.objects.get_or_create(
            template=template,
            name="Legitimidad investigación",
            defaults={'order': 2}
        )
        ev_cat3, _ = TemplateCategory.objects.get_or_create(
            template=template,
            name="Presupuesto y cronograma",
            defaults={'order': 3}
        )

        # --- TEMPLATE SUBCATEGORIES ---
        # Category 1: 6 subcategories
        sub1_1, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Marco Teorico", defaults={'order': 1})
        sub1_2, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Protocolo metodológico", defaults={'order': 2})
        sub1_3, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Objetivos", defaults={'order': 3})
        sub1_4, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Efectos estratégicos y productos", defaults={'order': 4})
        sub1_5, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Gestión de riesgos", defaults={'order': 5})
        sub1_6, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat1, name="Marco ético", defaults={'order': 6})

        # Category 2: 6 subcategories
        sub2_1, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Contexto territorial y social (Teniendo en cuenta que el territorio y el contexto socio-económico son determinantes de la salud)", defaults={'order': 1})
        sub2_2, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Comunidades étnicas, rurales, campesinas u otras asociatividades comunitarias", defaults={'order': 2})
        sub2_3, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Consciente de género", defaults={'order': 3})
        sub2_4, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Sensible al género", defaults={'order': 4})
        sub2_5, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Sensible y activo al género", defaults={'order': 5})
        sub2_6, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat2, name="Transformativo al género", defaults={'order': 6})

        # Category 3: 2 subcategories
        sub3_1, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat3, name="Coherencia presupuesto-cronograma (Descripción de los productos y actividades)", defaults={'order': 1})
        sub3_2, _ = TemplateSubcategory.objects.get_or_create(category=ev_cat3, name="Contrapartida", defaults={'order': 2})

        # --- QUESTIONS AND OPTIONS ---
        
        # Helper function to create a question + options
        def create_eval_question(subcat, question_text, options_with_scores):
            item = TemplateItem.objects.create(
                subcategory=subcat,
                question=question_text,
                field_type='dropdown',
                order=1,  # will be overridden by loop
                max_score=max(score for _, score in options_with_scores)
            )
            for display_text, score in options_with_scores:
                TemplateItemOption.objects.get_or_create(
                    item=item,
                    display_text=display_text,
                    defaults={'score': Decimal(str(score))}
                )
            return item

        # CATEGORY 1: 19 questions
        cat1_questions = [
            # Marco Teorico
            (sub1_1, "¿Qué tan bien delimitado esta el marco teorico del proyecto dentro del eje temático seleccionado?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_1, "¿Qué tan bien delimitado esta el marco teorico del proyecto dentro de los efectos estratégicos seleccionados?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_1, "¿El marco teorico considera el marco normativo entorno al eje temático seleccionado? ", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_1, "¿La problemática está bien justificada y delimitada dentro de los efectos estratégicos seleccionados?", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),

            # Protocolo metodológico
            (sub1_2, "¿Qué tan bien delimitada y descrita está la metodología escogida según el eje temático seleccionado? ", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_2, "¿Qué tan bien articulado y claro es el protocolo metodológico?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_2, "¿El protocolo metodológico del proyecto se adhiere al logro de los efectos estratégicos seleccionados? ", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_2, "¿El protocolo metodológico del proyecto considera un plan de recolección y análisis de datos?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_2, "¿El plan de recolección y análisis de datos considera el manejo y la protección de datos sensibles? ", [("Aceptable", 1), ("Inaceptable", 0)]),

            # Objetivos
            (sub1_3, "¿Qué tan bien articulado y claro es el objetivo general del proyecto según el eje temático seleccionado?", [("Aceptable", 2), ("Inaceptable", 0)]),
            (sub1_3, "¿El objetivo general del proyecto responde a la poblemática planteada?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_3, "¿Qué tan bien articulados y claros son los objetivos específicos del proyecto con los efectos estratégicos seleccionados?", [("Aceptable", 2), ("Inaceptable", 0)]),

            # Efectos estratégicos y productos
            (sub1_4, "¿Los productos son coherentes con las actividades propuestas para el desarrollo de la metodología seleccionada?", [("Aceptable", 2), ("Inaceptable", 0)]),
            (sub1_4, "¿Son claros los aportes de los productos a los efectos estratégicos previamente seleccionados?", [("Aceptable", 3), ("Inaceptable", 0)]),

            # Gestión de riesgos
            (sub1_5, "Para determinar el riesgo interno: ¿Parece el contexto institucional (prioridades institucionales, incentivos, infraestructura, regulación interna)suficiente para  que el equipo investigador desarrolle el proyecto?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_5, "Para determinar el riesgo externo: ¿Es el contexto político, económico y la gobernanza del país en el cual se desarolla el proyecto lo suficientemente estable para no interferir en la ejecución del proyecto? ", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_5, "¿La descripción de los posibles riesgos inernos y externos es clara?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub1_5, "¿La descripción de las estrategías de mitigación de riesgos internos y externos son claras y factibles?", [("Aceptable", 2), ("Inaceptable", 0)]),
            
            # Marco ético
            (sub1_6, "El protocolo metodológico ya ha sido aprobado por un comité de ética?", [("Aceptable", 5), ("Inaceptable", 0)]),
        ]

        # CATEGORY 2: 19 questions
        cat2_questions = [
            #Contexto territorial y social 
            (sub2_1, "¿En el diseño del proyecto es considerado dentro del marco teórico  un análisis profundo del territorio (Ubicación geográfica, urbanidad y ruralidad, clima etc)?", [("Muy bueno", 5), ("Aceptable", 2), ("Inaceptable", 0)]),
            (sub2_1, "¿En el diseño del proyecto es considerado dentro del marco teórico  un análisis profundo de las desigualdades en salud identificadas en la población participante?", [("Muy bueno", 5), ("Aceptable", 2), ("Inaceptable", 0)]),

            # Comunidades étnicas, rurales, campesinas u otras asociatividades comunitarias
            (sub2_2, "¿En el diseño del proyecto es considerada una estrategía de caracterización de las comunidades étnicas presentes en el territorio? (La estrategía es clara, detalla y bien descrita).", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_2, "¿En el protocolo metodológico está  articulada la inclusión y/o participación de alguna de las comunidades étnicas y/o  poblaciones rurales previamente caracterizadas de manera clara y detallada?", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_2, "¿En el diseño del proyecto  esta establecido un proceso de selección y priorización de una de las comunidades étnicas y/o poblaciones rurales presentes en el país de implementación? (Este proceso es claro y permite justificar la selección de la comunidad)", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_2, "¿En el diseño del proyecto es considerada una estrategía para identificar y caracterizar sistemas de conocimientos locales y/o tradicionales? (La estrategía es clara, detalla y bien descrita)", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_2, "¿En el protocolo metodológico esta descrita una estrategía para el trabajo colaborativo y la co-producción de productos con actores de comunidades indigenas/Afro-descendientes/rurales?", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_2, "¿La organización de base comunitaría es reconocida por la comunidad con la que se aspira a desarrollar el proyecto?", [("Aceptable", 5), ("Inaceptable", 0)]),

            # Consciente de género
            (sub2_3, "¿El género es considerado en el desarrollo del marco teorico del proyecto?", [("Aceptable", 5), ("Inaceptable", 0)]),

            # Sensible al género
            (sub2_4, "¿El género es considerado en el desarrollo del marco teorico del proyecto?", [("Aceptable", 2), ("Inaceptable", 0)]),
            (sub2_4, "¿El género es considerado como un concepto operativo en el diseño metodológico?", [("Aceptable", 3), ("Inaceptable", 0)]),

            # Sensible y activo al género
            (sub2_5, "¿El género es considerado en el desarrollo del marco teorico del proyecto?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_5, "¿El género es considerado como un concepto operativo en el diseño metodológico?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_5, "¿El género se extiende al plan de análisis de los datos?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_5, "¿Los productos estan destinados a informar y divulgar el análisis previamente realizado considerando el genero?", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),

            # Transformativo al género
            (sub2_6, "¿En el desarrollo del marco teorico del proyecto se examina, analiza y construye una base de evidencia en torno a las causas de las desigualdades en salud y el género?", [("Muy bueno", 2), ("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_6, "¿El protocolo metodológico busca construir evidencia considerado el género como un concepto operativo?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_6, "¿El género se extiende al plan de análisis de los datos?", [("Aceptable", 1), ("Inaceptable", 0)]),
            (sub2_6, "¿Los productos estan destinados a informar y divulgar el análisis previamente realizado considerando el género?", [("Aceptable", 1), ("Inaceptable", 0)]),
        ]

        # CATEGORY 3: 3 questions
        cat3_questions = [
            # Coherencia presupuesto-cronograma (Descripción de los productos y actividades)
            (sub3_1, "¿El propuesto es coherente con las actividades programadas?", [("Aceptable", 2), ("Inaceptable", 0)]),
            (sub3_1, "¿Las actividades programadas son coherentes para el cumplimiento de los productos esperados?", [("Aceptable", 3), ("Inaceptable", 0)]),

            # Contrapartida
            (sub3_2, "¿La propuesta incluye una contrapartida institucional?", [("Aceptable", 5), ("Inaceptable", 0)]),
        ]

        # Create all items with explicit subcategory assignment
        all_items = []

        for subcat, q_text, opts in cat1_questions + cat2_questions + cat3_questions:
            item = create_eval_question(subcat, q_text, opts)
            all_items.append(item)

        # Set correct order within each subcategory
        
        subcat_items = defaultdict(list)
        for item in all_items:
            subcat_items[item.subcategory_id].append(item)

        for subcat_id, items in subcat_items.items():
            for idx, item in enumerate(items, start=1):
                item.order = idx
                item.save(update_fields=['order'])

        self.stdout.write(self.style.SUCCESS(f"Created {len(all_items)} evaluation questions with explicit subcategory assignment"))

        self.stdout.write(self.style.SUCCESS("All sample questions loaded successfully!"))
