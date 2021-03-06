import logging
import uuid
import pytest

import sdk_auth
import sdk_cmd
import sdk_hosts
import sdk_install
import sdk_marathon
import sdk_security
import sdk_utils

from tests import auth
from tests import config
from tests import test_utils


log = logging.getLogger(__name__)


pytestmark = pytest.mark.skipif(sdk_utils.is_open_dcos(),
                                reason='Feature only supported in DC/OS EE')


@pytest.fixture(scope='module', autouse=True)
def service_account(configure_security):
    """
    Creates service account and yields the name.
    """
    name = config.SERVICE_NAME
    sdk_security.create_service_account(
        service_account_name=name, service_account_secret=name)
    # TODO(mh): Fine grained permissions needs to be addressed in DCOS-16475
    sdk_cmd.run_cli(
        "security org groups add_user superusers {name}".format(name=name))
    yield name
    sdk_security.delete_service_account(
        service_account_name=name, service_account_secret=name)


@pytest.fixture(scope='module', autouse=True)
def kafka_principals():
    fqdn = "{service_name}.{host_suffix}".format(service_name=config.SERVICE_NAME,
                                                 host_suffix=sdk_hosts.AUTOIP_HOST_SUFFIX)

    brokers = [
        "kafka-0-broker",
        "kafka-1-broker",
        "kafka-2-broker",
    ]

    principals = []
    for b in brokers:
        principals.append("kafka/{instance}.{domain}@{realm}".format(
            instance=b,
            domain=fqdn,
            realm=sdk_auth.REALM))

    clients = [
        "client",
        "authorized",
        "unauthorized",
        "super"
    ]
    for c in clients:
        principals.append("{client}@{realm}".format(client=c, realm=sdk_auth.REALM))

    yield principals


@pytest.fixture(scope='module', autouse=True)
def kerberos(configure_security, kafka_principals):
    try:
        principals = []
        principals.extend(kafka_principals)

        kerberos_env = sdk_auth.KerberosEnvironment()
        kerberos_env.add_principals(principals)
        kerberos_env.finalize()

        yield kerberos_env

    finally:
        kerberos_env.cleanup()


@pytest.fixture(scope='module', autouse=True)
def kafka_server(kerberos, service_account):
    """
    A pytest fixture that installs a Kerberized kafka service.

    On teardown, the service is uninstalled.
    """
    service_kerberos_options = {
        "service": {
            "name": config.SERVICE_NAME,
            "service_account": service_account,
            "service_account_secret": service_account,
            "security": {
                "kerberos": {
                    "enabled": True,
                    "kdc": {
                        "hostname": kerberos.get_host(),
                        "port": int(kerberos.get_port())
                    },
                    "realm": sdk_auth.REALM,
                    "keytab_secret": kerberos.get_keytab_path(),
                },
                "transport_encryption": {
                    "enabled": True
                }
            }
        }
    }

    sdk_install.uninstall(config.PACKAGE_NAME, config.SERVICE_NAME)
    try:
        sdk_install.install(
            config.PACKAGE_NAME,
            config.SERVICE_NAME,
            config.DEFAULT_BROKER_COUNT,
            additional_options=service_kerberos_options,
            timeout_seconds=30 * 60)

        yield {**service_kerberos_options, **{"package_name": config.PACKAGE_NAME}}
    finally:
        sdk_install.uninstall(config.PACKAGE_NAME, config.SERVICE_NAME)


@pytest.fixture(scope='module', autouse=True)
def kafka_client(kerberos, kafka_server):

    brokers = sdk_cmd.svc_cli(
        kafka_server["package_name"],
        kafka_server["service"]["name"],
        "endpoint broker-tls", json=True)["dns"]

    try:
        client_id = "kafka-client"
        client = {
            "id": client_id,
            "mem": 512,
            "user": "nobody",
            "container": {
                "type": "MESOS",
                "docker": {
                    "image": "elezar/kafka-client:latest",
                    "forcePullImage": True
                },
                "volumes": [
                    {
                        "containerPath": "/tmp/kafkaconfig/kafka-client.keytab",
                        "secret": "kafka_keytab"
                    }
                ]
            },
            "secrets": {
                "kafka_keytab": {
                    "source": kerberos.get_keytab_path(),

                }
            },
            "networks": [
                {
                    "mode": "host"
                }
            ],
            "env": {
                "JVM_MaxHeapSize": "512",
                "KAFKA_CLIENT_MODE": "test",
                "KAFKA_TOPIC": "securetest",
                "KAFKA_BROKER_LIST": ",".join(brokers)
            }
        }

        sdk_marathon.install_app(client)

        auth.create_tls_artifacts(
            cn="client",
            task=client_id)

        yield {**client, **{"brokers": list(map(lambda x: x.split(':')[0], brokers))}}

    finally:
        sdk_marathon.destroy_app(client_id)


@pytest.mark.dcos_min_version('1.10')
@sdk_utils.dcos_ee_only
@pytest.mark.sanity
def test_client_can_read_and_write(kafka_client, kafka_server, kerberos):
    client_id = kafka_client["id"]

    auth.wait_for_brokers(kafka_client["id"], kafka_client["brokers"])

    topic_name = "authn.test"
    sdk_cmd.svc_cli(kafka_server["package_name"], kafka_server["service"]["name"],
                    "topic create {}".format(topic_name),
                    json=True)

    test_utils.wait_for_topic(kafka_server["package_name"], kafka_server["service"]["name"], topic_name)

    message = str(uuid.uuid4())

    assert write_to_topic("client", client_id, topic_name, message, kerberos)

    assert message in read_from_topic("client", client_id, topic_name, 1, kerberos)


def get_client_properties(cn: str) -> str:
    client_properties_lines = []
    client_properties_lines.extend(auth.get_kerberos_client_properties(ssl_enabled=True))
    client_properties_lines.extend(auth.get_ssl_client_properties(cn, True))

    return client_properties_lines


def write_to_topic(cn: str, task: str, topic: str, message: str, krb5: object) -> bool:

    return auth.write_to_topic(cn, task, topic, message,
                               get_client_properties(cn),
                               environment=auth.setup_krb5_env(cn, task, krb5))


def read_from_topic(cn: str, task: str, topic: str, messages: int, krb5: object) -> str:

    return auth.read_from_topic(cn, task, topic, messages,
                                get_client_properties(cn),
                                environment=auth.setup_krb5_env(cn, task, krb5))
