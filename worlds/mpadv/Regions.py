import typing

from enum import Enum

from BaseClasses import MultiWorld, Region, Entrance, Location

from .Locations import (MPADVLocation, locJungle_table, locBooSnow_table, locSea_table, locBowser_table,
                        locDesert_table, locTown_table, locChar_table)

mpadv_regions = {
    "Town Area": locTown_table,
    "Jungle Area": locJungle_table,
    "Horror/Snow Area": locBooSnow_table,
    "Seaside Area": locSea_table,
    "Desert Area": locDesert_table,
    "Bowser's Pipeyard": [loc for loc in locBowser_table.keys()],
    "Quests": locChar_table
}


def create_regions(mw: MultiWorld, player: int, idMap:dict):

    temp_regions = {}
    for areaName, areaTable in mpadv_regions.items():
        areaInfo = Region(areaName, player, mw)
        areaRenderTable = [MPADVLocation(player, quest, idMap[quest], areaInfo) for quest in areaTable]
        areaInfo.locations.extend(areaRenderTable)

        mw.regions.append(areaInfo)
        temp_regions[areaName] = areaInfo

    menuR = Region("Menu", player, mw)
    menuR.connect(temp_regions["Town Area"])
    menuR.connect(temp_regions["Quests"])
    mw.regions.append(menuR)

    temp_regions["Town Area"].connect(temp_regions["Horror/Snow Area"])
    temp_regions["Town Area"].connect(temp_regions["Desert Area"])
    temp_regions["Town Area"].connect(temp_regions["Seaside Area"])
    temp_regions["Desert Area"].connect(temp_regions["Bowser's Pipeyard"])
    temp_regions["Desert Area"].connect(temp_regions["Jungle Area"])