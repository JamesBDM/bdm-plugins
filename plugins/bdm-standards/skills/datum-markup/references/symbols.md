# Datum symbol catalogue — 311 symbols, 19 categories

Generated from `SYMBOL_LIBRARY` in `BDM-PDF-Markup-Tool.html` (Datum v3.42) by
`gen-skill-symbols.js`. Every id below resolves in the app; an unknown id draws as a dashed
placeholder box, so only use ids from this list.

## Shape matters — use the default proportions

Symbols are not all square. A sofa, a site office or a fence run carries a content box, and Datum maps the artwork into whatever rectangle the
annotation's two points give it. **A box of the wrong proportions draws the
symbol stretched.** Keep `w : h` equal to the default below and scale both
together — or use `p.symbol_at(page, cx, cy, id, width=…)`, which does it for you.

Default sizes are Datum's own placement sizes in PDF points. Furniture,
sanitary and kitchen items are sized from real millimetres at roughly 1:100
on A3; the **Construction** categories are sized to read on a 1:200–1:500
site plan (CMP / site establishment / traffic management) — scale them to
suit the sheet.

## Construction Management Plan quick picks

- Cranes at true size (place with `symbol_true_size`): tower `cr-tc-flat-50`,
  `cr-tc-flat-60`, `cr-tc-hammer-70`, luffing `cr-tc-luff-45`, `cr-tc-luff-60`,
  self-erecting `cr-tc-self-40`; Frannas `cr-franna-at15` / `-at20` / `-mac25` / `-at40`;
  all-terrain `cr-mc-25` / `-60` / `-100` / `-220` / `-400`
- Concrete at true size: boom pumps `cp-*` (17–58 m), agitators `tv-agi-mini`,
  `tv-agi-6`, `tv-agi-8`
- Deliveries at true size: `tv-srv`, `tv-mrv`, `tv-hrv`, `tv-crane` (Hiab),
  `tv-tipper`, `tv-truckdog`, `tv-semi`, `tv-bdouble`
- Access at true size: hoists `ac-hoist-single`, `ac-hoist-twin`, `ac-hoist-long`,
  `ac-hoist-mat`; scissors `ac-sc-19` … `ac-sc-40`, `ac-sc-rt33`, `ac-sc-rt43`;
  `ac-mast-20`; booms `ac-boom-k34` / `-k45` / `-k60` / `-t60` / `-t80` / `-t135`;
  `ac-spider-17`
- Scaffold and sheds at true size: runs `sf-run-1200`, `sf-run-700` (set
  `bays` / `bay_length` / `width`), `sf-stair`, `sf-loading`, `sf-tower-1450`,
  `sf-tower-850`; portables `ss-office-6` / `-9` / `-12` / `-stack`, `ss-crib-6`,
  `ss-crib-12`, `ss-toilet-6`, `ss-change-6`, `ss-firstaid`, `ss-portaloo`,
  `ss-portaloo-acc`; containers `ss-cont-10` / `-20` / `-40`
- Schematic (fixed-size) lifting: `cm-crane-tower`, `cm-crane-mobile`, `cm-hoist`,
  `cm-exclusion` (lift / exclusion zone); concrete `cm-pump-boom`, `cm-pump-line`,
  `cm-agitator`, `cm-washout`
- Site sheds: `cm-office`, `cm-crib`, `cm-amenities`, `cm-change`,
  `cm-portaloo`, `cm-container`, `cm-container40`
- Perimeter: `cm-hoarding`, `cm-tempfence`, `cm-gate-slide`, `cm-scaffold`,
  `cm-gantry`
- Waste and ESC: `cm-skip`, `cm-hookbin`, `cm-stockpile`, `cm-siltfence`,
  `cm-pitprotect`, `cm-shaker`, `cm-tpz`
- Traffic: `tc-route-veh`, `tc-route-ped`, `tc-controller`, `tc-spotter`,
  `tc-barrier`, `tc-cone`, `tc-sign-rw`, `tc-stopslow`, `tc-speed`,
  `tc-footpath`, `tc-arrowboard`, `tc-vms`, `tc-lights`

Linear symbols (fence, hoarding, silt fence, barrier, scaffold, route arrows,
retaining wall) are short fixed-proportion segments — stretching one just
spreads its posts and ticks apart and distorts the linework. For a long run,
place segments end to end (each at its default proportions, rotated to the
run), or draw the run as a `polyline` and use one symbol in a legend as the key.
Rotate any symbol with `rotation` (degrees).

## True-size symbols — pumps, trucks, cranes, hoists, EWPs, scaffold, sheds

Five categories are drawn from real dimensions and carry a real footprint
(the last column of their tables, in metres): **Concrete Pumps** (`cp-*`),
**Trucks & Vehicles** (`tv-*`), **Cranes** (`cr-*`), **Hoists & EWPs**
(`ac-*`) and **Scaffold & Site Sheds** (`sf-*`, `ss-*`). On a calibrated page
Datum places them at exactly that size, so the footprint is what the machine
occupies on site. Place them with `p.symbol_true_size(page, cx, cy, id, …)`,
which reads the page calibration (or takes `scale=`) and sizes the box from
the footprint — never from the default w × h, which is only Datum's
uncalibrated fallback.

Orientation at rotation 0: cab / boom / jib point to **+x** (right). Rotate
with `rotation` (degrees, clockwise). For a tower crane the placed box is
the base only; the jib and counter-jib are drawn out along +x at the
annotation's jib length, so rotate a tower crane to slew it.

Overlays (all optional, all editable later in Datum's Properties panel):

| option | applies to | draws |
|---|---|---|
| `show_reach=True`, `rings=[(r_m, "label"), …]` | pumps, cranes, boom & spider lifts | reach chart: one dashed ring per radius with its label (capacity). Omit `rings` for the machine's default chart |
| `jib=`, `cj=` (m) | tower cranes | jib length, counter-jib / tail radius |
| `parked=` (m) | luffing cranes | out-of-service (jib parked) radius |
| `show_vane=True` | tower cranes | weathervane zone (out-of-service slew circle) with a vane glyph, plus the counter-jib circle |
| `show_vane=True`, `tail=` (m) | mobile cranes | tail-swing circle |
| `show_turn=True`, `turn_right=True` | trucks | indicative turning circle (outer body sweep + inner wheel path) |
| `bays=`, `bay_length=` (2.4 / 1.8 / 1.2 / 0.7 m), `width=` (1.2 / 0.7 m) | scaffold runs (`sf-run-*`) | the run is drawn live from these and the box is sized to bays × bay length — the run starts at the left end (before rotation) |

Crane and pump capacities in the default charts are **typical for the
class, not a load chart**. When the job has a real crane, pass its radii and
capacities in `rings`.

### General / Drafting (10)

| id | name | default w × h |
|---|---|---|
| `g-north` | North Arrow | 44 × 44 |
| `g-section` | Section Marker | 40 × 40 |
| `g-detail` | Detail Marker | 40 × 40 |
| `g-elevation` | Elevation Marker | 40 × 40 |
| `g-level` | Level / RL Marker | 44 × 44 |
| `g-grid` | Grid Bubble | 36 × 36 |
| `g-rev` | Revision Triangle | 36 × 36 |
| `g-keynote` | Keynote Hexagon | 38 × 38 |
| `g-benchmark` | Benchmark | 36 × 36 |
| `g-scalebar` | Scale Bar | 60 × 60 |

### Architectural (17)

| id | name | default w × h |
|---|---|---|
| `a-door` | Door — Single Swing | 50 × 50 |
| `a-door2` | Door — Double Swing | 56 × 56 |
| `a-slider` | Door — Sliding | 56 × 56 |
| `a-bifold` | Door — Bi-fold | 52 × 52 |
| `a-cavity` | Door — Cavity Slider | 56 × 56 |
| `a-window` | Window — Fixed | 56 × 56 |
| `a-window-s` | Window — Sliding | 56 × 56 |
| `a-stair` | Stair — Straight Flight | 29 × 86.83 |
| `a-stair-cut` | Stair — Flight w/ Cut Line | 29 × 86.83 |
| `a-stair-l` | Stair — Quarter Landing (L) | 88 × 76.3 |
| `a-stair-u` | Stair — Half Landing (U) | 65 × 100.31 |
| `a-stair-spiral` | Stair — Spiral | 59 × 59 |
| `a-ramp` | Ramp | 35 × 116.67 |
| `a-skylight` | Skylight / Void Over | 44 × 44 |
| `a-break` | Break Line | 52 × 14.56 |
| `a-lift` | Lift / Elevator | 44 × 44 |
| `a-hatch` | Roof / Floor Hatch | 34 × 34 |

### Furniture — Bedroom (12)

| id | name | default w × h |
|---|---|---|
| `u-bed-k` | Bed — King + Bedsides | 80 × 59.52 |
| `u-bed-q` | Bed — Queen + Bedsides | 71 × 59.29 |
| `u-bed-d` | Bed — Double | 40 × 55.48 |
| `u-bed-ks` | Bed — King Single | 31 × 59.39 |
| `u-bed-s` | Bed — Single | 27 × 54.88 |
| `u-bunk` | Bunk Bed | 27 × 66.67 |
| `u-bedside` | Bedside Table | 25 × 22.23 |
| `u-drawers` | Chest of Drawers | 35 × 14.6 |
| `u-dresser` | Dressing Table + Stool | 35 × 26.25 |
| `u-robe` | Wardrobe / Robe | 53 × 17.65 |
| `u-wir` | Walk-in Robe — Shelving | 70 × 17.5 |
| `u-desk` | Desk + Chair | 44 × 39.34 |

### Furniture — Living & Dining (15)

| id | name | default w × h |
|---|---|---|
| `u-sofa` | Sofa — 3 Seat | 62 × 26.6 |
| `u-sofa2` | Sofa — 2 Seat | 44 × 26.4 |
| `u-sofa-l` | Sofa — L / Chaise | 76 × 55.56 |
| `u-armchair` | Armchair | 26 × 24.54 |
| `u-coffee` | Coffee Table | 35 × 20.41 |
| `u-sidetable` | Side Table | 25 × 25 |
| `u-tv` | TV / Entertainment Unit | 53 × 15.11 |
| `u-rug` | Rug | 70 × 55.16 |
| `u-table` | Dining — Rect (6) | 53 × 55.97 |
| `u-table-8` | Dining — Rect (8) | 70 × 41.16 |
| `u-table-r` | Dining — Round (4) | 65 × 65 |
| `u-table-r6` | Dining — Round (6) | 74 × 74 |
| `u-stool` | Bar Stool | 25 × 27.5 |
| `u-bookshelf` | Bookshelf | 53 × 10.28 |
| `u-chair` | Office Chair | 25 × 20.83 |

### Kitchen & Laundry (15)

| id | name | default w × h |
|---|---|---|
| `k-island` | Island Bench + Sink | 70 × 29.19 |
| `p-sink` | Kitchen Sink — Double | 28 × 17.5 |
| `k-sink1` | Kitchen Sink — Single | 25 × 22.5 |
| `u-cooktop` | Cooktop — 4 Burner | 25 × 25 |
| `k-cooktop9` | Cooktop — 900 (5 Burner) | 26 × 17.34 |
| `k-oven` | Oven | 25 × 25 |
| `k-rangehood` | Rangehood | 26 × 17.34 |
| `u-fridge` | Fridge | 26 × 20.23 |
| `u-dw` | Dishwasher | 25 × 25 |
| `k-mw` | Microwave | 25 × 16.68 |
| `k-pantry` | Pantry — Shelving | 26 × 17.34 |
| `u-wash` | Washing Machine | 25 × 25 |
| `u-dryer` | Dryer | 25 × 25 |
| `p-tub` | Laundry Tub | 25 × 22.73 |
| `k-bins` | Bins / Recycling | 30 × 15 |

### Sanitary / Plumbing (18)

| id | name | default w × h |
|---|---|---|
| `p-wc` | Toilet / WC | 25 × 43.78 |
| `p-wc-wh` | WC — Wall Hung | 25 × 35.51 |
| `p-bidet` | Bidet | 25 × 40.32 |
| `p-basin` | Basin — Round | 25 × 25 |
| `p-basin-o` | Basin — Oval | 25 × 20 |
| `p-vanity` | Vanity — Single | 30 × 16.68 |
| `p-vanity-2` | Vanity — Double | 53 × 16.22 |
| `p-bath` | Bath | 50 × 22.05 |
| `p-bath-fs` | Bath — Freestanding | 50 × 23.55 |
| `p-shower` | Shower — Square | 26 × 26 |
| `p-shower-w` | Shower — Walk-in | 47 × 26.41 |
| `p-urinal` | Urinal | 25 × 41.67 |
| `p-fw` | Floor Waste | 24 × 24 |
| `p-hwu` | Hot Water Unit | 36 × 36 |
| `p-dp` | Downpipe | 24 × 24 |
| `p-tap` | Tap / Hose Cock | 34 × 15.81 |
| `p-valve` | Isolation Valve | 34 × 18.7 |
| `p-wm` | Water Meter | 30 × 30 |

### Landscape & External (26)

| id | name | default w × h |
|---|---|---|
| `c-tree` | Tree — Canopy | 88 × 88 |
| `l-tree-lg` | Tree — Large / Mature | 90 × 90 |
| `l-tree-sm` | Tree — Small / Ornamental | 53 × 53 |
| `l-palm` | Palm | 80 × 80 |
| `l-conifer` | Conifer / Pencil Pine | 44 × 44 |
| `c-shrub` | Shrub | 35 × 35 |
| `l-hedge` | Hedge — Run | 90 × 14.4 |
| `l-ground` | Garden Bed / Groundcover | 70 × 70 |
| `l-planter` | Planter Box | 53 × 17.65 |
| `l-pot` | Pot Plant | 25 × 25 |
| `l-turf` | Turf / Lawn | 88 × 58.7 |
| `l-step` | Stepping Stones | 88 × 21.12 |
| `l-deck` | Deck / Timber | 88 × 58.7 |
| `l-pergola` | Pergola | 90 × 67.5 |
| `l-pool` | Swimming Pool | 90 × 55.71 |
| `l-spa` | Spa | 59 × 59 |
| `l-lounger` | Sun Lounger | 26 × 74.29 |
| `l-outdoor` | Outdoor Setting + Umbrella | 70 × 70 |
| `l-bbq` | BBQ | 35 × 17.5 |
| `l-firepit` | Fire Pit | 29 × 29 |
| `l-fence` | Fence | 90 × 14.4 |
| `l-retwall` | Retaining Wall | 90 × 18 |
| `l-clothesline` | Clothesline | 70 × 35 |
| `l-tank` | Rainwater Tank | 59 × 59 |
| `l-letterbox` | Letterbox | 25 × 35.71 |
| `l-car` | Car — Plan | 53 × 110.42 |

### Electrical (19)

| id | name | default w × h |
|---|---|---|
| `e-gpo` | GPO — Single | 28 × 28 |
| `e-gpo2` | GPO — Double | 28 × 28 |
| `e-gpowp` | GPO — Weatherproof | 30 × 30 |
| `e-switch` | Light Switch | 26 × 26 |
| `e-switch2` | Switch — Two-way | 28 × 28 |
| `e-downlight` | Downlight | 26 × 26 |
| `e-batten` | Batten Light | 28 × 28 |
| `e-led` | LED Strip | 56 × 11.2 |
| `e-fan` | Ceiling Fan | 36 × 36 |
| `e-smoke` | Smoke Detector | 28 × 28 |
| `e-exhaust` | Exhaust Fan | 32 × 32 |
| `e-db` | Distribution Board | 40 × 24 |
| `e-data` | Data Point | 26 × 26 |
| `e-tv` | TV Point | 28 × 28 |
| `e-3p` | Three-phase Outlet | 30 × 30 |
| `e-iso` | Isolator | 34 × 17 |
| `e-pir` | Motion Sensor | 30 × 30 |
| `e-em` | Emergency Light | 26 × 26 |
| `e-exit` | Exit Sign | 44 × 19.36 |

### Mechanical / HVAC (10)

| id | name | default w × h |
|---|---|---|
| `m-supply` | Supply Air Diffuser | 36 × 36 |
| `m-return` | Return Air Grille | 36 × 36 |
| `m-exhaustg` | Exhaust Grille | 36 × 36 |
| `m-duct` | Duct (w/ Flow) | 40 × 40 |
| `m-split` | AC Split — Indoor | 52 × 39.52 |
| `m-cond` | AC Condenser — Outdoor | 44 × 30.8 |
| `m-thermo` | Thermostat | 26 × 26 |
| `m-damper` | Damper | 36 × 18 |
| `m-ef` | Roof Exhaust Fan | 32 × 32 |
| `m-fcu` | Fan Coil Unit | 44 × 23.76 |

### Fire Services (10)

| id | name | default w × h |
|---|---|---|
| `f-ext` | Fire Extinguisher | 28 × 28 |
| `f-hr` | Fire Hose Reel | 32 × 32 |
| `f-hyd` | Fire Hydrant | 28 × 28 |
| `f-spk` | Sprinkler Head | 22 × 22 |
| `f-sd` | Smoke Detector (Fire) | 28 × 28 |
| `f-hd` | Heat Detector | 28 × 28 |
| `f-mcp` | Break Glass Call Point | 30 × 30 |
| `f-fb` | Fire Blanket | 26 × 26 |
| `f-wip` | WIP / EWIS Phone | 28 × 28 |
| `f-fip` | Fire Indicator Panel | 40 × 22.4 |

### Civil / Siteworks (8)

| id | name | default w × h |
|---|---|---|
| `c-park` | Parking Bay | 44 × 44 |
| `c-parkdis` | Accessible Parking | 44 × 44 |
| `c-bollard` | Bollard | 20 × 20 |
| `c-gate` | Gate (Swing) | 48 × 48 |
| `c-pit` | Stormwater Pit | 32 × 32 |
| `c-mh` | Manhole | 30 × 30 |
| `c-pole` | Light Pole | 26 × 26 |
| `c-sign` | Sign Post | 30 × 48 |

### Construction — Plant & Lifting (15)

| id | name | default w × h |
|---|---|---|
| `cm-crane-tower` | Tower Crane (with Slew Radius) | 90 × 90 |
| `cm-crane-mobile` | Mobile Crane (with Radius) | 80 × 80 |
| `cm-pump-boom` | Concrete Pump — Boom | 70 × 49.15 |
| `cm-pump-line` | Concrete Pump — Line / Trailer | 40 × 20 |
| `cm-agitator` | Concrete Agitator Truck | 60 × 21.6 |
| `cm-excavator` | Excavator | 50 × 50 |
| `cm-truck` | Truck — Delivery / Semi | 70 × 25.2 |
| `cm-ewp` | EWP / Scissor Lift | 30 × 18 |
| `cm-telehandler` | Telehandler / Forklift | 44 × 22 |
| `cm-hoist` | Materials / Personnel Hoist | 44 × 30.61 |
| `cm-gen` | Generator | 36 × 18 |
| `cm-lighttower` | Lighting Tower | 30 × 30 |
| `cm-tpb` | Temporary Power Board | 30 × 16.8 |
| `cm-water` | Temporary Water / Standpipe | 26 × 26 |
| `cm-cctv` | CCTV Camera | 28 × 28 |

### Construction — Site Establishment (30)

| id | name | default w × h |
|---|---|---|
| `cm-office` | Site Office (Portable) | 60 × 27.6 |
| `cm-crib` | Lunch / Crib Room | 60 × 27.6 |
| `cm-amenities` | Amenities / Toilet Block | 60 × 27.6 |
| `cm-change` | Change / Drying Room | 60 × 27.6 |
| `cm-portaloo` | Portable Toilet | 25 × 25 |
| `cm-container` | Shipping Container — 20ft | 60 × 24 |
| `cm-container40` | Shipping Container — 40ft | 90 × 18 |
| `cm-firstaid` | First Aid | 28 × 28 |
| `cm-muster` | Emergency Assembly Point | 36 × 36 |
| `cm-signin` | Site Sign-in / Induction | 34 × 17 |
| `cm-entry` | Site Entry Sign | 40 × 17.6 |
| `cm-spill` | Spill Kit | 28 × 28 |
| `cm-smoking` | Designated Smoking Area | 36 × 36 |
| `cm-laydown` | Material Laydown Area | 70 × 42 |
| `cm-loading` | Loading / Set-down Zone | 70 × 42 |
| `cm-exclusion` | Exclusion / Lift Zone | 60 × 60 |
| `cm-hoarding` | Site Hoarding | 90 × 18 |
| `cm-tempfence` | Temporary Fence | 90 × 14.4 |
| `cm-gate-slide` | Site Gate — Sliding | 60 × 24 |
| `cm-scaffold` | Scaffold | 80 × 24 |
| `cm-gantry` | Overhead Protection / Gantry | 80 × 32 |
| `cm-shaker` | Shaker Grid / Wheel Wash | 50 × 25 |
| `cm-washout` | Concrete Washout | 44 × 26.4 |
| `cm-skip` | Skip Bin | 34 × 17 |
| `cm-hookbin` | Hook-lift Bin | 56 × 20.16 |
| `cm-stockpile` | Stockpile | 50 × 50 |
| `cm-siltfence` | Sediment / Silt Fence | 90 × 14.4 |
| `cm-pitprotect` | Pit Inlet Protection | 34 × 34 |
| `cm-tpz` | Tree Protection Zone | 70 × 70 |
| `cm-monitor` | Noise / Dust / Vibration Monitor | 26 × 26 |

### Construction — Traffic Control (14)

| id | name | default w × h |
|---|---|---|
| `tc-route-veh` | Vehicle Route Arrow | 70 × 21 |
| `tc-route-ped` | Pedestrian Route Arrow | 70 × 21 |
| `tc-controller` | Traffic Controller | 26 × 26 |
| `tc-spotter` | Spotter | 26 × 26 |
| `tc-cone` | Traffic Cone | 25 × 25 |
| `tc-barrier` | Water-filled Barrier | 90 × 18 |
| `tc-barricade` | Barricade | 50 × 12 |
| `tc-sign-rw` | Sign — Road Work Ahead | 30 × 30 |
| `tc-stopslow` | Sign — Stop / Slow Bat | 26 × 26 |
| `tc-speed` | Sign — Speed Limit | 26 × 26 |
| `tc-footpath` | Sign — Footpath Closed | 36 × 18 |
| `tc-arrowboard` | Arrow Board | 40 × 20 |
| `tc-vms` | VMS Board | 40 × 20 |
| `tc-lights` | Portable Traffic Lights | 25 × 53.41 |

### Construction — Concrete Pumps (true size) (25)

| id | name | default w × h | real footprint (m) | overlays |
|---|---|---|---|---|
| `cp-schwing-17` | Schwing S17 (BPL500) — 17m boom pump | 90 × 45 | 8.6 × 4.3 | reach |
| `cp-putz-20` | Putzmeister BSF 20-4.09 H — 20m boom pump | 90 × 49.84 | 9.39 × 5.2 | reach |
| `cp-junjin-20` | Junjin JXZZ20-4.09HP — 20m boom pump | 90 × 42.78 | 9.05 × 4.3 | reach |
| `cp-hangil-21` | Hangil 21ZX-4 — 21m boom pump | 90 × 50.93 | 9.1 × 5.15 | reach |
| `cp-putz-24` | Putzmeister BSF 24-4.11 H — 24m boom pump | 90 × 44.15 | 10.6 × 5.2 | reach |
| `cp-sany-25` | Sany SY25 Z4-150 — 25m boom pump | 90 × 54 | 10.5 × 6.3 | reach |
| `cp-junjin-25` | Junjin JXZZ25-4.11HP — 25m boom pump | 90 × 54.23 | 10.46 × 6.3 | reach |
| `cp-putz-28` | Putzmeister BSF 28-4 — 28m boom pump | 90 × 50.14 | 10.59 × 5.9 | reach |
| `cp-junjin-30` | Junjin JXZ30-4.16HP — 30m boom pump | 90 × 53.11 | 11.1 × 6.55 | reach |
| `cp-sany-30` | Sany SY30 Z4-150 — 30m boom pump | 90 × 52.17 | 11.3 × 6.55 | reach |
| `cp-zoomlion-32` | Zoomlion 32X-4 — 32m boom pump | 90 × 51.63 | 11.54 × 6.62 | reach |
| `cp-putz-33` | Putzmeister BSF 33-4 — 32m boom pump | 90 × 57.27 | 12.1 × 7.7 | reach |
| `cp-putz-36` | Putzmeister BSF 36-4 — 36m boom pump | 90 × 57.27 | 12.1 × 7.7 | reach |
| `cp-junjin-38` | Junjin JXZZ38-5.16HP — 38m boom pump | 90 × 69.89 | 11.2 × 8.7 | reach |
| `cp-sany-39` | Sany SY39 RZ5-165 — 38m boom pump | 90 × 61.78 | 11.8 × 8.1 | reach |
| `cp-putz-42` | Putzmeister M42-5 — 42m boom pump | 90 × 67.78 | 11.95 × 9 | reach |
| `cp-sany-45` | Sany SY45 RZ5-165 — 44m boom pump | 90 × 69.01 | 12.52 × 9.6 | reach |
| `cp-putz-47` | Putzmeister BSF 47-5 — 46m boom pump | 90 × 72.29 | 12.45 × 10 | reach |
| `cp-junjin-47` | Junjin JXRZ47-5 — 46m boom pump | 90 × 73.61 | 12.47 × 10.2 | reach |
| `cp-everdigm-48` | Everdigm 48CX-5 — 47m boom pump | 90 × 63.33 | 14.07 × 9.9 | reach |
| `cp-junjin-50` | Junjin JXRZ50-5.18HP — 49m boom pump | 90 × 73.48 | 13.35 × 10.9 | reach |
| `cp-everdigm-50` | Everdigm 50CX-5 — 50m boom pump | 90 × 73.42 | 14.22 × 11.6 | reach |
| `cp-everdigm-56` | Everdigm 56RZ-5 — 56m boom pump | 90 × 77.97 | 14.77 × 12.8 | reach |
| `cp-junjin-57` | Junjin JXRZ57-5.18HP — 56m boom pump | 90 × 80.2 | 14.81 × 13.2 | reach |
| `cp-putz-58` | Putzmeister 58CX-5 — 57m boom pump | 90 × 73.37 | 15.1 × 12.31 | reach |

### Construction — Trucks & Vehicles (true size) (14)

| id | name | default w × h | real footprint (m) | overlays |
|---|---|---|---|---|
| `tv-b99` | Car — B99 design vehicle | 90 × 33.58 | 5.2 × 1.94 | turning circle |
| `tv-ute` | Ute / Van — light commercial | 90 × 32.5 | 5.4 × 1.95 | turning circle |
| `tv-srv` | Small Rigid Vehicle (SRV) — light truck | 90 × 32.77 | 6.4 × 2.33 | turning circle |
| `tv-mrv` | Medium Rigid Vehicle (MRV) — tray / tautliner | 90 × 25.57 | 8.8 × 2.5 | turning circle |
| `tv-crane` | Crane Truck (Hiab) — 6×4 rigid | 90 × 57.6 | 10 × 6.4 | turning circle |
| `tv-hrv` | Heavy Rigid Vehicle (HRV) — 12.5 m | 90 × 18 | 12.5 × 2.5 | turning circle |
| `tv-tipper` | Tipper — 6×4 (≈10 m³) | 90 × 27.11 | 8.3 × 2.5 | turning circle |
| `tv-tipper8` | Tipper — 8×4 twin steer (≈14 m³) | 90 × 23.68 | 9.5 × 2.5 | turning circle |
| `tv-agi-mini` | Concrete Truck — minimix 4×2 (≈3 m³) | 90 × 28.43 | 7.6 × 2.4 | turning circle |
| `tv-agi-6` | Concrete Truck — 6×4 agitator (≈5.5–6 m³) | 90 × 23.93 | 9.4 × 2.5 | turning circle |
| `tv-agi-8` | Concrete Truck — 8×4 agitator (≈7.6–8 m³) | 90 × 21.23 | 10.6 × 2.5 | turning circle |
| `tv-semi` | Semi-trailer — 19 m (AV) | 90 × 11.91 | 18.9 × 2.5 | turning circle |
| `tv-truckdog` | Truck & Dog — 19 m | 90 × 11.84 | 19 × 2.5 | turning circle |
| `tv-bdouble` | B-double — 26 m | 90 × 8.65 | 26 × 2.5 | turning circle |

### Construction — Cranes (true size) (15)

| id | name | default w × h | real footprint (m) | overlays |
|---|---|---|---|---|
| `cr-tc-flat-50` | Tower Crane — flat-top, 50 m jib | 40 × 40 | 6 × 6 | jib, reach, vane |
| `cr-tc-flat-60` | Tower Crane — flat-top, 60 m jib | 40 × 40 | 8 × 8 | jib, reach, vane |
| `cr-tc-hammer-70` | Tower Crane — hammerhead, 70 m jib | 40 × 40 | 8 × 8 | jib, reach, vane |
| `cr-tc-luff-45` | Tower Crane — luffing jib, 45 m | 40 × 40 | 6 × 6 | jib, reach, vane |
| `cr-tc-luff-60` | Tower Crane — luffing jib, 60 m | 40 × 40 | 10 × 10 | jib, reach, vane |
| `cr-tc-self-40` | Tower Crane — self-erecting, 40 m jib | 40 × 40 | 4.5 × 4.5 | jib, reach, vane |
| `cr-franna-at15` | Franna — AT15 (15 t pick & carry) | 90 × 24.31 | 8.7 × 2.35 | reach (front arc) |
| `cr-franna-at20` | Franna — AT20 (20 t pick & carry) | 90 × 22.96 | 9.8 × 2.5 | reach (front arc) |
| `cr-franna-mac25` | Franna — MAC25 (25 t pick & carry) | 90 × 20.09 | 11.2 × 2.5 | reach (front arc) |
| `cr-franna-at40` | Franna — AT40 (40 t pick & carry) | 90 × 19.49 | 12.7 × 2.75 | reach (front arc) |
| `cr-mc-25` | Mobile Crane — 25 t city crane | 90 × 66.32 | 9.5 × 7 | reach, tail swing |
| `cr-mc-60` | Mobile Crane — 60 t all-terrain | 90 × 63.16 | 11.4 × 8 | reach, tail swing |
| `cr-mc-100` | Mobile Crane — 100 t all-terrain | 90 × 56.92 | 13.6 × 8.6 | reach, tail swing |
| `cr-mc-220` | Mobile Crane — 220 t all-terrain | 90 × 55.47 | 15.9 × 9.8 | reach, tail swing |
| `cr-mc-400` | Mobile Crane — 400 t all-terrain | 90 × 49.59 | 19.6 × 10.8 | reach, tail swing |

### Construction — Hoists & EWPs (true size) (18)

| id | name | default w × h | real footprint (m) | overlays |
|---|---|---|---|---|
| `ac-hoist-single` | Builder’s Hoist — single cage (Alimak Scando 650 class) | 40 × 53.33 | 3.15 × 4.2 | — |
| `ac-hoist-twin` | Builder’s Hoist — twin cage (Alimak Scando 650 class) | 40 × 36.13 | 4.65 × 4.2 | — |
| `ac-hoist-long` | Builder’s Hoist — long cage 4.2 m | 40 × 66.04 | 3.15 × 5.2 | — |
| `ac-hoist-mat` | Materials Hoist — transport platform | 40 × 42.11 | 2.85 × 3 | — |
| `ac-sc-19` | Scissor Lift — 19 ft electric (5.8 m) | 30 × 8.35 | 2.73 × 0.76 | — |
| `ac-sc-26` | Scissor Lift — 26 ft electric (7.9 m) | 30 × 7.28 | 3.34 × 0.81 | — |
| `ac-sc-32` | Scissor Lift — 32 ft electric (9.8 m) | 30 × 10.51 | 3.34 × 1.17 | — |
| `ac-sc-40` | Scissor Lift — 40 ft electric (12.2 m) | 30 × 9.06 | 3.94 × 1.19 | — |
| `ac-sc-rt33` | Scissor Lift — 33 ft rough terrain (10 m) | 30 × 9.79 | 5.36 × 1.75 | — |
| `ac-sc-rt43` | Scissor Lift — 43 ft rough terrain (13 m) | 30 × 10.77 | 6.38 × 2.29 | — |
| `ac-mast-20` | Vertical Mast Lift — 20 ft (6 m) | 30 × 16.64 | 1.37 × 0.76 | — |
| `ac-boom-k34` | Boom Lift — 34 ft knuckle, electric | 30 × 11.25 | 4 × 1.5 | reach (outreach) |
| `ac-boom-k45` | Boom Lift — 45 ft knuckle | 30 × 10 | 6.9 × 2.3 | reach (outreach) |
| `ac-boom-k60` | Boom Lift — 60 ft knuckle | 30 × 8.72 | 8.6 × 2.5 | reach (outreach) |
| `ac-boom-t60` | Boom Lift — 60 ft telescopic | 30 × 8.33 | 9 × 2.5 | reach (outreach) |
| `ac-boom-t80` | Boom Lift — 80 ft telescopic | 30 × 6.64 | 11.3 × 2.5 | reach (outreach) |
| `ac-boom-t135` | Boom Lift — 135 ft telescopic | 30 × 5.6 | 13.4 × 2.5 | reach (outreach) |
| `ac-spider-17` | Spider Lift — 17 m tracked | 30 × 30 | 4.3 × 4.3 | reach (outreach) |

### Construction — Scaffold & Site Sheds (true size) (20)

| id | name | default w × h | real footprint (m) | overlays |
|---|---|---|---|---|
| `sf-run-1200` | Scaffold Run — 1.2 m wide (editable bays) | 90 × 9 | 12 × 1.2 | bays, bay length, width |
| `sf-run-700` | Scaffold Run — 0.7 m narrow (editable bays) | 90 × 5.25 | 12 × 0.7 | bays, bay length, width |
| `sf-stair` | Scaffold Stair Tower — 2.4 × 2.4 m | 60 × 60 | 2.4 × 2.4 | — |
| `sf-loading` | Scaffold Loading Bay — 2.4 × 2.4 m | 60 × 60 | 2.4 × 2.4 | — |
| `sf-tower-1450` | Mobile Scaffold Tower — 2.5 × 1.35 m | 60 × 42.31 | 3.9 × 2.75 | — |
| `sf-tower-850` | Mobile Scaffold Tower — 1.8 × 0.7 m narrow | 60 × 38.43 | 3.06 × 1.96 | — |
| `ss-office-6` | Site Office — 6.0 × 3.0 m | 60 × 30 | 6 × 3 | — |
| `ss-office-9` | Site Office — 9.6 × 3.0 m | 60 × 18.75 | 9.6 × 3 | — |
| `ss-office-12` | Site Office — 12.0 × 3.3 m | 60 × 16.5 | 12 × 3.3 | — |
| `ss-office-stack` | Site Office — 2-storey stack 12.0 × 3.3 m + stair | 60 × 16.5 | 12 × 3.3 | — |
| `ss-crib-6` | Crib Room — 6.0 × 3.0 m | 60 × 30 | 6 × 3 | — |
| `ss-crib-12` | Crib Room — 12.0 × 3.3 m | 60 × 16.5 | 12 × 3.3 | — |
| `ss-toilet-6` | Toilet Block — 6.0 × 3.0 m (M / F) | 60 × 30 | 6 × 3 | — |
| `ss-change-6` | Change Room — 6.0 × 3.0 m | 60 × 30 | 6 × 3 | — |
| `ss-firstaid` | First Aid Room — 3.6 × 2.4 m | 60 × 40 | 3.6 × 2.4 | — |
| `ss-portaloo` | Portaloo — 1.2 × 1.2 m | 60 × 60 | 1.2 × 1.2 | — |
| `ss-portaloo-acc` | Portaloo — accessible 2.2 × 2.2 m | 60 × 60 | 2.2 × 2.2 | — |
| `ss-cont-10` | Shipping Container — 10 ft (3.0 × 2.4 m) | 60 × 48.96 | 2.99 × 2.44 | — |
| `ss-cont-20` | Shipping Container — 20 ft (6.1 × 2.4 m) | 60 × 24.16 | 6.06 × 2.44 | — |
| `ss-cont-40` | Shipping Container — 40 ft (12.2 × 2.4 m) | 60 × 12.01 | 12.19 × 2.44 | — |
