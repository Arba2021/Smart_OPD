INSERT INTO registration_queue (name, phone, reg_token, status)
VALUES 
    ('Test Patient 1', '9876543210', 'REG-D001', 'REG_COMPLETED'),
    ('Test Patient 2', '9876543211', 'REG-D002', 'REG_COMPLETED'),
    ('Test Patient 3', '9876543212', 'REG-D003', 'REG_COMPLETED')
ON CONFLICT (reg_token) DO NOTHING;

INSERT INTO doctor_queue (registration_id, doctor_id, doctor_name, doctor_token, status, symptom, triage_color, predicted_duration_mins)
SELECT id, 'gen-001', 'Dr. Sharma (General)', 'DOC-GEN-001', 'IN_ROOM', 'Fever and headache', 'YELLOW', 10
FROM registration_queue WHERE reg_token = 'REG-D001';

INSERT INTO doctor_queue (registration_id, doctor_id, doctor_name, doctor_token, status, symptom, triage_color, predicted_duration_mins)
SELECT id, 'gen-001', 'Dr. Sharma (General)', 'DOC-GEN-002', 'WAITING', 'Body pain', 'GREEN', 5
FROM registration_queue WHERE reg_token = 'REG-D002';

INSERT INTO doctor_queue (registration_id, doctor_id, doctor_name, doctor_token, status, symptom, triage_color, predicted_duration_mins)
SELECT id, 'orth-002', 'Dr. Patel (Ortho)', 'DOC-ORT-001', 'CALLED', 'Joint pain', 'YELLOW', 15
FROM registration_queue WHERE reg_token = 'REG-D003';

INSERT INTO patient_master (phone, name)
VALUES 
    ('9876543210', 'Test Patient 1'),
    ('9876543211', 'Test Patient 2'),
    ('9876543212', 'Test Patient 3')
ON CONFLICT (phone) DO NOTHING;