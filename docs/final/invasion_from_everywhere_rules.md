# Invasion from Everywhere — Chapter 9 Wizard

Implemented 2026-09-20 from the September 20 checkpoint.

- 3-ball multiball; 20s opening ball save; 4-ball maximum.
- Add-a-balls receive a 15s ball save.
- Ends when multiball drops to one ball.
- Core loop: LOAD VUK -> Igor -> Atlantean -> LOAD VUK -> Molemen -> Atlantean -> LOAD VUK -> DeVargas -> Atlantean -> repeat.
- VUK holds indefinitely during each lower phase. Saucers park for up to 20s, while always preserving at least one free ball.
- Igor: existing good/bad shot sets; 500K correct, 50K wrong; 3 correct in a row lights all saucers until one locks.
- Molemen: existing left-pop / center-web / right-pop area mapping. First qualified lock scores 250K + add-a-ball when below four balls, otherwise 500K. Second qualified lock scores 250K and launches the VUK ball.
- DeVargas: right bank is restaged to targets 1 and 5 standing. Required sequence is 5 -> 1 -> any right-bank target -> lower spinner -> saucer. Correct shots 250K; wrong opening-bank target 50K and restages 1/5.
- Doctor Atlantean rooftop payoff: visit 1 requires 1 upper-target hit; visit 2 requires 2; visit 3+ requires 3. Any target counts, repeats allowed. Each target hit is 250K. Jackpot starts at 1M + 20K per Chapter 9 Case File. Upper spinner adds 50K per spin for that rooftop visit.
