from __future__ import print_function
from oauth2client import file, client, tools
from googleapiclient.discovery import build
from httplib2 import Http


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
                    X = element['elementGroup']['children'][0]['transform'].get('translateX', 0) / emu
                    Y = element['elementGroup']['children'][0]['transform'].get('translateY', 0) / emu
                    a = round(((x + X) * 10) / 10 + 1)
                    b = round(((y + Y) * 10) / 10 + 1)
                    temp['coords'] = (AlphConv(a), int(b))
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

    def get_combatant(self, name):
        for x in self.list:
            if name.lower() in x.get('name').lower():
                return simpleCombatant(self.presentation, x)


class simpleCombatant:
    def __init__(self, presentation, name):
        self.objectId = name.get('objectId')
        self.name = name.get('name')
        self.coords = tuple(name.get('coords'))
        self.size = name.get('size')


# Converts alpha coords to and from integers (A-1 ,B-2....Z-26)
def AlphConv(coord):
    alph = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    alph += [i+i for i in alph]
    if type(coord) == str:
        if coord.isalpha():
            return alph.index(coord)+1
        elif coord.isdigit():
            return int(coord)
    elif type(coord) == int:
        if coord>len(alph):
            return coord
        return alph[coord-1]


# Get the presentation
class GetPresentation:
    def __init__(self, id):
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)
        self.service = build('slides', 'v1', http=creds.authorize(Http()))
        self.id = id
        # Call the Slides API
        self.presentation = self.service.presentations().get(
            presentationId=self.id).execute()
        self.slides = self.presentation.get('slides')


# Moves a given object a certain number of squares (0.5"), given by x and y transforms
class move:
    def __init__(self, presentation, combatant, x=0, y: int = 0, absolute: bool = False):
        emu = 914400 / 2
        if type(x) == str:
            if x.isalpha():
                x = AlphConv(x)
            else:
                x = int(x)
        self.name = combatant.name
        self.message = ""
        if absolute:
            X, Y = combatant.coords
            X = AlphConv(X)
            self.message += "Moving {0.name} to {1}, {2}\n".format(
                self, AlphConv(x), y)
            x = x - X
            y = y - Y
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
        if x and y:
            self.message += "Moving {} : {} {} and {} {}".format(
                self.name, int(abs(x) / emu), 'Left' if x < 0 else 'Right', int(abs(y) / emu),
                'Up' if y < 0 else 'Down')
        elif x and not y:
            self.message += "Moving {} : {} {}".format(
                self.name, int(abs(x) / emu), 'Left' if x < 0 else 'Right')
        elif y and not x:
            self.message += "Moving {} : {} {}".format(
                self.name, int(abs(y) / emu), 'Up' if y < 0 else 'Down')
        else:
            self.message = "Not moving {}".format(
                self.name)
        presentation.service.presentations().batchUpdate(presentationId=presentation.id,
                                                         body={'requests': req}).execute()
