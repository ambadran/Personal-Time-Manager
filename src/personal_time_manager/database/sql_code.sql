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

