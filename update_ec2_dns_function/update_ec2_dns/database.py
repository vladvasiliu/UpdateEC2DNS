from pydantic import BaseModel, constr, conint, validator

from .helpers import check_domain


class Domain(BaseModel):
    name: constr(
        strip_whitespace=True,
    )

    _normalize_name = validator("name", allow_reuse=True)(check_domain)


class InstanceRecord(BaseModel):
    instance_id: constr(regex=r"i-([0-9a-f]){17}")
    name: constr(strip_whitespace=True)
    domain: constr(strip_whitespace=True)
    ttl: conint(strict=True, ge=300, le=2592000) = 300

    _normalize_name = validator("name", allow_reuse=True)(check_domain)
    _normalize_domain = validator("domain", allow_reuse=True)(check_domain)
