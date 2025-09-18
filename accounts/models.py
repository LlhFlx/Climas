#from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from django.core.validators import RegexValidator

class Role(TimestampMixin, CreatedByMixin, models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID Rol"
    )
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


    # Link to Django Groups
    group = models.OneToOneField(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name="Grupo de Permisos",
        help_text="Grupo de Permisos de Django asociado a este rol",
        null=True,
        blank=True
    )

    class Meta:
        db_table= 'role'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                #condition=models.Q(is_active=True),
                name='unique_active_role_name'
            )
        ]
    def __str__(self):
        return self.name

#class User(AbstractUser):
class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    person = models.OneToOneField(
        'people.Person',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_account'
    )

    role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.PROTECT, # We keep the user even  if the role is deleted
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Rol'
    )

    birthdate = models.DateField(
        verbose_name="Fecha de nacimiento",
        blank=True,
        null=True
    )

    email = models.EmailField(unique=True, verbose_name="Correo electronico")

    phone_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]{9,17}$',
                message="Por favor, ingrese un numero de telefono valido (por ejemplo, +57(601)1234444, +1 555-123-4567 o (44) 20 7946 0958)."
            )
        ]
    )

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='accounts_user_groups',
        related_query_name='accounts_user'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='accounts_user_permissions',
        related_query_name='acounts_user'
    )

    class Meta:
        db_table = 'accounts_user' # Customize talbe name

    def __str__(self):
        return f"{self.user.username} ({self.role.name if self.role else 'No Role'})"