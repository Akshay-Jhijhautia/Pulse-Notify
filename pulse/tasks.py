import requests
from celery import shared_task

from .models import NotificationLog, PriceAlert


@shared_task
def check_prices():
    """
    Celery Beat task (every 60s): fetch prices for active alert routes
    and enqueue send_notification when a threshold is met.
    """
    active_alerts = PriceAlert.objects.filter(status=PriceAlert.Status.ACTIVE)
    routes = active_alerts.values_list('origin', 'destination').distinct()

    for origin, destination in routes:
        route = f'{origin}-{destination}'

        response = requests.get(
            'http://localhost:8000/api/flights/price/',
            params={'route': route},
            timeout=10,
        )
        if response.status_code != 200:
            continue

        current_price = response.json().get('price')
        if current_price is None:
            continue

        route_alerts = active_alerts.filter(
            origin=origin,
            destination=destination,
        )
        for alert in route_alerts:
            if current_price <= float(alert.threshold_price):
                # .delay() = enqueue async; Beat does not wait for the write
                send_notification.delay(alert.id, current_price)


@shared_task
def send_notification(alert_id, triggered_price):
    """Async task: write NotificationLog and mark the alert as TRIGGERED."""
    alert = PriceAlert.objects.get(id=alert_id)
    message = (
        f'Price alert triggered! {alert.origin}-{alert.destination} '
        f'is now ₹{triggered_price} — below your threshold of '
        f'₹{alert.threshold_price}'
    )
    NotificationLog.objects.create(
        alert=alert,
        triggered_price=triggered_price,
        message=message,
    )
    alert.status = PriceAlert.Status.TRIGGERED
    alert.save(update_fields=['status'])
