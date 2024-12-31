import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { DateTime } from "https://esm.sh/luxon@3.3.0"

// Types
interface OddsResponse {
  success: boolean
  data?: any[]
  error?: string
}

interface GameData {
  id: string
  sport_key: string
  commence_time: string
  home_team: string
  away_team: string
  bookmakers: BookmakerData[]
}

interface BookmakerData {
  key: string
  markets: MarketData[]
}

interface MarketData {
  key: string
  outcomes: OutcomeData[]
}

interface OutcomeData {
  name: string
  price: number
  point?: number
}

// Constants
const ODDS_API_KEY = Deno.env.get('ODDS_API_KEY')
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

if (!ODDS_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  throw new Error('Required environment variables are not set')
}

// Initialize Supabase client with service role key
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async function fetchOdds(date: string): Promise<OddsResponse> {
  const url = `https://api.the-odds-api.com/v4/sports/basketball_nba/odds-history/?apiKey=${ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals&date=${date}`
  
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`)
    }
    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error('Error fetching odds:', error)
    return { success: false, error: error.message }
  }
}

async function processGameData(gameData: GameData, timestamp: string) {
  const { data: game } = await supabase
    .from('games')
    .select('id')
    .eq('game_id', gameData.id)
    .single()

  if (!game) {
    // Get team IDs
    const [homeTeam, awayTeam] = await Promise.all([
      supabase
        .from('nba_teams')
        .select('id')
        .eq('name', gameData.home_team)
        .single(),
      supabase
        .from('nba_teams')
        .select('id')
        .eq('name', gameData.away_team)
        .single()
    ])

    if (!homeTeam.data || !awayTeam.data) {
      console.error('Could not find teams:', gameData.home_team, gameData.away_team)
      return
    }

    // Insert game
    const { data: newGame, error: gameError } = await supabase
      .from('games')
      .insert({
        game_id: gameData.id,
        home_team_id: homeTeam.data.id,
        away_team_id: awayTeam.data.id,
        commence_time: gameData.commence_time
      })
      .select()
      .single()

    if (gameError) {
      console.error('Error inserting game:', gameError)
      return
    }

    // Process odds for each bookmaker
    for (const bm of gameData.bookmakers) {
      const { data: bookmaker } = await supabase
        .from('bookmakers')
        .select('id')
        .eq('key', bm.key)
        .single()

      if (!bookmaker) {
        continue
      }

      for (const market of bm.markets) {
        // Skip unknown market types
        if (!['h2h', 'spreads', 'totals'].includes(market.key)) {
          continue
        }

        // Check for existing odds
        const { data: existingOdds } = await supabase
          .from('game_odds')
          .select()
          .eq('game_id', newGame.id)
          .eq('bookmaker_id', bookmaker.id)
          .eq('market_type', market.key)
          .eq('timestamp', timestamp)

        if (existingOdds?.length) {
          continue
        }

        // Process outcomes based on market type
        const oddsData: any = {
          game_id: newGame.id,
          bookmaker_id: bookmaker.id,
          market_type: market.key,
          timestamp
        }

        if (market.key === 'h2h') {
          // Moneyline
          for (const outcome of market.outcomes) {
            if (outcome.name === gameData.home_team) {
              oddsData.home_price = outcome.price
            } else if (outcome.name === gameData.away_team) {
              oddsData.away_price = outcome.price
            }
          }
        } else if (market.key === 'spreads') {
          // Point spread
          for (const outcome of market.outcomes) {
            if (outcome.name === gameData.home_team) {
              oddsData.home_price = outcome.price
              oddsData.spread = outcome.point
            } else if (outcome.name === gameData.away_team) {
              oddsData.away_price = outcome.price
            }
          }
        } else if (market.key === 'totals') {
          // Over/under
          for (const outcome of market.outcomes) {
            if (outcome.name === 'Over') {
              oddsData.over_price = outcome.price
              oddsData.total = outcome.point
            } else if (outcome.name === 'Under') {
              oddsData.under_price = outcome.price
            }
          }
        }

        // Insert odds
        const { error: oddsError } = await supabase
          .from('game_odds')
          .insert(oddsData)

        if (oddsError) {
          console.error('Error inserting odds:', oddsError)
        }
      }
    }
  }
}

serve(async (req) => {
  try {
    const { date } = await req.json()
    if (!date) {
      return new Response(
        JSON.stringify({ error: 'Date parameter is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const { success, data, error } = await fetchOdds(date)
    if (!success) {
      return new Response(
        JSON.stringify({ error }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Process each game
    const timestamp = DateTime.now().toUTC().toISO()
    await Promise.all(data.map(game => processGameData(game, timestamp)))

    return new Response(
      JSON.stringify({ success: true, message: `Processed ${data.length} games` }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}) 