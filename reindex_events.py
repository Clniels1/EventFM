from website import create_app
from website.models import Event
from website.semantic import index_event

app = create_app()

with app.app_context():
    events = Event.query.all()
    for event in events:
        index_event(event)
        print(f'Indexed event {event.id}: {event.title}')
    print(f'Done. {len(events)} events indexed.')
