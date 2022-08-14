# Big-SLPP

Big-SLPP is a simple lua-python data structures parser that also has trailing comma's.

It also has two helper functions to help me re-create the files, as created by WoW.

## Example input

```lua
-- This is a lua file from the game World of Warcraft: Wrath of the Lich King
-- I need those keys sorted, because WoW/Lua keeps moving around the keys for
-- no good damn reason >:(
-- HOW DO YOU EXPECT ME TO TRACK MY SETTINGS IN A REPO, BLIZZARD!?
-- jk, I know Wrath is still relatively rough around the edges.

_NPCScanOptionsCharacter = {
	["Achievements"] = {
		[1312] = true,
		[2257] = true,
	},
	["NPCs"] = {
		[18684] = "Bro'Gaz the Clanless",
		[32491] = "Time-Lost Proto Drake",
	},
	["Version"] = "3.3.5.5",
	["NPCWorldIDs"] = {
		[18684] = 3,
		[32491] = 4,
	},
}

```

## `SLPP.decode()` output (not what I was looking for)

```lua

-- This is a lua file from the game World of Warcraft: Wrath of the Lich King
-- I need those keys sorted, because WoW/Lua keeps moving around the keys for
-- no good damn reason >:(
-- HOW DO YOU EXPECT ME TO TRACK MY SETTINGS IN A REPO, BLIZZARD!?
-- jk, I know Wrath is still relatively rough around the edges.


["_NPCScanOptionsCharacter"] = {
	["Achievements"] = {
		[1312] = true,
		[2257] = true
	},
	["NPCWorldIDs"] = {
		[18684] = 3,
		[32491] = 4
	},
	["NPCs"] = {
		[18684] = "Bro'Gaz the Clanless",
		[32491] = "Time-Lost Proto Drake"
	},
	["Version"] = "3.3.5.5"
}

```

Note the lack of trailing comma's, and _NPCScanOptionsCharacter being wrapped
in quotes and brackets.

## `big_slpp.utils.unwrap()`'s output

```lua

_NPCScanOptionsCharacter = {
	["Achievements"] = {
		[1312] = true,
		[2257] = true,
	},
	["NPCWorldIDs"] = {
		[18684] = 3,
		[32491] = 4,
	},
	["NPCs"] = {
		[18684] = "Bro'Gaz the Clanless",
		[32491] = "Time-Lost Proto Drake",
	},
	["Version"] = "3.3.5.5",
}
```

Practically the same, but sorted! :D
Also, trailing comma's!
