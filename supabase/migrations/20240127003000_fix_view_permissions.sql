-- Drop existing view
DROP VIEW IF EXISTS public.function_monitoring;

-- Create view with proper schema
CREATE OR REPLACE VIEW public.function_monitoring AS
SELECT * FROM nba_game_lines.function_monitoring;

-- Grant permissions on the view
GRANT SELECT ON public.function_monitoring TO authenticated;
GRANT ALL ON public.function_monitoring TO service_role;

-- Verify the view exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_views
    WHERE schemaname = 'public'
    AND viewname = 'function_monitoring'
  ) THEN
    RAISE EXCEPTION 'View public.function_monitoring does not exist';
  END IF;
END;
$$;