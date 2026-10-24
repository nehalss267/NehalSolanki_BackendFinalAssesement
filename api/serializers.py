from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()


class HealthCheckViewSet(viewsets.ViewSet):
    serializer_class = HealthCheckSerializer
    
    def list(self, request):
        return Response({
            'status': 'ok',
            'message': 'Backend API is running successfully'
        })
    
    @action(detail=False, methods=['get'])
    def ping(self, request):
        return Response({'message': 'pong'})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
