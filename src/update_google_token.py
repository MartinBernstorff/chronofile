from output_services.gcal.syncer import GcalSyncer
from utils.log import log

if __name__ == "__main__":
    log.info("Updating API key")
    GcalSyncer().sync_events_to_calendar(do_not_sync=True)
