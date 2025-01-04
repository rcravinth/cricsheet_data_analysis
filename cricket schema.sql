-- Create Schema

create schema cricket;

use cricket;

CREATE TABLE Matches (
    match_id bigint not null auto_increment PRIMARY KEY,
    city VARCHAR(255),
    date DATE,
    event_name VARCHAR(255),
    match_number INT,
    gender VARCHAR(50),
    match_type VARCHAR(50),
    match_type_number INT,
    season VARCHAR(50),
    team_type VARCHAR(50),
    toss_winner VARCHAR(255),
    toss_decision VARCHAR(50),
    outcome_winner VARCHAR(255),
    outcome_by_wickets int,
    outcome_by_runs int
);

CREATE TABLE Teams (
    team_id bigint not null auto_increment PRIMARY KEY,
    team_name VARCHAR(255)
);

-- Create the Players table
CREATE TABLE Players (
    player_id bigint not null auto_increment PRIMARY KEY,
    player_name VARCHAR(255),
    team_id bigint,
    FOREIGN KEY (team_id) REFERENCES Teams(team_id) ON DELETE CASCADE
);

-- Create the Innings table
CREATE TABLE Innings (
    inning_id bigint not null auto_increment PRIMARY KEY,
    match_id bigint,
    team_id bigint,
    target_runs INT,
    target_overs INT,
    FOREIGN KEY (match_id) REFERENCES Matches(match_id),
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
);

-- Create the Deliveries table
CREATE TABLE Deliveries (
    delivery_id bigint not null auto_increment PRIMARY KEY,
    match_id bigint,
    over_number INT,
    batter_id bigint,
    bowler_id bigint,
    non_striker_id bigint,
    runs_batter INT,
    runs_extras INT,
    runs_total INT,
    wicket_player_out VARCHAR(255),
    wicket_kind VARCHAR(50),
    FOREIGN KEY (batter_id) REFERENCES Players(player_id),
    FOREIGN KEY (bowler_id) REFERENCES Players(player_id),
    FOREIGN KEY (non_striker_id) REFERENCES Players(player_id),
    FOREIGN KEY (match_id) REFERENCES Matches(match_id)
);
