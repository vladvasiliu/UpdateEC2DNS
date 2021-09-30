import validators


def check_domain(domain: str):
    if validators.domain(domain):
        return domain
