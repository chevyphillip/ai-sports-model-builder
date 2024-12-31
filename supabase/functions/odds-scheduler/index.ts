import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { DateTime } from "https://esm.sh/luxon@3.3.0"

const FUNCTION_URL = Deno.env.get('FUNCTION_URL') // URL of the odds-collector function
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY')

if (!FUNCTION_URL || !SUPABASE_ANON_KEY) {
  throw new Error('Required environment variables are not set')
}

serve(async (_req) => {
  try {
    // Get current date in ISO format
    const date = DateTime.now().toUTC().toFormat('yyyy-MM-dd\'T\'HH:mm:ss\'Z\'')

    // Call the odds-collector function
    const response = await fetch(FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      },
      body: JSON.stringify({ date })
    })

    if (!response.ok) {
      throw new Error(`Collector function returned ${response.status}`)
    }

    const result = await response.json()
    return new Response(
      JSON.stringify({ success: true, result }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}) 