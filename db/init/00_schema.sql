-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema orchestrator
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema orchestrator
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `orchestrator` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `orchestrator` ;

-- -----------------------------------------------------
-- Table `orchestrator`.`roles`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`roles` (
  `role_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE INDEX `name` (`name` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`users` (
  `user_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `role_id` BIGINT UNSIGNED NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `full_name` VARCHAR(120) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT '1',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `email` (`email` ASC) VISIBLE,
  INDEX `fk_users_roles1_idx` (`role_id` ASC) VISIBLE,
  CONSTRAINT `fk_users_roles1`
    FOREIGN KEY (`role_id`)
    REFERENCES `orchestrator`.`roles` (`role_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`api_tokens`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`api_tokens` (
  `token_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `token_type` ENUM('session', 'pat', 'service') NOT NULL DEFAULT 'session',
  `token_hash` CHAR(64) NOT NULL,
  `scopes` JSON NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  `last_used_at` TIMESTAMP NULL DEFAULT NULL,
  `inactive_timeout_sec` INT UNSIGNED NULL DEFAULT NULL,
  `revoked` TINYINT(1) NOT NULL DEFAULT '0',
  `created_by_ip` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`token_id`),
  UNIQUE INDEX `token_hash` (`token_hash` ASC) VISIBLE,
  INDEX `idx_tokens_user` (`user_id` ASC) VISIBLE,
  INDEX `idx_tokens_exp` (`expires_at` ASC) VISIBLE,
  INDEX `idx_tokens_last_used` (`last_used_at` ASC) VISIBLE,
  CONSTRAINT `api_tokens_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`availability_zones`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`availability_zones` (
  `az_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(120) NOT NULL,
  `provider` VARCHAR(120) NULL DEFAULT NULL,
  `description` VARCHAR(255) NULL DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `updated_at` TIMESTAMP NULL DEFAULT NULL,
  `updated_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `deleted_at` TIMESTAMP NULL DEFAULT NULL,
  `deleted_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `delete_reason` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`az_id`),
  INDEX `fk_az_created_by` (`created_by` ASC) VISIBLE,
  INDEX `fk_az_updated_by` (`updated_by` ASC) VISIBLE,
  INDEX `fk_az_deleted_by` (`deleted_by` ASC) VISIBLE,
  CONSTRAINT `fk_az_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_az_deleted_by`
    FOREIGN KEY (`deleted_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_az_updated_by`
    FOREIGN KEY (`updated_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`flavours`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`flavours` (
  `flavour_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `vcpu` INT NOT NULL,
  `ram_gb` DECIMAL(5,2) NOT NULL,
  `disk_gb` DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (`flavour_id`),
  UNIQUE INDEX `uq_flavour_name` (`name` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 4
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`templates`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`templates` (
  `template_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(150) NULL DEFAULT NULL,
  `description` VARCHAR(255) NULL DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_last_at` TIMESTAMP NULL DEFAULT NULL,
  `json_template` JSON NULL,
  PRIMARY KEY (`template_id`),
  UNIQUE INDEX `uq_templates_owner_name` (`user_id` ASC, `name` ASC) VISIBLE,
  INDEX `fk_templates_owner` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_templates_owner`
    FOREIGN KEY (`user_id`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`slices`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`slices` (
  `slice_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `owner_id` BIGINT UNSIGNED NOT NULL,
  `az_id` BIGINT UNSIGNED NULL DEFAULT NULL,
  `template_id` BIGINT UNSIGNED NULL DEFAULT NULL,
  `name` VARCHAR(150) NOT NULL,
  `status` VARCHAR(40) NULL DEFAULT 'active',
  `placement_strategy` VARCHAR(40) NULL DEFAULT NULL,
  `sla_overcommit_cpu_pct` DECIMAL(5,2) NULL DEFAULT NULL,
  `sla_overcommit_ram_pct` DECIMAL(5,2) NULL DEFAULT NULL,
  `internet_egress` TINYINT(1) NULL DEFAULT '0',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `updated_at` TIMESTAMP NULL DEFAULT NULL,
  `updated_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `deleted_at` TIMESTAMP NULL DEFAULT NULL,
  `deleted_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `delete_reason` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`slice_id`),
  INDEX `fk_slices_owner` (`owner_id` ASC) VISIBLE,
  INDEX `fk_slices_az` (`az_id` ASC) VISIBLE,
  INDEX `fk_slices_template` (`template_id` ASC) VISIBLE,
  INDEX `fk_slices_created_by` (`created_by` ASC) VISIBLE,
  INDEX `fk_slices_updated_by` (`updated_by` ASC) VISIBLE,
  INDEX `fk_slices_deleted_by` (`deleted_by` ASC) VISIBLE,
  CONSTRAINT `fk_slices_az`
    FOREIGN KEY (`az_id`)
    REFERENCES `orchestrator`.`availability_zones` (`az_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_slices_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_slices_deleted_by`
    FOREIGN KEY (`deleted_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_slices_owner`
    FOREIGN KEY (`owner_id`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_slices_template`
    FOREIGN KEY (`template_id`)
    REFERENCES `orchestrator`.`templates` (`template_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_slices_updated_by`
    FOREIGN KEY (`updated_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`template_vms`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`template_vms` (
  `template_vm_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `template_id`    BIGINT UNSIGNED NOT NULL,
  `flavour_id`     BIGINT UNSIGNED NOT NULL,
  `name`           VARCHAR(150) NOT NULL,
  `imagen`         VARCHAR(40) NULL DEFAULT NULL,
  `public_access`  TINYINT(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`template_vm_id`),
  UNIQUE INDEX `uq_tpl_vm_name` (`template_id` ASC, `name` ASC) VISIBLE,
  INDEX `idx_template_vms_flavour` (`flavour_id` ASC) VISIBLE,
  CONSTRAINT `fk_template_vms_flavour`
    FOREIGN KEY (`flavour_id`)
    REFERENCES `orchestrator`.`flavours` (`flavour_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_tpl_vms_template`
    FOREIGN KEY (`template_id`)
    REFERENCES `orchestrator`.`templates` (`template_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;



-- -----------------------------------------------------
-- Table `orchestrator`.`template_edges`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`template_edges` (
  `template_edge_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `template_id` BIGINT UNSIGNED NOT NULL,
  `from_vm_id` BIGINT UNSIGNED NOT NULL,
  `to_vm_id` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`template_edge_id`),
  UNIQUE INDEX `uq_tpl_edge` (`template_id` ASC, `from_vm_id` ASC, `to_vm_id` ASC) VISIBLE,
  INDEX `fk_tpl_edges_from` (`from_vm_id` ASC) VISIBLE,
  INDEX `fk_tpl_edges_to` (`to_vm_id` ASC) VISIBLE,
  CONSTRAINT `fk_tpl_edges_from`
    FOREIGN KEY (`from_vm_id`)
    REFERENCES `orchestrator`.`template_vms` (`template_vm_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_tpl_edges_template`
    FOREIGN KEY (`template_id`)
    REFERENCES `orchestrator`.`templates` (`template_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_tpl_edges_to`
    FOREIGN KEY (`to_vm_id`)
    REFERENCES `orchestrator`.`template_vms` (`template_vm_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`vm_images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`vm_images` (
  `image_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `os_type` VARCHAR(40) NULL DEFAULT NULL,
  `os_version` VARCHAR(60) NULL DEFAULT NULL,
  `source` VARCHAR(60) NULL DEFAULT NULL,
  `checksum` VARCHAR(128) NULL DEFAULT NULL,
  `size_mb` INT NULL DEFAULT NULL,
  `is_public` TINYINT(1) NULL DEFAULT '1',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `updated_at` TIMESTAMP NULL DEFAULT NULL,
  `updated_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `deleted_at` TIMESTAMP NULL DEFAULT NULL,
  `deleted_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `delete_reason` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`image_id`),
  INDEX `fk_images_created_by` (`created_by` ASC) VISIBLE,
  INDEX `fk_images_updated_by` (`updated_by` ASC) VISIBLE,
  INDEX `fk_images_deleted_by` (`deleted_by` ASC) VISIBLE,
  CONSTRAINT `fk_images_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_images_deleted_by`
    FOREIGN KEY (`deleted_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_images_updated_by`
    FOREIGN KEY (`updated_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`vms`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`vms` (
  `vm_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `slice_id` BIGINT UNSIGNED NOT NULL,
  `az_id` BIGINT UNSIGNED NULL DEFAULT NULL,
  `image_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `vcpu` INT NOT NULL,
  `ram_mb` INT NOT NULL,
  `disk_gb` INT NOT NULL,
  `status` VARCHAR(40) NULL DEFAULT 'stopped',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `updated_at` TIMESTAMP NULL DEFAULT NULL,
  `updated_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `deleted_at` TIMESTAMP NULL DEFAULT NULL,
  `deleted_by` BIGINT UNSIGNED NULL DEFAULT NULL,
  `delete_reason` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`vm_id`),
  INDEX `fk_vms_slice` (`slice_id` ASC) VISIBLE,
  INDEX `fk_vms_image` (`image_id` ASC) VISIBLE,
  INDEX `fk_vms_az` (`az_id` ASC) VISIBLE,
  INDEX `fk_vms_created_by` (`created_by` ASC) VISIBLE,
  INDEX `fk_vms_updated_by` (`updated_by` ASC) VISIBLE,
  INDEX `fk_vms_deleted_by` (`deleted_by` ASC) VISIBLE,
  CONSTRAINT `fk_vms_az`
    FOREIGN KEY (`az_id`)
    REFERENCES `orchestrator`.`availability_zones` (`az_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_vms_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_vms_deleted_by`
    FOREIGN KEY (`deleted_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_vms_image`
    FOREIGN KEY (`image_id`)
    REFERENCES `orchestrator`.`vm_images` (`image_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_vms_slice`
    FOREIGN KEY (`slice_id`)
    REFERENCES `orchestrator`.`slices` (`slice_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_vms_updated_by`
    FOREIGN KEY (`updated_by`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `orchestrator`.`vm_console_tokens`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `orchestrator`.`vm_console_tokens` (
  `vct_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `vm_id` BIGINT UNSIGNED NOT NULL,
  `user_id` BIGINT UNSIGNED NOT NULL,
  `token_hash` CHAR(64) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  `last_used_at` TIMESTAMP NULL DEFAULT NULL,
  `one_time` TINYINT(1) NOT NULL DEFAULT '1',
  `used_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`vct_id`),
  UNIQUE INDEX `token_hash` (`token_hash` ASC) VISIBLE,
  INDEX `user_id` (`user_id` ASC) VISIBLE,
  INDEX `fk_vct_vm` (`vm_id` ASC) VISIBLE,
  CONSTRAINT `fk_vct_vm`
    FOREIGN KEY (`vm_id`)
    REFERENCES `orchestrator`.`vms` (`vm_id`)
    ON DELETE CASCADE,
  CONSTRAINT `vm_console_tokens_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `orchestrator`.`users` (`user_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
