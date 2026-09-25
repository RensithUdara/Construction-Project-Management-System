from rest_framework import serializers

from . import models


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    budget_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    actual_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = models.Project
        fields = '__all__'


class BOQItemSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)
    completion_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = models.BOQItem
        fields = '__all__'


class BudgetItemSerializer(serializers.ModelSerializer):
    variance = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = models.BudgetItem
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Activity
        fields = '__all__'


class RFISerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RFI
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = '__all__'


class GenericModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'


def serializer_for(model):
    explicit = {
        models.Company: CompanySerializer,
        models.Project: ProjectSerializer,
        models.BOQItem: BOQItemSerializer,
        models.BudgetItem: BudgetItemSerializer,
        models.Activity: ActivitySerializer,
        models.RFI: RFISerializer,
        models.Document: DocumentSerializer,
    }
    if model in explicit:
        return explicit[model]

    meta = type('Meta', (), {'model': model, 'fields': '__all__'})
    return type(f'{model.__name__}Serializer', (GenericModelSerializer,), {'Meta': meta})
