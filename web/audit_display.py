"""Select recorded audit events for display; never infer missing history."""
from datetime import datetime, timezone


def latest_recorded_change(events):
    meaningful = []
    prose = []
    undated = []
    for event in events:
        category = event.get('category')
        if category not in {'tier_promotion', 'tier_demotion', 'retraction', 'evidence_added', 'prose'}:
            continue
        # An unchanged tier is not a change, even if a legacy classifier labels it one.
        raw = event.get('raw') or {}
        if raw.get('field') == 'tier' and event.get('old_value') == event.get('new_value'):
            continue
        value = event.get('changed_at') or ''
        try:
            # A partial date cannot establish chronology.
            if len(value) < 10:
                raise ValueError('incomplete date')
            date = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            undated.append(event)
            continue
        target = prose if category == 'prose' else meaningful
        target.append((date, event))
    # IDs break equal-date ties reproducibly; they do not imply finer chronology.
    def ordering(item):
        return item[0], (item[1].get('raw') or {}).get('id') or 0
    return {
        'change': max(meaningful, key=ordering)[1] if meaningful else None,
        'prose': max(prose, key=ordering)[1] if prose else None,
        'undated': len(undated),
        'undated_events': undated,
    }
