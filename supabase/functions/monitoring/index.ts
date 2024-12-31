import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing environment variables:', {
    hasUrl: !!SUPABASE_URL,
    hasServiceKey: !!SUPABASE_SERVICE_ROLE_KEY
  })
  throw new Error('Required environment variables are not set')
}

console.log('Initializing Supabase client with URL:', SUPABASE_URL)
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    autoRefreshToken: false,
    persistSession: false,
    detectSessionInUrl: false
  }
})

interface MonitoringEvent {
  function_name: string
  event_type: 'start' | 'success' | 'error'
  duration_ms?: number
  error_message?: string
  metadata?: Record<string, any>
  timestamp: string
}

serve(async (req) => {
  try {
    console.log('Received monitoring event request:', {
      method: req.method,
      headers: Object.fromEntries(req.headers.entries())
    })
    
    // Verify authentication
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      console.error('No authorization header provided')
      return new Response(
        JSON.stringify({ error: 'No authorization header provided' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      console.error('Authentication failed:', authError)
      return new Response(
        JSON.stringify({ error: 'Authentication failed', details: authError }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }
    
    console.log('Authenticated user:', { id: user.id, role: user.role })
    
    const event: MonitoringEvent = await req.json()
    console.log('Parsed event data:', JSON.stringify(event, null, 2))

    // Validate event data
    const missingFields = []
    if (!event.function_name) missingFields.push('function_name')
    if (!event.event_type) missingFields.push('event_type')
    if (!event.timestamp) missingFields.push('timestamp')

    if (missingFields.length > 0) {
      console.error('Validation failed - missing fields:', missingFields)
      return new Response(
        JSON.stringify({ 
          error: 'Invalid event data: missing required fields',
          missingFields
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log('Attempting to insert event using function...')
    // Insert event using the function
    const { data, error } = await supabase.rpc('insert_monitoring_event', {
      p_function_name: event.function_name,
      p_event_type: event.event_type,
      p_duration_ms: event.duration_ms || null,
      p_error_message: event.error_message || null,
      p_metadata: event.metadata || null,
      p_timestamp: event.timestamp
    })

    if (error) {
      console.error('Database error:', {
        code: error.code,
        message: error.message,
        details: error.details,
        hint: error.hint,
        query: error.query
      })
      return new Response(
        JSON.stringify({ 
          error: 'Database error',
          details: error
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log('Event saved successfully:', JSON.stringify(data, null, 2))

    // If it's an error event, send alert
    if (event.event_type === 'error') {
      console.error('Error event received:', {
        function: event.function_name,
        error: event.error_message,
        metadata: event.metadata
      })
      // TODO: Implement alert mechanism (email, Slack, etc.)
    }

    return new Response(
      JSON.stringify({ success: true, data }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Function error:', {
      name: error.name,
      message: error.message,
      stack: error.stack,
      cause: error.cause
    })
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: {
          name: error.name,
          message: error.message,
          stack: error.stack,
          cause: error.cause
        }
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}) 