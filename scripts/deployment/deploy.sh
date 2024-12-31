#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Supabase CLI is installed
check_supabase_cli() {
    if ! command -v supabase &> /dev/null; then
        print_status "$YELLOW" "Installing Supabase CLI..."
        brew install supabase/tap/supabase
    else
        print_status "$GREEN" "Supabase CLI is already installed"
    fi
}

# Check if required environment variables exist in .env
check_env_vars() {
    local required_vars=(
        "ODDS_API_KEY"
        "SUPABASE_URL"
        "SUPABASE_SERVICE_ROLE_KEY"
        "SUPABASE_ANON_KEY"
        "SUPABASE_DB_PASSWORD"
        "ODDS_COLLECTOR_URL"
        "ODDS_SCHEDULER_URL"
    )
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_status "$RED" "Missing required environment variables in .env file:"
        for var in "${missing_vars[@]}"; do
            echo "- $var"
        done
        exit 1
    fi

    print_status "$GREEN" "All required environment variables found in .env file"
}

# Initialize Supabase project if needed
init_supabase() {
    if [ ! -f "supabase/config.toml" ]; then
        print_status "$YELLOW" "Initializing Supabase project..."
        supabase init
    fi
}

# Link to Supabase project
link_project() {
    print_status "$YELLOW" "Linking to Supabase project..."
    local project_ref=$(grep SUPABASE_URL .env | sed -n 's/.*https:\/\/\([^.]*\).*/\1/p')
    local db_password=$(grep SUPABASE_DB_PASSWORD .env | cut -d'=' -f2-)
    
    if [ -z "$project_ref" ]; then
        print_status "$RED" "Could not extract project reference from SUPABASE_URL"
        exit 1
    fi
    
    if [ -z "$db_password" ]; then
        print_status "$RED" "Could not find SUPABASE_DB_PASSWORD in .env"
        exit 1
    fi
    
    print_status "$YELLOW" "Using project reference: $project_ref"
    if ! supabase link --project-ref "$project_ref" --password "$db_password"; then
        print_status "$RED" "Failed to link Supabase project"
        exit 1
    fi
}

# Deploy Edge Functions
deploy_functions() {
    print_status "$YELLOW" "Deploying Edge Functions..."
    
    # Deploy monitoring function first
    print_status "$YELLOW" "Deploying monitoring function..."
    if ! supabase functions deploy monitoring --no-verify-jwt; then
        print_status "$RED" "Failed to deploy monitoring function"
        exit 1
    fi
    
    # Deploy odds-collector function
    print_status "$YELLOW" "Deploying odds-collector function..."
    if ! supabase functions deploy odds-collector --no-verify-jwt; then
        print_status "$RED" "Failed to deploy odds-collector function"
        exit 1
    fi

    # Deploy odds-scheduler function
    print_status "$YELLOW" "Deploying odds-scheduler function..."
    if ! supabase functions deploy odds-scheduler --no-verify-jwt; then
        print_status "$RED" "Failed to deploy odds-scheduler function"
        exit 1
    fi
}

# Apply database migrations
apply_migrations() {
    print_status "$YELLOW" "Applying database migrations..."
    
    if ! supabase db push; then
        print_status "$RED" "Failed to apply database migrations"
        exit 1
    fi
    
    print_status "$GREEN" "Database migrations applied successfully"
}

# Run deployment tests
run_tests() {
    print_status "$YELLOW" "Running deployment tests..."
    
    if ! npm run test:deployment; then
        print_status "$RED" "Deployment tests failed"
        exit 1
    fi
    
    print_status "$GREEN" "Deployment tests passed"
}

# Set environment variables in Supabase
set_env_vars() {
    print_status "$YELLOW" "Setting environment variables in Supabase..."
    
    # Read variables from .env file
    local env_vars=""
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        
        # Remove any quotes from the value
        value=$(echo "$value" | tr -d '"' | tr -d "'")
        
        # Add to env_vars string
        if [ -n "$env_vars" ]; then
            env_vars="$env_vars,$key=$value"
        else
            env_vars="$key=$value"
        fi
    done < .env

    # Set all variables at once
    if ! supabase secrets set "$env_vars" &>/dev/null; then
        print_status "$RED" "Failed to set environment variables"
        exit 1
    fi

    print_status "$GREEN" "Environment variables set successfully"
}

# Verify deployment
verify_deployment() {
    print_status "$YELLOW" "Verifying deployment..."
    
    # List deployed functions
    supabase functions list

    print_status "$GREEN" "Deployment verification complete"
}

# Main deployment process
main() {
    print_status "$YELLOW" "Starting deployment process..."

    # Create necessary directories if they don't exist
    mkdir -p supabase/functions

    # Run deployment steps
    check_supabase_cli
    check_env_vars
    init_supabase
    link_project
    apply_migrations
    set_env_vars
    deploy_functions
    verify_deployment
    run_tests

    print_status "$GREEN" "Deployment completed successfully!"
}

# Run main function
main 