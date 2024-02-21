import settings
import typing
from .Options import MPADVOptions  # the options we defined earlier
from .Items import MPADVItem, mpadv_items
from .Locations import mpadv_locations  # same as above
from .Regions import create_regions
from .Rules import set_rules
from .Rom import Rom
from .Client import MPADVClient
from worlds.AutoWorld import World, WebWorld
from BaseClasses import Region, Location, Entrance, Item, ItemClassification


class MPADVWebWorld(WebWorld):
    theme = 'partyTime'
    bug_report_page = "example.net"  # dont forget to update with repo name




class MPADVSettings(settings.Group):
    class MPADVRomFile(settings.UserFilePath):
        """File name of your English Pokemon Emerald ROM"""
        description = "Mario Party Advance ROM File"
        copy_to = "Mario Party Advance (USA).gba"
        #md5s = [PokemonEmeraldDeltaPatch.hash]

    rom_file: MPADVRomFile = MPADVRomFile(MPADVRomFile.copy_to)


class MPADVWorld(World):
    """
    Explore the Party World with Mario, Luigi, Peach, or Yoshi to
    recover all the Gaddgets and defeat Bowser!
    """
    game = "Mario Party Advance"
    topology_present = True
    option_definitions = MPADVOptions

    base_id = 1  # REPLACE WITH RANDOM NUMBER, IN RANGE OF 2^53

    item_name_to_id = mpadv_items
    location_name_to_id = mpadv_locations

    web = MPADVWebWorld()
    required_client_version = (0, 4, 3)

    def create_regions(self) -> None:
        create_regions(self.multiworld, self.player, self.location_name_to_id)

    def set_rules(self) -> None:
        set_rules(self.multiworld, self.player)

    def create_items(self) -> None:
        # Add items to the Multiworld.
        # If there are two of the same item, the item has to be twice in the pool.
        # Which items are added to the pool may depend on player options, e.g. custom win condition like triforce hunt.
        # Having an item in the start inventory won't remove it from the pool.
        # If an item can't have duplicates it has to be excluded manually.

        itempool = [self.create_item("Quest Completion") for _ in range(0, 100)]
        while len(itempool) < self.location_count:
            itempool.append(self.create_item(self.get_filler_item_name()))

        self.multiworld.itempool += itempool

    def get_filler_item_name(self) -> str:
        return "Roll Mushroom"

    def create_item(self, name:str) -> Item:
        item_id = self.item_name_to_id[name]

        classification = ItemClassification.progression
        if name == "Quest Completion":
            classification = ItemClassification.progression_skip_balancing
        elif name == "Roll Mushroom":
            classification = ItemClassification.filler

        return MPADVItem(name, classification, item_id, self.player)

    def generate_output(self, output_directory: str) -> None:
        rom = Rom(self.multiworld, self.player)
        rom.close(output_directory)
