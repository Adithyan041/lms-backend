from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # validated_data['password']=make_password(validated_data['password'])
        # return super(UserSerializer, self).create(validated_data)

        role = validated_data.pop('role', 'student')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        user.role = role
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
            data = super().validate(attrs)

        # ✅ Add extra response data
            data['username'] = self.user.username
            data['role'] = self.user.role

            return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Optional (JWT payload)
        token['username'] = user.username
        token['role'] = user.role

        return token
    