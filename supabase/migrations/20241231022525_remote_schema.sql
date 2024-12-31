create type "nba_game_lines"."markettype" as enum ('H2H', 'SPREAD', 'TOTAL');

create type "nba_game_lines"."sporttype" as enum ('NBA', 'NFL', 'MLB', 'NHL');

create sequence "nba_game_lines"."bookmakers_id_seq";

create sequence "nba_game_lines"."nba_teams_id_seq";

drop policy "Allow authenticated read access to function_monitoring" on "nba_game_lines"."function_monitoring";

drop policy "Allow service role write access to function_monitoring" on "nba_game_lines"."function_monitoring";

drop policy "Allow authenticated read access to game_odds" on "nba_game_lines"."game_odds";

drop policy "Allow service role write access to game_odds" on "nba_game_lines"."game_odds";

drop policy "Allow authenticated read access to games" on "nba_game_lines"."games";

drop policy "Allow service role write access to games" on "nba_game_lines"."games";

revoke select on table "nba_game_lines"."function_monitoring" from "authenticated";

revoke insert on table "nba_game_lines"."function_monitoring" from "service_role";

revoke select on table "nba_game_lines"."game_odds" from "authenticated";

revoke insert on table "nba_game_lines"."game_odds" from "service_role";

revoke select on table "nba_game_lines"."games" from "authenticated";

revoke insert on table "nba_game_lines"."games" from "service_role";

alter table "nba_game_lines"."game_odds" drop constraint "game_odds_game_id_bookmaker_key_market_key_timestamp_key";

alter table "nba_game_lines"."game_odds" drop constraint "game_odds_game_id_timestamp_fkey";

alter table "nba_game_lines"."games" drop constraint "games_game_id_timestamp_key";

drop index if exists "nba_game_lines"."game_odds_game_id_bookmaker_key_market_key_timestamp_key";

drop index if exists "nba_game_lines"."games_game_id_timestamp_key";

drop index if exists "nba_game_lines"."idx_game_odds_market";

drop index if exists "nba_game_lines"."idx_game_odds_timestamp";

drop index if exists "nba_game_lines"."idx_games_commence_time";

drop index if exists "nba_game_lines"."idx_games_timestamp";

create table "nba_game_lines"."alembic_version" (
    "version_num" character varying(32) not null
);


alter table "nba_game_lines"."alembic_version" enable row level security;

create table "nba_game_lines"."bookmakers" (
    "id" integer not null default nextval('nba_game_lines.bookmakers_id_seq'::regclass),
    "key" character varying not null,
    "name" character varying not null,
    "is_active" boolean,
    "created_at" timestamp with time zone
);


alter table "nba_game_lines"."bookmakers" enable row level security;

create table "nba_game_lines"."nba_teams" (
    "id" integer not null default nextval('nba_game_lines.nba_teams_id_seq'::regclass),
    "name" character varying not null,
    "location" character varying not null,
    "abbreviation" character varying(3),
    "created_at" timestamp with time zone
);


alter table "nba_game_lines"."nba_teams" enable row level security;

alter table "nba_game_lines"."game_odds" drop column "bookmaker_key";

alter table "nba_game_lines"."game_odds" drop column "bookmaker_title";

alter table "nba_game_lines"."game_odds" drop column "market_key";

alter table "nba_game_lines"."game_odds" drop column "market_last_update";

alter table "nba_game_lines"."game_odds" drop column "outcomes";

alter table "nba_game_lines"."game_odds" add column "away_price" double precision;

alter table "nba_game_lines"."game_odds" add column "bookmaker_id" integer not null;

alter table "nba_game_lines"."game_odds" add column "home_price" double precision;

alter table "nba_game_lines"."game_odds" add column "market_type" nba_game_lines.markettype not null;

alter table "nba_game_lines"."game_odds" add column "over_price" double precision;

alter table "nba_game_lines"."game_odds" add column "spread" double precision;

alter table "nba_game_lines"."game_odds" add column "total" double precision;

alter table "nba_game_lines"."game_odds" add column "under_price" double precision;

alter table "nba_game_lines"."game_odds" alter column "created_at" drop default;

alter table "nba_game_lines"."game_odds" alter column "created_at" drop not null;

alter table "nba_game_lines"."game_odds" alter column "game_id" set data type integer using "game_id"::integer;

alter table "nba_game_lines"."game_odds" alter column "id" set data type integer using "id"::integer;

alter table "nba_game_lines"."games" drop column "away_team";

alter table "nba_game_lines"."games" drop column "home_team";

alter table "nba_game_lines"."games" drop column "sport_key";

alter table "nba_game_lines"."games" drop column "sport_title";

alter table "nba_game_lines"."games" drop column "timestamp";

alter table "nba_game_lines"."games" add column "away_team_id" integer not null;

alter table "nba_game_lines"."games" add column "home_team_id" integer not null;

alter table "nba_game_lines"."games" alter column "created_at" drop default;

alter table "nba_game_lines"."games" alter column "created_at" drop not null;

alter table "nba_game_lines"."games" alter column "game_id" set data type character varying using "game_id"::character varying;

alter table "nba_game_lines"."games" alter column "id" set data type integer using "id"::integer;

alter sequence "nba_game_lines"."bookmakers_id_seq" owned by "nba_game_lines"."bookmakers"."id";

alter sequence "nba_game_lines"."nba_teams_id_seq" owned by "nba_game_lines"."nba_teams"."id";

CREATE UNIQUE INDEX alembic_version_pkc ON nba_game_lines.alembic_version USING btree (version_num);

CREATE UNIQUE INDEX bookmakers_key_key ON nba_game_lines.bookmakers USING btree (key);

CREATE UNIQUE INDEX bookmakers_pkey ON nba_game_lines.bookmakers USING btree (id);

CREATE UNIQUE INDEX games_game_id_key ON nba_game_lines.games USING btree (game_id);

CREATE INDEX idx_game_commence_time ON nba_game_lines.games USING btree (commence_time);

CREATE INDEX idx_odds_timestamp ON nba_game_lines.game_odds USING btree ("timestamp");

CREATE UNIQUE INDEX nba_teams_abbreviation_key ON nba_game_lines.nba_teams USING btree (abbreviation);

CREATE UNIQUE INDEX nba_teams_name_key ON nba_game_lines.nba_teams USING btree (name);

CREATE UNIQUE INDEX nba_teams_pkey ON nba_game_lines.nba_teams USING btree (id);

CREATE UNIQUE INDEX unique_game_odds ON nba_game_lines.game_odds USING btree (game_id, bookmaker_id, market_type, "timestamp");

alter table "nba_game_lines"."alembic_version" add constraint "alembic_version_pkc" PRIMARY KEY using index "alembic_version_pkc";

alter table "nba_game_lines"."bookmakers" add constraint "bookmakers_pkey" PRIMARY KEY using index "bookmakers_pkey";

alter table "nba_game_lines"."nba_teams" add constraint "nba_teams_pkey" PRIMARY KEY using index "nba_teams_pkey";

alter table "nba_game_lines"."bookmakers" add constraint "bookmakers_key_key" UNIQUE using index "bookmakers_key_key";

alter table "nba_game_lines"."game_odds" add constraint "game_odds_bookmaker_id_fkey" FOREIGN KEY (bookmaker_id) REFERENCES nba_game_lines.bookmakers(id) not valid;

alter table "nba_game_lines"."game_odds" validate constraint "game_odds_bookmaker_id_fkey";

alter table "nba_game_lines"."game_odds" add constraint "game_odds_game_id_fkey" FOREIGN KEY (game_id) REFERENCES nba_game_lines.games(id) not valid;

alter table "nba_game_lines"."game_odds" validate constraint "game_odds_game_id_fkey";

alter table "nba_game_lines"."game_odds" add constraint "unique_game_odds" UNIQUE using index "unique_game_odds";

alter table "nba_game_lines"."games" add constraint "games_away_team_id_fkey" FOREIGN KEY (away_team_id) REFERENCES nba_game_lines.nba_teams(id) not valid;

alter table "nba_game_lines"."games" validate constraint "games_away_team_id_fkey";

alter table "nba_game_lines"."games" add constraint "games_game_id_key" UNIQUE using index "games_game_id_key";

alter table "nba_game_lines"."games" add constraint "games_home_team_id_fkey" FOREIGN KEY (home_team_id) REFERENCES nba_game_lines.nba_teams(id) not valid;

alter table "nba_game_lines"."games" validate constraint "games_home_team_id_fkey";

alter table "nba_game_lines"."nba_teams" add constraint "nba_teams_abbreviation_key" UNIQUE using index "nba_teams_abbreviation_key";

alter table "nba_game_lines"."nba_teams" add constraint "nba_teams_name_key" UNIQUE using index "nba_teams_name_key";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION nba_game_lines.fn_alert_on_error()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- You can customize this to send alerts via email, webhooks, etc.
    IF NEW.event_type = 'error' THEN
        -- For now, just raise a notice
        RAISE NOTICE 'Error in function %: %', NEW.function_name, NEW.error_message;
    END IF;
    RETURN NEW;
END;
$function$
;

CREATE TRIGGER trg_alert_on_error AFTER INSERT ON nba_game_lines.function_monitoring FOR EACH ROW EXECUTE FUNCTION nba_game_lines.fn_alert_on_error();


drop view if exists "public"."function_monitoring";

drop function if exists "public"."insert_monitoring_event"(p_function_name text, p_event_type text, p_duration_ms integer, p_error_message text, p_metadata jsonb, p_timestamp timestamp with time zone);


