from __future__ import absolute_import

from sentry.plugins.bases.notify import NotifyPlugin

from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config

from .client import PushsaferClient


class PushsaferPlugin(CorePluginMixin, NotifyPlugin):
    slug = 'pushsafer'
    title = 'Pushsafer'
    conf_title = 'Pushsafer'
    conf_key = 'pushsafer'

    def is_configured(self, project):
        return all(self.get_option(key, project) for key in ('privatekey', 'device', 'icon', 'iconcolor', 'sound', 'vibration', 'time2live'))

    def get_config(self, **kwargs):
        privatekey = self.get_option('privatekey', kwargs['project'])
        device = self.get_option('device', kwargs['project'])
        icon = self.get_option('icon', kwargs['project'])
        iconcolor = self.get_option('iconcolor', kwargs['project'])
        sound = self.get_option('sound', kwargs['project'])
        vibration = self.get_option('vibration', kwargs['project'])
        time2live = self.get_option('time2live', kwargs['project'])

        privatekey_field = get_secret_field_config(
            privatekey, 'Your private key. See https://www.pushsafer.com', include_prefix=True
        )
        privatekey_field.update({'name': 'privatekey', 'label': 'Private or Alias Key'})

        device_field = get_secret_field_config(
            device, 'Your Device or Device Group ID. See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        device_field.update({'name': 'device', 'label': 'Device or Device Group ID'})

        icon_field = get_secret_field_config(
            icon, 'Your Icon ID (1-176). See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        icon_field.update({'name': 'icon', 'label': 'Icon'})

        iconcolor_field = get_secret_field_config(
            iconcolor, 'Your Icon Color (Hexadecimal Colorcode, Example: #FF0000). See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        iconcolor_field.update({'name': 'iconcolor', 'label': 'Icon Color'})

        sound_field = get_secret_field_config(
            sound, 'Your Sound ID (0-50). See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        sound_field.update({'name': 'sound', 'label': 'Sound'})

        vibration_field = get_secret_field_config(
            vibration, 'Your Vibration (empty or 1-3). See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        vibration_field.update({'name': 'vibration', 'label': 'Vibration'})

        time2live_field = get_secret_field_config(
            time2live, 'Time to Live (0-43200: Time in minutes, after which message automatically gets purged). See https://www.pushsafer.com/pushapi', include_prefix=True
        )
        time2live_field.update({'name': 'time2live', 'label': 'Time to Live'})

        return [
            privatekey_field, device_field, icon_field, iconcolor_field, sound_field, vibration_field, time2live_field
        ]

    def get_client(self, project):
        return PushsaferClient(
            privatekey=self.get_option('privatekey', project),
        )

    def notify(self, notification):
        event = notification.event
        group = event.group
        project = group.project

        title = '%s: %s' % (project.name, group.title)
        link = group.get_absolute_url()

        message = event.get_legacy_message()[:256]

        tags = event.get_tags()
        if tags:
            message += '\n\nTags: %s' % (', '.join('%s=%s' % (k, v) for (k, v) in tags))

        client = self.get_client(project)
        response = client.send_message(
            {
                'm': message[:1024],
                't': title[:255],
                'd': self.get_option('device', project),
                'i': int(self.get_option('icon', project) or 1),
                'c': self.get_option('iconcolor', project),
                's': int(self.get_option('sound', project)),
                'v': int(self.get_option('vibration', project)),
                'l': int(self.get_option('time2live', project) or 0),
                'u': link,
                'ut': 'Issue Details',
            }
        )
        assert response['status']
