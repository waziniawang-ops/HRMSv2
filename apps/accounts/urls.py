from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    path('oauth/status/', views.OAuthStatusView.as_view(), name='oauth-status'),
    path('oauth/login/', views.OAuthLoginView.as_view(), name='oauth-login'),
    path('oauth/callback/', views.OAuthCallbackView.as_view(), name='oauth-callback'),

    path('roles/', views.RoleListView.as_view(), name='role-list'),

    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:pk>/roles/', views.UserRolesView.as_view(), name='user-roles'),
]
