from ..generic.Rules import set_rule
from .Locations import locBowser_table
from BaseClasses import MultiWorld


def set_rules(multiworld: MultiWorld, player: int):
    for quest, req in locBowser_table.items():
        set_rule(multiworld.get_location(quest, player),
                 lambda state, r=req: state.has("Quest Completion", player, r))
