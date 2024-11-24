# World Generator

Changes to make each season relative to the vanilla world generation

## World Size

- WorldLength 100
- WorldWidth 100

## Flatter map

- MaxElevationOceanDistance (double)
- (the other thing that controls Y in the equation, TODO)
- NumHighDeserts (zero, it has no unique flora / fauna)
- NumSteppes (zero, it has no unique flora / fauna)

## More Fresh Water

- LakeSizeRange (increase)
- NumLakesRange (increase)
- NumRiversRange (increase)
- RiverCellWidth (increase)

## One Continent, More Islands

- NumContinentsRange [1, 1]
- NumSmallIslandsRange (triple)
