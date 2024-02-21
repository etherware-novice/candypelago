from typing import TYPE_CHECKING, Optional, Dict, Set, List
from NetUtils import ClientStatus
from itertools import zip_longest
from .Items import mpadv_items
from .Locations import mpadv_locations, locChar_table

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

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
    patch_suffix = ".apmpadv"
    local_checked_locations: Set[int]
    item_process = 0    # index into the items_received for items that have been gotten

    codepoints = {
        "Quests Discovered":    ("EWRAM", 0x34E00, 0xFF),
        "Character Library":    ("EWRAM", 0x34E08, 0xFF),
        "Quests Completed":     ("EWRAM", 0x34E14, 0xFF),
        "Game Mode":            ("unknown", 0x38001, 0xFF),    # check mem region at some point
        "Current Char":         ("unknown", 0x440E, 0xFF),
        "Minigames Discovered": ("unknown", 0x398C1, 0xFF),
        "Current Minigame":     ("unknown", 0x440D, 0xFF),
        "Mushroom Total":       ("EWRAM", 0x3CBFD, 0xFF),
        "Passport Creation":    ("unknown", 0x39055, 0x01)
    }
    """
    A mapping for ram values with recognizable names.
    The first string in the value set is memory region, second is the address,
    and third is the optional bitmask.
    If the bitmask is not used, leave it as 0xFF
    """

    def __init__(self) -> None:
        super().__init__()
        self.local_checked_locations = set()

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            # Check ROM name/patch version
            rom_name = ((await bizhawk.read(ctx.bizhawk_ctx, [(0xA0, 12, "ROM")]))[0])
            if rom_name.decode("ascii") != "MARIOPARTYUS":
                return False

        except UnicodeDecodeError:
            return False
        except bizhawk.RequestFailedError:
            return False  # Should verify on the next pass

        ctx.game = self.game
        ctx.items_handling = 0b101
        ctx.watcher_timeout = 0.125

        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        from CommonClient import logger

        try:
            quests_loc = await self.readByName(ctx, "Quests Discovered", 7)

            locations_sent = []

            # this needs to be the first check for the bowser char library condition
            byte = 0
            bit = 0
            chars_loc = await self.readByName(ctx, "Character Library", 8)
            for char_name in locChar_table:
                char_id = mpadv_locations[char_name]
                if bit > 7:
                    bit = 0
                    byte += 1

                if chars_loc[byte] & (1 << bit):
                    locations_sent.append(char_id)

                bit += 1

            # reading completed quests from the discovered bitfield
            byte = 0
            bit = 0
            for quest_name in bitorder:
                quest_id = mpadv_locations[quest_name]
                if bit > 7:
                    bit = 0
                    byte += 1
                if byte > 7:
                    break

                if quests_loc[byte] & (1 << bit):
                    locations_sent.append(quest_id)
                    if not ctx.finished_game and quest_name == "Bowser Quest: Final Showdown":
                        await ctx.send_msgs([{
                            "cmd": "StatusUpdate",
                            "status": ClientStatus.CLIENT_GOAL
                        }])

                bit += 1

            if locations_sent is not None:
                self.local_checked_locations = set(locations_sent)
                await ctx.send_msgs([{
                    "cmd": "LocationChecks",
                    "locations": list(locations_sent)
                }])


            # setting flags based on gotten items
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


            # individual item handling
            if self.item_process > len(ctx.items_received):
                self.item_process = 0
            elif self.item_process < len(ctx.items_received):
                curitem = ctx.items_received[self.item_process].item
                if curitem == mpadv_items["Roll Mushroom"]:
                    currentshroom = await self.readByName(ctx, "Mushroom Total", 1)
                    currentshroom[0] += 1
                    if currentshroom[0] < 100:
                        await self.writeByName(ctx, "Mushroom Total", currentshroom)
                        self.item_process += 1

                else:
                    self.item_process += 1

        except bizhawk.RequestFailedError as e:
            print(e)
            pass

    async def readByName(self, ctx: "BizHawkClientContext", name:str, bytecount:int) -> list:
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

    async def writeByName(self, ctx: "BizHawkClientContext", name:str, written) -> None:
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