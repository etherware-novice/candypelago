from BaseClasses import Region, Location, Entrance, Item, ItemClassification
import typing

class MPADVItem(Item):
    game = "Mario Party Advance"


mpadv_items_balance: typing.Dict[str, int] = {
    "Quest Completion": 50,
    "Roll Maximum Increase": 10,
    "Roll Mushroom": 0  # junk item
}

mpadv_items = {name:id for id, name in enumerate(mpadv_items_balance.keys(), 3245432567842)}
