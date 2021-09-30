from enum import Enum
from typing import List, Optional
from urllib.parse import urljoin

import validators
from pydantic import BaseModel, conint, validator, root_validator
import requests
from requests.auth import AuthBase

from .helpers import check_domain


class RRSetType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    ALIAS = "ALIAS"
    CAA = "CAA"
    CDS = "CDS"
    CNAME = "CNAME"
    DNAME = "DNAME"
    DS = "DS"
    KEY = "KEY"
    LOC = "LOC"
    MX = "MX"
    NAPTR = "NAPTR"
    NS = "NS"
    OPENPGPKEY = "OPENPGPKEY"
    PTR = "PTR"
    RP = "RP"
    SPF = "SPF"
    SRV = "SRV"
    SSHFP = "SSHFP"
    TLSA = "TLSA"
    TXT = "TXT"
    WKS = "WKS"


class RRSet(BaseModel):
    rrset_name: str
    rrset_type: RRSetType
    rrset_values: List[str]
    rrset_ttl: Optional[conint(strict=True, ge=300, le=2592000)]

    _normalize_name = validator("name", allow_reuse=True)(check_domain)

    @root_validator
    def check_rrset_values(cls, values):
        rrset_type = values.get("rrset_type")
        rrset_values = values.get("rrset_values")

        if rrset_type == RRSetType.A:
            checker = validators.ipv4
        elif rrset_type == RRSetType.AAAA:
            checker = validators.ipv6
        else:
            raise ValueError("We're only handling A and AAAA records")
        return all(checker(v) for v in rrset_values)


class DNSClient:
    def set_record(self, rrset_list: List[RRSet]):
        raise NotImplementedError

    def remove_record(self, record_name: str):
        raise NotImplementedError


class GandiAuthentication(AuthBase):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def __call__(self, r):
        r.headers["Authorization"] = f"Apikey {self._api_key}"
        return r


class GandiClient(DNSClient):
    def __init__(
        self,
        api_key: str,
        domain: str,
        base_url: str = "https://api.gandi.net/v5/livedns/domains/",
    ):
        self._api_key = api_key
        self._base_url = urljoin(base_url, f"{domain}/")
        self._session = requests.Session()
        self._session.auth = GandiAuthentication(self._api_key)

    def get_record(self, record_name: str) -> Optional[List[RRSet]]:
        """Return the record sets for a given name"""
        url = urljoin(self._base_url, f"records/{record_name}")
        print(url)
        response = self._session.get(url)
        if response.status_code == requests.codes.not_found:
            return None
        response.raise_for_status()
        return [RRSet(**record) for record in response.json()]

    def set_record(self, rrset_list: List[RRSet]):
        rrset_name = _check_set_record_param(rrset_list)
        url = urljoin(self._base_url, f"records/{rrset_name}")
        payload = {
            "items": [
                {"rrset_type": rrset.rrset_type, "rrset_values": rrset.rrset_values}
                for rrset in rrset_list
            ]
        }
        response = self._session.put(url, json=payload)
        response.raise_for_status()

    def remove_record(self, record_name: str):
        url = urljoin(self._base_url, f"records/{record_name}")
        response = self._session.delete(url)
        response.raise_for_status()


def _check_set_record_param(rrset_list: List[RRSet]) -> str:
    """Sanity check for the parameter used to update the RecordSet, and returns the name to use"""
    record_names_set = set()
    record_types_set = set()

    for rrset in rrset_list:
        record_types_set.add(rrset.rrset_type)
        record_names_set.add(rrset.rrset_name)

    if len(record_names_set) > 1:
        raise Exception("Can only update one record set at a time")

    if record_types_set - {RRSetType.A, RRSetType.AAAA}:
        raise Exception("Will only manage A and AAAA record set types")

    return record_names_set.pop()
