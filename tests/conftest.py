import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def system_admin(db):
    return User.objects.create_user(
        username='sysadmin',
        email='sysadmin@hrms.test',
        password='TestPass123!',
        user_type='INTERNAL',
        role='SYSTEM_ADMIN',
        is_staff=True,
    )


@pytest.fixture
def hr_maker(db):
    return User.objects.create_user(
        username='hr_maker',
        email='hr.maker@hrms.test',
        password='TestPass123!',
        user_type='INTERNAL',
        role='HR_MAKER',
    )


@pytest.fixture
def hr_checker(db):
    return User.objects.create_user(
        username='hr_checker',
        email='hr.checker@hrms.test',
        password='TestPass123!',
        user_type='INTERNAL',
        role='HR_CHECKER',
    )


@pytest.fixture
def recruiter(db):
    return User.objects.create_user(
        username='recruiter',
        email='recruiter@hrms.test',
        password='TestPass123!',
        user_type='INTERNAL',
        role='RECRUITER',
    )


@pytest.fixture
def hiring_manager(db):
    return User.objects.create_user(
        username='hiring_mgr',
        email='hiring.mgr@hrms.test',
        password='TestPass123!',
        user_type='INTERNAL',
        role='HIRING_MANAGER',
    )


@pytest.fixture
def applicant_user(db):
    return User.objects.create_user(
        username='applicant1',
        email='applicant1@external.test',
        password='TestPass123!',
        user_type='EXTERNAL',
        role='APPLICANT',
    )


@pytest.fixture
def auth_client(api_client, hr_maker):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(hr_maker)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


@pytest.fixture
def admin_client(api_client, system_admin):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(system_admin)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


@pytest.fixture
def checker_client(api_client, hr_checker):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(hr_checker)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client
