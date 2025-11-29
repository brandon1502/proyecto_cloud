-- ================================================================
-- Seed data para VLANs y puertos VNC
-- ================================================================

USE `orchestrator`;

-- ================================================================
-- Insertar VLANs disponibles (VLAN IDs comunes: 100-199, 1000-1099)
-- ================================================================

-- VLANs para la zona por defecto (sin AZ específica)
INSERT INTO `vlans` (`vlan_number`, `az_id`, `is_used`, `description`, `created_at`) VALUES
(100, NULL, 0, 'VLAN disponible para slices', NOW()),
(101, NULL, 0, 'VLAN disponible para slices', NOW()),
(102, NULL, 0, 'VLAN disponible para slices', NOW()),
(103, NULL, 0, 'VLAN disponible para slices', NOW()),
(104, NULL, 0, 'VLAN disponible para slices', NOW()),
(105, NULL, 0, 'VLAN disponible para slices', NOW()),
(106, NULL, 0, 'VLAN disponible para slices', NOW()),
(107, NULL, 0, 'VLAN disponible para slices', NOW()),
(108, NULL, 0, 'VLAN disponible para slices', NOW()),
(109, NULL, 0, 'VLAN disponible para slices', NOW()),
(110, NULL, 0, 'VLAN disponible para slices', NOW()),
(111, NULL, 0, 'VLAN disponible para slices', NOW()),
(112, NULL, 0, 'VLAN disponible para slices', NOW()),
(113, NULL, 0, 'VLAN disponible para slices', NOW()),
(114, NULL, 0, 'VLAN disponible para slices', NOW()),
(115, NULL, 0, 'VLAN disponible para slices', NOW()),
(116, NULL, 0, 'VLAN disponible para slices', NOW()),
(117, NULL, 0, 'VLAN disponible para slices', NOW()),
(118, NULL, 0, 'VLAN disponible para slices', NOW()),
(119, NULL, 0, 'VLAN disponible para slices', NOW()),
(120, NULL, 0, 'VLAN disponible para slices', NOW()),
(121, NULL, 0, 'VLAN disponible para slices', NOW()),
(122, NULL, 0, 'VLAN disponible para slices', NOW()),
(123, NULL, 0, 'VLAN disponible para slices', NOW()),
(124, NULL, 0, 'VLAN disponible para slices', NOW()),
(125, NULL, 0, 'VLAN disponible para slices', NOW()),
(126, NULL, 0, 'VLAN disponible para slices', NOW()),
(127, NULL, 0, 'VLAN disponible para slices', NOW()),
(128, NULL, 0, 'VLAN disponible para slices', NOW()),
(129, NULL, 0, 'VLAN disponible para slices', NOW()),
(130, NULL, 0, 'VLAN disponible para slices', NOW());

-- ================================================================
-- Insertar puertos VNC disponibles (rango típico: 5900-5999)
-- ================================================================

-- Puertos VNC para la zona por defecto (sin AZ específica)
INSERT INTO `vnc_ports` (`port_number`, `az_id`, `is_used`, `description`, `created_at`) VALUES
(5900, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5901, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5902, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5903, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5904, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5905, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5906, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5907, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5908, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5909, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5910, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5911, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5912, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5913, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5914, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5915, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5916, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5917, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5918, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5919, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5920, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5921, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5922, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5923, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5924, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5925, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5926, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5927, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5928, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5929, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5930, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5931, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5932, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5933, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5934, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5935, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5936, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5937, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5938, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5939, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5940, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5941, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5942, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5943, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5944, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5945, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5946, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5947, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5948, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5949, NULL, 0, 'Puerto VNC disponible para VMs', NOW()),
(5950, NULL, 0, 'Puerto VNC disponible para VMs', NOW());
