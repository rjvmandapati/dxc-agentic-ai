import pytest

from triage import triage


def test_ac1_60_affected_users_is_p1_with_sla_4():
    assert triage({"title": "Issue", "affected_users": 60}) == {
        "priority": "P1",
        "queue": "General",
        "sla_hours": 2,
    }


def test_ac2_email_outage_is_p1():
    assert triage({"title": "Email outage"})["priority"] == "P1"


def test_ac3_download_does_not_match_down():
    assert triage({"title": "Slow download speed"})["priority"] == "P4"


def test_ac4_12_users_is_p2_with_sla_8():
    assert triage({"title": "Issue", "affected_users": 12}) == {
        "priority": "P2",
        "queue": "General",
        "sla_hours": 8,
    }


def test_ac5_urgent_is_p2():
    assert triage({"title": "URGENT: cannot print"})["priority"] == "P2"


def test_ac6_3_users_is_p3_with_sla_24():
    assert triage({"title": "Issue", "affected_users": 3}) == {
        "priority": "P3",
        "queue": "General",
        "sla_hours": 24,
    }


def test_ac7_laptop_wifi_goes_to_network_queue():
    assert triage({"title": "Laptop wifi broken"})["queue"] == "Network"


def test_ac8_password_reset_goes_to_access_queue():
    assert triage({"title": "Password reset"})["queue"] == "Access"


def test_ac9_empty_title_and_zero_users_raise_value_error():
    with pytest.raises(ValueError):
        triage({"title": ""})

    with pytest.raises(ValueError):
        triage({"title": "Issue", "affected_users": 0})


def test_ac10_phishing_goes_to_security_queue():
    assert triage({"title": "Phishing attempt"})["queue"] == "Security"


def test_ac11_vip_ticket_with_p4_base_priority_is_raised_to_p3():
    assert triage({"title": "Issue", "customer_tier": "vip"})["priority"] == "P3"


def test_ac12_vip_ticket_with_p1_base_priority_stays_p1_with_sla_2():
    assert triage({"title": "Email outage", "customer_tier": "vip"}) == {
        "priority": "P1",
        "queue": "General",
        "sla_hours": 2,
    }