import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'

// Load environment variables
dotenv.config()

const supabaseUrl = process.env.SUPABASE_URL
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseServiceRoleKey) {
  throw new Error('Missing environment variables')
}

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey)

async function setupRLS() {
  console.log('🔒 Setting up database permissions...')

  try {
    // First, revoke all privileges
    console.log('\n📝 Revoking all privileges...')
    await supabase.rpc('execute_sql', {
      sql: `
        -- Revoke all privileges from public schema
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM public CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM public CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM public CASCADE;
        REVOKE ALL ON SCHEMA public FROM public CASCADE;
        
        -- Revoke all privileges from nba_game_lines schema
        REVOKE ALL ON ALL TABLES IN SCHEMA nba_game_lines FROM public CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nba_game_lines FROM public CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA nba_game_lines FROM public CASCADE;
        REVOKE ALL ON SCHEMA nba_game_lines FROM public CASCADE;
        
        -- Revoke from anon role
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon CASCADE;
        REVOKE ALL ON SCHEMA public FROM anon CASCADE;
        
        REVOKE ALL ON ALL TABLES IN SCHEMA nba_game_lines FROM anon CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nba_game_lines FROM anon CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA nba_game_lines FROM anon CASCADE;
        REVOKE ALL ON SCHEMA nba_game_lines FROM anon CASCADE;
        
        -- Revoke from authenticated role
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM authenticated CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM authenticated CASCADE;
        REVOKE ALL ON SCHEMA public FROM authenticated CASCADE;
        
        REVOKE ALL ON ALL TABLES IN SCHEMA nba_game_lines FROM authenticated CASCADE;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nba_game_lines FROM authenticated CASCADE;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA nba_game_lines FROM authenticated CASCADE;
        REVOKE ALL ON SCHEMA nba_game_lines FROM authenticated CASCADE;
      `
    })
    console.log('✅ Revoked all privileges')

    // Grant necessary permissions
    console.log('\n📝 Setting up role permissions...')
    await supabase.rpc('execute_sql', {
      sql: `
        -- Grant schema usage
        GRANT USAGE ON SCHEMA public TO authenticated;
        GRANT USAGE ON SCHEMA public TO service_role;
        GRANT USAGE ON SCHEMA nba_game_lines TO authenticated;
        GRANT USAGE ON SCHEMA nba_game_lines TO service_role;
        
        -- Grant table permissions
        GRANT SELECT ON ALL TABLES IN SCHEMA nba_game_lines TO authenticated;
        GRANT ALL ON ALL TABLES IN SCHEMA nba_game_lines TO service_role;
        
        -- Grant sequence permissions
        GRANT USAGE ON ALL SEQUENCES IN SCHEMA nba_game_lines TO authenticated;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA nba_game_lines TO service_role;
        
        -- Set up default privileges for future objects
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public 
        REVOKE ALL ON TABLES FROM public;
        
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA nba_game_lines 
        REVOKE ALL ON TABLES FROM public;
        
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public 
        REVOKE ALL ON TABLES FROM anon;
        
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA nba_game_lines 
        REVOKE ALL ON TABLES FROM anon;
        
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA nba_game_lines 
        GRANT SELECT ON TABLES TO authenticated;
        
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA nba_game_lines 
        GRANT ALL ON TABLES TO service_role;
        
        -- Disable RLS on all tables (we'll use grants instead)
        ALTER TABLE nba_game_lines.function_monitoring DISABLE ROW LEVEL SECURITY;
        ALTER TABLE nba_game_lines.games DISABLE ROW LEVEL SECURITY;
        ALTER TABLE nba_game_lines.game_odds DISABLE ROW LEVEL SECURITY;
      `
    })
    console.log('✅ Set up role permissions')

    console.log('\n✅ Database permissions set up successfully')
  } catch (error) {
    console.error('\n❌ Failed to set up database permissions:', error)
    process.exit(1)
  }
}

setupRLS() 