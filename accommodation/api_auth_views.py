from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .dynamo_users import get_user_from_dynamo
import json

@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    """Login user using DynamoDB and return JWT tokens."""
    username_or_email = request.data.get('username')
    password = request.data.get('password')

    user = get_user_from_dynamo(username_or_email)
    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if not check_password(password, user.get('password')):
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    # Create tokens
    refresh = RefreshToken.for_user_id(user['user_id'])
    access_token = str(refresh.access_token)

    return Response({
        'access': access_token,
        'refresh': str(refresh),
        'username': user['username'],
        'email': user['email'],
        'role': user.get('role', 'customer')
    }, status=status.HTTP_200_OK)
