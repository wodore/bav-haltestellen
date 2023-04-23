#!/usr/bin/env python
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel
from rich import print as rprint
from geojson_pydantic import Feature, FeatureCollection, Point

# Source file
# https://opentransportdata.swiss/de/dataset/didok/resource_permalink/dienststellen_actualdate.csv
source = "src/dienststellen_actualdate.csv"
dest = "static/bav_list.csv"
COUNTRIES = ["CH"]

nrows = None #4000 
USECOLS=['BPUIC','BEZEICHNUNG_OFFIZIELL',
         'BEZEICHNUNG_LANG','IS_HALTESTELLE','ORTSCHAFTSNAME',
         'KANTONSKUERZEL','LAND_ISO2_GEO','LAENDERCODE','E_WGS84','N_WGS84',
         'BPVH_VERKEHRSMITTEL_TEXT_DE'] #,'ABKUERZUNG','GEAENDERT_AM']

HEADER=['id','name',
         'name_long','is_stop','community',
         'state','country','country_code','lon','lat',
         'types']#,'name_short','changed']

TYPES =  {
   'Aufzug': "elevator",
   'Bus': "bus",
   'Kabinenbahn': "cable_car",
   'Metro': "metro",
   'Tram': "tram",
   'Standseilbahn': "funicular",
   'Zug': "train",
   'Zahnradbahn': "rack_railroad",
   'Schiff': "ship",
   'Sesselbahn': "chairlift",
   'Skilift': "skilift",
   'U': 'unknown'
   }
def convert_types(types_string:str, as_string=False, short=False):
     types_string.strip("~")
     types_list =  types_string.strip("~").split("~")
     types = [TYPES.get(t,"unknown") for t in types_list]
     if short:
         types = [t[:2].upper() for t in types]
     if as_string:
         return "~".join(types)
     return types

df = pd.read_csv(source, sep=";", comment="#", nrows=nrows, usecols=USECOLS)[USECOLS]
df.columns = HEADER
#df = df.set_index("id", drop=True)
df = df[df['is_stop'] == 1]
df = df[df['country'].isin(COUNTRIES)]
del df['is_stop']

df['types_list'] = df['types'].apply(lambda x: convert_types(x, as_string=False, short=False))

df.to_csv(dest, index=False)

class JsonWithNames(BaseModel):
    id: str
    name: str
    alias: Optional[str]
    types: List[str]

class Data(BaseModel):
    data: List[JsonWithNames]


objs = []
for i, row in df.iterrows():
    obj = JsonWithNames(id=row['id'], name=row['name'], types=row['types_list'])
    objs.append(obj)

data = Data(data=objs)
#rprint(data)
with open(dest.replace("csv","json"), "w") as f:
    f.write(data.json(exclude_none=True,separators=(',', ':'),  ensure_ascii=False))



features = []
for i, row in df.iterrows():
    if row['lon'] and row['lat']:
        geojson_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(row['lon'],5), round(row['lat'],5)],
            },
            "properties": {
                "id": row["id"],
                "types": row["types_list"],
                "name": row["name"],
            },
        }
        features.append(Feature(**geojson_feature))

fc = FeatureCollection(features=features)
with open(dest.replace("csv","geojson"), "w") as f:
    f.write(fc.json(exclude_none=True,separators=(',', ':'),  ensure_ascii=False))
