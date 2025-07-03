# signals.py - Création automatique des groupes
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Créer les groupes par défaut après migration"""
    default_groups = ['admin', 'fournisseur', 'employee', 'gestionnaire']
    
    for group_name in default_groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f'Groupe "{group_name}" créé avec succès')
