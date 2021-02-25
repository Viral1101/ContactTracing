from django import template

register = template.Library()


@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)


@register.simple_tag(name='in_log_list')
def in_log_list(logs, log_id):
    for log in logs:
        if log.log_id == log_id:
            return True
    return False
