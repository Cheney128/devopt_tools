from unittest.mock import Mock
from app.services.ip_location_service import IPLocationService
from app.services.ip_location_validation_service import IPLocationValidationService


def test_snapshot_query_and_rollback_flow():
    service = IPLocationService(Mock())
    service.snapshot_service = Mock()
    service.snapshot_service.get_locations.return_value = [
        {"ip_address": "10.0.0.1", "match_type": "same_device", "calculate_batch_id": "batch_new"}
    ]
    locations = service.locate_ip("10.0.0.1", mode="snapshot")
    assert len(locations) == 1
    assert locations[0]["calculate_batch_id"] == "batch_new"

    validator = IPLocationValidationService(Mock())
    validator.snapshot_service = Mock()
    validator.snapshot_service.rollback_to_batch.return_value = True
    validator.snapshot_service.get_active_batch_id.return_value = "batch_old"
    rollback = validator.rollback("batch_old")
    assert rollback["success"] is True
    assert rollback["active_batch_id"] == "batch_old"
