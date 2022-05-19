import json
import logging

import click

from stactools.eclipse import stac

logger = logging.getLogger(__name__)


def create_eclipse_command(cli):
    """Creates the stactools-eclipse command line utility."""

    @cli.group(
        "eclipse",
        short_help=("Commands for working with stactools-eclipse"),
    )
    def eclipse():
        pass

    @eclipse.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    def create_collection_command(destination: str):
        """Creates a STAC Collection

        Args:
            destination (str): An HREF for the Collection JSON
        """
        import planetary_computer

        sas_token = planetary_computer.sas.get_token(
            stac.ACCOUNT_NAME, stac.CONTAINER_NAME
        ).token
        storage_options = {"account_name": stac.ACCOUNT_NAME, "credential": sas_token}
        asset_extra_fields = {
            "table:storage_options": {"account_name": stac.ACCOUNT_NAME}
        }

        sample_item = stac.create_item(
            "Chicago/2021-10-10",
            protocol="abfs",
            storage_options=storage_options,
            asset_extra_fields=asset_extra_fields,
        )
        collection = stac.create_collection(sample_item)
        with open(destination, "w") as f:
            f.write(json.dumps(collection.to_dict(), indent=2))

        return None

    @eclipse.command("create-item", short_help="Create a STAC item")
    @click.argument("destination")
    def create_item_command(destination: str):
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Collection
        """
        import planetary_computer

        sas_token = planetary_computer.sas.get_token(
            stac.ACCOUNT_NAME, stac.CONTAINER_NAME
        ).token
        storage_options = {"account_name": stac.ACCOUNT_NAME, "credential": sas_token}
        asset_extra_fields = {
            "table:storage_options": {"account_name": stac.ACCOUNT_NAME}
        }
        sample_item = stac.create_item(
            "eclipse/Chicago/2021-10-10",
            protocol="abfs",
            storage_options=storage_options,
            asset_extra_fields=asset_extra_fields,
        )

        sample_item.save_object(dest_href=destination)

        return None

    return eclipse
