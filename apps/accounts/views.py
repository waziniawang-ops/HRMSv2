from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.utils import log_action
from . import oauth
from .models import CustomUser, Role
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserCreateSerializer, ChangePasswordSerializer, RoleSerializer,
)
from .permissions import IsSystemAdmin


class IsHRAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.role == CustomUser.ROLE_APPLICANT:
            from apps.recruitment.models import Applicant
            Applicant.objects.get_or_create(
                user=user,
                defaults={
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'phone': user.phone or '',
                },
            )
        refresh = RefreshToken.for_user(user)
        log_action(request, 'REGISTER', 'CustomUser', str(user.id), after_json={'username': user.username})
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        log_action(request, 'LOGIN_SUCCESS', 'CustomUser', str(user.id))
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            log_action(request, 'LOGOUT', 'CustomUser', str(request.user.id))
        except Exception:
            pass
        return Response({'detail': 'Successfully logged out.'})


class OAuthStatusView(APIView):
    """Public, pre-login endpoint the login page calls to decide whether to
    show an SSO button."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not settings.OAUTH_ENABLED:
            return Response({'enabled': False})
        return Response({'enabled': True, 'button_label': settings.OAUTH_BUTTON_LABEL})


class OAuthLoginView(APIView):
    """Starts the OIDC login — a real browser redirect to the IdP."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            oauth.require_config()
        except oauth.OAuthConfigError:
            return HttpResponseRedirect(_frontend_login_redirect('oauth_not_configured'))
        state, nonce = oauth.make_state_and_nonce()
        return HttpResponseRedirect(oauth.build_authorization_url(state, nonce))


class OAuthCallbackView(APIView):
    """Where the IdP redirects back to. On success, hands the JWT pair to the
    SPA in the URL fragment, which browsers never send to any server."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.query_params.get('error'):
            return HttpResponseRedirect(_frontend_login_redirect('oauth_denied'))

        state = request.query_params.get('state')
        code = request.query_params.get('code')
        if not code or not state:
            return HttpResponseRedirect(_frontend_login_redirect('oauth_invalid_state'))
        try:
            expected_nonce = oauth.validate_state(state)
        except Exception:
            # covers signing.BadSignature and its SignatureExpired subclass
            return HttpResponseRedirect(_frontend_login_redirect('oauth_invalid_state'))

        try:
            claims = oauth.exchange_code_for_claims(code, expected_nonce)
        except oauth.OAuthLoginError:
            log_action(request, 'OAUTH_LOGIN_FAILED', 'CustomUser')
            return HttpResponseRedirect(_frontend_login_redirect('oauth_failed'))

        email = claims.get('email')
        if not email or claims.get('email_verified') is False:
            return HttpResponseRedirect(_frontend_login_redirect('oauth_email_unverified'))

        # No auto-provisioning: an admin must already have created a user with
        # this email — a successful IdP login alone never grants an account.
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            log_action(request, 'OAUTH_LOGIN_NO_ACCOUNT', 'CustomUser', extra={'email': email})
            return HttpResponseRedirect(_frontend_login_redirect('oauth_no_account'))

        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        log_action(request, 'OAUTH_LOGIN_SUCCESS', 'CustomUser', str(user.id))
        fragment = urlencode({'access': str(refresh.access_token), 'refresh': str(refresh)})
        return HttpResponseRedirect(f'{settings.FRONTEND_URL}/oauth/callback#{fragment}')


def _frontend_login_redirect(error_code):
    return f'{settings.FRONTEND_URL}/login?{urlencode({"oauth_error": error_code})}'


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        log_action(request, 'PASSWORD_CHANGED', 'CustomUser', str(request.user.id))
        return Response({'detail': 'Password changed successfully.'})


class UserListView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.prefetch_related('roles').all().order_by('username')
    permission_classes = [IsHRAdmin]
    filterset_fields = ['user_type', 'role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.prefetch_related('roles').all()
    permission_classes = [IsHRAdmin]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserCreateSerializer
        return UserSerializer


class RoleListView(generics.ListAPIView):
    """Read-only list of all system roles — used by the frontend role picker."""
    queryset = Role.objects.filter(is_active=True).order_by('code')
    serializer_class = RoleSerializer
    permission_classes = [IsHRAdmin]


class UserRolesView(APIView):
    """
    GET  /auth/users/<pk>/roles/  → current roles for user
    POST /auth/users/<pk>/roles/  → replace roles; body: {"role_codes": ["HR_MAKER", "RECRUITER"]}
    """
    permission_classes = [IsHRAdmin]

    def _get_user(self, pk):
        try:
            return CustomUser.objects.prefetch_related('roles').get(pk=pk)
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'user_id': str(user.pk),
            'username': user.username,
            'primary_role': user.role,
            'roles': sorted(user.role_codes),
        })

    def post(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        role_codes = request.data.get('role_codes', [])
        if not isinstance(role_codes, list):
            return Response({'detail': 'role_codes must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_codes = set(c for c, _ in CustomUser.ROLE_CHOICES)
        invalid = [c for c in role_codes if c not in valid_codes]
        if invalid:
            return Response(
                {'detail': f'Unknown role codes: {invalid}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Primary role always stays in M2M; combine with submitted list
        codes_to_set = set(role_codes)
        if user.role:
            codes_to_set.add(user.role)

        role_objs = Role.objects.filter(code__in=codes_to_set)
        user.roles.set(role_objs)

        log_action(
            request, 'ROLES_UPDATED', 'CustomUser', str(user.pk),
            after_json={'roles': sorted(codes_to_set)},
        )
        return Response({
            'user_id': str(user.pk),
            'username': user.username,
            'primary_role': user.role,
            'roles': sorted(codes_to_set),
        })
