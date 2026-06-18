from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SignupViewTests(TestCase):
    def test_signup_page_is_available(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())
