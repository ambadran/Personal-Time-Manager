/*
Here is the SQL code I used so far to create the tables:
  - Users:
  - Students:
  - Timetables:
  - Tuitions:
*/

-- Create a table to store user accounts
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_first_sign_in BOOLEAN DEFAULT TRUE
);

-- Create a table to store student information
CREATE TABLE students (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_data JSONB NOT NULL
);

-- updating the students table to include admin parameters data
-- Step 1: (Optional but Recommended) Create a custom ENUM type for the status.
-- This ensures data integrity for the 'status' field.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'student_status_enum') THEN
        CREATE TYPE student_status_enum AS ENUM ('NONE', 'Alpha', 'Omega', 'Sigma', 'HIM');
    END IF;
END$$;


-- Step 2: Add the new columns to the 'students' table with default values.
-- The DEFAULT clause will automatically populate these new columns for all existing rows.

ALTER TABLE students
ADD COLUMN IF NOT EXISTS cost_per_hour NUMERIC(10, 2) NOT NULL DEFAULT 6.00,
ADD COLUMN IF NOT EXISTS status student_status_enum NOT NULL DEFAULT 'NONE',
ADD COLUMN IF NOT EXISTS min_duration_mins INTEGER NOT NULL DEFAULT 60,
ADD COLUMN IF NOT EXISTS max_duration_mins INTEGER NOT NULL DEFAULT 90;

-- Optional: Add a check constraint to ensure durations are always positive.
ALTER TABLE students
ADD CONSTRAINT positive_durations CHECK (min_duration_mins >= 0 AND max_duration_mins >= 0);

/*#TODO: make the students database more modular, bring more data out of the jsonb to being their own column */
/* CREATE TYPE student_status_enum AS ENUM ('NONE', 'Alpha', 'Omega', 'Sigma', 'HIM'); */

/* CREATE TABLE students ( */
/*     -- Core Identifiers -- */
/*     id UUID PRIMARY KEY DEFAULT gen_random_uuid(), */
/*     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, */

/*     -- Dedicated Columns for Structured Data (from the old JSONB) -- */
/*     first_name TEXT NOT NULL, */
/*     last_name TEXT NOT NULL, */
/*     grade INTEGER NOT NULL, */

/*     -- JSONB Columns for Complex/Evolving Data -- */
/*     subjects_data JSONB,      -- Contains the list of subject objects */
/*     availability_data JSONB,  -- Contains the nested availability schedule */

/*     -- Dedicated Columns for Admin Data -- */
/*     cost_per_hour NUMERIC(10, 2) NOT NULL DEFAULT 6.00, */
/*     status student_status_enum NOT NULL DEFAULT 'NONE', */
/*     min_duration_mins INTEGER NOT NULL DEFAULT 60, */
/*     max_duration_mins INTEGER NOT NULL DEFAULT 90, */
    
/*     -- Add indexes on frequently queried columns */
/*     INDEX idx_students_grade (grade), */
/*     INDEX idx_students_last_name (last_name) */
/* ); */


/* the prayers parameters table */
CREATE TABLE prayer_settings (
    -- A fixed primary key to ensure only one row can ever exist.
    id SMALLINT PRIMARY KEY DEFAULT 1,
    
    -- Dedicated columns for prayer settings
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    api_method INTEGER NOT NULL,
    
    -- JSONB columns for dictionary-like data
    eqama_times_mins JSONB NOT NULL,
    duration_mins JSONB NOT NULL,
    
    -- Automatically track when the settings were last modified
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- This constraint enforces the single-row rule
    CONSTRAINT single_row_check CHECK (id = 1)
);


-- Add a check constraint for valid latitude/longitude values
ALTER TABLE prayer_settings 
ADD CONSTRAINT valid_location 
CHECK (latitude >= -90 AND latitude <= 90 AND longitude >= -180 AND longitude <= 180);

-- This single "upsert" command will create the row the first time,
-- and update it on any subsequent runs.
INSERT INTO prayer_settings (id, latitude, longitude, api_method, eqama_times_mins, duration_mins)
VALUES (
    1, -- The fixed ID for the single settings row
    29.954090,
    31.067551,
    2,
    '{ "FAJR": 25, "DHUHR": 20, "ASR": 20, "MAGHRIB": 10, "ISHA": 20 }'::jsonb,
    '{ "default_min": 15, "default_max": 25, "JUMAH_min": 45, "JUMAH_max": 60 }'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    api_method = EXCLUDED.api_method,
    eqama_times_mins = EXCLUDED.eqama_times_mins,
    duration_mins = EXCLUDED.duration_mins,
    last_updated = NOW();


/* fixed_activities */
-- creating the enums for the .type for each of the fixed_activities SessionDescriptor types
DO $$
BEGIN
    -- For Work. Note: 'MainJob_Freelance' is a single value.
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'work_type_enum') THEN
        CREATE TYPE work_type_enum AS ENUM ('MainJob', 'Freelance', 'MainJob_Freelance', 'tuition');
    END IF;

    -- For Gym
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gym_workout_enum') THEN
        CREATE TYPE gym_workout_enum AS ENUM ('PUSH', 'PULL', 'LEG');
    END IF;

    -- For Sleep
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sleep_type_enum') THEN
        CREATE TYPE sleep_type_enum AS ENUM ('NIGHT', 'NAP');
    END IF;

    -- For Meal
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meal_type_enum') THEN
        CREATE TYPE meal_type_enum AS ENUM ('MEALPREP', 'BREAKFAST', 'SNACK', 'LUNCH', 'DINNER');
    END IF;
END$$;

-- creating the main enum that holds the main SessionDescriptor types
-- Create a new ENUM for the main activity categories
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'activity_category_enum') THEN
        CREATE TYPE activity_category_enum AS ENUM ('Gym', 'Sleep', 'Work', 'Meal');
    END IF;
END$$;


-- now creating the actual table that will hold the personal fixed_activities
-- Create the main table to store records of fixed activities
CREATE TABLE IF NOT EXISTS fixed_activities (
    id BIGSERIAL PRIMARY KEY,

    -- General category for this fixed_activity record
    fixed_activity_category fixed_activity_category_enum NOT NULL,

    -- Specific type columns; only one can be NOT NULL per row
    gym_type gym_workout_enum,
    sleep_type sleep_type_enum,
    work_type work_type_enum,
    meal_type meal_type_enum,

    -- Common parameters for all fixed activities
    sessions_per_week INTEGER NOT NULL DEFAULT 1,
    min_duration_mins INTEGER NOT NULL,
    max_duration_mins INTEGER NOT NULL,
    allowed_intervals JSONB, -- Stores the availability rules

    -- Constraint to ensure data consistency
    CONSTRAINT one_type_per_fixed_activity CHECK (
        (CASE WHEN fixed_activity_category = 'Gym' THEN 1 ELSE 0 END +
         CASE WHEN fixed_activity_category = 'Sleep' THEN 1 ELSE 0 END +
         CASE WHEN fixed_activity_category = 'Work' THEN 1 ELSE 0 END +
         CASE WHEN fixed_activity_category = 'Meal' THEN 1 ELSE 0 END) = 1
        AND
        (CASE WHEN gym_type IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN sleep_type IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN work_type IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN meal_type IS NOT NULL THEN 1 ELSE 0 END) = 1
        AND
        (fixed_activity_category = 'Gym' AND gym_type IS NOT NULL OR
         fixed_activity_category = 'Sleep' AND sleep_type IS NOT NULL OR
         fixed_activity_category = 'Work' AND work_type IS NOT NULL OR
         fixed_activity_category = 'Meal' AND meal_type IS NOT NULL)
    )
);
-- Step 1: Rename the ENUM type itself.
ALTER TYPE activity_category_enum RENAME TO fixed_activity_category_enum;

-- Step 2: Rename the column in the 'fixed_activities' table that uses this type.
ALTER TABLE fixed_activities
RENAME COLUMN activity_category TO fixed_activity_category;

-- Update the values in work_type_enum to follow standard ALL_CAPS convention
ALTER TYPE work_type_enum RENAME VALUE 'MainJob' TO 'MAIN_JOB';
ALTER TYPE work_type_enum RENAME VALUE 'Freelance' TO 'FREELANCE';
ALTER TYPE work_type_enum RENAME VALUE 'MainJob_Freelance' TO 'MAIN_JOB_FREELANCE';
ALTER TYPE work_type_enum RENAME VALUE 'tuition' TO 'TUITION';

-- V imp updating naming convention to latest 3 rule method of fixed_activities
ALTER TYPE gym_workout_enum RENAME TO gym_type_enum;

/* dealing with allowed_to_overlap settings */
-- Create a single ENUM to represent all session categories
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_category_enum') THEN
        CREATE TYPE session_category_enum AS ENUM (
            'Gym',
            'Sleep',
            'Work',
            'Meal',
            'Tuition',
            'Prayer',
            'CalendarEvent' -- For future use with Google/Apple Calendar
        );
    END IF;
END$$;

-- Create the table to store the overlap rules
CREATE TABLE IF NOT EXISTS activity_overlap_rules (
    -- The category of the session that can BE interrupted (e.g., 'Gym')
    host_category session_category_enum NOT NULL,

    -- The category of the session that CAN interrupt (e.g., 'Prayer')
    interrupter_category session_category_enum NOT NULL,

    /* A composite primary key ensures that each rule is unique (e.g., you can't have Gym-Prayer twice)*/
    PRIMARY KEY (host_category, interrupter_category)
);

-- Insert the overlap rules. This query will ignore duplicates if run again.
INSERT INTO activity_overlap_rules (host_category, interrupter_category) VALUES
    ('Gym', 'Prayer'),
    ('Tuition', 'Prayer'),
    ('Sleep', 'Prayer')
ON CONFLICT (host_category, interrupter_category) DO NOTHING;


/* now the timetable_runs table that will store the output of CSP */
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_status_enum') THEN
        CREATE TYPE run_status_enum AS ENUM ('SUCCESS', 'FAILED');
    END IF;
END$$;

-- Create the table to log every CSP run
CREATE TABLE IF NOT EXISTS timetable_runs (
    id BIGSERIAL PRIMARY KEY,
    run_started_at TIMESTAMPTZ NOT NULL,
    run_duration_ms INTEGER,
    status run_status_enum NOT NULL,
    input_version_hash TEXT NOT NULL,
    trigger_source TEXT,
    solution_data JSONB,
    error_message TEXT,
    INDEX idx_runs_input_hash (input_version_hash)
);
