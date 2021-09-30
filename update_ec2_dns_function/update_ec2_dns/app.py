from logging import getLogger

from schema.aws.ec2.ec2instancestatechangenotification import Marshaller
from schema.aws.ec2.ec2instancestatechangenotification import AWSEvent
from schema.aws.ec2.ec2instancestatechangenotification import (
    EC2InstanceStateChangeNotification,
)

from .aws import get_ec2_public_ip
from .config import BaseConfig
from .database import DB, InstanceRecord
from .gandi import DNSClient, RRSet, RRSetType, GandiClient

logger = getLogger(__name__)


def lambda_handler(event, context):
    """Sample Lambda function reacting to EventBridge events

    Parameters
    ----------
    event: dict, required
        Event Bridge Events Format
        Event doc: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-types.html

    context: object, required
        Lambda Context runtime methods and attributes
        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
        The same input event file
    """

    aws_event: AWSEvent = Marshaller.unmarshall(event, AWSEvent)
    detail: EC2InstanceStateChangeNotification = aws_event.detail

    if detail.state == "running":
        action = add_dns
    elif detail.state == "shutting-down":
        action = remove_dns
    else:
        return

    config = BaseConfig().get_config()
    instance = DB[0]
    dns_client = GandiClient(
        api_key=config.gandi_api_key.get_secret_value(), domain=instance.domain
    )
    action(dns_client, instance=instance)

    # return Marshaller.marshall(result)


def add_dns(dns_client: DNSClient, instance: InstanceRecord):
    pub_ip = get_ec2_public_ip(instance.instance_id)
    record = RRSet(
        rrset_name=instance.name, rrset_type=RRSetType.A, rrset_values=[pub_ip]
    )
    dns_client.set_record([record])


def remove_dns(dns_client: DNSClient, instance: InstanceRecord):
    dns_client.remove_record(instance.name)
