from __future__ import absolute_import

import responses

from exam import fixture
from django.core.urlresolvers import reverse
from sentry.models import Rule
from sentry.plugins import Notification
from sentry.testutils import PluginTestCase
from sentry.utils import json
from six.moves.urllib.parse import parse_qs

from sentry_plugins.pushsafer.plugin import PushsaferPlugin

SUCCESS = """{"status":1,"request":"e460545a8b333d0da2f3602aff3133d6"}"""


class PushsaferPluginTest(PluginTestCase):
    @fixture
    def plugin(self):
        return PushsaferPlugin()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'pushsafer'

    def test_entry_point(self):
        self.assertAppInstalled('pushsafer', 'sentry_plugins.pushsafer')
        self.assertPluginInstalled('pushsafer', self.plugin)

    def test_is_configured(self):
        assert self.plugin.is_configured(self.project) is False
        self.plugin.set_option('privatekey', 'XXXXXXXXXXXXXXXXXXXX', self.project)
        assert self.plugin.is_configured(self.project) is True

    @responses.activate
    def test_simple_notification(self):
        responses.add('POST', 'https://api.pushsafer.net/1/messages.json', body=SUCCESS)
        self.plugin.set_option('privatekey', 'XXXXXXXXXXXXXXXXXXXX', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(
            group=group,
            message='Hello world',
            tags={'level': 'warning'},
        )

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)

        request = responses.calls[0].request
        payload = parse_qs(request.body)
        assert payload == {
            'm': ['{}\n\nTags: level=warning'.format(event.get_legacy_message())],
            't': ['Bar: Hello world'],
            'u': ['http://example.com/baz/bar/issues/{}/'.format(group.id)],
            'ut': ['Issue Details'],
            'd': ['a'],
            'k': ['XXXXXXXXXXXXXXXXXXXX'],
        }

    def test_no_secrets(self):
        self.user = self.create_user('foo@example.com')
        self.org = self.create_organization(owner=self.user, name='Rowdy Tiger')
        self.team = self.create_team(organization=self.org, name='Mariachi Band')
        self.project = self.create_project(
            organization=self.org,
            teams=[self.team],
            name='Bengal',
        )
        self.login_as(self.user)
        self.plugin.set_option('privatekey', 'XXXXXXXXXXXXXXXXXXXX', self.project)
        url = reverse(
            'sentry-api-0-project-plugin-details',
            args=[self.org.slug, self.project.slug, 'pushsafer']
        )
        res = self.client.get(url)
        config = json.loads(res.content)['config']
        privatekey_config = [item for item in config if item['name'] == 'privatekey'][0]
        assert privatekey_config.get('type') == 'secret'
        assert privatekey_config.get('value') is None
        assert privatekey_config.get('hasSavedValue') is True
        assert privatekey_config.get('prefix') == ''
