# Stationary Sawmill

A gasoline powered stationary sawmill: a 6 m bed with a saw carriage on rails. Left click it with an uncut log in hand to lay the log on the track, then right click it, choose the lumber you want and the carriage makes three passes. The cut lumber is stacked beside it. It runs on gasoline: pour a can into its tank (right click it with the can in hand); a cut burns half a liter.

Procedural model (tools/make_sawmill.py), 2656 triangles, 6.35 x 1.42 x 1.77 m, detail painted (tools/sawmill_pictures.py). Parts the game finds by name: `Frame`, `SawCarriage` (travels along x from its home end to the mirror of it) and `SawBlade` (spins). See docs/SAWMILL.md.
