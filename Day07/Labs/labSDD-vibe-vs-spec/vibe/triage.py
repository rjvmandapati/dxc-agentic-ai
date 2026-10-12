import re


def triage(ticket):
    title = ticket.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")

    description = ticket.get("description")
    if description is None:
        description = ""
    elif not isinstance(description, str):
        description = str(description)

    affected_users = ticket.get("affected_users", 1)
    if not isinstance(affected_users, int) or affected_users < 1:
        raise ValueError("affected_users must be a positive integer")

    customer_tier = ticket.get("customer_tier", "standard")
    if customer_tier not in ("standard", "vip"):
        raise ValueError("customer_tier must be standard or vip")

    text = f"{title} {description}".lower()

    def has_word(word):
        return re.search(rf"\b{re.escape(word)}\b", text) is not None

    if affected_users >= 50 or has_word("outage") or has_word("down"):
        priority = "P1"
    elif affected_users >= 10 or has_word("urgent") or has_word("blocked"):
        priority = "P2"
    elif affected_users >= 2:
        priority = "P3"
    else:
        priority = "P4"

    if customer_tier == "vip":
        priority = {"P4": "P3", "P3": "P2", "P2": "P1", "P1": "P1"}[priority]

    if any(has_word(word) for word in ("phishing", "breach", "malware")):
        queue = "Security"
    elif any(has_word(word) for word in ("vpn", "wifi", "network")):
        queue = "Network"
    elif any(has_word(word) for word in ("password", "login", "locked")):
        queue = "Access"
    elif any(has_word(word) for word in ("laptop", "keyboard", "screen")):
        queue = "Hardware"
    else:
        queue = "General"

    sla_hours = {"P1": 2, "P2": 8, "P3": 24, "P4": 72}[priority]

    return {"priority": priority, "queue": queue, "sla_hours": sla_hours}