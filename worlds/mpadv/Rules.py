from ..generic.Rules import set_rule
from .Locations import locBowser_table

def set_rules(multiworld: MultiWorld, player: int):
    for quest, req in locBowser_table:
        set_rule(multiworld.get_location(quest, player),
                 lambda state: state.has("Quest Completion", player, req))