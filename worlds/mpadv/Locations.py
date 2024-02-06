from BaseClasses import Location


class MPADVLocation(Location):
    game = "Mario Party Advance"


# note: some quests may require traveling to other regions, re-evaluate rules when adding region keys
locTown_table = [
    "Quest: Accessorize!",
    "Quest: Big Boss Bob-omb",
    "Quest: Chomper Stomper",
    "Quest: Find the Password",
    "Quest: Flowers are a Blast!",
    "Quest: Hearts A-flutter",
    "Quest: Hey, UFO!",
    "Quest: Kamek Krew Live!",
    "Quest: Kind Goomba",
    "Quest: Locomotionless",
    "Quest: Losing Streak",
    "Quest: Possibly a Robbery?",
    "Quest: Weeping Twomp",
    "Quest: Winners Keepers"
]

locDesert_table = [
    "Quest: A Speeding Bill",
    "Quest: Game Mage",
    "Quest: Hammerama",
    "Quest: Mysterious Riddles",    # note: this one is seperated from the main desert area and requires diff. key
    "Quest: Treasure of Mystery!"
]

locSea_table = [
    "Quest: Blooper Battle",
    "Quest: Comedy Bomb",
    "Quest: Duel Tower 1F",
    "Quest: Duel Tower 2F",
    "Quest: Duel Tower 3F",
    "Quest: Mathematician!",
    "Quest: Sploosh!",
    "Quest: Swimmin' Wimp",
    "Quest: What's that line?"
]

# the snow area only has two quests, so its merged with the horror area
locBooSnow_table = [
    "Quest: Condo of Mystery!",
    "Quest: DVD for Me",
    "Quest: Love that Princess!",
    "Quest: Nerd Force V",
    "Quest: True Blue Boo",
    "Quest: Cool as Ice",
    "Quest: Engaging Game"
]

locJungle_table = [
    "Quest: Blossom of my Heart",
    "Quest: Debt's a Hoot",
    "Quest: Dino of Mystery!",
    "Quest: Jungle Jive",
    "Quest: Monkeynapping?!",
    "Quest: Mustached Hero!"
]

# keys here reffer to how many quests must be complete to do the quest
locBowser_table = {
    "Bowser Quest: Goal Tenderizer": 3,
    "Bowser Quest: Chillin' Villan": 10,
    "Bowser Quest: Bowser Accused!": 15,
    "Bowser Quest: Bowser's Toys": 20,
    "Bowser Quest: Boss Bowser": 25,
    "Bowser Quest: Besteset Buds": 30,
    "Bowser Quest: Game King": 35,
    "Bowser Quest: Bowserstein!": 40,
    "Bowser Quest: Final Showdown": 49
}


mpadv_locations = {name: id for id, name in enumerate(
    [*locTown_table, *locDesert_table, *locSea_table,
        *locBooSnow_table, *locJungle_table, *locBowser_table.keys()], 5454540
)}