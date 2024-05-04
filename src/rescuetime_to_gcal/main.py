import pandas as pd

from rescuetime_to_gcal.input_services.rescuetime import (
    RecordCategory,
    RecordMetadata,
    Rescuetime,
)
from rescuetime_to_gcal.output_services.gcal.converter import df_to_gcsa_events
from rescuetime_to_gcal.output_services.gcal.syncer import GcalSyncer
from rescuetime_to_gcal.utils.log import log

API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"


if __name__ == "__main__":
    log.info("Starting script")

    rescuetime = Rescuetime(api_key=API_KEY)

    rescuetime_df = rescuetime.pull(
        perspective="interval",
        resolution_time="minute",
        anchor_date=pd.Timestamp.today(),
        lookbehind_distance=pd.Timedelta(days=2),
        titles_to_exclude=["newtab", "raycast"],
        titles_to_keep=None,
        metadata=[
            RecordMetadata(
                title_matcher=["dr.dk"],
                prettified_title="DR",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["citrix"],
                prettified_title="Citrix",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["facebook"],
                prettified_title="Facebook",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["chrome"],
                prettified_title="Chrome",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["github"],
                prettified_title="GitHub",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["hey"],
                prettified_title="Hey",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["linkedin"],
                prettified_title="LinkedIn",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["google.com"],
                prettified_title="Google",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["Notes"],
                prettified_title="Notes",
                category=RecordCategory.PLANNING,
            ),
            RecordMetadata(
                title_matcher=["mail"],
                prettified_title="Mail",
                category=RecordCategory.COMMUNICATING,
            ),
            RecordMetadata(
                title_matcher=["macrumors"],
                prettified_title="Browsing",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["reddit"],
                prettified_title="Reddit",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["slack"],
                prettified_title="Slack",
                category=RecordCategory.COMMUNICATING,
            ),
            RecordMetadata(
                title_matcher=["star realms"],
                prettified_title="Star Realms",
                category=RecordCategory.GAMING,
            ),
            RecordMetadata(
                title_matcher=["stackoverflow"],
                prettified_title="Stack Overflow",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["twitter"],
                prettified_title="Browsing",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["Visual"],
                prettified_title="Visual Studio Code",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["wandb.ai"],
                prettified_title="Programming",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["spotify"],
                prettified_title="Spotify",
                category=RecordCategory.SOUND,
            ),
            RecordMetadata(
                title_matcher=["omnivore"],
                prettified_title="Omnivore",
                category=RecordCategory.READING,
            ),
            RecordMetadata(
                title_matcher=["twitter"],
                prettified_title="Twitter",
                category=RecordCategory.BROWSING,
            ),
            RecordMetadata(
                title_matcher=["Word"],
                prettified_title="Word",
                category=RecordCategory.WRITING,
            ),
            RecordMetadata(
                title_matcher=["Calendar"],
                prettified_title="Calendar",
                category=RecordCategory.PLANNING,
            ),
            RecordMetadata(
                title_matcher=["Obsidian"],
                prettified_title="Obsidian",
                category=RecordCategory.WRITING,
            ),
            RecordMetadata(
                title_matcher=["Docs"],
                prettified_title=None,
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["Alacritty"],
                prettified_title="Alacritty",
                category=RecordCategory.PROGRAMMING,
            ),
            RecordMetadata(
                title_matcher=["Orbstack"],
                prettified_title="Orbstack",
                category=RecordCategory.PROGRAMMING,
            ),
        ],
        min_duration="5 seconds",
        allowed_gap_for_combining=pd.Timedelta("15 minutes"),
    )

    events = df_to_gcsa_events(rescuetime_df)

    calendar = GcalSyncer().sync_events_to_calendar(events)
