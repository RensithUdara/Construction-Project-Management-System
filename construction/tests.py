from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import models


class ConstructionSmokeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass12345')
        self.company = models.Company.objects.create(name='Test Construction')
        self.project = models.Project.objects.create(
            company=self.company,
            name='Test Project',
            code='TP-001',
            project_type=models.Project.ProjectType.COMMERCIAL,
            contract_value=Decimal('1000000'),
            status=models.Project.Status.CONSTRUCTION,
        )

    def test_dashboard_requires_login_then_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.client.login(username='tester', password='pass12345')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Live project intelligence')

    def test_project_calculates_budget_and_progress(self):
        models.BudgetItem.objects.create(
            project=self.project,
            category=models.BudgetItem.Category.MATERIALS,
            original_budget=Decimal('1000'),
            current_budget=Decimal('1200'),
            actual_cost=Decimal('900'),
        )
        models.Activity.objects.create(
            project=self.project,
            code='A1',
            name='Start',
            start_date=date.today(),
            end_date=date.today(),
            progress=50,
        )
        self.assertEqual(self.project.budget_total, Decimal('1200'))
        self.assertEqual(self.project.actual_total, Decimal('900'))
        self.assertEqual(self.project.progress_percent, 50)

# Create your tests here.
