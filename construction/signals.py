from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from . import models
from .middleware import get_current_user
from .models import Profile


@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


AUDITED_MODELS = {
    models.Company,
    models.Department,
    models.BusinessPartner,
    models.Project,
    models.ProjectTeamMember,
    models.Contract,
    models.BOQSection,
    models.BOQItem,
    models.BudgetItem,
    models.Material,
    models.StockMovement,
    models.PurchaseRequest,
    models.PurchaseOrder,
    models.Activity,
    models.DailyReport,
    models.RFI,
    models.Variation,
    models.EOTApplication,
    models.PaymentCertificate,
    models.Invoice,
    models.Document,
    models.Risk,
    models.SafetyIncident,
    models.Defect,
    models.ProjectTask,
    models.ApprovalRequest,
}


@receiver(post_save)
def audit_save(sender, instance, created, raw=False, **kwargs):
    if raw or sender not in AUDITED_MODELS:
        return
    action = 'created' if created else 'updated'
    models.AuditLog.objects.create(
        user=get_current_user(),
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        summary=f'{sender.__name__} {instance} was {action}.',
    )


@receiver(post_delete)
def audit_delete(sender, instance, **kwargs):
    if sender not in AUDITED_MODELS:
        return
    models.AuditLog.objects.create(
        user=get_current_user(),
        action='deleted',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        summary=f'{sender.__name__} {instance} was deleted.',
    )
