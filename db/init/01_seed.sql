USE orchestrator;

-- Roles base
INSERT IGNORE INTO roles (name) VALUES ('admin'), ('user');

-- Flavours base
INSERT INTO orchestrator.flavours (name, vcpu, ram_gb, disk_gb) VALUES
  ('nano',   1, 1.00, 2.00),
  ('mini',   1, 2.00, 3.00),
  ('micro',  2, 2.00, 4.00),
  ('small',  2, 4.00, 6.00),
  ('medium', 4, 8.00, 8.00),
  ('large',  8, 12.00, 10.00),
  ('xlarge', 16, 16.00, 12.00);
