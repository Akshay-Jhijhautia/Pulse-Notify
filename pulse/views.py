from django.contrib.auth import authenticate, get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationLog, PriceAlert
from .permissions import IsAdminUser
from .serializers import (
    LoginSerializer,
    PriceAlertCreateSerializer,
    PriceAlertSerializer,
    RegisterSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    """Public endpoint — create a user and return a JWT access token."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        if User.objects.filter(username=username).exists():
            return Response(
                {'username': ['A user with that username already exists.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=serializer.validated_data.get('email', ''),
            password=serializer.validated_data['password'],
        )
        # UserProfile is created by the post_save signal (Feature 2)
        access = str(RefreshToken.for_user(user).access_token)
        return Response(
            {
                'username': user.username,
                'access': access,
                'role': user.profile.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Public endpoint — validate credentials and return a JWT access token."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access = str(RefreshToken.for_user(user).access_token)
        return Response(
            {
                'username': user.username,
                'access': access,
                'role': user.profile.role,
            },
            status=status.HTTP_200_OK,
        )


class PriceAlertListCreateView(APIView):
    """List and create price alerts for the authenticated user only."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user).order_by(
            '-created_at'
        )

    def get(self, request):
        serializer = PriceAlertSerializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PriceAlertCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        alert = PriceAlert.objects.create(
            user=request.user,
            origin=serializer.validated_data['origin'],
            destination=serializer.validated_data['destination'],
            threshold_price=serializer.validated_data['threshold_price'],
        )
        return Response(
            PriceAlertSerializer(alert).data,
            status=status.HTTP_201_CREATED,
        )


class PriceAlertDeactivateView(APIView):
    """Soft-deactivate an alert (INACTIVE). Does not delete the row."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        alert = get_object_or_404(PriceAlert, id=id)
        # Hide existence of other users' alerts
        if alert.user != request.user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        alert.status = PriceAlert.Status.INACTIVE
        alert.save(update_fields=['status'])
        return Response({'status': 'inactive'}, status=status.HTTP_200_OK)


MOCK_PRICES = {
    'DEL-BOM': (3000, 7000),
    'BLR-HYD': (1500, 4000),
    'DEL-BLR': (4000, 9000),
    'BOM-GOA': (2000, 5000),
}


def get_flight_price(request):
    """
    Internal mock price feed.

    Celery tasks will call this with requests.get() — same pattern as a
    real external flight API, but fully under our control.
    """
    import random

    from django.http import JsonResponse

    route = request.GET.get('route', '')
    price_range = MOCK_PRICES.get(route)
    if not price_range:
        return JsonResponse({'error': 'Route not found'}, status=404)

    price = random.randint(*price_range)
    return JsonResponse({'route': route, 'price': price})


class AdminSummaryView(APIView):
    """Platform-wide alert/notification stats — admin role only."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        alert_stats = PriceAlert.objects.aggregate(
            total_alerts=Count('id'),
            active_alerts=Count('id', filter=Q(status=PriceAlert.Status.ACTIVE)),
            triggered_alerts=Count(
                'id',
                filter=Q(status=PriceAlert.Status.TRIGGERED),
            ),
        )
        notification_stats = NotificationLog.objects.aggregate(
            total_notifications=Count('id'),
        )
        top_routes_qs = (
            PriceAlert.objects.values('origin', 'destination')
            .annotate(alert_count=Count('id'))
            .order_by('-alert_count')[:5]
        )
        top_routes = [
            {
                'route': f"{row['origin']}-{row['destination']}",
                'alert_count': row['alert_count'],
            }
            for row in top_routes_qs
        ]

        return Response(
            {
                'total_alerts': alert_stats['total_alerts'],
                'active_alerts': alert_stats['active_alerts'],
                'triggered_alerts': alert_stats['triggered_alerts'],
                'total_notifications': notification_stats['total_notifications'],
                'top_routes': top_routes,
            },
            status=status.HTTP_200_OK,
        )
