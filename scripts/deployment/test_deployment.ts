import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'

dotenv.config()

const {
  SUPABASE_URL = '',
  SUPABASE_SERVICE_ROLE_KEY = '',
  SUPABASE_ANON_KEY = '',
  SUPABASE_TEST_EMAIL = '',
  SUPABASE_TEST_PASSWORD = ''
} = process.env

// Verify environment variables
const environment = {
  supabaseUrl: SUPABASE_URL,
  hasServiceKey: !!SUPABASE_SERVICE_ROLE_KEY,
  hasAnonKey: !!SUPABASE_ANON_KEY,
  hasTestEmail: !!SUPABASE_TEST_EMAIL,
  hasTestPassword: !!SUPABASE_TEST_PASSWORD
}

console.log('Initializing Supabase client with URL:', SUPABASE_URL)

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !SUPABASE_ANON_KEY || !SUPABASE_TEST_EMAIL || !SUPABASE_TEST_PASSWORD) {
  console.error('Missing required environment variables:', environment)
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async function main() {
  console.log('🚀 Starting deployment tests...')
  console.log('Environment:', environment)

  console.log('\n🧪 Verifying database tables and permissions...')

  // Test tables
  const tables = [
    'nba_game_lines.function_monitoring',
    'nba_game_lines.games',
    'nba_game_lines.game_odds'
  ]

  for (const table of tables) {
    console.log(`\nChecking table: ${table}`)
    const { data, error, count } = await supabase.from(table).select('*', { count: 'exact', head: true })
    
    if (error) {
      console.error(`❌ Error accessing ${table}:`, error)
      process.exit(1)
    }
    
    console.log(`✅ ${table} table exists and is accessible (count: ${count})`)
  }

  console.log('\n🔒 Verifying RLS policies...')
  console.log('Creating anonymous client...')
  const anonClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

  // Test anonymous access
  for (const table of tables) {
    console.log(`\nTesting anonymous access to ${table}...`)
    const { data, error } = await anonClient.from(table).select('*', { head: true })
    
    if (!error || error.code !== 'PGRST301') {
      console.warn(`⚠️ Warning: ${table} table might be publicly accessible`)
    } else {
      console.log(`✅ ${table} table is protected by RLS`)
    }
  }

  console.log('\n🧪 Testing monitoring function...')
  const testEvent = {
    function_name: 'test',
    event_type: 'success',
    duration_ms: 100,
    metadata: { test: true },
    timestamp: new Date().toISOString()
  }
  console.log('Test event:', JSON.stringify(testEvent, null, 2))

  // Get auth token
  console.log('Getting authentication token...')
  let { data: { session }, error: signInError } = await anonClient.auth.getSession()
  
  if (!session) {
    console.log('No existing session, attempting to sign in...')
    const { data: { session: newSession }, error: signInError } = await anonClient.auth.signInWithPassword({
      email: SUPABASE_TEST_EMAIL,
      password: SUPABASE_TEST_PASSWORD
    })
    
    if (signInError) {
      console.error('Failed to sign in:', signInError)
      process.exit(1)
    }
    
    session = newSession
    console.log('Successfully signed in and got token')
  }

  if (!session?.access_token) {
    console.error('No access token available')
    process.exit(1)
  }

  console.log('Got auth token:', session.access_token.slice(0, 10) + '...')

  // Test monitoring function
  console.log('Making request to monitoring function...')
  const response = await fetch(`${SUPABASE_URL}/functions/v1/monitoring`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify(testEvent)
  })

  const responseData = await response.json()

  if (!response.ok) {
    console.error('Monitoring function error:', {
      status: response.status,
      statusText: response.statusText,
      body: JSON.stringify(responseData),
      headers: Object.fromEntries(response.headers.entries())
    })
    console.error('\n❌ Test failed: Monitoring test failed:', response.statusText)
    console.error(JSON.stringify(responseData))
    process.exit(1)
  }

  console.log('Monitoring response:', JSON.stringify(responseData, null, 2))

  // Verify the event was saved
  console.log('Verifying saved monitoring event...')
  const { data: savedEvent, error: verifyError } = await supabase
    .from('function_monitoring')
    .select('*')
    .eq('function_name', testEvent.function_name)
    .eq('event_type', testEvent.event_type)
    .eq('timestamp', testEvent.timestamp)
    .single()

  if (verifyError) {
    console.error('Error verifying saved monitoring event:', verifyError)
    console.error('\n❌ Test failed: Failed to verify saved monitoring event:', verifyError.message)
    process.exit(1)
  }

  if (!savedEvent) {
    console.error('\n❌ Test failed: Monitoring event was not found in the database')
    process.exit(1)
  }

  console.log('✅ All tests passed!')
}

main().catch(error => {
  console.error('Unhandled error:', error)
  process.exit(1)
}) 