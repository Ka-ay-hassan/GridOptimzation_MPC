import geopandas as gpd
from pathlib import Path


def export_district_area(plot: bool = True) -> None:
    from shapely import Polygon
    PROJ_PATH = Path(__file__).parents[3]
    df = gpd.read_file(PROJ_PATH / "data" / "layer" / "strom.shp")
    district_area = Polygon([(3507432, 5400956), (3507604, 5400956), (3507604, 5401090), (3507432, 5401090)])
    district_objects = df[df["geometry"].apply(lambda el: el.within(district_area))]
    district_objects.to_file(PROJ_PATH / "data" / "layer" / "district_area.shp")
    if plot:
        import matplotlib.pyplot as plt
        district_objects.plot()
        plt.show()


if __name__ == "__main__":
    export_district_area()
