# mandala
### codename — working title

---

## Core philosophy

A mandala is beautiful, time-heavy to create, and infinitely destroyable.

You build with total care. Completion is the ending. The ending is the dissolution.
You begin again — not because you failed, but because that is what you do with a mandala.

The win condition is not survival. It is completion. When the area reaches natural balance,
the game ends. The mandala is swept. A new area is generated. You begin again.

Each run is a different organism. Each organism is a different mandala.
The whole game is a mandala of mandalas.

---

## The levels

Sequential. Each level must be completed to unlock the next.
Each organism works the same patch of earth, seen at a different scale and moment in time.

1. **Archaebacteria** — extremophiles. First life. Mineral gradients, heat, chemical reactions.
   No oxygen. No photosynthesis. Making the substrate viable for what comes next.
   *Visual: terminal/curses, monochrome. No light — only chemistry.*

2. **Cyanobacteria** — first photosynthesizers. Oxygenating the atmosphere.
   The Great Oxygenation Event. Success poisons the world the archaebacteria built
   and makes every subsequent level possible.
   *Visual: terminal with color. Photosynthesis — light enters the world for the first time.*

3. **Fungus** — decomposer, network builder. The bridge between the chemical world
   and the plant world. Breaking down mineral substrate, building soil.
   *Visual: terminal, richer. Network topology. Still underground.*

4. **Lichens** — symbiosis. You are two things (fungus + algae) that must stay in balance.
   Pioneer species on bare rock. Going where nothing else survives.
   *Visual: transition point. First organism that perceives in any meaningful sense.*

5. **Symbiotes** — broader symbiotic relationships. Mycorrhizal networks.
   The network becomes the mechanic.
   *Visual: 2D graphical. Relationships require spatial representation.*

6. **Beetles and bugs** — decomposers, pollinators, dispersers. First truly mobile actors.
   You move through the world rather than growing through it.
   *Visual: full 2D, fluid. Movement, color, texture.*

7. **Worms** — soil engineers. Making the ground itself. Everything that grows in soil
   owes something to worms. The final stage before the climax ecosystem.
   *Visual: particle/procedural. Tactile, physical, underground but rich.*

---

## The carryforward

Nothing mechanical carries between levels. No resources, no unlocks, no stats.

What carries: **position and substrate quality**. The location of the small within the
greater landscape. The archaebacteria conditioned specific tiles. The cyanobacteria
inherited that conditioned ground. The spatial continuity is the thread.

The player feels it even when the organism doesn't.

---

## The ending

No human settlers until animals have fully populated a healthy forest.
Humans are a consequence, not players. They arrive because the ground is ready —
because every organism before them did its work and dissolved.

The mandala is swept the moment something walks onto the ground
and doesn't know what made it possible.

That is the ending of the whole game.

---

## The lifecycle arc (within each level)

Each level moves through ecological succession appropriate to that organism:

- **Stage 0** — devastated substrate. Dead, hostile, inherited. The player did not make it this way.
- **Stage 1** — pioneer activity. First interventions. Slow, unglamorous, foundational.
- **Stage 2** — colonization. Invisible infrastructure. Building connectivity.
- **Stage 3** — emergence. First visible signs of life. Patchy, fragile, meaningful.
- **Stage 4** — expression. The organism doing what it does fully.
- **Stage 5** — climax. Self-sustaining. The system runs itself.
  The player's role shifts from laborer to steward to witness.

"Natural balance" as a win condition: the area is self-sustaining across all stages
simultaneously, requiring no player intervention for a sustained period.

---

## Player role arc (within each level)

Early game — active and laborious. You are doing the work.
Mid game — tending and watching. You are maintaining conditions.
Late game — stepping back. The system runs without you.
Ending — witness. You are no longer needed. The mandala is complete.

---

## Timescale and pacing

Each level should feel time-heavy. Rushing is not possible — only tending.
The pacing should honor the investment. Each stage asks something of the player.

The timescale *feels* different per level even if game ticks are consistent:
archaebacteria operate on geological time; beetles are almost frenetic by comparison.

---

## Tone

Inherited from quietcurrent:
- Quiet, observational.
- All prose lowercase except proper nouns. No exclamation points.
- Never confirm, never deny what the player is. The organism is never named.
  The player infers from mechanics, flavor text, scale.
- The writing is the world noticing itself.

---

## Architecture

```
mandala/
  launcher.py         ← progression state, level sequencing, seamless transitions
  state.py            ← cross-level carryforward (location, conditioned tiles)
  levels/
    01_archaea/       ← terminal/curses
    02_cyano/         ← terminal + color
    03_fungus/
    04_lichens/
    05_symbiotes/
    06_beetles/
    07_worms/
```

Each level exposes a single `run(carry: CarryState) -> CarryState` function.
The launcher calls it, plays the dissolution ceremony on return, then calls the next.
The player never touches the seam between levels.

Visual technology escalates per level — terminal for early life, graphical for later.
The transition between renderers is itself a narrative moment: gaining a new sense.

---

## Level 1 — Archaebacteria (design notes)

### What you are
An archaebacterium moving through primordial substrate. The player controls a single
organism directly — fluid, spatial movement through a living chemical medium.
You are not managing the colony from above. You are the pioneer cell.
The colony is what you leave in your wake.

### The medium
A cross-section of substrate: rock, mineral seams, chemical gradients, temperature zones.
The environment is in constant motion — chemical plumes drift, temperature zones pulse,
competing organisms move. It is hostile and alive.

### What you do
- Move through the substrate consuming chemical compounds (sulfur, iron, methane)
- Leave a conditioned biofilm trail — this is the product, the carryforward
- Compete with other microbial mats for the best chemical seams
- Survive hostile zones (extreme pH, temperature, competing colonies)
- Adapt to new chemical environments as you expand

### Resources
- **Chemical compounds** — sulfur, iron, methane; harvested by moving through seams
- **Biomass** — generated by processing chemicals; funds colony spread and adaptation
- **Heat** — geothermal energy; beneficial in optimal range, damaging at extremes

### What you produce (the carryforward)
A healthy archaebacterial colony conditions the substrate through:
- **Fixed nitrogen** — atmospheric nitrogen converted to usable ammonia compounds;
  cyanobacteria need this to build proteins and chlorophyll
- **Bioavailable minerals** — iron, phosphorus, calcium released from mineral bonds
- **Organic carbon** — dead archaebacteria become the first organic matter, first "soil"
- **pH moderation** — sulfur consumption buffers local chemistry toward the tolerable

The tiles the player has colonized and processed become **conditioned substrate** —
the starting quality of the ground the next level inherits.

### Spore parallel
The cell stage: swim toward food, eat, grow, avoid predators, collect adaptations.
Translated: move through substrate, consume chemicals, spread biofilm, avoid hostile zones,
adapt to chemical environments. Same loop, different medium, different stakes.

### Win condition
The colony reaches natural balance — conditioned substrate covers sufficient area,
biomass is self-sustaining without active intervention, chemical gradients are stable.
The pioneer work is done. The mandala is complete.

---

## Open questions

- Does the biofilm trail grow autonomously once laid (colony self-expands), or is the
  player always the active front edge and the trail is the record of where they've been?
- What does the dissolution ceremony look like for each level? Each should feel distinct.
- Are setbacks (competing colony overtaking ground, temperature spike, chemical depletion)
  possible? Yes — they are part of the making, not failures.
- What does "going outside" look like for archaebacteria? Reaching a new mineral seam
  deeper in the rock, perhaps — high risk, high reward.
