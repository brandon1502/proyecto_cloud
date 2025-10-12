-- =========================================================
-- Proyecto Cloud Orchestrator - Base de Datos EX1
-- =========================================================
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='STRICT_TRANS_TABLES,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `orchestrator` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `orchestrator`;

-- =========================================================
-- USERS
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(120) NOT NULL UNIQUE,
  full_name VARCHAR(120) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- ROLES / USER_ROLES
-- =========================================================
CREATE TABLE IF NOT EXISTS roles (
  role_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id BIGINT UNSIGNED NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- API TOKENS
-- =========================================================
CREATE TABLE IF NOT EXISTS api_tokens (
  token_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_type ENUM('session','pat','service') DEFAULT 'session',
  token_hash CHAR(64) NOT NULL UNIQUE,
  scopes JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NULL DEFAULT NULL,
  inactive_timeout_sec INT UNSIGNED NULL DEFAULT NULL,
  revoked TINYINT(1) DEFAULT 0,
  created_by_ip VARCHAR(45) NULL DEFAULT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- =========================================================
-- AVAILABILITY ZONES
-- =========================================================
CREATE TABLE IF NOT EXISTS availability_zones (
  az_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  provider VARCHAR(120),
  description VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  created_by BIGINT UNSIGNED NULL,
  updated_by BIGINT UNSIGNED NULL,
  FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
  FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- VM IMAGES
-- =========================================================
CREATE TABLE IF NOT EXISTS vm_images (
  image_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  os_type VARCHAR(40),
  os_version VARCHAR(60),
  source VARCHAR(60),
  checksum VARCHAR(128),
  size_mb INT,
  is_public TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  created_by BIGINT UNSIGNED NULL,
  updated_by BIGINT UNSIGNED NULL,
  FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
  FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- TEMPLATES
-- =========================================================
CREATE TABLE IF NOT EXISTS templates (
  template_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  owner_id BIGINT UNSIGNED NOT NULL,
  az_id BIGINT UNSIGNED NULL,
  name VARCHAR(150) NOT NULL,
  status ENUM('draft','published','archived') DEFAULT 'draft',
  placement_strategy VARCHAR(40),
  sla_overcommit_cpu_pct DECIMAL(5,2),
  sla_overcommit_ram_pct DECIMAL(5,2),
  internet_egress TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_templates_owner_name (owner_id, name),
  FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (az_id) REFERENCES availability_zones(az_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

  -- Auditoría (añadir después de CREATE TABLE templates)
ALTER TABLE templates
ADD COLUMN created_by BIGINT UNSIGNED NULL,
ADD COLUMN updated_by BIGINT UNSIGNED NULL,
ADD COLUMN deleted_by BIGINT UNSIGNED NULL,
ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL,
ADD COLUMN delete_reason VARCHAR(255) NULL,
ADD CONSTRAINT fk_templates_created_by FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
ADD CONSTRAINT fk_templates_updated_by FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL,
ADD CONSTRAINT fk_templates_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(user_id) ON DELETE SET NULL;

-- =========================================================
-- SLICES
-- =========================================================
CREATE TABLE IF NOT EXISTS slices (
  slice_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  owner_id BIGINT UNSIGNED NOT NULL,
  az_id BIGINT UNSIGNED NULL,
  template_id BIGINT UNSIGNED NULL,
  name VARCHAR(150) NOT NULL,
  status ENUM('creating','active','error','deleting','deleted') DEFAULT 'creating',
  placement_strategy VARCHAR(40),
  sla_overcommit_cpu_pct DECIMAL(5,2),
  sla_overcommit_ram_pct DECIMAL(5,2),
  internet_egress TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_slices_owner_name (owner_id, name),
  FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (template_id) REFERENCES templates(template_id) ON DELETE SET NULL,
  FOREIGN KEY (az_id) REFERENCES availability_zones(az_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- SLICE EVENTS (Logs paso a paso)
-- =========================================================
CREATE TABLE IF NOT EXISTS slice_events (
  event_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  slice_id BIGINT UNSIGNED NOT NULL,
  step_name VARCHAR(255) NOT NULL,
  command TEXT NULL,
  stdout MEDIUMTEXT NULL,
  stderr MEDIUMTEXT NULL,
  status ENUM('pending','running','ok','warn','error') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (slice_id) REFERENCES slices(slice_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- VMS
-- =========================================================
CREATE TABLE IF NOT EXISTS vms (
  vm_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  slice_id BIGINT UNSIGNED NOT NULL,
  az_id BIGINT UNSIGNED NULL,
  image_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(150) NOT NULL,
  vcpu INT NOT NULL CHECK (vcpu > 0),
  ram_mb INT NOT NULL CHECK (ram_mb > 0),
  disk_gb INT NOT NULL CHECK (disk_gb >= 0),
  status ENUM('stopped','building','running','error','deleting','deleted') DEFAULT 'stopped',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (slice_id) REFERENCES slices(slice_id) ON DELETE CASCADE,
  FOREIGN KEY (image_id) REFERENCES vm_images(image_id) ON DELETE RESTRICT,
  FOREIGN KEY (az_id) REFERENCES availability_zones(az_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- VM CONSOLE TOKENS
-- =========================================================
CREATE TABLE IF NOT EXISTS vm_console_tokens (
  vct_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  vm_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NULL DEFAULT NULL,
  one_time TINYINT(1) DEFAULT 1,
  used_at TIMESTAMP NULL DEFAULT NULL,
  FOREIGN KEY (vm_id) REFERENCES vms(vm_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =========================================================
-- SEMILLAS MÍNIMAS
-- =========================================================
INSERT IGNORE INTO roles (role_id, name) VALUES (1,'admin'),(2,'user');

INSERT INTO availability_zones (az_id, name, provider)
VALUES (1,'linux-lab','onprem')
ON DUPLICATE KEY UPDATE name=VALUES(name),provider=VALUES(provider);

INSERT INTO vm_images (image_id,name,os_type,os_version,source,is_public)
VALUES (1,'cirros','linux','0.6.2','local',1)
ON DUPLICATE KEY UPDATE name=VALUES(name);

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
