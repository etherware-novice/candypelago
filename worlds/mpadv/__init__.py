import settings
import typing
from .options import MyGameOptions  # the options we defined earlier
from .Locations import mpadv_locations  # same as above
from .Regions import create_regions
from .Rules import set_rules
from worlds.AutoWorld import World
from BaseClasses import Region, Location, Entrance, Item, RegionType, ItemClassification


class MPADVWebWorld(WebWorld):
    theme = 'partyTime'
    bug_report_page = "example.net"  # dont forget to update with repo name


class MPADVItem(Item):
    game = "Mario Party Advance"


mpadv_items: typing.Dict[str, int] = {
    "Quest Completion": 50,
    "Roll Maximum Increase": 10,
    "Roll Mushroom": 0  # junk item
}


class MPADVWorld(World):
    """
    Explore the Party World with Mario, Luigi, Peach, or Yoshi to
    recover all the Gaddgets and defeat Bowser!
    """
    game = "Mario Party Advance"
    topology_present = True

    base_id = 0  # REPLACE WITH RANDOM NUMBER, IN RANGE OF 2^53

    item_name_to_id = {name: id for
                       id, name in enumerate(mpadv_items.keys(), base_id)}
    location_name_to_id = {name: id for
                           id, name in enumerate(mpadv_locations, base_id)}

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

        # for now, just create the 50 quest completions for the 50 quest locations..
        self.multiworld.itempool += [self.create_item("Quest Completion") for _ in range(0, 50)]


    def create_item(self, name:str) -> Item:
        item_id = self.item_name_to_id[name]

        classification = ItemClassification.progression
        if name == "Quest Completion":
            classification = ItemClassification.progression_skip_balancing
        elif name == "Roll Mushroom":
            classification = ItemClassification.filler

        return MPADVItem(name, classification, item_id, self.player)