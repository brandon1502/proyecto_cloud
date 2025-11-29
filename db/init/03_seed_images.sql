-- Seed data for VM images
-- Insertar imágenes de VM comunes

USE orchestrator;

-- Imágenes de Ubuntu
INSERT INTO vm_images (image_id, name, os_type, os_version, source, is_public, created_at)
VALUES 
  (1, 'Ubuntu 22.04 LTS', 'ubuntu', '22.04', 'official', 1, NOW()),
  (2, 'Ubuntu 20.04 LTS', 'ubuntu', '20.04', 'official', 1, NOW()),
  (3, 'Ubuntu 24.04 LTS', 'ubuntu', '24.04', 'official', 1, NOW());

-- Imagen de CirrOS (imagen ligera para testing)
INSERT INTO vm_images (image_id, name, os_type, os_version, source, is_public, created_at)
VALUES 
  (4, 'CirrOS 0.6.2', 'cirros', '0.6.2', 'official', 1, NOW());

-- Imágenes de Debian
INSERT INTO vm_images (image_id, name, os_type, os_version, source, is_public, created_at)
VALUES 
  (5, 'Debian 12 (Bookworm)', 'debian', '12', 'official', 1, NOW()),
  (6, 'Debian 11 (Bullseye)', 'debian', '11', 'official', 1, NOW());

-- Imágenes de CentOS/Rocky
INSERT INTO vm_images (image_id, name, os_type, os_version, source, is_public, created_at)
VALUES 
  (7, 'Rocky Linux 9', 'rocky', '9', 'official', 1, NOW()),
  (8, 'Rocky Linux 8', 'rocky', '8', 'official', 1, NOW());
