-- DELETE FROM location_paths;

-- ========================================================
-- 1. 메인 룸 내부 연결 (Main Room Internal Grid)
-- ========================================================
USE SMART_CART;
-- [1-1] 가로(Horizontal) 통로 연결: 로봇이 동서로 이동하는 안전한 길
-- 상단 통로: 좌상코너 <-> 상단중앙(진열대) <-> 우상코너
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-002'), (SELECT location_id FROM locations WHERE location_code='SHELF-001')),
((SELECT location_id FROM locations WHERE location_code='SHELF-001'), (SELECT location_id FROM locations WHERE location_code='PTH-003'));

-- 중앙 통로: 좌측중앙 <-> 센터 <-> 우측중앙
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-006'), (SELECT location_id FROM locations WHERE location_code='PTH-001')),
((SELECT location_id FROM locations WHERE location_code='PTH-001'), (SELECT location_id FROM locations WHERE location_code='PTH-007'));

-- 하단 통로: 좌하코너 <-> 하단중앙(진열대) <-> 우하코너
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-004'), (SELECT location_id FROM locations WHERE location_code='SHELF-002')),
((SELECT location_id FROM locations WHERE location_code='SHELF-002'), (SELECT location_id FROM locations WHERE location_code='PTH-005'));


-- [1-2] 세로(Vertical) 라인 연결: 로봇이 남북으로 이동하는 길
-- 좌측 라인: 좌상코너 <-> 진열대(좌상) <-> 중앙(좌) <-> 진열대(좌하) <-> 좌하코너
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-002'), (SELECT location_id FROM locations WHERE location_code='SHELF-003')),
((SELECT location_id FROM locations WHERE location_code='SHELF-003'), (SELECT location_id FROM locations WHERE location_code='PTH-006')),
((SELECT location_id FROM locations WHERE location_code='PTH-006'), (SELECT location_id FROM locations WHERE location_code='SHELF-006')),
((SELECT location_id FROM locations WHERE location_code='SHELF-006'), (SELECT location_id FROM locations WHERE location_code='PTH-004'));

-- 중앙 라인: 상단중앙 <-> 진열대(중상) <-> 센터 <-> 진열대(중하) <-> 하단중앙
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='SHELF-001'), (SELECT location_id FROM locations WHERE location_code='SHELF-004')),
((SELECT location_id FROM locations WHERE location_code='SHELF-004'), (SELECT location_id FROM locations WHERE location_code='PTH-001')),
((SELECT location_id FROM locations WHERE location_code='PTH-001'), (SELECT location_id FROM locations WHERE location_code='SHELF-007')),
((SELECT location_id FROM locations WHERE location_code='SHELF-007'), (SELECT location_id FROM locations WHERE location_code='SHELF-002'));

-- 우측 라인: 우상코너 <-> 진열대(우상) <-> 중앙(우) <-> 진열대(우하) <-> 우하코너
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-003'), (SELECT location_id FROM locations WHERE location_code='SHELF-005')),
((SELECT location_id FROM locations WHERE location_code='SHELF-005'), (SELECT location_id FROM locations WHERE location_code='PTH-007')),
((SELECT location_id FROM locations WHERE location_code='PTH-007'), (SELECT location_id FROM locations WHERE location_code='SHELF-008')),
((SELECT location_id FROM locations WHERE location_code='SHELF-008'), (SELECT location_id FROM locations WHERE location_code='PTH-005'));


-- ========================================================
-- 2. 주차장 연결 (Parking Area)
-- ========================================================
-- 위에서 아래로 순차 연결 (1 <-> 2 <-> 3 <-> 4)
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PARK-001'), (SELECT location_id FROM locations WHERE location_code='PARK-002')),
((SELECT location_id FROM locations WHERE location_code='PARK-002'), (SELECT location_id FROM locations WHERE location_code='PARK-003')),
((SELECT location_id FROM locations WHERE location_code='PARK-003'), (SELECT location_id FROM locations WHERE location_code='PARK-004'));

-- ========================================================
-- 3. 진입로 연결 (Entrance & Connections)
-- ========================================================

-- [3-1] 상단 진입로: 주차장(상) <-> 상단 게이트 <-> 상단 진입점(PTH-008)
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PARK-001'), (SELECT location_id FROM locations WHERE location_code='GATE-001')),
((SELECT location_id FROM locations WHERE location_code='GATE-001'), (SELECT location_id FROM locations WHERE location_code='PTH-008'));

-- [3-2] 하단 진입로: 주차장(하) <-> 하단 게이트 <-> 하단 진입점(PTH-009)
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PARK-004'), (SELECT location_id FROM locations WHERE location_code='GATE-002')),
((SELECT location_id FROM locations WHERE location_code='GATE-002'), (SELECT location_id FROM locations WHERE location_code='PTH-009'));

-- [3-3] 카트 보관소 연결 (로비 순환)
-- 상단 진입점 <-> 카트보관함 <-> 하단 진입점
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='PTH-008'), (SELECT location_id FROM locations WHERE location_code='STOR-001')),
((SELECT location_id FROM locations WHERE location_code='STOR-001'), (SELECT location_id FROM locations WHERE location_code='PTH-009'));

-- [3-4] 매장 내부로의 진입 (상단)
-- 상단 진입점(PTH-008)에서 갈 수 있는 곳: 상단 우측 선반, 중앙 우측 통로
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='SHELF-005'), (SELECT location_id FROM locations WHERE location_code='PTH-008')),
((SELECT location_id FROM locations WHERE location_code='PTH-007'),   (SELECT location_id FROM locations WHERE location_code='PTH-008'));

-- [3-5] 매장 내부로의 진입 (하단)
-- 하단 진입점(PTH-009)에서 갈 수 있는 곳: 하단 우측 선반, 하단 우측 코너
INSERT INTO location_paths (node1_id, node2_id) VALUES
((SELECT location_id FROM locations WHERE location_code='SHELF-008'), (SELECT location_id FROM locations WHERE location_code='PTH-009')),
((SELECT location_id FROM locations WHERE location_code='PTH-005'),   (SELECT location_id FROM locations WHERE location_code='PTH-009'));