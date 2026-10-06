# admin_panel/events/views.py
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Event
import csv

@csrf_exempt
def export_events(request):
    telegram_id = request.GET.get('telegram_id')
    if not telegram_id:
        return HttpResponse("Не указан telegram_id", status=400)

    events = Event.objects.filter(telegram_id=telegram_id)

    fmt = request.GET.get('format', 'json')

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="events.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Название', 'Дата', 'Время', 'Описание'])
        for event in events:
            writer.writerow([
                event.id,
                event.name,
                event.date,
                event.time,
                event.details
            ])
        return response

    data = [
        {
            'id': event.id,
            'name': event.name,
            'date': event.date.isoformat(),
            'time': event.time.isoformat(),
            'details': event.details
        }
        for event in events
    ]
    return JsonResponse(data, safe=False)
