import time
from typing import TYPE_CHECKING, Optional, Dict, Set, List
import struct
from BaseClasses import MultiWorld
from NetUtils import ClientStatus
from collections import defaultdict
import sys
import logging
import math
import asyncio
from itertools import zip_longest
from .Items import mpadv_items
from .Locations import mpadv_locations

if "worlds._bizhawk" not in sys.modules:
    import importlib
    import os
    import zipimport

    bh_apworld_path = os.path.join(os.path.dirname(sys.modules["worlds"].__file__), "_bizhawk.apworld")
    if os.path.isfile(bh_apworld_path):
        importer = zipimport.zipimporter(bh_apworld_path)
        spec = importer.find_spec(os.path.basename(bh_apworld_path).rsplit(".", 1)[0])
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = f"worlds.{mod.__package__}"
        mod.__name__ = f"worlds.{mod.__name__}"
        sys.modules[mod.__name__] = mod
        # importer.exec_module(mod)     # no idea what this does but the mlss code did it
    elif not os.path.isdir(os.path.splitext(bh_apworld_path)[0]):
        raise Exception("Did not find _bizhawk.apworld required to play Mario Party Advance.")

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext
else:
    BizHawkClientContext = object

# Add .apmpadv suffix to bizhawk client
from worlds.LauncherComponents import SuffixIdentifier, components
for component in components:
    if component.script_name == "BizHawkClient":
        component.file_identifier = SuffixIdentifier(*(*component.file_identifier.suffixes, ".apmpadv"))
        break

# how the bitfield is ordered in memory, seemingly random order
bitorder = [
    "Quest: Possibly a Robbery?",
    "Quest: True Blue Boo",
    "Quest: Monkeynapping?!",
    "Quest: Weeping Twomp",
    "Quest: Sploosh!",
    "Bowser Quest: Bowser Accused!",
    "Quest: Hearts A-flutter",
    "Quest: Blossom of my Heart",

    "Quest: Love that Princess!",
    "Quest: Accessorize!",
    "Bowser Quest: Besteset Buds",
    "Quest: A Speeding Bill",
    "Quest: Jungle Jive",
    "Quest: Hammerama",
    "Quest: Cool as Ice",
    "Quest: Swimmin' Wimp",

    "Bowser Quest: Goal Tenderizer",
    "Quest: Hey, UFO!",
    "Quest: Treasure of Mystery!",
    "Quest: Condo of Mystery!",
    "Quest: Dino of Mystery!",
    "Bowser Quest: Chillin' Villan",
    "Quest: Find the Password",
    "Quest: Flowers are a Blast!",

    "Quest: Big Boss Bob-omb",
    "Bowser Quest: Boss Bowser",
    "Quest: DVD for Me",
    "Quest: What's that line?",
    "Quest: Nerd Force V",
    "Bowser Quest: Bowser's Toys",
    "Quest: Winners Keepers",
    "Quest: Losing Streak",

    "Quest: Dino of Mystery!",
    "Quest: Engaging Game",
    "Quest: Game Mage",
    "Bowser Quest: Game King",
    "Quest: Duel Tower 1F",
    "Quest: Duel Tower 2F",
    "Quest: Duel Tower 3F",
    "Quest: Mustached Hero!",

    "Quest: Blooper Battle",
    "Quest: Chomper Stomper",
    "Bowser Quest: Bowserstein!",
    "Quest: Locomotionless",
    "Quest: Mysterious Riddles",
    "Quest: Kamek Krew Live!",
    "Quest: Mathematician!",
    "Quest: Comedy Bomb",

    "Quest: Kind Goomba",
    "Bowser Quest: Final Showdown"
]


class MPADVClient(BizHawkClient):
    game = "Mario Party Advance"
    system = "GBA"
    local_checked_locations: Set[int]
    goal_flag: int
    rom_slot_name: Optional[str]
    player: int

    """
    A mapping for ram values with recognizable names.
    The first string in the value set is memory region, second is the address,
    and third is the optional bitmask.
    If the bitmask is not used, leave it as 0xFF
    """
    codepoints = {
        "Quests Discovered":    ("EWRAM", 0x34E00, 0xFF),
        "Quests Completed":     ("EWRAM", 0x34E14, 0xFF),
        "Game Mode":            ("unknown", 0x38001, 0xFF),    # check mem region at some point
        "Current Char":         ("unknown", 0x440E, 0xFF),
        "Minigames Discovered": ("unknown", 0x398C1, 0xFF),
        "Current Minigame":     ("unknown", 0x440D, 0xFF),
        "Mushroom Total":       ("unknown", 0x3CBF1, 0x0F),
        "Passport Creation":    ("unknown", 0x39055, 0x01)
    }

    def __init__(self) -> None:
        super().__init__()
        self.local_checked_locations = set()
        self.local_set_events = {}
        self.local_found_key_items = {}
        self.lock = asyncio.Lock()

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        ctx.game = self.game
        ctx.items_handling = 0b101
        ctx.want_slot_data = True
        ctx.watcher_timeout = 0.125

        return True

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        from CommonClient import logger

        try:
            quests_loc = await self.readByName(ctx, "Quests Discovered", 7)

            locations_sent = []

            # reading completed quests from the discovered bitfield
            byte = 0
            bit = 0
            for i in range(0, len(bitorder)):
                quest_name = bitorder[i]
                quest_id = mpadv_locations[quest_name]
                if bit > 7:
                    bit = 0
                    byte += 1

                if quests_loc[byte] & (1 << bit):
                    locations_sent.append(quest_id)

                bit += 1

            if locations_sent is not None:
                self.local_checked_locations = set(locations_sent)
                await ctx.send_msgs([{
                    "cmd": "LocationChecks",
                    "locations": list(locations_sent)
                }])


            # writing quest completions
            byte = 0
            quest_hex = [0x0 for i in range(0, 7)]
            for i in ctx.items_received:
                if i.item != mpadv_items["Quest Completion"]:
                    continue

                curbyte = quest_hex[byte]
                curbyte <<= 1
                curbyte |= 1
                quest_hex[byte] = curbyte

                if curbyte == 0xFF:
                    byte += 1

                if byte >= 7:
                    break

            await self.writeByName(ctx, "Quests Completed", quest_hex)

        except bizhawk.RequestFailedError:
            pass

    async def readByName(self, ctx: BizHawkClientContext, name:str, bytecount:int) -> list:
        region, addr, mask = self.codepoints.get(name, ("ROM", 0x0, 0x0))
        shift = 0
        if mask == 0x0:
            print(f"Error while reading codepoint {name} ({addr}): Invalid mask")

        else:
            shift = 0
            tempmask = mask
            while not (tempmask & 1):
                tempmask >>= 1
                shift += 1

        ramslice = await bizhawk.read(ctx.bizhawk_ctx, [(addr, bytecount, region)])
        return [(x & mask) >> shift for x in ramslice[0]]

    async def writeByName(self, ctx: BizHawkClientContext, name:str, written) -> None:
        region, addr, mask = self.codepoints.get(name, ("ROM", 0x0, 0x0))
        bytecount = len(written)
        if mask == 0x0:
            print(f"Error while writing codepoint {name} ({addr}): Invalid mask")

        if mask != 0xFF:
            underlying = await self.readByName(ctx, name, bytecount)
            written = [
                (new & mask) | (old & ~mask) for
                new, old in zip_longest(written, underlying, fillvalue=0x0)
            ]

        return await bizhawk.write(ctx.bizhawk_ctx, [(addr, written, region)])
