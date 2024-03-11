# curl 'https://api.memberhub.co/services/memberhub-service/events' -X POST -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://somersetelementary.memberhub.com/' -H 'Content-Type: application/json' -H 'MemberHub-Session-Token: ad8497e0-0a7a-4f6f-a6e7-3f7ce172a42a' -H 'MemberHub-Session-Secret: 1ed608ef-6826-4648-a984-4b9b7878c92d' -H 'Origin: https://somersetelementary.memberhub.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -H 'TE: trailers' --data-raw '{"event":{"loaded":true,"calendar":true,"saving":false,"repeat_every":1,"remind_timeframe":"day","remind_hour":9,"timezone":"America/New_York","name":"BSTN K-2","public":true,"country":"US","state":"AL","location_name":"All Purpose Room","starting_at":"2022-09-07T22:30:00.000Z","ending_at":"2022-09-08T00:00:00.000Z","recipients":{"everyone":false,"organizations":[],"officers":[],"roles":[],"stripe":[],"traits":[],"users":[],"years":[],"checked":[],"recipients":[],"meta":{"count":0,"has_more":false,"limit":20,"offset":0,"total":0},"organization":{"uuid":"5e3494f2-db0d-4f81-a25a-8058e4abced5"},"school_year":{"end_date":"2023-06-30","end_time":"2023-06-30T23:59:59-04:00","end_year":2023,"start_date":"2022-07-01","start_time":"2022-07-01T00:00:00-04:00","start_year":2022,"today":"2022-08-31","now":"2022-08-31T16:32:25-04:00","year":2023},"current_school_year":{"end_date":"2023-06-30","end_time":"2023-06-30T23:59:59-04:00","end_year":2023,"start_date":"2022-07-01","start_time":"2022-07-01T00:00:00-04:00","start_year":2022,"today":"2022-08-31","now":"2022-08-31T16:32:25-04:00","year":2023},"viewing_previous_year":false,"year_difference":0,"role_names":["admin","member","other","student","child","officer","customer"],"loaded":true}},"organization_uuid":"5e3494f2-db0d-4f81-a25a-8058e4abced5"}'

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://somersetelementary.memberhub.com/',
    # Already added when you pass json=
    # 'Content-Type': 'application/json',
    'MemberHub-Session-Token': 'ad8497e0-0a7a-4f6f-a6e7-3f7ce172a42a',
    'MemberHub-Session-Secret': '1ed608ef-6826-4648-a984-4b9b7878c92d',
    'Origin': 'https://somersetelementary.memberhub.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

json_data = {
    'event': {
        'loaded': True,
        'calendar': True,
        'saving': False,
        'repeat_every': 1,
        'remind_timeframe': 'day',
        'remind_hour': 9,
        'timezone': 'America/New_York',
        'name': 'BSTN K-2',
        'public': True,
        'country': 'US',
        'state': 'AL',
        'location_name': 'All Purpose Room',
        'starting_at': '2022-09-07T22:30:00.000Z',
        'ending_at': '2022-09-08T00:00:00.000Z',
        'recipients': {
            'everyone': False,
            'organizations': [],
            'officers': [],
            'roles': [],
            'stripe': [],
            'traits': [],
            'users': [],
            'years': [],
            'checked': [],
            'recipients': [],
            'meta': {
                'count': 0,
                'has_more': False,
                'limit': 20,
                'offset': 0,
                'total': 0,
            },
            'organization': {
                'uuid': '5e3494f2-db0d-4f81-a25a-8058e4abced5',
            },
            'school_year': {
                'end_date': '2023-06-30',
                'end_time': '2023-06-30T23:59:59-04:00',
                'end_year': 2023,
                'start_date': '2022-07-01',
                'start_time': '2022-07-01T00:00:00-04:00',
                'start_year': 2022,
                'today': '2022-08-31',
                'now': '2022-08-31T16:32:25-04:00',
                'year': 2023,
            },
            'current_school_year': {
                'end_date': '2023-06-30',
                'end_time': '2023-06-30T23:59:59-04:00',
                'end_year': 2023,
                'start_date': '2022-07-01',
                'start_time': '2022-07-01T00:00:00-04:00',
                'start_year': 2022,
                'today': '2022-08-31',
                'now': '2022-08-31T16:32:25-04:00',
                'year': 2023,
            },
            'viewing_previous_year': False,
            'year_difference': 0,
            'role_names': [
                'admin',
                'member',
                'other',
                'student',
                'child',
                'officer',
                'customer',
            ],
            'loaded': True,
        },
    },
    'organization_uuid': '5e3494f2-db0d-4f81-a25a-8058e4abced5',
}

response = requests.post('https://api.memberhub.co/services/memberhub-service/events', headers=headers, json=json_data)
