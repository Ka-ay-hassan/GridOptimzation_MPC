from os import listdir
from os.path import isfile, join
import xml.etree.ElementTree as et
from Code.paths import DATA
import pandas as pd


def get_id(filename) -> list:
    tree = et.parse(filename)
    root = tree.getroot()

    ns = {'gml': 'http://www.opengis.net/gml',
          'bldg': 'http://www.opengis.net/citygml/building/1.0',
          'core': 'http://www.opengis.net/citygml/1.0',
          'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'}

    building_ids = []

    for building in root.findall('.//bldg:Building', namespaces=ns):
        name = building.get('{http://www.opengis.net/gml}id', 'No ID')
        street_element = building.find('.//xal:ThoroughfareName', namespaces=ns)
        number_element = building.find('.//xal:ThoroughfareNumber', namespaces=ns)
        street_name = ""
        street_number = ""
        if street_element is not None:
            street_name = street_element.text
        if number_element is not None:
            street_number = number_element.text
        if street_name != "":
            building_ids.append({"city_gml_id": name, "Straße": street_name, "Hausnummer": street_number})
    return building_ids


def match_ids_to_loads(city_gml_ids: pd.DataFrame, loads: pd.DataFrame):
    loads["Straße"] = loads["Straße"].replace("Nobel Str", "Nobelstraße")
    loads["Straße"] = loads["Straße"].replace("Allmandring ", "Allmandring")
    loads["Straße"] = loads["Straße"].replace("Universitäts-Str.", "Universitätsstraße")
    loads["Hausnummer"] = loads["Hausnummer"].replace(r'^[0]*', '', regex=True)
    loads["Hausnummer"] = loads["Hausnummer"].astype(str).str.lower()
    city_gml_ids["Hausnummer"] = city_gml_ids["Hausnummer"].astype(str).str.lower()
    df = loads.merge(city_gml_ids, how="left", on=["Straße", "Hausnummer"])
    df.to_excel(DATA / "City_gml" / "mapping.xlsx")
    pass


def import_addresses() -> pd.DataFrame:
    filepath = DATA / "Campus" / "data.xlsx"
    return pd.read_excel(io=filepath, usecols="A, B, C, H").dropna().reset_index(drop=True)[:-1]


def main_xml() -> None:
    city_gml_ids = []
    path1 = DATA / "City_gml" / "LoD2_32_505_5398_2_bw"
    files_folder1 = [f for f in listdir(path1) if isfile(join(path1, f)) and (f.endswith('.gml'))]
    for file in files_folder1:
        city_gml_ids.extend(get_id(path1 / file))
    path2 = DATA / "City_gml" / "LoD2_32_507_5398_2_bw"
    files_folder2 = [f for f in listdir(path2) if isfile(join(path2, f)) and (f.endswith('.gml'))]
    for file in files_folder2:
        city_gml_ids.extend(get_id(path2 / file))
    city_gml_ids = pd.DataFrame(city_gml_ids)
    loads = import_addresses()
    match_ids_to_loads(city_gml_ids, loads)


if __name__ == "__main__":
    """
    -- only run if really necessary -- 
    Load names are not the same in all files and may need to be matched again after rerunning this skript!
    this skript extracts addresses from city gml files in data/City_gml folder and matches them to loads on Campus, so 
    City gml IDs are mapped to load names and intern building IDs
    """
    main_xml()


# list loads from grid
# get address from address_dict
# find address in gml data, get matching building ID

# Datenquelle: LGL, www.lgl-bw.de
