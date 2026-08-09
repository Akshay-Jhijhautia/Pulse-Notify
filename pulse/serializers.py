from rest_framework import serializers

from .models import PriceAlert


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=1)
    email = serializers.EmailField(required=False, allow_blank=True)
    # role is intentionally omitted — always defaults to USER via UserProfile signal


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = (
            'id',
            'origin',
            'destination',
            'threshold_price',
            'status',
            'created_at',
        )
        read_only_fields = ('id', 'status', 'created_at')


class PriceAlertCreateSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=10)
    destination = serializers.CharField(max_length=10)
    threshold_price = serializers.DecimalField(max_digits=10, decimal_places=2)
