-- MAPUTI2.0 Space Invaders Database
-- Database name: Space_Invaders_Andaya
-- Import this file in XAMPP phpMyAdmin.

CREATE DATABASE IF NOT EXISTS Space_Invaders_Andaya
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE Space_Invaders_Andaya;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    total_games INT DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    best_score INT DEFAULT 0,
    status ENUM('active','inactive') DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    score INT NOT NULL,
    game_mode VARCHAR(30) NOT NULL,
    stage INT NOT NULL,
    lives_remaining INT DEFAULT 0,
    play_time FLOAT DEFAULT 0,
    enemies_destroyed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_scores_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS game_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    enemies_destroyed INT DEFAULT 0,
    bosses_defeated INT DEFAULT 0,
    shots_fired INT DEFAULT 0,
    shots_hit INT DEFAULT 0,
    powerups_collected INT DEFAULT 0,
    games_played INT DEFAULT 0,
    games_completed INT DEFAULT 0,
    games_over INT DEFAULT 0,
    total_play_time FLOAT DEFAULT 0,
    highest_stage INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_statistics_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ship_id VARCHAR(40) NOT NULL,
    unlocked BOOLEAN DEFAULT FALSE,
    selected BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP NULL,
    UNIQUE KEY user_ship (user_id, ship_id),
    CONSTRAINT fk_ships_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    master_volume FLOAT DEFAULT 0.8,
    music_volume FLOAT DEFAULT 0.6,
    sfx_volume FLOAT DEFAULT 0.8,
    fullscreen BOOLEAN DEFAULT FALSE,
    resolution VARCHAR(20) DEFAULT '1280x832',
    screen_shake BOOLEAN DEFAULT TRUE,
    animations BOOLEAN DEFAULT TRUE,
    selected_ship VARCHAR(40) DEFAULT 'standard',
    selected_game_mode VARCHAR(30) DEFAULT 'CLASSIC',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_mode VARCHAR(30) NOT NULL,
    current_stage INT DEFAULT 1,
    score INT DEFAULT 0,
    lives INT DEFAULT 3,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    session_status VARCHAR(20) DEFAULT 'active',
    CONSTRAINT fk_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- Create the default ship for each player when your game registers/initializes a player.
-- The application should run its normal ensure-player logic after registration.
