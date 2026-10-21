import re
from markupsafe import Markup, escape
from .models import Acknowledgement

GENERIC_STATEMENT = ('We acknowledge the Traditional Custodians of the land on which this event takes place, '
                     'and pay our respects to their Elders past and present. We recognise their continuing '
                     'connection to land, waters and culture.')

# Traditional Custodians of Australia's capital cities, based on the acknowledgements published by
# local councils and government bodies. These cover the city centre only - greater metropolitan
# areas include other Countries, so events outside the CBD should be checked locally.
CAPITAL_CITIES = {
    'adelaide': {
        'city': 'Adelaide', 'state': 'SA',
        'custodians': 'Kaurna people',
        'place_name': 'Tarntanya',
        'note': 'Spellings vary (Tarntanya / Tarndanya). The council publishes its acknowledgement with a Kaurna translation.',
        'source': 'City of Adelaide',
        'url': 'https://www.cityofadelaide.com.au/community/reconciliation/acknowledgement-and-welcome-to-country/',
    },
    'brisbane': {
        'city': 'Brisbane', 'state': 'QLD',
        'custodians': 'Turrbal and Jagera peoples',
        'place_name': 'Meanjin',
        'note': 'Spellings vary (Turrbal / Turrbul, Jagera / Yuggera / Yugara). Custodianship of parts of Brisbane is disputed, so most state government bodies name both peoples.',
        'source': 'Office of the Queensland Parliamentary Counsel',
        'url': 'https://www.oqpc.qld.gov.au/acknowledgement-country',
    },
    'canberra': {
        'city': 'Canberra', 'state': 'ACT',
        'custodians': 'Ngunnawal people',
        'place_name': '',
        'note': 'Contested. The ACT Government recognises the Ngunnawal people, and in 2023 apologised to the Ngambri people for recognising only one group. Check current advice.',
        'source': 'SBS NITV',
        'url': 'https://www.sbs.com.au/nitv/article/act-govt-apologies-to-ngambri-people-for-failing-to-recognise-them-as-traditional-custodians/nobqw2lx5',
    },
    'darwin': {
        'city': 'Darwin', 'state': 'NT',
        'custodians': 'Larrakia people',
        'place_name': 'Garramilla',
        'note': "The council's acknowledgement covers all land and waters of Greater Darwin and was written with Larrakia Traditional Owners.",
        'source': 'City of Darwin',
        'url': 'https://www.darwin.nt.gov.au/',
    },
    'hobart': {
        'city': 'Hobart', 'state': 'TAS',
        'custodians': 'muwinina people',
        'place_name': 'nipaluna',
        'note': 'palawa kani names are written in lower case. The council also pays respect to Aboriginal people living in and around the city today.',
        'source': 'City of Hobart',
        'url': 'https://www.hobartcity.com.au/Services/Community-programs/Aboriginal-programs',
    },
    'melbourne': {
        'city': 'Melbourne', 'state': 'VIC',
        'custodians': 'Wurundjeri Woi-wurrung and Bunurong / Boon Wurrung peoples of the Kulin',
        'place_name': 'Naarm',
        'note': "The council names both peoples. Outside the city, Victoria's Registered Aboriginal Parties can confirm the custodians.",
        'source': 'City of Melbourne',
        'url': 'https://www.melbourne.vic.gov.au/',
    },
    'perth': {
        'city': 'Perth', 'state': 'WA',
        'custodians': 'Whadjuk Noongar people',
        'place_name': 'Boorloo',
        'note': "Spellings vary (Noongar / Nyoongar / Nyungar). Recognised in the City of Perth's Yacker Danjoo Ngala Bidi agreement (2021).",
        'source': 'National Indigenous Times',
        'url': 'https://nit.com.au/recognition-for-whadjuk-over-boorloo/',
    },
    'sydney': {
        'city': 'Sydney', 'state': 'NSW',
        'custodians': 'Gadigal people of the Eora Nation',
        'place_name': '',
        'note': 'Gadigal Country is the CBD. Greater Sydney takes in other Countries, including Dharug, Dharawal, Gundungurra and Guringai.',
        'source': 'City of Sydney',
        'url': 'https://www.cityofsydney.nsw.gov.au/',
    },
}

REGION_CHOICES = ([('', 'Select a city or region')]
                  + [(key, f"{c['city']}, {c['state']} (city centre)") for key, c in CAPITAL_CITIES.items()]
                  + [('other', 'Somewhere else in Australia')])

# How the event creator confirmed who the Traditional Custodians are
SOURCE_CHOICES = [
    ('', 'Select the source you used'),
    ('capital', 'EventFM capital city reference (council-published acknowledgements)'),
    ('council', 'Local council website or Reconciliation Action Plan'),
    ('land-council', 'Local Aboriginal Land Council, Registered Aboriginal Party or Traditional Owner organisation'),
    ('traditional-owners', 'Spoke directly with Traditional Owners or a local Aboriginal organisation'),
    ('aiatsis', 'AIATSIS Map of Indigenous Australia, confirmed with a local source'),
    ('nntt', 'National Native Title Tribunal register'),
    ('know-your-country', 'Know Your Country'),
]
SOURCE_LABELS = dict(SOURCE_CHOICES)

# Where to look up the Traditional Custodians of a specific place
RESOURCES = [
    {'name': 'AIATSIS: Whose Country am I on?',
     'url': 'https://aiatsis.gov.au/whose-country-am-i',
     'use': "How to research whose Country you're on."},
    {'name': 'AIATSIS: Map of Indigenous Australia',
     'url': 'https://aiatsis.gov.au/map-indigenous-australia',
     'use': 'Shows roughly where language and nation groups are. Boundaries are approximate, so confirm names locally.'},
    {'name': 'Know Your Country',
     'url': 'https://www.knowyourcountry.com.au/',
     'use': "First Nations-led campaign for finding out whose Country you're on."},
    {'name': 'Your local council',
     'url': None,
     'use': 'Most councils publish an acknowledgement or Reconciliation Action Plan agreed with local Traditional Owners.'},
    {'name': 'Land councils and Traditional Owner organisations',
     'url': 'https://alc.org.au/',
     'use': 'Local Aboriginal Land Councils in NSW, Registered Aboriginal Parties in Victoria, native title bodies '
            'elsewhere. These are also who to contact about a Welcome to Country.'},
    {'name': 'National Native Title Tribunal',
     'url': 'https://www.nntt.gov.au/',
     'use': "Native title registers. No determination for an area doesn't mean there are no Traditional Owners."},
    {'name': 'Reconciliation Australia',
     'url': 'https://www.reconciliation.org.au/reconciliation/acknowledgement-of-country-and-welcome-to-country/',
     'use': 'Background on both protocols, with sample wording.'},
]

MISTAKES = [
    ('Treating it as a formality',
     'Rushing through a script before the event starts. If it isn\'t sincere, it\'s not appropriate.'),
    ('Welcoming people to Country',
     'Only Traditional Owners can do this. Avoid wording like "we welcome you to this land".'),
    ('Guessing who the custodians are',
     "Check names and spelling with a local source. A capital city's custodians don't cover the whole metro area."),
    ('Using the past tense',
     'Phrases like "who used to live here" ignore that the connection to Country continues.'),
    ('Overclaiming',
     "Don't mention First Nations artists or community support unless your event actually has them."),
    ('Using language words unchecked',
     'Check the spelling, whether local custodians are happy for it to be used, and how to pronounce it.'),
]

CONTESTED = [
    ('"Elders past, present and emerging"',
     'Widely used, but some people question "emerging". Reconciliation Australia uses "Elders past and present".'),
    ('Disputed custodianship',
     "In Canberra and parts of Brisbane more than one group claims a connection. Don't pick a side: follow "
     'current local advice or acknowledge all groups.'),
    ('Sovereignty',
     '"Sovereignty was never ceded" is accurate and common, but only say it if your organisation stands behind it.'),
]


def guess_region(location):
    """Suggest a capital city key from a free-text event location."""
    location = (location or '').lower()
    for key, city in CAPITAL_CITIES.items():
        if city['city'].lower() in location:
            return key
    return ''


def _sentence(text):
    text = ' '.join((text or '').split())
    if text and text[-1] not in '.!?':
        text += '.'
    return text


def build_enhanced_statement(custodians, region='', place_name='', connection='', commitment=''):
    """Assemble a tailored acknowledgement from the builder's parts."""
    city = CAPITAL_CITIES.get(region, {}).get('city')
    place_name = (place_name or '').strip()
    if place_name and city:
        where = f'{place_name} ({city})'
    elif place_name:
        where = place_name
    elif city:
        where = f'the land now known as {city}'
    else:
        where = 'the land'

    parts = [
        f'We acknowledge the {custodians.strip()} as the Traditional Custodians of {where}, '
        f'where this event takes place.',
        'We pay our respects to their Elders past and present, and extend that respect to all '
        'Aboriginal and Torres Strait Islander people joining us.',
        _sentence(connection),
        _sentence(commitment),
    ]
    return ' '.join(p for p in parts if p)


def review_statement(text, custodians=''):
    """Check a draft for common mistakes. Returns a list of (level, message) tuples."""
    text = text or ''
    lowered = text.lower()
    issues = []
    if re.search(r'\bwelcom', lowered):
        issues.append(('warning', 'Your statement uses "welcome". Only Traditional Owners can welcome people '
                                  'to Country, so an Acknowledgement should not welcome people to the land.'))
    if re.search(r'\b(used to|once (lived|owned|inhabited|occupied))\b', lowered):
        issues.append(('warning', 'Avoid the past tense: connection to Country is continuing.'))
    if re.search(r'\baborigines\b', lowered):
        issues.append(('warning', '"Aborigines" is outdated. Use "Aboriginal and Torres Strait Islander '
                                  'peoples" or "First Nations peoples".'))
    name_words = [w for w in custodians.lower().split() if w != 'the']
    if name_words and name_words[0] not in lowered:
        issues.append(('warning', f'Your statement does not name the {custodians.strip()}, the Traditional '
                                  'Custodians you identified.'))
    if re.search(r'\bemerging\b', lowered):
        issues.append(('note', 'Some people question "Elders emerging". "Elders past and present" is the '
                               'wording in Reconciliation Australia\'s guidance.'))
    if re.search(r'\b(ceded|sovereignty)\b', lowered):
        issues.append(('note', 'Include a sovereignty statement only if your organisation genuinely stands '
                               'behind it.'))
    if len(text.split()) < 30:
        issues.append(('note', 'This is quite short. A sentence about why this Country matters to your event '
                               'makes an acknowledgement meaningful rather than formulaic.'))
    return issues


# Labels for the parts of the statement template that have not been filled in yet
PREVIEW_SLOTS = {
    'custodians': 'custodian names',
    'place': 'place',
    'connection': 'why this Country matters to your event',
    'commitment': 'what your event is doing (optional)',
}


def preview_statement(form):
    """Statement the builder will write from the current answers, as HTML with
    highlighted slots for the parts that have not been filled in yet."""
    def slot(name):
        return f'\x00{name}\x00'  # marker swapped for a highlighted span below

    region = form.aoc_region.data
    custodians = (form.aoc_custodians.data or '').strip()
    if not custodians and region in CAPITAL_CITIES:
        custodians = CAPITAL_CITIES[region]['custodians']
    place_name = (form.aoc_place_name.data or '').strip()
    if not place_name and region not in CAPITAL_CITIES:
        place_name = slot('place')

    text = build_enhanced_statement(custodians or slot('custodians'), region, place_name,
                                    (form.aoc_connection.data or '').strip() or slot('connection'),
                                    (form.aoc_commitment.data or '').strip() or slot('commitment'))
    # escape the user's text first, then insert the slot markup (dropping the full stop added after a slot)
    html = re.sub(r'\x00(\w+)\x00\.?',
                  lambda m: f'<span class="aoc-slot">{PREVIEW_SLOTS[m.group(1)]}</span>',
                  str(escape(text)))
    return Markup(html)


def load_into_form(form, event):
    """Pre-fill the builder fields when editing an event."""
    detail = event.acknowledgement
    if not detail:
        form.aoc_region.data = guess_region(event.location)
    else:
        form.aoc_region.data = detail.region
        form.aoc_custodians.data = detail.custodians
        form.aoc_place_name.data = detail.place_name
        form.aoc_source.data = detail.source
        form.aoc_connection.data = detail.connection
        form.aoc_commitment.data = detail.commitment
        form.aoc_welcome.data = detail.welcome_to_country
        # the creator already confirmed these when the acknowledgement was first saved
        form.aoc_check_names.data = form.aoc_check_genuine.data = form.aoc_check_difference.data = True
        # only show the statement as custom wording if the creator wrote it themselves,
        # so an auto-written statement keeps following the answers
        auto = build_enhanced_statement(detail.custodians, detail.region, detail.place_name or '',
                                        detail.connection, detail.commitment or '')
        if event.acknowledgement_text == auto:
            form.acknowledgement_text.data = ''


def apply_to_event(form, event):
    """Save the chosen acknowledgement type, statement and builder details onto an event."""
    choice = form.acknowledgement_type.data
    event.acknowledgement_type = choice
    if choice != 'enhanced':
        event.acknowledgement_text = GENERIC_STATEMENT if choice == 'generic' else None
        event.acknowledgement = None
        return

    detail = event.acknowledgement or Acknowledgement()
    detail.region = form.aoc_region.data
    detail.custodians = form.aoc_custodians.data.strip()
    detail.place_name = (form.aoc_place_name.data or '').strip() or None
    detail.source = form.aoc_source.data
    detail.connection = form.aoc_connection.data.strip()
    detail.commitment = (form.aoc_commitment.data or '').strip() or None
    detail.welcome_to_country = bool(form.aoc_welcome.data)
    event.acknowledgement = detail

    text = (form.acknowledgement_text.data or '').strip()
    event.acknowledgement_text = text or build_enhanced_statement(
        detail.custodians, detail.region, detail.place_name or '', detail.connection, detail.commitment or '')
