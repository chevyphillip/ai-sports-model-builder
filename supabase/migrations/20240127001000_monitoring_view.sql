-- Create a view in the public schema for the monitoring table
CREATE OR REPLACE VIEW public.function_monitoring AS
SELECT * FROM nba_game_lines.function_monitoring;
-- Grant permissions on the view
GRANT SELECT ON public.function_monitoring TO authenticated;
GRANT ALL ON public.function_monitoring TO service_role;
-- Create a function to insert monitoring events
CREATE OR REPLACE FUNCTION public.insert_monitoring_event(
  p_function_name text,
  p_event_type text,
  p_duration_ms integer DEFAULT NULL,
  p_error_message text DEFAULT NULL,
  p_metadata jsonb DEFAULT NULL,
  p_timestamp timestamptz DEFAULT CURRENT_TIMESTAMP
)
RETURNS nba_game_lines.function_monitoring
SECURITY DEFINER
SET search_path = nba_game_lines, public
LANGUAGE plpgsql
AS $$
DECLARE
  v_result nba_game_lines.function_monitoring;
BEGIN
  INSERT INTO nba_game_lines.function_monitoring (
    function_name,
    event_type,
    duration_ms,
    error_message,
    metadata,
    timestamp
  ) VALUES (
    p_function_name,
    p_event_type,
    p_duration_ms,
    p_error_message,
    p_metadata,
    p_timestamp
  )
  RETURNING * INTO v_result;

  RETURN v_result;
END;
$$;
-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.insert_monitoring_event TO authenticated;
GRANT EXECUTE ON FUNCTION public.insert_monitoring_event TO service_role;
