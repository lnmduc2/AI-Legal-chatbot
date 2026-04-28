from dataclasses import dataclass

from app.automation.config import AutomationConfig, load_automation_config
from app.automation.event_store import EventStore, MailStateStore
from app.automation.gmail_client import GmailClient
from app.automation.ingestor import LegalUpdateIngestor
from app.automation.poller import LegalMailPoller
from app.automation.subscriber_store import SubscriberStore


@dataclass
class AutomationServices:
    config: AutomationConfig
    event_store: EventStore
    state_store: MailStateStore
    subscriber_store: SubscriberStore
    gmail_client: GmailClient
    ingestor: LegalUpdateIngestor
    poller: LegalMailPoller


_services: AutomationServices | None = None


def get_automation_services() -> AutomationServices:
    global _services
    if _services is None:
        config = load_automation_config()
        event_store = EventStore(config.event_log_path)
        state_store = MailStateStore(config.mail_state_path)
        subscriber_store = SubscriberStore(
            config.subscriber_path,
            initial_subscribers=config.team_recipients,
        )
        gmail_client = GmailClient(config)
        ingestor = LegalUpdateIngestor(
            config=config,
            event_store=event_store,
            subscriber_store=subscriber_store,
            gmail_client=gmail_client,
        )
        poller = LegalMailPoller(
            config=config,
            gmail_client=gmail_client,
            event_store=event_store,
            state_store=state_store,
            ingestor=ingestor,
        )
        _services = AutomationServices(
            config=config,
            event_store=event_store,
            state_store=state_store,
            subscriber_store=subscriber_store,
            gmail_client=gmail_client,
            ingestor=ingestor,
            poller=poller,
        )
    return _services
