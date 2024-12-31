# Outcome

## name string

example: Houston Texans
The outcome label. The value will depend on the market. For totals markets, this will be 'Over' or 'Under'. For team markets, it will be the name of the team or participant, or 'Draw'

## price number

example: 2.23
The odds of the outcome. The format is determined by the oddsFormat query param. The format is decimal by default.

## point number

example: 20.5
nullable: true
The handicap or points of the outcome, only applicable to spreads and totals markets (this property will be missing for h2h and outrights markets)

## description string

nullable: true
This field is only relevant for certain markets. It contains more information about the outcome (for example, for player prop markets, it includes the player's name)

## link string

nullable: true
If available, link to the bookmaker's website and populate the betslip. This field is included when providing the query parameter includeLinks=true

## sid string

nullable: true
The bookmaker's id for the bet selection, if available. This field is included when providing the query parameter includeSids=true

## bet_limit number

nullable: true
The bookmaker's or exchange's monetary limit on the betting selection. The currency will depend on the bookmaker/exchange. This field is included when providing the query parameter includeBetLimits=true, and is mainly populated for betting exchanges.
