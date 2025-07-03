# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from django.contrib.auth.models import User, Group  # ← Ajoutez Group ici
from django.core.validators import validate_email  # ← Ajoutez ceci aussi


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data["user"] = user
                    return data
                else:
                    raise serializers.ValidationError("User account is disabled.")
            else:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Must include username and password.")


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "roles"]

    def get_roles(self, obj):
        groups = obj.groups.all()

        return groups[0].name if groups else ""


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    roles = serializers.ListField(child=serializers.CharField(), required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "roles"]

    def validate_email(self, value):
        if value:
            validate_email(value)
        return value

    def validate_roles(self, value):
        if value:
            # Vérifier que les rôles existent
            existing_groups = Group.objects.filter(name__in=value)
            if len(existing_groups) != len(value):
                invalid_roles = set(value) - set(
                    existing_groups.values_list("name", flat=True)
                )
                raise serializers.ValidationError(
                    f"Rôles invalides: {list(invalid_roles)}"
                )
        return value

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        user = User.objects.create_user(**validated_data)

        # Assigner les rôles
        if roles:
            groups = Group.objects.filter(name__in=roles)
            user.groups.set(groups)

        return user


class AssignRoleSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    roles = serializers.ListField(child=serializers.CharField())

    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")
        return value

    def validate_roles(self, value):
        existing_groups = Group.objects.filter(name__in=value)
        if len(existing_groups) != len(value):
            invalid_roles = set(value) - set(
                existing_groups.values_list("name", flat=True)
            )
            raise serializers.ValidationError(f"Rôles invalides: {list(invalid_roles)}")
        return value
    
    

class GetCurrentUserInfoSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "roles"]

    def get_roles(self, obj):
        groups = obj.groups.all()
        return groups[0].name if groups else ""
