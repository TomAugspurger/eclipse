import dataclasses
import json
import datetime
import re
from pathlib import Path
import importlib.resources

import fsspec
import shapely
import pystac
import stac_table
import adlfs
import planetary_computer


ACCOUNT_NAME =  "ai4edataeuwest"
CONTAINER_NAME = "eclipse"


@dataclasses.dataclass
class PathParts:
    """
    The components of an Eclipse Path like "Chicago/2021-07-11"
    """
    region: str
    date: datetime.datetime

    @classmethod
    def from_path(cls, p: str) -> "PathParts":
        region, date_part = p.split("/")
        date = datetime.datetime(*list(map(int, date_part.split("-"))))

        return cls(region=region, date=date)

    @property
    def stac_id(self):
        return f"{self.region}-{self.date:%Y-%m-%d}"


def create_item(path, protocol, storage_options, asset_extra_fields):
    # 3. Get Chicago Coordinates from local file
    path = path.rstrip("/")
    p = importlib.resources.read_text("stactools.eclipse", "ChicagoBoundaries.geojson")
    geojsondata = json.loads(p)
    geocoord = geojsondata["features"][0]["geometry"]
    sf = shapely.geometry.shape(geocoord).simplify(0.0001)

    parts = PathParts.from_path(path)

    item = pystac.Item(
        parts.stac_id,
        geometry=shapely.geometry.mapping(sf),
        bbox=list(sf.bounds),
        datetime=None,
        properties={
            "start_datetime": parts.date.isoformat() + "Z",
            "end_datetime": (parts.date + datetime.timedelta(days=7)).isoformat() + "Z",
        },
    )

    fs = fsspec.filesystem(protocol, **storage_options)

    parquet_files = fs.ls(f"eclipse/{path}/")
    # Note: For now there is only one parquet file in a folder
    result = stac_table.generate(
        f"abfs://{parquet_files[0]}",
        item,
        storage_options=storage_options,
        proj=False,
        asset_extra_fields=asset_extra_fields,
        count_rows=False,
    )
    result.assets["data"].title = "Weekly dataset"
    xpr = re.compile(
        r"^\|\s*(\w*?)\s*\| \w.*?\|.*?\|\s*(.*?)\s*\|$", re.UNICODE | re.MULTILINE
    )
    p = importlib.resources.read_text("stactools.eclipse", "column_descriptions.md")
    column_descriptions = dict(xpr.findall(p))

    for column in result.properties["table:columns"]:
        # print(column["name"])
        column["description"] = column_descriptions[column["name"]]

    result.validate()
    return result


def create_collection(sample_item: pystac.Item):
    dates = [
        datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc),
        None,
    ]
    extra_fields = {
        "msft:short_description":  "A network of low-cost air quality sensing network for cities and led by the Urban Innovation Group at Microsoft Research",  # noqa: E501
        "msft:container": CONTAINER_NAME,
        "msft:storage_account": ACCOUNT_NAME,

    }
    collection = pystac.Collection(
        "eclipse",
        description="{{ collection.description }}",
        extent=pystac.Extent(
            spatial=pystac.collection.SpatialExtent(
                [
                    sample_item.bbox,
                ]
            ),
            temporal=pystac.collection.TemporalExtent([dates]),
        ),
        extra_fields=extra_fields
    )
    collection.extra_fields["table:columns"] = sample_item.properties["table:columns"]
    collection.title = "Urban Innovation Eclipse Sensor Data"

    pystac.extensions.item_assets.ItemAssetsExtension.add_to(collection)
    collection.extra_fields["item_assets"] = {
        "data": {
            "type": stac_table.PARQUET_MEDIA_TYPE,
            "title": "Weekly dataset",
            "roles": ["data"],
            **sample_item.assets["data"].extra_fields,
        }
    }

    pystac.extensions.scientific.ScientificExtension.add_to(collection)
    collection.extra_fields["sci:citation"] = "Daepp, Cabral, Ranganathan et al. (2022) Eclipse: An End-to-End Platform for Low-Cost, Hyperlocal Environmental Sensing in Cities. ACM/IEEE Information Processing in Sensor Networks. Milan, Italy. Eclipse: An End-to-End Platform for Low-Cost, Hyperlocal Environmental Sensing in Cities"  # noqa: E501

    collection.stac_extensions.append(stac_table.SCHEMA_URI)
    collection.keywords = ["Eclipse", "PM25", "air pollution"]
    collection.providers = [
        pystac.Provider(
            "Urban Innovation",
            roles=[
                pystac.provider.ProviderRole.PRODUCER,
                pystac.provider.ProviderRole.LICENSOR,
                pystac.provider.ProviderRole.PROCESSOR,
            ],
            url="https://www.microsoft.com/en-us/research/urban-innovation-research/",
        ),
        pystac.Provider(
            "Microsoft",
            roles=[pystac.provider.ProviderRole.HOST],
            url="https://planetarycomputer.microsoft.com",
        ),
    ]
    # TODO: Upload the eclipse (thumbnail) to the assets directory
    collection.assets["thumbnail"] = pystac.Asset(
        title="Urban Innovation Chicago Sensors",
        href="https://ai4edatasetspublicassets.blob.core.windows.net/assets/pc_thumbnails/eclipse-thumbnail.png",  # noqa: E501
        media_type="image/png",
        roles=["thumbnail"],
    )
    collection.assets["data"] = pystac.Asset(
        title="Full dataset",
        href="abfs://eclipse/Chicago/",
        media_type=stac_table.PARQUET_MEDIA_TYPE,
        description="Full parquet dataset",
        roles=["data"],
        extra_fields=sample_item.assets["data"].extra_fields,
    )

    # TODO: Point to the license pdf (has to be uploaded)
    collection.links = [
        pystac.Link(
            pystac.RelType.LICENSE,
            target="https://ai4edatasetspublicassets.blob.core.windows.net/assets/aod_docs/Microsoft%20Project%20Eclipse%20API%20Terms%20of%20Use_Mar%202022.pdf",  # noqa: E501
            media_type="application/pdf",
            title="Terms of use",
        ),
        pystac.Link(
            rel="cite-as",
            target="https://www.microsoft.com/en-us/research/uploads/prod/2022/05/ACM_2022-IPSN_FINAL_Eclipse.pdf",  # noqa: E501
            media_type="application/pdf",
            title="Eclipse: An End-to-End Platform for Low-Cost, Hyperlocal Environment Sensing in Cities",
        )
    ]
    collection.validate()

    with open("collection.json", "w") as f:
        json.dump(collection.to_dict(), f, indent=2)

    return collection


def make_items():
    # 1. Set blob storage account and container name, sas token etc..
    account_name = "ai4edataeuwest"
    sas_token = planetary_computer.sas.get_token(ACCOUNT_NAME, CONTAINER_NAME).token
    storage_options = {"account_name": account_name}
    asset_extra_fields = {"table:storage_options": storage_options}

    # 2. Each folder name is a date, grab that list
    fs = adlfs.AzureBlobFileSystem("ai4edataeuwest", credential=sas_token)
    dates = fs.ls("eclipse/Chicago")

    items = [
        create_item(path, "abfs", storage_options, asset_extra_fields)
        for path in dates
    ]


    # 4. Set Storage options to have sas token
    storage_options = dict(account_name=account_name, credential=sas_token)

    # Create items directory to place items from the data folder
    p = Path("items")
    p.mkdir(exist_ok=True)
    for item in items:
        with open(p.joinpath(item.id + ".json"), "w") as f:
            json.dump(item.to_dict(), f)


if __name__ == "__main__":
    sas_token = planetary_computer.sas.get_token(ACCOUNT_NAME, CONTAINER_NAME).token
    storage_options = {"account_name": ACCOUNT_NAME, "credential": sas_token}
    asset_extra_fields = {"table:storage_options": {"account_name": ACCOUNT_NAME}}

    sample_item = create_item("eclipse/Chicago/2021-10-10", protocol="abfs", storage_options=storage_options, asset_extra_fields=asset_extra_fields)
    create_collection(sample_item)