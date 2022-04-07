import json
import datetime
import re
from pathlib import Path
import importlib.resources

import fsspec
import geopandas
import pystac
import stac_table
import adlfs
import planetary_computer


ACCOUNT_NAME =  "ai4edataeuwest"
CONTAINER_NAME = "eclipse"


def create_item(path, protocol, storage_options, asset_extra_fields):
    # 3. Get Chicago Coordinates from local file
    p = importlib.resources.files("stactools.eclipse") / "ChicagoBoundaries.geojson"
    geojsondata = json.loads(p.read_text())
    geocoord = geojsondata["features"][0]["geometry"]
    geometry_type = geocoord["type"]
    chicago_coords = geocoord["coordinates"]

    print("Processing", path)
    date = datetime.datetime(*list(map(int, path.split("/")[-1].split("-"))))
    date_id = f"{date:%Y-%m-%d}"
    print(date_id)
    item = pystac.Item(
        f"eclipse-{date_id}",
        geometry={
            "type": geometry_type,
            "coordinates": chicago_coords,
        },
        bbox=[
            -87.93514385942143,
            42.00088911607326,
            -87.82413707733014,
            41.9783005778378,
        ],
        datetime=date,  # snapshot date seems most useful?
        properties={
            "start_datetime": date.isoformat() + "Z",
            "end_datetime": (date + datetime.timedelta(days=7)).isoformat() + "Z",
        },
    )

    fs = fsspec.filesystem(protocol, **storage_options)

    parquet_files = fs.ls(f"eclipse/Chicago/{date_id}/")
    for pf in parquet_files:
        print(pf)
    # Note: For now there is only one parquet file in a folder
    result = stac_table.generate(
        f"abfs://{parquet_files[0]}",
        item,
        storage_options=storage_options,
        proj=False,
        asset_extra_fields=asset_extra_fields,
        count_rows=False,
    )
    xpr = re.compile(
        r"^\|\s*(\w*?)\s*\| \w.*?\|.*?\|\s*(.*?)\s*\|$", re.UNICODE | re.MULTILINE
    )
    p = importlib.resources.files("stactools.eclipse") / "column_descriptions.md"
    column_descriptions = dict(xpr.findall(p.read_text()))

    for column in result.properties["table:columns"]:
        # print(column["name"])
        column["description"] = column_descriptions[column["name"]]

    result.validate()
    return result


def create_collection(sample_item):
    dates = [
        datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc),
        None,
    ]
    extra_fields = {
        "msft:short_description":  "The Project Eclipse Network is a low-cost air quality sensing network for cities and a research project led by the [Urban Innovation Group]( https://www.microsoft.com/en-us/research/urban-innovation-research/) at Microsoft Research.",
        "msft:container": CONTAINER_NAME,
        "msft:storage_account": ACCOUNT_NAME,

    }
    collection = pystac.Collection(
        "eclipse",
        description="{{ collection.description }}",
        extent=pystac.Extent(
            spatial=pystac.collection.SpatialExtent(
                [
                    [
                        -87.93514385942143,
                        42.00088911607326,
                        -87.82413707733014,
                        41.9783005778378,
                    ]
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
            "title": "Dataset root",
            "roles": ["data"],
            **sample_item.assets["data"].extra_fields,
        }
    }

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
        href=(
            "https://ai4edatasetspublicassets.blob.core.windows.net/"
            "assets/eclipse/eclipse.png"
        ),
        media_type="image/png",
    )
    # TODO: Point to the license pdf (has to be uploaded)
    collection.links = [
        pystac.Link(
            pystac.RelType.LICENSE,
            target="https://www.microsoft.com/en-us/legal/terms-of-use",
            media_type="text/html",
            title="Terms of use",
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
    print(dates)

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