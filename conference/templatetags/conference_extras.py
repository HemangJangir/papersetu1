from django import template
from conference.models import UserConferenceRole
register = template.Library()

@register.filter
def has_conference_role(user, args):
    """
    Usage: user|has_conference_role:conference_id:'role'
    Example: user|has_conference_role:conference.id:'author'
    """
    try:
        conference_id, role = args.split(',')
        return UserConferenceRole.objects.filter(user=user, conference_id=conference_id, role=role).exists()
    except Exception:
        return False

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key) 