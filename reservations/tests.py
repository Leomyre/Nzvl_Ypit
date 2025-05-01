from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()

class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer des notifications de test
        Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test",
            notification_type="info"
        )

    def test_list_notifications(self):
        url = reverse('notifications-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_unread_count(self):
        url = reverse('notifications-unread-count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_mark_as_read(self):
        url = reverse('notifications-mark-as-read')
        data = {'ids': [1]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked'], 1)