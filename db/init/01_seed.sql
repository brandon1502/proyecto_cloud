USE orchestrator;

-- Roles base
INSERT IGNORE INTO roles (name) VALUES ('admin'), ('user');

-- Flavours base
INSERT INTO orchestrator.flavours (name, vcpu, ram_gb, disk_gb) VALUES
  ('mini',   1, 0.50, 1.00),
  ('nano',   1, 0.50, 2.20),
  ('micro',  1, 0.50, 4.00),
  ('small',  2, 1.00, 6.00),
  ('medium', 2, 2.00, 6.00),
  ('large',  4, 4.00, 6.00),
  ('xlarge', 4, 8.00, 8.00);
