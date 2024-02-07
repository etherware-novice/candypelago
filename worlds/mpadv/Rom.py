import pkgutil
from typing import TYPE_CHECKING, List, Tuple
import io, os, bsdiff4

from worlds.Files import APDeltaPatch
from BaseClasses import MultiWorld, Region, Entrance, Location
from settings import get_settings

class MPADVDeltaPatch(APDeltaPatch):
    game = "Mario Party Advance"
    hash = "9d0d27345bf88de8b025aa24d54d6bad"
    patch_file_ending = ".apmpadv"
    result_file_ending = ".gba"

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_as_bytes()


def get_base_rom_as_bytes() -> bytes:
    with open("Mario Party Advance (USA).gba", "rb") as infile: # make this do some fancy custom path thing like mlss
        base_rom_bytes = bytes(infile.read())

    return base_rom_bytes

class Rom:
    hash = "9d0d27345bf88de8b025aa24d54d6bad"

    def __init__(self, world: MultiWorld, player: int):
        with open("Mario Party Advance (USA).gba", 'rb') as file:
            content = file.read()
        patched = self.apply_static_delta(content)
        self.random = world.per_slot_randoms[player]
        self.stream = io.BytesIO(patched)
        self.world = world
        self.player = player

    def apply_static_delta(self, b: bytes) -> bytes:
        """
        Gets the patched ROM data generated from applying the ap-patch diff file to the provided ROM.
        Which should contain all changed text banks and assembly code
        """
        import pkgutil
        patch_bytes = pkgutil.get_data(__name__, "data/basepatch.bsdiff")
        patched_rom = bsdiff4.patch(b, patch_bytes)
        return patched_rom

    def close(self, path):
        output_path = os.path.join(path, f"AP_{self.world.seed_name}_P{self.player}_{self.world.player_name[self.player]}.gba")
        with open(output_path, 'wb') as outfile:
            outfile.write(self.stream.getvalue())
        patch = MPADVDeltaPatch(os.path.splitext(output_path)[0] + ".apmpadv", player=self.player,
                                player_name=self.world.player_name[self.player], patched_path=output_path)
        patch.write()
        os.unlink(output_path)
        self.stream.close()
