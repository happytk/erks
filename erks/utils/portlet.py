from flask import render_template, url_for
from erks.portlets import erks_portlets
import uuid


class Portlet:

    portlet_cls = 'light'

    def __init__(
        self,
        endpoint,
        **kwargs
    ):
        url = url_for(endpoint, **kwargs)
        icon, subject, helper, pclses, clses = erks_portlets.get(endpoint, ('', '', '', '', ''))
        self.caption_helper = helper
        self.caption_subject = subject
        self.url = url
        self.icon_cls = icon
        self.portlet_body_cls = clses
        self.portlet_cls = pclses or self.portlet_cls

    def render(self, display_header=True, direct=False):
        return render_template(
            'portlet.htm.j2',
            display_header=display_header,
            url=self.url,
            uuid=uuid.uuid4(),
            portlet_cls=self.portlet_cls,
            portlet_body_cls=self.portlet_body_cls,
            caption_subject=self.caption_subject,
            caption_helper=self.caption_helper,
            icon_cls=self.icon_cls,
            direct=direct,
        )
