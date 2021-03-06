from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from googleapiclient.discovery import build
from constants import emu
import pickle
import os.path
import math
SCOPES = 'https://www.googleapis.com/auth/presentations'


# Get the presentation
class GetPresentation:
    def __init__(self, id):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('slides', 'v1', credentials=creds)
        self.id = id
        # Call the Slides API
        self.presentation = self.service.presentations().get(
            presentationId=self.id).execute()
        self.slides = self.presentation.get('slides')
        self.size = []
        self.size.append(int(self.presentation.get('pageSize').get('width').get('magnitude')/emu))
        self.size.append(int(self.presentation.get('pageSize').get('height').get('magnitude')/emu))


class ObjectList:
    def __init__(self, presentation, slide: int = 0):
        self.presentation = presentation
        slides = self.presentation.slides
        out = []
        for i, slideNum in enumerate(slides):
            if slideNum.get('pageElements'):
                for element in slideNum.get('pageElements'):
                    temp = {}
                    temp['objectId'] = element['objectId']
                    name = ""
                    if element.get('shape'):
                        for I in element['shape']['text']['textElements']:
                            if I.get('textRun'):
                                name += I['textRun'].get('content')
                    elif element.get('elementGroup'):
                        for I in element['elementGroup']['children']:
                            if I.get('shape'):
                                for x in I['shape']['text']['textElements']:
                                    if x.get('textRun'):
                                        name += x['textRun'].get('content')
                    temp['name'] = name.strip()
                    emu = 914400 / 2

                    x = element['transform'].get('translateX',0) / emu
                    y = element['transform'].get('translateY',0) / emu
                    X = element.get('elementGroup')['children'][0]['transform'].get('translateX', 0) / emu
                    Y = element.get('elementGroup')['children'][0]['transform'].get('translateY', 0) / emu
                    a = round(((x + X) * 10) / 10 + 4)
                    b = round(((y + Y) * 10) / 10 + 4)
                    temp['coords'] = (int(a), int(b))
                    scaleX = element['elementGroup']['children'][0]['transform'].get('scaleX', 0)
                    scaleY = element['elementGroup']['children'][0]['transform'].get('scaleY', 0)
                    magY = element['elementGroup']['children'][0]['size']['height'].get('magnitude', 0)
                    magX = element['elementGroup']['children'][0]['size']['width'].get('magnitude', 0)
                    A = int(round((magX) / emu * scaleX))
                    B = int(round((magY) / emu * scaleY))
                    size = 'Unknown'
                    if A == 1 and B == 1:
                        size = 'Medium'
                    elif A == 2 and B == 2:
                        size = 'Large'
                    temp['size'] = size
                    if temp['name'] == 'Mrs Horse':
                        temp['size'] = 'Thicc'
                    out.append(temp)
        self.list = out

    def get_combatant(self, name: str):
        for x in self.list:
            if name:
                if name.lower() in x.get('name').lower():
                    return SimpleCombatant(self.presentation, x)


class SimpleCombatant:
    def __init__(self, presentation, name):
        self.objectId = name.get('objectId')
        self.name = name.get('name')
        self.coords = tuple(name.get('coords'))
        self.size = name.get('size')
        x = alpha_conv(self.coords[0])
        y = self.coords[1]
        self.pos = "{}, {}".format(x, y)


# Converts alpha coords to and from integers (A-1 ,B-2....Z-26)
def alpha_conv(coord):
    alph = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    alph += [i+i for i in alph]
    if type(coord) == str:
        if coord.isalpha():
            return alph.index(coord.upper())+1
        elif coord.isdigit():
            return int(coord)
    elif type(coord) == int:
        if coord > len(alph):
            return coord
        return alph[coord-1]


# Moves a given object a certain number of squares (0.5"), given by x and y transforms
class Move:
    def __init__(self, presentation, combatant, x=0, y: int = 0, absolute: bool = False):
        emu = 914400 / 2
        if type(x) == str:
            if x.isalpha():
                x = alpha_conv(x)
            else:
                x = int(x)
        self.name = combatant.name
        if absolute:
            X, Y = combatant.coords
            self.title = "({0.pos}) -> ({1}, {2})".format(
                combatant, alpha_conv(min(x, presentation.size[0])), min(presentation.size[1], y))
            x = x - X
            y = y - Y
        else:
            self.title = "({0.pos}) -> ({1}, {2})".format(
                combatant, alpha_conv(min(presentation.size[0], combatant.coords[0] + x)),
                min(presentation.size[1], combatant.coords[1]+y))
        if x + combatant.coords[0] > presentation.size[0]:
            x = presentation.size[0] - combatant.coords[0]
        if y + combatant.coords[1] > presentation.size[1]:
            y = presentation.size[1] - combatant.coords[1]
        x = x * emu
        y = y * emu
        req = [
            {
                "updatePageElementTransform": {
                    "objectId": combatant.objectId,
                    "applyMode": "RELATIVE",
                    "transform": {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': x,
                        'translateY': y,
                        'unit': 'EMU'
                    }
                }
            }
        ]
        self.moving = True
        if x and y:
            self.message = "{} {} and {} {}".format(
                int(abs(x) / emu),
                'West' if x < 0 else 'East', int(abs(y) / emu),
                'North' if y < 0 else 'South')
        elif x and not y:
            self.message = "{} {}".format(
                int(abs(x) / emu), 'West' if x < 0 else 'East')
        elif y and not x:
            self.message = "{} {}".format(
                int(abs(y) / emu), 'North' if y < 0 else 'South')
        else:
            self.message = "Not moving"
            self.moving = False
        if self.moving:
            presentation.service.presentations().batchUpdate(presentationId=presentation.id,
                                                             body={'requests': req}).execute()


class Distance:
    def __init__(self, pointA, pointB):


        if isinstance(pointA, SimpleCombatant):
            x1 ,y1 = pointA.coords


            if pointA.size != "Medium":
                x1 += 0.5
                y1 += 0.5
        else:
            x1, y1 = pointA
        if isinstance(pointB, SimpleCombatant):
            x2 ,y2 = pointB.coords
            if pointB.size != "Medium":
                x2 += 0.5
                y2 += 0.5
        else:
            x2, y2 = pointB
        dist = math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
        dist = round(dist,2)

        self.dist = dist
        self.ft = math.floor(dist*5)

        lat1 = math.radians(x1)
        lat2 = math.radians(x2)

        diffLong = math.radians(y2 - y1)

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                               * math.cos(lat2) * math.cos(diffLong))

        initial_bearing = math.atan2(x, y)

        # Now we have the initial bearing but math.atan2 return values
        # from -180° to + 180° which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 180)
        self.degree = round(compass_bearing, 2)
        compass_list =  ["W", "WNW", "NW", "NNW", "N", "NNE", "NE", "ENE",
                         "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W"]
        ix = int((self.degree + 11.25) / 22.5)
        self.compass = compass_list[ix % 16]
        self.quad = ['West','North','East','South'][int((((self.degree-45)//90)+1)%4)]