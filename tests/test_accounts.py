import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAuthFlow:
    def test_register_user(self, api_client):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 201
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_success(self, api_client, hr_maker):
        url = reverse('login')
        data = {'username': 'hr_maker', 'password': 'TestPass123!'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        assert 'access' in response.data

    def test_login_wrong_password(self, api_client, hr_maker):
        url = reverse('login')
        data = {'username': 'hr_maker', 'password': 'WrongPass!'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400

    def test_profile_requires_auth(self, api_client):
        url = reverse('profile')
        response = api_client.get(url)
        assert response.status_code == 401

    def test_profile_authenticated(self, auth_client):
        url = reverse('profile')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data['username'] == 'hr_maker'
