from datetime import date, time
from werkzeug.security import generate_password_hash
from website import create_app, db
from website.models import User, Event
from website.semantic import index_event

DUMMY_EVENTS = [
    {
        "title": "Riverstage Indie Fest",
        "description": "An electrifying outdoor festival featuring Australia's best indie-rock bands along the Brisbane River. Enjoy food trucks, local craft brews, and unforgettable live performances.",
        "date": date(2026, 11, 14),
        "start_time": time(14, 0),
        "end_time": time(22, 30),
        "location": "Riverstage, Brisbane, QLD",
        "genre": "indie-rock",
        "price": 89.00,
        "capacity": 5000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Turrbal and Jagera peoples as the Traditional Custodians of Meanjin (Brisbane), the lands and waterways on which this festival takes place. We pay our respects to their Elders past, present, and emerging."
    },
    {
        "title": "Neon Horizon Electronic Carnival",
        "description": "A multi-stage electronic wonderland featuring world-renowned DJs, immersive laser installations, and pulsating basslines across the open fields.",
        "date": date(2026, 12, 5),
        "start_time": time(15, 0),
        "end_time": time(23, 0),
        "location": "Flemington Racecourse, Melbourne, VIC",
        "genre": "electronic-dance",
        "price": 135.50,
        "capacity": 12000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Traditional Custodians of the land upon which this event is held, and pay our respects to their Elders past, present, and emerging."
    },
    {
        "title": "Sunset Rhythms Jazz & Blues",
        "description": "Intimate open-air jazz and soul sessions set against the iconic harbour backdrop as the sun sinks beneath the horizon.",
        "date": date(2026, 11, 28),
        "start_time": time(16, 30),
        "end_time": time(22, 0),
        "location": "Sydney Opera House Forecourt, Sydney, NSW",
        "genre": "jazz-blues",
        "price": 95.00,
        "capacity": 2500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Gadigal people of the Eora Nation, the Traditional Custodians of the land on which Bennelong Point stands. We celebrate their enduring storytelling and musical traditions."
    },
    {
        "title": "Outback Sunset Country Muster",
        "description": "Stomp your boots to high-energy modern country anthems, acoustic balladeers, and heartland rock under the expansive Queensland sky.",
        "date": date(2026, 10, 24),
        "start_time": time(12, 0),
        "end_time": time(21, 0),
        "location": "Roma Street Parkland, Brisbane, QLD",
        "genre": "country",
        "price": 75.00,
        "capacity": 3500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We pay our respects to the Traditional Custodians of the land on which we gather and their continuous connection to Country."
    },
    {
        "title": "Urban Pulse Hip-Hop Summit",
        "description": "Australia's premier celebration of urban music featuring headline lyricists, beat battles, breakdancing jams, and community street art.",
        "date": date(2026, 12, 18),
        "start_time": time(17, 0),
        "end_time": time(23, 30),
        "location": "Hordern Pavilion, Sydney, NSW",
        "genre": "hip-hop-rap",
        "price": 110.00,
        "capacity": 5500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We recognize the Gadigal people of the Eora Nation and honour the rich history of First Nations artists who lead Australian hip-hop and truth-telling."
    },
    {
        "title": "Symphony Under the Stars",
        "description": "An enchanting evening of timeless masterpieces performed by a full 70-piece philharmonic orchestra amidst lush botanical gardens.",
        "date": date(2026, 11, 8),
        "start_time": time(18, 0),
        "end_time": time(21, 30),
        "location": "Kings Park, Perth, WA",
        "genre": "classical",
        "price": 60.00,
        "capacity": 4000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Whadjuk Nyoongar people as the Traditional Custodians of Boorloo (Perth) and pay respect to their sacred connection to these lands."
    },
    {
        "title": "Iron & Steel Metal Massacre",
        "description": "Relentless riffs, thundering double-kicks, and fierce moshpits featuring the heaviest thrash, groove, and death metal acts across Australasia.",
        "date": date(2026, 11, 21),
        "start_time": time(13, 0),
        "end_time": time(23, 0),
        "location": "Eaton's Hill Outdoor Arena, Brisbane, QLD",
        "genre": "heavy-metal",
        "price": 120.00,
        "capacity": 3000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "none",
        "acknowledgement_text": None
    },
    {
        "title": "Byron Bay Acoustic & Folk Gathering",
        "description": "Soul-stirring songwriting, fingerstyle guitars, and intimate storytelling surrounded by coastal hinterland trees and artisan markets.",
        "date": date(2026, 12, 12),
        "start_time": time(11, 0),
        "end_time": time(22, 0),
        "location": "Tyagarah Tea Tree Farm, Byron Bay, NSW",
        "genre": "folk-acoustic",
        "price": 105.00,
        "capacity": 6000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We pay tribute to the Bundjalung Nation, custodians of this sacred coastal gathering place for thousands of generations."
    },
    {
        "title": "Bassquake Bass & EDM Fest",
        "description": "A high-octane celebration of dubstep, trap, and drum-and-bass powered by mammoth custom horn sound systems and pyrotechnics.",
        "date": date(2027, 1, 16),
        "start_time": time(14, 0),
        "end_time": time(23, 0),
        "location": "Sydney Showground, Olympic Park, Sydney, NSW",
        "genre": "edm",
        "price": 145.00,
        "capacity": 15000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Traditional Owners of the lands on which this venue stands and pay respects to Elders past, present, and emerging."
    },
    {
        "title": "Soul Haven R&B Revival",
        "description": "Smooth harmonies, golden-hour grooves, and contemporary soul sensations delivering emotional vocals and live horns in Melbourne's amphitheatre.",
        "date": date(2026, 11, 20),
        "start_time": time(16, 0),
        "end_time": time(22, 30),
        "location": "Sidney Myer Music Bowl, Melbourne, VIC",
        "genre": "rnb-soul",
        "price": 99.00,
        "capacity": 7000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Wurundjeri Woi-wurrung people of the Kulin Nation and pay our deepest respects to their Elders past and present."
    },
    {
        "title": "Concrete Chaos Punk Fest",
        "description": "Fast, raw, and unapologetic three-chord punk rock, DIY zine stalls, and unhinged energy in a legendary underground Brisbane venue.",
        "date": date(2026, 10, 31),
        "start_time": time(15, 0),
        "end_time": time(23, 30),
        "location": "The Tivoli, Brisbane, QLD",
        "genre": "punk-hardcore",
        "price": 65.00,
        "capacity": 1500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "none",
        "acknowledgement_text": None
    },
    {
        "title": "Grit & Feedback Grunge Fest",
        "description": "Distorted guitars, flannel shirts, and visceral 90s alternative anthems performed by veteran rockers and emerging powerhouse trios.",
        "date": date(2026, 11, 6),
        "start_time": time(18, 0),
        "end_time": time(23, 0),
        "location": "Enmore Theatre, Sydney, NSW",
        "genre": "post-grunge",
        "price": 70.00,
        "capacity": 2200,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Traditional Custodians of this land and extend our respect to all First Nations people present today."
    },
    {
        "title": "Coastal Chill Pop Fiesta",
        "description": "A sun-drenched family-friendly pop spectacle featuring chart-topping Australian soloists, beachside activities, and fireworks.",
        "date": date(2027, 1, 23),
        "start_time": time(13, 0),
        "end_time": time(21, 30),
        "location": "Broadwater Parklands, Gold Coast, QLD",
        "genre": "pop",
        "price": 85.00,
        "capacity": 8000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We honour the Yugambeh language people, Traditional Owners of Kombumerri Country, and their enduring kinship with land, waters, and community."
    },
    {
        "title": "Subterranean Sounds Alternative Showcase",
        "description": "Shoegaze, dream-pop, and math-rock collectives meeting for an audiovisual experience of hypnotic projections and reverb-drenched riffs.",
        "date": date(2026, 12, 4),
        "start_time": time(17, 0),
        "end_time": time(23, 0),
        "location": "Adelaide Entertainment Centre, Adelaide, SA",
        "genre": "alternative",
        "price": 88.00,
        "capacity": 3200,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Kaurna people as the Traditional Custodians of the Adelaide Plains where we gather to share art and song."
    },
    {
        "title": "Solaris Twilight EDM Expedition",
        "description": "An open-air amphitheatre festival with melodic house and techno tracks welcoming the sunset over the Western Australian hills.",
        "date": date(2026, 11, 27),
        "start_time": time(16, 0),
        "end_time": time(23, 45),
        "location": "Red Hill Auditorium, Perth, WA",
        "genre": "edm",
        "price": 115.00,
        "capacity": 4500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We pay respect to the Traditional Custodians of this land and recognise their continuous connection to Country."
    },
    {
        "title": "Velvet Lounge Midnight Jazz",
        "description": "A sophisticated cabaret-style showcase celebrating jazz improvisations, smoky saxophones, and timeless vocal swing under chandelier lights.",
        "date": date(2027, 2, 14),
        "start_time": time(19, 0),
        "end_time": time(23, 0),
        "location": "Palais Theatre, Melbourne, VIC",
        "genre": "jazz-blues",
        "price": 110.00,
        "capacity": 2800,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We respectfully acknowledge the Bunurong Boon Wurrung and Wurundjeri Woi-wurrung peoples of the Kulin Nation."
    },
    {
        "title": "High Voltage Rock Clash",
        "description": "Loud, arena-sized guitars, roaring crowds, and hard rock anthems paying tribute to legendary Australian rock heritage.",
        "date": date(2027, 2, 20),
        "start_time": time(14, 0),
        "end_time": time(22, 30),
        "location": "Newcastle Entertainment Centre, Newcastle, NSW",
        "genre": "indie-rock",
        "price": 92.00,
        "capacity": 4000,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Awabakal and Worimi peoples, Traditional Custodians of Newcastle and the surrounding waterways."
    },
    {
        "title": "Harbour Beats Urban Jam",
        "description": "Flows, 808 beats, and boundary-pushing Australian grime and hip-hop acts rocking the waterside on Sydney Harbour.",
        "date": date(2027, 3, 6),
        "start_time": time(15, 30),
        "end_time": time(22, 30),
        "location": "Overseas Passenger Terminal, Sydney, NSW",
        "genre": "hip-hop-rap",
        "price": 105.00,
        "capacity": 3500,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We pay our deepest respects to the Gadigal people of the Eora Nation, whose sovereign custodianship of these waters was never ceded."
    },
    {
        "title": "Mountain Mist Folk & Strings",
        "description": "Echoing banjos, cellos, and poignant lyricism nestled high in the misty mountain ranges. Warm cider and campfire vibes included.",
        "date": date(2027, 3, 20),
        "start_time": time(11, 0),
        "end_time": time(20, 0),
        "location": "Blue Mountains Cultural Centre, Katoomba, NSW",
        "genre": "folk-acoustic",
        "price": 55.00,
        "capacity": 1200,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We acknowledge the Dharug and Gundungurra peoples as the traditional owners of Ngurra (Country) in the Blue Mountains."
    },
    {
        "title": "Echoes of Eternity Chamber Orchestra",
        "description": "A transcendent acoustic experience bringing together classical concertos, baroque suites, and modern minimalist compositions.",
        "date": date(2027, 4, 10),
        "start_time": time(19, 30),
        "end_time": time(22, 0),
        "location": "Queensland Performing Arts Centre (QPAC), Brisbane, QLD",
        "genre": "classical",
        "price": 80.00,
        "capacity": 1800,
        "image_filename": None,
        "status": "Open",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Traditional Custodians of this region and pay respects to Elders past, present, and emerging."
    },
    {
        "title": "Autumn Equinox Dance Carnival",
        "description": "A landmark outdoor dance event celebrating the turning of the season with heavyweight UK garage and progressive house producers.",
        "date": date(2026, 3, 21),
        "start_time": time(12, 0),
        "end_time": time(22, 0),
        "location": "Melbourne Showgrounds, Melbourne, VIC",
        "genre": "electronic-dance",
        "price": 125.00,
        "capacity": 10000,
        "image_filename": None,
        "status": "Inactive",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We honour the Wurundjeri Woi-wurrung people of the Kulin Nation, custodians of these lands where music has united people for millennia."
    },
    {
        "title": "Winter Solstice Blues Jam",
        "description": "Warming the coldest night of winter with searing blues guitar solos, smoky harmonicas, and Southern-style BBQ cookouts.",
        "date": date(2026, 6, 21),
        "start_time": time(16, 0),
        "end_time": time(23, 0),
        "location": "The Gov, Adelaide, SA",
        "genre": "jazz-blues",
        "price": 60.00,
        "capacity": 800,
        "image_filename": None,
        "status": "Inactive",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Kaurna people, Traditional Owners of Adelaide, and pay our respects to their culture."
    },
    {
        "title": "Retro Rewind 90s Pop Bash",
        "description": "A nostalgic celebration of dance-pop anthems, boyband hits, and glittery synth hooks that defined an unforgettable decade.",
        "date": date(2026, 8, 15),
        "start_time": time(18, 0),
        "end_time": time(23, 30),
        "location": "Fortitude Music Hall, Brisbane, QLD",
        "genre": "pop",
        "price": 75.00,
        "capacity": 3000,
        "image_filename": None,
        "status": "Inactive",
        "acknowledgement_type": "none",
        "acknowledgement_text": None
    },
    {
        "title": "Stormfront Hardcore Fest",
        "description": "Aggressive breakdown-heavy hardcore and crossover thrash in an intense warehouse venue. Cancelled due to severe regional cyclone warnings.",
        "date": date(2026, 10, 17),
        "start_time": time(16, 0),
        "end_time": time(23, 0),
        "location": "Manning Bar, Sydney, NSW",
        "genre": "punk-hardcore",
        "price": 50.00,
        "capacity": 950,
        "image_filename": None,
        "status": "Cancelled",
        "acknowledgement_type": "generic",
        "acknowledgement_text": "We acknowledge the Traditional Custodians of this land and honour their enduring heritage."
    },
    {
        "title": "Desert Bloom Indie Extravaganza",
        "description": "A destination desert music festival showcasing alternative talent under the red sands. Cancelled due to scheduled park maintenance and logistics.",
        "date": date(2026, 11, 7),
        "start_time": time(13, 0),
        "end_time": time(22, 0),
        "location": "Alice Springs Desert Park, Alice Springs, NT",
        "genre": "alternative",
        "price": 110.00,
        "capacity": 2500,
        "image_filename": None,
        "status": "Cancelled",
        "acknowledgement_type": "enhanced",
        "acknowledgement_text": "We pay respect to the Arrernte people, Traditional Owners of Mparntwe (Alice Springs) and surrounding desert country."
    }
]

def seed_database():
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Find or create a default organiser user to satisfy the foreign key constraint
        organiser = User.query.filter_by(name="festival_host").first()
        if not organiser:
            organiser = User(
                name="festival_host",
                first_name="Event",
                surname="Admin",
                emailid="organiser@eventfm.com.au",
                password_hash=generate_password_hash("EventFM2026!"),
                contact_number="0412345678",
                street_address="123 Cultural Way, Brisbane QLD 4000",
                user_type="organiser"
            )
            db.session.add(organiser)
            db.session.commit()
            print(f"Created default organiser user '{organiser.name}' (id={organiser.id}).")
        else:
            print(f"Found existing organiser user '{organiser.name}' (id={organiser.id}).")

        # Insert events if they don't already exist
        created_count = 0
        for event_data in DUMMY_EVENTS:
            existing_event = Event.query.filter_by(title=event_data["title"]).first()
            if not existing_event:
                event = Event(
                    title=event_data["title"],
                    description=event_data["description"],
                    date=event_data["date"],
                    start_time=event_data["start_time"],
                    end_time=event_data["end_time"],
                    location=event_data["location"],
                    genre=event_data["genre"],
                    price=event_data["price"],
                    capacity=event_data["capacity"],
                    image_filename=event_data["image_filename"],
                    status=event_data["status"],
                    acknowledgement_type=event_data["acknowledgement_type"],
                    acknowledgement_text=event_data["acknowledgement_text"],
                    user_id=organiser.id
                )
                db.session.add(event)
                created_count += 1

        db.session.commit()

        # embed every event that has no chunks yet so semantic search can find it
        for event in Event.query.all():
            if not event.chunks:
                index_event(event)

        print(f"Successfully seeded {created_count} events into the database. Total events now: {Event.query.count()}.")

if __name__ == '__main__':
    seed_database()
