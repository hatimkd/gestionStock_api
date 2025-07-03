# users/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User, Group

from rest_framework.views import APIView


from .serializers import (
    LoginSerializer,
    UserSerializer,
    CreateUserSerializer,
    AssignRoleSerializer,
    GetCurrentUserInfoSerializer,
)


def is_admin(user):
    """Vérifier si l'utilisateur est admin"""
    return user.is_superuser or user.groups.filter(name="admin").exists()


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):

    print(request.data)

    """Vue de connexion"""
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data["user"]

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Données utilisateur avec rôles
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access_token": str(access_token),
                "refresh_token": str(refresh),
                "user": user_serializer.data,
                "message": "Connexion réussie",
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Identifiants invalides", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_user_view(request):
    """Créer un nouvel utilisateur (admin seulement)"""
    if not is_admin(request.user):
        return Response(
            {
                "error": "Permission refusée. Seuls les admins peuvent créer des utilisateurs."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateUserSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        user_serializer = UserSerializer(user)

        return Response(
            {
                "message": f"Utilisateur {user.username} créé avec succès",
                "user": user_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"error": "Erreur lors de la création", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_roles_view(request):
    """Assigner des rôles à un utilisateur"""
    if not is_admin(request.user):
        return Response(
            {"error": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN
        )

    serializer = AssignRoleSerializer(data=request.data)

    if serializer.is_valid():
        user_id = serializer.validated_data["user_id"]
        roles = serializer.validated_data["roles"]

        user = User.objects.get(id=user_id)
        groups = Group.objects.filter(name__in=roles)
        user.groups.set(groups)

        user_serializer = UserSerializer(user)

        return Response(
            {
                "message": f"Rôles assignés à {user.username}",
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Erreur lors de l'assignation", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_users_view(request):
    """Lister tous les utilisateurs (admin seulement)"""
    if not is_admin(request.user):
        return Response(
            {"error": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN
        )

    users = User.objects.all()
    serializer = UserSerializer(users, many=True)

    return Response(
        {"users": serializer.data, "total": users.count()}, status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_groups_view(request):
    """Lister tous les groupes disponibles"""
    if not is_admin(request.user):
        return Response(
            {"error": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN
        )

    groups = Group.objects.all()
    groups_data = [{"id": g.id, "name": g.name} for g in groups]

    return Response(
        {"groups": groups_data, "total": groups.count()}, status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_user_view(request, user_id):
    """Supprimer un utilisateur"""
    if not is_admin(request.user):
        return Response(
            {"error": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN
        )

    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return Response(
                {"error": "Impossible de supprimer un superutilisateur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = user.username
        user.delete()

        return Response(
            {"message": f"Utilisateur {username} supprimé avec succès"},
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        return Response(
            {"error": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = GetCurrentUserInfoSerializer(request.user)
        return Response(serializer.data)


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Vérifie si l'utilisateur est dans le groupe "admin"
        if user.groups.filter(name="admin").exists():
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        return Response({"detail": "Accès refusé"}, status=403)


class FournisseurListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
            user = request.user
        # Vérifie si l'utilisateur est dans le groupe "admin"

            users = User.objects.filter(groups__name="fournisseur")
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
