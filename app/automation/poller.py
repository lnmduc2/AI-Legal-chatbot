import asyncio

from app.automation.config import AutomationConfig
from app.automation.event_store import EventStore, MailStateStore
from app.automation.gmail_client import GmailClient
from app.automation.ingestor import LegalUpdateIngestor


class LegalMailPoller:
    def __init__(
        self,
        *,
        config: AutomationConfig,
        gmail_client: GmailClient,
        event_store: EventStore,
        state_store: MailStateStore,
        ingestor: LegalUpdateIngestor,
    ) -> None:
        self.config = config
        self.gmail_client = gmail_client
        self.event_store = event_store
        self.state_store = state_store
        self.ingestor = ingestor
        self._started = False

    def is_ready(self) -> bool:
        return self.config.poller_ready

    async def run_forever(self) -> None:
        if self._started:
            return
        self._started = True

        if not self.is_ready():
            print("Legal automation poller disabled: admin mailbox is not configured.")
            return

        print(
            "Legal automation poller started "
            f"(interval={self.config.poll_interval_seconds}s, inbox={self.config.admin_sender_email})"
        )
        while True:
            try:
                await asyncio.to_thread(self.poll_once)
            except Exception as exc:
                print(f"Legal automation poll failed: {exc}")
            await asyncio.sleep(self.config.poll_interval_seconds)

    def poll_once(self) -> int:
        if not self.is_ready():
            return 0

        last_seen_uid = self.state_store.get_last_seen_uid()
        messages = self.gmail_client.fetch_messages_since_uid(
            account=self.config.admin_account,
            last_seen_uid=last_seen_uid,
            limit=self.config.max_messages_per_poll,
        )
        processed = 0
        max_uid = last_seen_uid

        for message in messages:
            if message.imap_uid is not None:
                max_uid = max(max_uid, message.imap_uid)
            if self.state_store.has_processed(message.message_id) or self.event_store.has_message_id(
                message.message_id
            ):
                if message.imap_uid is not None:
                    self.state_store.mark_processed(message.message_id, message.imap_uid)
                continue

            self.ingestor.ingest_message(message)
            if message.imap_uid is not None:
                self.gmail_client.mark_as_seen(
                    account=self.config.admin_account,
                    uid=message.imap_uid,
                )
                self.state_store.mark_processed(message.message_id, message.imap_uid)
            else:
                self.state_store.mark_processed(message.message_id, None)
            processed += 1

        if max_uid > last_seen_uid:
            self.state_store.update_last_seen_uid(max_uid)
        return processed
