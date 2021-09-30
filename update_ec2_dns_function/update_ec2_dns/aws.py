import boto3


def get_ec2_public_ip(instance_id: str):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    return instance.public_ip_address
